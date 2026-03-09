"""Configuration management for the QA Agent system."""

import os
from pathlib import Path
from typing import Any, Dict, Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class AIConfig(BaseModel):
    """AI model configuration supporting both Kiro and OpenAI."""

    provider: Literal["kiro", "openai"] = Field(
        default="kiro", description="AI provider to use (kiro or openai)"
    )
    api_key: Optional[str] = Field(
        default=None, description="API key (required only for OpenAI provider)"
    )
    model: str = Field(
        default="auto",
        description="Model to use. For Kiro: 'auto', 'fast', 'balanced', 'quality'. For OpenAI: model name like 'gpt-4'",
    )
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Temperature for generation"
    )
    max_tokens: int = Field(
        default=2000, gt=0, le=128000, description="Maximum tokens for generation"
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate API key based on provider."""
        if v is not None:
            v = v.strip()
            if not v:
                return None
        return v

    def model_post_init(self, __context: Any) -> None:
        """Validate configuration after initialization."""
        if self.provider == "openai" and not self.api_key:
            raise ValueError(
                "OpenAI provider requires an API key. "
                "Please provide 'api_key' in the configuration or set the OPENAI_API_KEY environment variable."
            )


class OutputConfig(BaseModel):
    """Output directory configuration."""

    directory: Path = Field(
        default=Path("output"), description="Directory for generated artifacts"
    )

    @field_validator("directory", mode="before")
    @classmethod
    def validate_directory(cls, v: Any) -> Path:
        """Convert string to Path and validate."""
        if isinstance(v, str):
            v = Path(v)
        if not isinstance(v, Path):
            raise ValueError(f"Output directory must be a string or Path, got {type(v)}")
        return v


class Config(BaseModel):
    """Main configuration for the QA Agent system."""

    ai: AIConfig = Field(default_factory=AIConfig, description="AI model configuration")
    output: OutputConfig = Field(
        default_factory=OutputConfig, description="Output configuration"
    )

    @classmethod
    def from_yaml(cls, config_path: str | Path) -> "Config":
        """
        Load configuration from a YAML file.

        Args:
            config_path: Path to the YAML configuration file

        Returns:
            Config instance loaded from the file

        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            ValueError: If the configuration file is invalid or malformed
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}\n"
                f"Please create a configuration file at this location."
            )

        if not config_path.is_file():
            raise ValueError(
                f"Configuration path is not a file: {config_path}\n"
                f"Please provide a valid YAML configuration file."
            )

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(
                f"Failed to parse YAML configuration file: {config_path}\n"
                f"Error: {str(e)}\n"
                f"Please ensure the file contains valid YAML syntax."
            ) from e
        except Exception as e:
            raise ValueError(
                f"Failed to read configuration file: {config_path}\n"
                f"Error: {str(e)}"
            ) from e

        if config_data is None:
            raise ValueError(
                f"Configuration file is empty: {config_path}\n"
                f"Please provide a valid configuration."
            )

        if not isinstance(config_data, dict):
            raise ValueError(
                f"Configuration file must contain a YAML dictionary, got {type(config_data)}\n"
                f"Please ensure the file contains valid configuration structure."
            )

        # Support environment variable substitution for API key
        if "ai" in config_data and isinstance(config_data["ai"], dict):
            api_key = config_data["ai"].get("api_key", "")
            if api_key and api_key.startswith("${") and api_key.endswith("}"):
                env_var = api_key[2:-1]
                env_value = os.getenv(env_var)
                if env_value:
                    config_data["ai"]["api_key"] = env_value
                else:
                    raise ValueError(
                        f"Environment variable '{env_var}' not found\n"
                        f"Please set the environment variable or provide the API key directly."
                    )
        
        # Support legacy 'openai' key for backward compatibility
        if "openai" in config_data and "ai" not in config_data:
            config_data["ai"] = config_data.pop("openai")
            if "ai" in config_data and isinstance(config_data["ai"], dict):
                config_data["ai"]["provider"] = "openai"

        try:
            return cls(**config_data)
        except Exception as e:
            raise ValueError(
                f"Invalid configuration in file: {config_path}\n"
                f"Error: {str(e)}\n"
                f"Please check the configuration structure and values."
            ) from e

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """
        Load configuration from a dictionary.

        Args:
            config_dict: Dictionary containing configuration

        Returns:
            Config instance

        Raises:
            ValueError: If the configuration is invalid
        """
        # Support legacy 'openai' key for backward compatibility
        if "openai" in config_dict and "ai" not in config_dict:
            config_dict = config_dict.copy()
            config_dict["ai"] = config_dict.pop("openai")
            if "ai" in config_dict and isinstance(config_dict["ai"], dict):
                config_dict["ai"]["provider"] = "openai"
        
        try:
            return cls(**config_dict)
        except Exception as e:
            raise ValueError(
                f"Invalid configuration dictionary\n"
                f"Error: {str(e)}\n"
                f"Please check the configuration structure and values."
            ) from e

    def ensure_output_directory(self) -> None:
        """
        Ensure the output directory exists, creating it if necessary.

        Raises:
            OSError: If the directory cannot be created
        """
        try:
            self.output.directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise OSError(
                f"Failed to create output directory: {self.output.directory}\n"
                f"Error: {str(e)}"
            ) from e
