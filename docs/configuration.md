# Configuration Guide

The QA Agent supports flexible configuration through YAML files, supporting both Kiro's built-in AI models and OpenAI's API.

## AI Provider Options

### Kiro Provider (Recommended)

Kiro is the recommended provider as it uses built-in AI models without requiring an API key.

**Configuration:**

```yaml
ai:
  provider: "kiro"
  model: "auto"  # Options: auto, fast, balanced, quality
  temperature: 0.7
  max_tokens: 2000
```

**Model Options:**
- `auto`: Automatically selects the best model for each task (recommended)
- `fast`: Optimized for speed, suitable for simple tasks
- `balanced`: Balance between speed and quality
- `quality`: Best quality output, may be slower

**Quick Start:**

```bash
cp config.kiro.yaml config.yaml
```

### OpenAI Provider

Use OpenAI's API for AI model access. Requires an API key.

**Configuration:**

```yaml
ai:
  provider: "openai"
  api_key: "${OPENAI_API_KEY}"  # Environment variable substitution
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 2000
```

**Quick Start:**

```bash
cp config.example.yaml config.yaml
# Edit config.yaml and add your OpenAI API key
```

## Configuration Parameters

### AI Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `provider` | string | `"kiro"` | AI provider: `"kiro"` or `"openai"` |
| `api_key` | string | `null` | API key (required only for OpenAI) |
| `model` | string | `"auto"` | Model to use (provider-specific) |
| `temperature` | float | `0.7` | Generation temperature (0.0-2.0) |
| `max_tokens` | int | `2000` | Maximum tokens per generation |

### Output Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `directory` | string | `"output"` | Directory for generated artifacts |

## Environment Variable Substitution

You can use environment variables in your configuration:

```yaml
ai:
  provider: "openai"
  api_key: "${OPENAI_API_KEY}"
```

Set the environment variable:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Loading Configuration

### From YAML File

```python
from qa_agent.config import Config

config = Config.from_yaml("config.yaml")
```

### From Dictionary

```python
from qa_agent.config import Config

config_dict = {
    "ai": {
        "provider": "kiro",
        "model": "balanced",
    },
    "output": {
        "directory": "my_output"
    }
}

config = Config.from_dict(config_dict)
```

### Programmatically

```python
from qa_agent.config import Config, AIConfig, OutputConfig

config = Config(
    ai=AIConfig(
        provider="kiro",
        model="quality",
        temperature=0.5,
    ),
    output=OutputConfig(directory="output")
)
```

## Validation

The configuration system validates all parameters:

- **Provider validation**: Must be `"kiro"` or `"openai"`
- **API key validation**: Required for OpenAI provider
- **Temperature bounds**: Must be between 0.0 and 2.0
- **Max tokens bounds**: Must be between 1 and 128,000
- **File validation**: YAML files must be valid and contain proper structure

Descriptive error messages are provided for all validation failures.

## Examples

See `examples/config_usage.py` for complete usage examples.

## Backward Compatibility

The configuration system supports legacy `openai` key for backward compatibility:

```yaml
# Legacy format (still supported)
openai:
  api_key: "sk-..."
  model: "gpt-4"

# Automatically converted to:
ai:
  provider: "openai"
  api_key: "sk-..."
  model: "gpt-4"
```
