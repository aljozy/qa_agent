"""Example demonstrating configuration usage."""

from qa_agent.config import Config

# Example 1: Load Kiro configuration from YAML
print("Example 1: Loading Kiro configuration")
kiro_config = Config.from_yaml("config.kiro.yaml")
print(f"Provider: {kiro_config.ai.provider}")
print(f"Model: {kiro_config.ai.model}")
print(f"Temperature: {kiro_config.ai.temperature}")
print(f"Output directory: {kiro_config.output.directory}")
print()

# Example 2: Create configuration programmatically
print("Example 2: Creating configuration programmatically")
from qa_agent.config import AIConfig, OutputConfig

config = Config(
    ai=AIConfig(
        provider="kiro",
        model="balanced",
        temperature=0.8,
        max_tokens=3000,
    ),
    output=OutputConfig(directory="my_output"),
)
print(f"Provider: {config.ai.provider}")
print(f"Model: {config.ai.model}")
print()

# Example 3: Load from dictionary
print("Example 3: Loading from dictionary")
config_dict = {
    "ai": {
        "provider": "kiro",
        "model": "quality",
        "temperature": 0.5,
    },
    "output": {"directory": "test_output"},
}
config = Config.from_dict(config_dict)
print(f"Provider: {config.ai.provider}")
print(f"Model: {config.ai.model}")
print()

# Example 4: Ensure output directory exists
print("Example 4: Creating output directory")
config.ensure_output_directory()
print(f"Output directory created: {config.output.directory}")
