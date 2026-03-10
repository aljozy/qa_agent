# AI-Powered QA Agent

An intelligent test automation system that analyzes software requirements from multiple sources and automatically generates comprehensive testing artifacts using AI agent architecture, Retrieval Augmented Generation (RAG), and Model Context Protocol (MCP) servers.

## Features

- **Multi-Format Requirement Ingestion**: Parse requirements from Markdown PRDs (MVP), with future support for Jira user stories, OpenAPI/Swagger specs, and database schemas
- **Intelligent Test Generation**: Generate manual test cases with positive, negative, and edge case scenarios
- **Requirement Traceability**: Automatic RTM (Requirement Traceability Matrix) generation with coverage metrics
- **AI-Powered**: Uses Kiro's built-in AI models (default) or OpenAI for intelligent test case generation
- **Modular Architecture**: Plugin-based system for parsers and generators
- **CLI Interface**: Easy-to-use command-line interface with progress tracking

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Configuration Guide](#configuration-guide)
- [Architecture Overview](#architecture-overview)
- [CLI Commands](#cli-commands)
- [Development](#development)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

- Python 3.10 or higher
- pip or poetry for package management

### Install from Source

```bash
# Clone the repository
git clone <repository-url>
cd qa_agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks (for development)
pre-commit install
```

### Verify Installation

```bash
# Check version
qa-agent --version

# View help
qa-agent --help
```

## Quick Start

Here's a simple workflow to get started:

```bash
# 1. Create a configuration file (using Kiro - no API key needed)
cp config.kiro.yaml config.yaml

# 2. Run the full pipeline on a requirements document
qa-agent run examples/sample_requirements.md --output output

# That's it! Check the output directory for:
# - output/requirements/sample_requirements.json (parsed requirements)
# - output/tests/sample_requirements_tests.json (generated test cases)
# - output/rtm/rtm.csv (requirement traceability matrix)
```

## Usage Examples

### Example 1: Parse Requirements Only

Parse a Markdown requirements document and save structured requirements:

```bash
qa-agent parse examples/sample_requirements.md \
  --output output/requirements
```

**Output**: `output/requirements/sample_requirements.json`

### Example 2: Generate Test Cases

Generate test cases from parsed requirements:

```bash
qa-agent generate output/requirements/sample_requirements.json \
  --output output/tests \
  --config config.yaml
```

**Options**:
- `--positive/--no-positive`: Include/exclude positive test scenarios (default: true)
- `--negative/--no-negative`: Include/exclude negative test scenarios (default: true)
- `--edge-cases/--no-edge-cases`: Include/exclude edge case scenarios (default: true)
- `--provider kiro|openai`: Override AI provider from config

**Output**: `output/tests/sample_requirements_tests.json`

### Example 3: Generate RTM

Create a Requirement Traceability Matrix:

```bash
qa-agent rtm \
  output/requirements/sample_requirements.json \
  output/tests/sample_requirements_tests.json \
  --output output/rtm
```

**Output**: `output/rtm/rtm.csv` with coverage metrics

### Example 4: Full Pipeline

Run the complete workflow in one command:

```bash
qa-agent run examples/sample_requirements.md \
  --output output \
  --config config.yaml \
  --provider kiro
```

This command:
1. Parses the requirements document
2. Generates test cases (positive, negative, edge cases)
3. Creates an RTM with coverage metrics

## Configuration Guide

### Configuration File Structure

The QA Agent uses YAML configuration files. Here's a complete example:

```yaml
# AI Model Configuration
ai:
  # Provider: "kiro" (default, uses Kiro's built-in models) or "openai"
  provider: "kiro"
  
  # Model selection:
  # For Kiro: "auto" (default), "fast", "balanced", "quality"
  # For OpenAI: "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"
  model: "auto"
  
  # Temperature (0.0-2.0): Lower = deterministic, Higher = creative
  temperature: 0.7
  
  # Maximum tokens per generation
  max_tokens: 2000
  
  # API key (only for OpenAI provider)
  # api_key: "${OPENAI_API_KEY}"  # Use environment variable
  # api_key: "sk-..."              # Or provide directly

# Output Configuration
output:
  # Base directory for all generated artifacts
  directory: "output"
```

### Using Kiro Models (Recommended)

Kiro's built-in models require no API key and work out of the box:

```yaml
ai:
  provider: "kiro"
  model: "auto"  # Let Kiro choose the best model
  temperature: 0.7
  max_tokens: 2000
```

**Model Options**:
- `auto`: Automatically selects the best model for each task (recommended)
- `fast`: Faster responses, good for simple requirements
- `balanced`: Balance between speed and quality
- `quality`: Best quality output, slower responses

### Using OpenAI Models

For OpenAI, you need an API key:

```yaml
ai:
  provider: "openai"
  api_key: "${OPENAI_API_KEY}"  # Reference environment variable
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 2000
```

Set your API key as an environment variable:

```bash
export OPENAI_API_KEY="sk-..."
```

Or create a `.env` file:

```bash
cp .env.example .env
# Edit .env and add: OPENAI_API_KEY=sk-...
```

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ai.provider` | string | `"kiro"` | AI provider: `kiro` or `openai` |
| `ai.model` | string | `"auto"` | Model name (provider-specific) |
| `ai.temperature` | float | `0.7` | Randomness (0.0-2.0) |
| `ai.max_tokens` | int | `2000` | Maximum tokens per generation |
| `ai.api_key` | string | - | API key (OpenAI only) |
| `output.directory` | string | `"output"` | Base output directory |

## Architecture Overview

The QA Agent follows a modular, plugin-based architecture designed for extensibility and maintainability.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Interface                         │
│                    (User Entry Point)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                    Core Components                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Parsers    │  │  Generators  │  │   Analysis   │     │
│  │  (Markdown)  │  │  (Manual     │  │     (RTM)    │     │
│  │              │  │   Tests)     │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                    Support Services                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  LLM Client  │  │    Config    │  │   Storage    │     │
│  │ (Kiro/OpenAI)│  │  Management  │  │  (File I/O)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Parsers
- **MarkdownParser**: Parses structured Markdown documents into requirement objects
- **Plugin Architecture**: Extensible design for adding new parsers (Jira, OpenAPI, SQL)
- **Validation**: Ensures requirements have required fields and proper structure

#### 2. Generators
- **ManualTestGenerator**: Creates manual test cases using AI
- **Batch Processing**: Efficiently processes multiple requirements with progress tracking
- **Scenario Types**: Generates positive, negative, and edge case test scenarios

#### 3. Analysis
- **RTMGenerator**: Creates requirement traceability matrices
- **Coverage Calculation**: Computes coverage percentages and identifies gaps
- **Export Formats**: Outputs RTM in CSV format for easy viewing

#### 4. LLM Client
- **Multi-Provider Support**: Works with Kiro (default) or OpenAI
- **Async Operations**: Non-blocking API calls for better performance
- **Error Handling**: Robust error handling with retries and fallbacks

#### 5. Storage
- **FileStorage**: Manages reading/writing of JSON artifacts
- **Structured Output**: Organizes artifacts in configurable directory structures

### Data Flow

```
Markdown Document
    │
    ├─> MarkdownParser
    │       │
    │       └─> Requirement Objects (JSON)
    │
    ├─> ManualTestGenerator
    │       │
    │       ├─> LLM Client (Kiro/OpenAI)
    │       │
    │       └─> Test Artifact Objects (JSON)
    │
    └─> RTMGenerator
            │
            └─> RTM Entries (CSV)
```

### Key Design Principles

1. **Modularity**: Components are loosely coupled and independently testable
2. **Extensibility**: Plugin architecture allows easy addition of new parsers/generators
3. **Configuration-Driven**: Behavior controlled through YAML configuration
4. **Error Resilience**: Comprehensive error handling and logging
5. **Type Safety**: Pydantic models ensure data validation and type safety

## CLI Commands

### `qa-agent --version`

Display the version of QA Agent.

```bash
qa-agent --version
```

### `qa-agent parse`

Parse a Markdown requirements document and save structured requirements.

**Usage**:
```bash
qa-agent parse INPUT_FILE [OPTIONS]
```

**Arguments**:
- `INPUT_FILE`: Path to the Markdown requirements file

**Options**:
- `--output, -o PATH`: Output directory (default: `output/requirements`)
- `--config, -c PATH`: Configuration file path
- `--log-level, -l LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `--json-logs`: Output logs in JSON format for CI/CD

**Example**:
```bash
qa-agent parse requirements.md --output parsed --log-level DEBUG
```

### `qa-agent generate`

Generate test cases from parsed requirements.

**Usage**:
```bash
qa-agent generate REQUIREMENTS_FILE [OPTIONS]
```

**Arguments**:
- `REQUIREMENTS_FILE`: Path to the requirements JSON file

**Options**:
- `--output, -o PATH`: Output directory (default: `output/tests`)
- `--config, -c PATH`: Configuration file path
- `--provider, -p PROVIDER`: Override AI provider (`kiro` or `openai`)
- `--positive/--no-positive`: Generate positive scenarios (default: true)
- `--negative/--no-negative`: Generate negative scenarios (default: true)
- `--edge-cases/--no-edge-cases`: Generate edge cases (default: true)

**Example**:
```bash
qa-agent generate requirements.json \
  --output tests \
  --provider kiro \
  --no-edge-cases
```

### `qa-agent rtm`

Generate a Requirement Traceability Matrix.

**Usage**:
```bash
qa-agent rtm REQUIREMENTS_FILE TESTS_FILE [OPTIONS]
```

**Arguments**:
- `REQUIREMENTS_FILE`: Path to the requirements JSON file
- `TESTS_FILE`: Path to the test artifacts JSON file

**Options**:
- `--output, -o PATH`: Output directory (default: `output/rtm`)
- `--config, -c PATH`: Configuration file path

**Example**:
```bash
qa-agent rtm requirements.json tests.json --output rtm
```

### `qa-agent run`

Run the full pipeline: parse → generate → rtm.

**Usage**:
```bash
qa-agent run INPUT_FILE [OPTIONS]
```

**Arguments**:
- `INPUT_FILE`: Path to the Markdown requirements file

**Options**:
- `--output, -o PATH`: Base output directory (default: `output`)
- `--config, -c PATH`: Configuration file path
- `--provider, -p PROVIDER`: Override AI provider (`kiro` or `openai`)

**Example**:
```bash
qa-agent run requirements.md --output results --provider kiro
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=qa_agent --cov-report=html

# Run specific test file
pytest tests/test_manual_test_generator.py

# Run with verbose output
pytest -v

# Run tests matching a pattern
pytest -k "test_parse"
```

### Code Quality

```bash
# Format code with Black
black qa_agent tests

# Lint with Ruff
ruff check qa_agent tests

# Type check with mypy
mypy qa_agent

# Run all quality checks
make lint  # If Makefile is configured
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Adding New Parsers

To add a new parser (e.g., for Jira):

1. Create a new parser class in `qa_agent/parsers/`:

```python
from qa_agent.parsers.base import BaseParser
from qa_agent.models.base import Requirement

class JiraParser(BaseParser):
    """Parser for Jira user stories."""
    
    def parse_file(self, file_path: Path) -> List[Requirement]:
        # Implementation
        pass
```

2. Register the parser in `qa_agent/parsers/__init__.py`

3. Add tests in `tests/test_jira_parser.py`

4. Update documentation

## Project Structure

```
qa_agent/
├── qa_agent/                   # Main package
│   ├── __init__.py
│   ├── cli.py                  # CLI interface (Typer)
│   ├── analysis/               # Analysis components
│   │   ├── __init__.py
│   │   └── rtm_generator.py    # RTM generation
│   ├── config/                 # Configuration management
│   │   ├── __init__.py
│   │   └── loader.py           # Config loading
│   ├── core/                   # Core utilities
│   │   ├── __init__.py
│   │   ├── exceptions.py       # Custom exceptions
│   │   ├── logging_config.py   # Logging setup
│   │   └── orchestrator.py     # Workflow orchestration
│   ├── generators/             # Test generators
│   │   ├── __init__.py
│   │   ├── base.py             # Base generator interface
│   │   └── manual_test_generator.py  # Manual test generation
│   ├── llm/                    # LLM integration
│   │   ├── __init__.py
│   │   └── client.py           # LLM client (Kiro/OpenAI)
│   ├── models/                 # Data models
│   │   ├── __init__.py
│   │   └── base.py             # Pydantic models
│   ├── parsers/                # Requirement parsers
│   │   ├── __init__.py
│   │   ├── base.py             # Base parser interface
│   │   ├── markdown_parser.py  # Markdown parser
│   │   ├── jira_parser.py      # Jira parser (future)
│   │   └── openapi_parser.py   # OpenAPI parser (future)
│   └── storage/                # Storage layer
│       ├── __init__.py
│       └── file_storage.py     # File I/O operations
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_cli.py
│   ├── test_manual_test_generator.py
│   ├── test_markdown_parser.py
│   ├── test_rtm_generator.py
│   └── ...
├── docs/                       # Documentation
│   ├── cli_usage.md
│   ├── configuration.md
│   └── ...
├── examples/                   # Example files
│   ├── sample_requirements.md
│   ├── config_usage.py
│   └── ...
├── config.example.yaml         # Example configuration
├── config.kiro.yaml            # Kiro configuration
├── .env.example                # Environment template
├── pyproject.toml              # Project metadata
├── requirements.txt            # Dependencies
├── requirements-dev.txt        # Dev dependencies
└── README.md                   # This file
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository** and create a feature branch
2. **Write tests** for new functionality
3. **Ensure all tests pass**: `pytest`
4. **Format code**: `black qa_agent tests`
5. **Lint code**: `ruff check qa_agent tests`
6. **Update documentation** as needed
7. **Submit a pull request** with a clear description

### Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/qa-agent.git
cd qa-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## License

MIT License - see LICENSE file for details.

## Support

For issues, questions, or contributions:
- **Issues**: Open an issue on GitHub
- **Documentation**: See the `docs/` directory
- **Examples**: Check the `examples/` directory

## Roadmap

### Current (MVP)
- ✅ Markdown requirement parsing
- ✅ Manual test case generation
- ✅ RTM generation
- ✅ Kiro and OpenAI support
- ✅ CLI interface

### Future Enhancements
- 🔄 Jira user story parser
- 🔄 OpenAPI/Swagger parser
- 🔄 Automation test skeleton generation
- 🔄 RAG-powered context retrieval
- 🔄 Vector store integration
- 🔄 MCP server integrations
- 🔄 Coverage gap analysis
- 🔄 UI workflow generation
