# Changelog

All notable changes to the AI-Powered QA Agent project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0-mvp] - 2024-12-XX

### Added

#### Core Features
- **Markdown Parser**: Parse structured Markdown PRD documents into requirement objects
  - Extract headings as requirement sections
  - Extract bullet points and paragraphs as requirements
  - Preserve document hierarchy in metadata
  - Automatic requirement classification (functional/non-functional)
  - Auto-generated requirement IDs

- **Manual Test Generator**: AI-powered test case generation
  - Generate positive scenario test cases
  - Generate negative scenario test cases
  - Generate edge case test scenarios
  - Structured test format with ID, description, preconditions, steps, and expected results
  - Requirement traceability linking
  - Batch processing with progress tracking
  - Parallel generation for improved performance

- **RTM Generator**: Requirement Traceability Matrix generation
  - Map requirements to test cases
  - Calculate coverage percentages
  - Identify requirements with no test cases
  - CSV export format
  - Coverage status reporting

- **LLM Client**: Multi-provider AI integration
  - Kiro AI provider support (default, no API key required)
  - OpenAI provider support (GPT-4, GPT-3.5-turbo)
  - Configurable model parameters (temperature, max_tokens)
  - Async API calls for performance
  - Retry logic with exponential backoff
  - Comprehensive error handling

- **File Storage**: JSON-based artifact storage
  - Save and load requirements
  - Save and load test artifacts
  - List saved files
  - Graceful error handling

- **Configuration Management**: YAML-based configuration
  - AI provider configuration (Kiro/OpenAI)
  - Model parameter configuration
  - Output directory configuration
  - Validation with descriptive error messages
  - Environment variable support

#### CLI Interface
- **parse command**: Parse Markdown requirements documents
  - Input file path argument
  - Configurable output directory
  - Progress tracking with rich console output

- **generate command**: Generate test cases from requirements
  - Requirements file input
  - Configurable test scenario types (positive/negative/edge cases)
  - Provider override option
  - Progress tracking and status updates

- **rtm command**: Generate requirement traceability matrix
  - Requirements and tests file inputs
  - CSV output format
  - Coverage metrics display

- **run command**: Execute full pipeline (parse → generate → rtm)
  - Single command for complete workflow
  - Automatic file path management
  - Comprehensive progress reporting

- **Global options**: 
  - `--config` flag for custom configuration files
  - `--log-level` for logging control
  - `--json-logs` for CI/CD integration
  - `--version` to display version information

#### Workflow Orchestration
- **WorkflowOrchestrator**: End-to-end workflow management
  - Coordinate parser → storage → generator → RTM pipeline
  - Error handling and recovery
  - Progress tracking across components
  - Structured logging

#### Error Handling & Logging
- Custom exception classes for different error types
- Descriptive error messages throughout
- Graceful degradation for non-critical failures
- Structured logging with multiple levels (DEBUG, INFO, WARNING, ERROR)
- Console and file logging support
- JSON log format for CI/CD integration

#### Documentation
- Comprehensive README with installation, usage, and examples
- API reference documentation
- Configuration guide with examples
- CLI usage documentation
- Architecture overview with diagrams
- Example Markdown PRD files
- Troubleshooting guide

#### Development Tools
- pytest test suite with 80%+ coverage
- Black code formatting
- Ruff linting
- mypy type checking
- pre-commit hooks
- GitHub Actions CI/CD pipeline

### Technical Details

#### Architecture
- Modular plugin-based architecture
- Abstract base classes for parsers and generators
- Pydantic models for data validation
- Async/await for I/O operations
- Type hints throughout codebase

#### Dependencies
- Python 3.10+ support
- pydantic 2.5+ for data models
- typer 0.9+ for CLI
- rich 13.7+ for console output
- openai 1.10+ for LLM integration
- pyyaml 6.0+ for configuration
- httpx 0.26+ for async HTTP

#### Performance
- Batch processing for multiple requirements
- Parallel test generation
- Async LLM API calls
- Efficient file I/O operations

### MVP Scope

This MVP release focuses on delivering core value with:
- **Input Format**: Markdown PRD documents only
- **Storage**: File-based JSON (no vector database)
- **AI Approach**: Direct LLM calls (no RAG)
- **Test Types**: Manual test cases only
- **Analysis**: Basic RTM with coverage metrics
- **Integrations**: None (no MCP servers)
- **CLI**: Basic commands with essential options

### Migration Path

Future versions will add:
- **v1.1**: Jira user story parser
- **v1.2**: OpenAPI/Swagger parser + API test generator
- **v1.3**: Vector store + RAG for semantic search
- **v1.4**: Coverage gap analyzer
- **v1.5**: MCP server integrations (GitHub, OpenAPI, Database)

### Known Limitations

- Only Markdown format supported for requirements input
- Manual test cases only (no automation skeletons)
- No vector database or semantic search
- No RAG-based context retrieval
- No MCP server integrations
- Basic RTM without advanced coverage analysis
- No test data generation
- No UI workflow generation
- No database validation test generation

### Breaking Changes

None (initial release)

### Security

- API keys stored in environment variables
- No hardcoded credentials
- Secure configuration file handling
- Input validation to prevent injection attacks

### Contributors

- QA Agent Team

---

## [Unreleased]

### Planned Features
- Jira user story parser
- OpenAPI/Swagger specification parser
- SQL schema parser
- Plain text parser with NLP
- Automation test skeleton generator
- API test generator
- UI workflow test generator
- Database validation test generator
- Vector store integration (Qdrant/Chroma)
- RAG engine for context-aware generation
- Coverage gap analyzer
- Test data generator
- MCP server integrations
- GitHub integration for PR creation
- Advanced RTM with HTML export
- CI/CD pipeline templates

---

## Version History

- **1.0.0-mvp** (2024-12-XX): Initial MVP release with Markdown parsing, manual test generation, and basic RTM
