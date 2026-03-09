"""Tests for configuration management."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest
import yaml

from qa_agent.config import AIConfig, Config, OutputConfig


class TestAIConfig:
    """Tests for AI configuration."""

    def test_valid_kiro_config(self) -> None:
        """Test creating a valid Kiro config."""
        config = AIConfig(
            provider="kiro",
            model="auto",
            temperature=0.7,
            max_tokens=2000,
        )
        assert config.provider == "kiro"
        assert config.model == "auto"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
        assert config.api_key is None

    def test_valid_openai_config(self) -> None:
        """Test creating a valid OpenAI config."""
        config = AIConfig(
            provider="openai",
            api_key="sk-test123",
            model="gpt-4",
            temperature=0.7,
            max_tokens=2000,
        )
        assert config.provider == "openai"
        assert config.api_key == "sk-test123"
        assert config.model == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000

    def test_default_values(self) -> None:
        """Test default values for AI config."""
        config = AIConfig()
        assert config.provider == "kiro"
        assert config.model == "auto"
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
        assert config.api_key is None

    def test_openai_without_api_key(self) -> None:
        """Test that OpenAI provider without API key raises validation error."""
        with pytest.raises(ValueError, match="OpenAI provider requires an API key"):
            AIConfig(provider="openai")

    def test_kiro_without_api_key(self) -> None:
        """Test that Kiro provider works without API key."""
        config = AIConfig(provider="kiro")
        assert config.api_key is None

    def test_empty_api_key_treated_as_none(self) -> None:
        """Test that empty API key is treated as None."""
        config = AIConfig(provider="kiro", api_key="")
        assert config.api_key is None

    def test_whitespace_api_key_treated_as_none(self) -> None:
        """Test that whitespace-only API key is treated as None."""
        config = AIConfig(provider="kiro", api_key="   ")
        assert config.api_key is None

    def test_api_key_stripped(self) -> None:
        """Test that API key is stripped of whitespace."""
        config = AIConfig(provider="openai", api_key="  sk-test123  ")
        assert config.api_key == "sk-test123"

    def test_temperature_bounds(self) -> None:
        """Test temperature validation bounds."""
        # Valid temperatures
        AIConfig(temperature=0.0)
        AIConfig(temperature=1.0)
        AIConfig(temperature=2.0)

        # Invalid temperatures
        with pytest.raises(ValueError):
            AIConfig(temperature=-0.1)
        with pytest.raises(ValueError):
            AIConfig(temperature=2.1)

    def test_max_tokens_bounds(self) -> None:
        """Test max_tokens validation bounds."""
        # Valid max_tokens
        AIConfig(max_tokens=1)
        AIConfig(max_tokens=128000)

        # Invalid max_tokens
        with pytest.raises(ValueError):
            AIConfig(max_tokens=0)
        with pytest.raises(ValueError):
            AIConfig(max_tokens=-1)
        with pytest.raises(ValueError):
            AIConfig(max_tokens=128001)

    def test_kiro_model_options(self) -> None:
        """Test various Kiro model options."""
        for model in ["auto", "fast", "balanced", "quality"]:
            config = AIConfig(provider="kiro", model=model)
            assert config.model == model


class TestOutputConfig:
    """Tests for output configuration."""

    def test_valid_config(self) -> None:
        """Test creating a valid output config."""
        config = OutputConfig(directory="output")
        assert config.directory == Path("output")

    def test_default_directory(self) -> None:
        """Test default output directory."""
        config = OutputConfig()
        assert config.directory == Path("output")

    def test_path_conversion(self) -> None:
        """Test that string is converted to Path."""
        config = OutputConfig(directory="test/path")
        assert isinstance(config.directory, Path)
        assert config.directory == Path("test/path")

    def test_path_object(self) -> None:
        """Test that Path object is accepted."""
        config = OutputConfig(directory=Path("test/path"))
        assert isinstance(config.directory, Path)
        assert config.directory == Path("test/path")


class TestConfig:
    """Tests for main configuration."""

    def test_valid_kiro_config(self) -> None:
        """Test creating a valid Kiro config."""
        config = Config(
            ai=AIConfig(provider="kiro"),
            output=OutputConfig(directory="output"),
        )
        assert config.ai.provider == "kiro"
        assert config.output.directory == Path("output")

    def test_valid_openai_config(self) -> None:
        """Test creating a valid OpenAI config."""
        config = Config(
            ai=AIConfig(provider="openai", api_key="sk-test123"),
            output=OutputConfig(directory="output"),
        )
        assert config.ai.provider == "openai"
        assert config.ai.api_key == "sk-test123"
        assert config.output.directory == Path("output")

    def test_default_config(self) -> None:
        """Test creating config with defaults."""
        config = Config()
        assert config.ai.provider == "kiro"
        assert config.ai.model == "auto"
        assert config.output.directory == Path("output")

    def test_from_dict_kiro(self) -> None:
        """Test loading Kiro config from dictionary."""
        config_dict = {
            "ai": {
                "provider": "kiro",
                "model": "balanced",
                "temperature": 0.8,
                "max_tokens": 3000,
            },
            "output": {"directory": "test_output"},
        }
        config = Config.from_dict(config_dict)
        assert config.ai.provider == "kiro"
        assert config.ai.model == "balanced"
        assert config.ai.temperature == 0.8
        assert config.ai.max_tokens == 3000
        assert config.output.directory == Path("test_output")

    def test_from_dict_openai(self) -> None:
        """Test loading OpenAI config from dictionary."""
        config_dict = {
            "ai": {
                "provider": "openai",
                "api_key": "sk-test123",
                "model": "gpt-4",
                "temperature": 0.8,
                "max_tokens": 3000,
            },
            "output": {"directory": "test_output"},
        }
        config = Config.from_dict(config_dict)
        assert config.ai.provider == "openai"
        assert config.ai.api_key == "sk-test123"
        assert config.ai.model == "gpt-4"
        assert config.ai.temperature == 0.8
        assert config.ai.max_tokens == 3000
        assert config.output.directory == Path("test_output")

    def test_from_dict_minimal(self) -> None:
        """Test loading config from minimal dictionary."""
        config_dict = {}
        config = Config.from_dict(config_dict)
        assert config.ai.provider == "kiro"
        assert config.ai.model == "auto"
        assert config.output.directory == Path("output")

    def test_from_dict_legacy_openai_key(self) -> None:
        """Test backward compatibility with legacy 'openai' key."""
        config_dict = {
            "openai": {
                "api_key": "sk-test123",
                "model": "gpt-4",
            }
        }
        config = Config.from_dict(config_dict)
        assert config.ai.provider == "openai"
        assert config.ai.api_key == "sk-test123"
        assert config.ai.model == "gpt-4"

    def test_from_dict_invalid(self) -> None:
        """Test that invalid dictionary raises error."""
        with pytest.raises(ValueError, match="Invalid configuration dictionary"):
            Config.from_dict({"ai": {"provider": "openai"}})  # Missing API key

    def test_from_yaml_valid_kiro(self) -> None:
        """Test loading Kiro config from valid YAML file."""
        config_data = {
            "ai": {
                "provider": "kiro",
                "model": "balanced",
                "temperature": 0.8,
                "max_tokens": 3000,
            },
            "output": {"directory": "test_output"},
        }

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = Config.from_yaml(temp_path)
            assert config.ai.provider == "kiro"
            assert config.ai.model == "balanced"
            assert config.ai.temperature == 0.8
            assert config.ai.max_tokens == 3000
            assert config.output.directory == Path("test_output")
        finally:
            os.unlink(temp_path)

    def test_from_yaml_valid_openai(self) -> None:
        """Test loading OpenAI config from valid YAML file."""
        config_data = {
            "ai": {
                "provider": "openai",
                "api_key": "sk-test123",
                "model": "gpt-4",
                "temperature": 0.8,
                "max_tokens": 3000,
            },
            "output": {"directory": "test_output"},
        }

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = Config.from_yaml(temp_path)
            assert config.ai.provider == "openai"
            assert config.ai.api_key == "sk-test123"
            assert config.ai.model == "gpt-4"
            assert config.ai.temperature == 0.8
            assert config.ai.max_tokens == 3000
            assert config.output.directory == Path("test_output")
        finally:
            os.unlink(temp_path)

    def test_from_yaml_file_not_found(self) -> None:
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            Config.from_yaml("nonexistent.yaml")

    def test_from_yaml_not_a_file(self) -> None:
        """Test that directory path raises ValueError."""
        with TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="Configuration path is not a file"):
                Config.from_yaml(tmpdir)

    def test_from_yaml_invalid_yaml(self) -> None:
        """Test that invalid YAML raises ValueError."""
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Failed to parse YAML configuration file"):
                Config.from_yaml(temp_path)
        finally:
            os.unlink(temp_path)

    def test_from_yaml_empty_file(self) -> None:
        """Test that empty YAML file raises ValueError."""
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Configuration file is empty"):
                Config.from_yaml(temp_path)
        finally:
            os.unlink(temp_path)

    def test_from_yaml_not_dict(self) -> None:
        """Test that non-dict YAML raises ValueError."""
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("- item1\n- item2\n")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Configuration file must contain a YAML dictionary"):
                Config.from_yaml(temp_path)
        finally:
            os.unlink(temp_path)

    def test_from_yaml_invalid_config(self) -> None:
        """Test that invalid config structure raises ValueError."""
        config_data = {"ai": {"provider": "openai"}}  # Missing API key for OpenAI

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid configuration in file"):
                Config.from_yaml(temp_path)
        finally:
            os.unlink(temp_path)

    def test_from_yaml_env_var_substitution(self) -> None:
        """Test environment variable substitution for API key."""
        os.environ["TEST_OPENAI_KEY"] = "sk-from-env"
        config_data = {"ai": {"provider": "openai", "api_key": "${TEST_OPENAI_KEY}"}}

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = Config.from_yaml(temp_path)
            assert config.ai.api_key == "sk-from-env"
        finally:
            os.unlink(temp_path)
            del os.environ["TEST_OPENAI_KEY"]

    def test_from_yaml_env_var_not_found(self) -> None:
        """Test that missing environment variable raises error."""
        config_data = {"ai": {"provider": "openai", "api_key": "${NONEXISTENT_VAR}"}}

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Environment variable 'NONEXISTENT_VAR' not found"):
                Config.from_yaml(temp_path)
        finally:
            os.unlink(temp_path)

    def test_ensure_output_directory(self) -> None:
        """Test that output directory is created."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output" / "nested"
            config = Config(
                ai=AIConfig(),
                output=OutputConfig(directory=output_path),
            )

            assert not output_path.exists()
            config.ensure_output_directory()
            assert output_path.exists()
            assert output_path.is_dir()

    def test_ensure_output_directory_already_exists(self) -> None:
        """Test that existing directory doesn't raise error."""
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir)
            config = Config(
                ai=AIConfig(),
                output=OutputConfig(directory=output_path),
            )

            config.ensure_output_directory()  # Should not raise
            assert output_path.exists()
