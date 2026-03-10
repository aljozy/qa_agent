# Changelog

All notable changes to the AI-Powered QA Agent project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Jira user story parser
- OpenAPI/Swagger specification parser
- SQL schema parser
- Automation test skeleton generation
- RAG-powered context retrieval with vector store
- MCP server integrations
- Coverage gap analysis
- UI workflow test generation
- Database validation test generation

## [0.1.0] - 2024-01-XX

### Added
- Initial MVP release
- Markdown requirement parser with structured extraction
- Manual test case generator with AI-powered generation
- Support for positive, negative, and edge case test scenarios
- Requirement Traceability Matrix (RTM) generation with coverage metrics
- CLI interface with commands: parse, generate, rtm, run
- Configuration management with YAML support
- Multi-provider AI support (Kiro and OpenAI)
- Comprehensive error handling and logging
- JSON output format for all artifacts
- Batch processing with progress tracking
- Rich console output with progress bars
- Type-safe data models using Pydantic
- Async/await support for LLM operations
- File-based storage layer
- Workflow orchestrator for end-to-end pipeline
- Example files and documentation
- Unit tests with pytest
- Property-based tests with hypothesis
- Development tooling (black, ruff, mypy, pre-commit)

### Documentation
- Comprehensive README with installation and usage guides
- CLI usage documentation
- Configuration guide with examples
- API reference documentation
- Architecture overview
- Example workflows and use cases
- Batch generation guide
- RTM generator documentation
- Workflow orchestrator documentation

### Configuration
- YAML-based configuration system
- Environment variable support via .env files
- Configurable AI providers and models
- Configurable output directories and formats
- Logging configuration with multiple levels
- JSON logging support for CI/CD integration

### Developer Experience
- Type hints throughout codebase
- Comprehensive docstrings
- Pre-commit hooks for code quality
- Automated testing with pytest
- Code coverage reporting
- Linting with ruff
- Formatting with black
- Type checking with mypy

## Version History

### Version Numbering

This project uses [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for new functionality in a backward compatible manner
- **PATCH** version for backward compatible bug fixes

### Release Process

1. Update version in `qa_agent/__init__.py`
2. Update version in `pyproject.toml`
3. Update CHANGELOG.md with release notes
4. Create git tag: `git tag -a v0.1.0 -m "Release v0.1.0"`
5. Push tag: `git push origin v0.1.0`
6. Build distribution: `python -m build`
7. Upload to PyPI: `python -m twine upload dist/*`

### Migration Guides

#### Upgrading to 0.1.0
This is the initial release. No migration needed.

---

[Unreleased]: https://github.com/qa-agent/qa-agent/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/qa-agent/qa-agent/releases/tag/v0.1.0
