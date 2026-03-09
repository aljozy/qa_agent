# AI-Powered QA Agent

An intelligent test automation system that analyzes software requirements from multiple sources and automatically generates comprehensive testing artifacts using AI agent architecture, Retrieval Augmented Generation (RAG), and Model Context Protocol (MCP) servers.

## Features

- **Multi-Format Requirement Ingestion**: Parse requirements from Jira user stories, OpenAPI/Swagger specs, Markdown PRDs, and database schemas
- **Intelligent Test Generation**: Generate manual test cases, automation test skeletons, API validation checks, UI workflows, and database validation queries
- **RAG-Powered Context**: Use semantic search and retrieval for context-aware test generation
- **Requirement Traceability**: Automatic RTM (Requirement Traceability Matrix) generation
- **Coverage Analysis**: Identify gaps in test coverage and suggest additional scenarios
- **MCP Integration**: Connect to external tools via Model Context Protocol servers
- **Modular Architecture**: Plugin-based system for parsers and generators

## Installation

### Prerequisites

- Python 3.10 or higher
- Qdrant vector database (optional, for vector store functionality)

### Install from source

```bash
# Clone the repository
git clone <repository-url>
cd qa_agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install
```

### Configuration

The QA Agent supports two AI providers:

1. **Kiro (Recommended)**: Uses Kiro's built-in AI models - no API key required
2. **OpenAI**: Uses OpenAI's API - requires an API key

#### Using Kiro Models (Recommended)

Create a `config.yaml` file:

```yaml
ai:
  provider: "kiro"
  model: "auto"  # Options: auto, fast, balanced, quality
  temperature: 0.7
  max_tokens: 2000

output:
  directory: "output"
```

Or use the provided example:

```bash
cp config.kiro.yaml config.yaml
```

#### Using OpenAI Models

Create a `config.yaml` file:

```yaml
ai:
  provider: "openai"
  api_key: "${OPENAI_API_KEY}"  # Or provide directly
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 2000

output:
  directory: "output"
```

Or use the provided example:

```bash
cp config.example.yaml config.yaml
# Edit config.yaml and add your OpenAI API key
```

You can also set environment variables:

```bash
cp .env.example .env
# Edit .env with your settings
```
- `VECTOR_STORE_HOST`: Qdrant host (default: localhost)
- `VECTOR_STORE_PORT`: Qdrant port (default: 6333)
- Additional settings for MCP servers, output formats, etc.

## Quick Start

```bash
# Check version
qa-agent version

# More commands coming soon...
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=qa_agent --cov-report=html

# Run specific test file
pytest tests/test_models.py
```

### Code Quality

```bash
# Format code
black qa_agent tests

# Lint code
ruff check qa_agent tests

# Type check
mypy qa_agent
```

## Architecture

The QA Agent uses a modular, plugin-based architecture:

- **Parsers**: Ingest requirements from various formats
- **Vector Store**: Store and retrieve requirement embeddings
- **RAG Engine**: Context-aware generation using semantic search
- **Generators**: Create test artifacts (manual tests, automation skeletons, etc.)
- **Analysis**: Coverage analysis and RTM generation
- **MCP Integration**: Connect to external tools and services

## Project Structure

```
qa_agent/
├── qa_agent/
│   ├── __init__.py
│   ├── cli.py              # Command-line interface
│   ├── analysis/           # Coverage and traceability analysis
│   ├── config/             # Configuration management
│   ├── generators/         # Test artifact generators
│   ├── mcp/                # MCP server integrations
│   ├── models/             # Core data models
│   ├── parsers/            # Requirement parsers
│   ├── rag/                # RAG engine
│   └── vector_store/       # Vector database management
├── tests/                  # Test suite
├── pyproject.toml          # Project configuration
├── .env.example            # Environment template
└── README.md
```

## License

MIT

## Contributing

Contributions are welcome! Please ensure all tests pass and code is formatted before submitting PRs.
