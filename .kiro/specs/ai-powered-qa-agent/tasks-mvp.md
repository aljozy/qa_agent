# Implementation Plan: AI-Powered QA Agent (MVP)

## Overview

This MVP implementation plan focuses on delivering core value in 6-8 weeks instead of 15 weeks. We'll build a working system that parses Markdown PRDs and generates manual test cases using OpenAI, with a simple CLI interface.

**MVP Scope**: Markdown parser → Manual test generator → Basic RTM → CLI

**Deferred to V2**: Multiple parsers, Vector store, RAG, MCP servers, multiple generators

## Tasks

### Phase 1: Core Infrastructure (Week 1)

- [x] 1. Set up project structure and development environment
  - ✓ Already complete

- [x] 2. Implement core data models
  - ✓ Already complete

- [x] 3. Implement simple configuration management
  - [x] 3.1 Create basic config loader
    - Implement `Config` class to load YAML configuration
    - Support OpenAI API parameters (api_key, model, temperature, max_tokens)
    - Support output directory configuration
    - Implement validation with descriptive error messages
    - _Requirements: 16.1, 16.2, 16.5, 16.6_

  - [ ]* 3.2 Write unit tests for configuration
    - Test valid configuration loading
    - Test invalid configuration error handling
    - _Requirements: 16.6_

### Phase 2: Markdown Parser (Week 2)

- [ ] 4. Implement Markdown parser
  - [ ] 4.1 Create Markdown parser implementation
    - Implement `MarkdownParser` class
    - Extract headings as requirement sections
    - Extract bullet points and paragraphs as requirements
    - Preserve document hierarchy in metadata
    - Classify requirements as functional/non-functional based on keywords
    - Generate requirement IDs automatically
    - _Requirements: 3.1, 3.3, 3.4_

  - [ ]* 4.2 Write unit tests for Markdown parser
    - Test heading extraction
    - Test requirement extraction
    - Test hierarchy preservation
    - Test requirement classification
    - _Requirements: 3.1, 3.3, 3.4_

### Phase 3: File Storage (Week 2)

- [ ] 5. Implement file-based storage
  - [ ] 5.1 Create file storage implementation
    - Implement `FileStorage` class
    - Implement `save()` method to write requirements to JSON
    - Implement `load()` method to read requirements from JSON
    - Implement `list()` method to list saved requirement files
    - Handle file I/O errors gracefully
    - _Requirements: 12.1, 12.3_

  - [ ]* 5.2 Write unit tests for file storage
    - Test save and load operations
    - Test error handling for missing files
    - Test JSON serialization/deserialization
    - _Requirements: 12.1, 12.3_

### Phase 4: OpenAI Integration (Week 3)

- [ ] 6. Implement OpenAI client wrapper
  - [ ] 6.1 Create OpenAI client
    - Implement `LLMClient` class wrapping OpenAI API
    - Implement `generate()` method for chat completions
    - Handle API errors and rate limiting
    - Implement retry logic with exponential backoff
    - Support configurable model, temperature, max_tokens
    - _Requirements: 13.1, 13.2, 16.2_

  - [ ]* 6.2 Write unit tests for LLM client
    - Test successful API calls (mocked)
    - Test error handling
    - Test retry logic
    - _Requirements: 13.1, 13.2_

### Phase 5: Manual Test Generator (Weeks 4-5)

- [ ] 7. Implement manual test case generator
  - [ ] 7.1 Create test generator implementation
    - Implement `ManualTestGenerator` class
    - Implement prompt templates for test case generation
    - Generate test cases for positive scenarios
    - Generate test cases for negative scenarios
    - Generate test cases for edge cases
    - Format output with test ID, description, preconditions, steps, expected results
    - Link test cases to source requirements
    - Parse LLM responses into structured TestArtifact objects
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ] 7.2 Implement batch generation
    - Process multiple requirements in parallel
    - Implement progress tracking
    - Handle partial failures gracefully
    - _Requirements: 5.1, 18.5_

  - [ ]* 7.3 Write unit tests for test generator
    - Test prompt construction
    - Test response parsing
    - Test requirement linking
    - Test batch processing
    - _Requirements: 5.1, 5.2, 5.3, 5.6_

### Phase 6: RTM Generator (Week 5)

- [ ] 8. Implement RTM generator
  - [ ] 8.1 Create RTM generator implementation
    - Implement `RTMGenerator` class
    - Create matrix mapping requirements to test cases
    - Identify requirements with no test cases
    - Calculate coverage percentage
    - Export to CSV format
    - Include requirement ID, description, test IDs, coverage status
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 8.2 Write unit tests for RTM generator
    - Test matrix generation
    - Test coverage calculation
    - Test CSV export
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

### Phase 7: CLI Interface (Week 6)

- [ ] 9. Implement command-line interface
  - [ ] 9.1 Create CLI with Typer
    - Implement main CLI entry point
    - Implement `parse` command to parse markdown and save requirements
    - Implement `generate` command to generate tests from requirements
    - Implement `rtm` command to generate RTM
    - Implement `run` command to execute full pipeline (parse + generate + rtm)
    - Accept input file path and output directory as arguments
    - Add `--config` flag for configuration file
    - Add `--api-key` flag for OpenAI API key
    - Return exit code 0 on success, non-zero on failure
    - Display progress with rich console output
    - _Requirements: 18.1, 18.2, 18.3_

  - [ ]* 9.2 Write integration tests for CLI
    - Test parse command
    - Test generate command
    - Test rtm command
    - Test run command (full pipeline)
    - Test error handling
    - _Requirements: 18.1, 18.2, 18.3_

### Phase 8: Integration & Testing (Week 7)

- [ ] 10. Implement end-to-end workflow
  - [ ] 10.1 Create workflow orchestrator
    - Implement `WorkflowOrchestrator` class
    - Wire parser → storage → generator → RTM
    - Implement error handling and logging
    - Add progress tracking
    - _Requirements: 15.3_

  - [ ]* 10.2 Write end-to-end integration tests
    - Test full workflow with sample markdown
    - Verify test case generation
    - Verify RTM generation
    - Test error scenarios
    - _Requirements: 3.1, 5.1, 7.1_

- [ ] 11. Add error handling and logging
  - [ ] 11.1 Implement error handling
    - Create custom exception classes
    - Add try-catch blocks with descriptive messages
    - Implement graceful degradation
    - _Requirements: 3.3, 16.6_

  - [ ] 11.2 Implement logging
    - Add structured logging throughout
    - Support log levels (DEBUG, INFO, WARNING, ERROR)
    - Log to console and file
    - _Requirements: 18.4_

### Phase 9: Documentation & Examples (Week 8)

- [ ] 12. Create documentation
  - [ ] 12.1 Write README
    - Installation instructions
    - Quick start guide
    - Usage examples
    - Configuration guide
    - Architecture overview
    - _Requirements: 19.1_

  - [ ] 12.2 Create example files
    - Example Markdown PRD
    - Example configuration file
    - Example output (test cases, RTM)
    - _Requirements: 19.4_

  - [ ] 12.3 Write API documentation
    - Document public classes and methods
    - Include code examples
    - Document configuration options
    - _Requirements: 19.2, 19.3_

### Phase 10: Polish & Release (Week 8)

- [ ] 13. Prepare for release
  - [ ] 13.1 Create deployment artifacts
    - Update pyproject.toml for distribution
    - Create requirements.txt
    - Add version information
    - _Requirements: 16.1_

  - [ ] 13.2 Final testing
    - Run full test suite
    - Test with real-world markdown documents
    - Verify all examples work
    - Fix any bugs found

  - [ ] 13.3 Create release
    - Create CHANGELOG
    - Tag v1.0.0-mvp
    - Create release notes
    - _Requirements: 19.1_

## MVP vs Full Feature Comparison

| Feature | MVP (8 weeks) | Full (15 weeks) |
|---------|---------------|-----------------|
| Input Formats | Markdown only | Jira, OpenAPI, SQL, Text |
| Storage | File-based JSON | Vector DB (Qdrant) |
| AI Approach | Direct LLM | RAG with semantic search |
| Test Types | Manual only | Manual, API, UI, DB, Automation |
| Analysis | Basic RTM | RTM, Coverage, Test Data |
| Integrations | None | GitHub, OpenAPI, DB MCPs |
| CLI | Basic commands | Full featured |

## Migration Path to Full Version

After MVP release, add features incrementally:

**V1.1 (2 weeks)**: Add Jira parser
**V1.2 (2 weeks)**: Add OpenAPI parser + API test generator
**V1.3 (3 weeks)**: Add Vector store + RAG
**V1.4 (2 weeks)**: Add coverage analyzer
**V1.5 (3 weeks)**: Add MCP integrations

## Notes

- MVP focuses on single use case done well
- All core architecture supports future expansion
- Plugin interfaces allow adding parsers/generators later
- File storage can be swapped for vector DB without changing interfaces
- Tasks marked with `*` are optional and can be skipped for faster delivery
