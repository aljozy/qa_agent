# Error Handling and Logging

This document describes the error handling and logging system implemented in the QA Agent MVP.

## Overview

The QA Agent implements comprehensive error handling and structured logging to provide:

- **Descriptive error messages** with context and details
- **Custom exception classes** for different error types
- **Structured logging** with JSON format support for CI/CD
- **Graceful degradation** when optional components fail
- **Multiple log levels** (DEBUG, INFO, WARNING, ERROR)
- **Console and file logging** support

## Custom Exception Classes

All custom exceptions inherit from `QAAgentError` base class and provide structured error information.

### Base Exception

```python
from qa_agent.core.exceptions import QAAgentError

try:
    # Some operation
    pass
except QAAgentError as e:
    print(f"Error: {e.message}")
    print(f"Details: {e.details}")
    error_dict = e.to_dict()  # Convert to dictionary for logging
```

### Exception Types

#### ParsingError

Raised when parsing requirements fails.

```python
from qa_agent.core.exceptions import ParsingError

raise ParsingError(
    "Invalid markdown syntax",
    source="requirements.md",
    line_number=42,
    details={"column": 10}
)
```

**Attributes:**
- `message`: Error message
- `source`: Source file or document
- `line_number`: Line number where error occurred
- `details`: Additional error details

#### ConfigurationError

Raised when configuration is invalid.

```python
from qa_agent.core.exceptions import ConfigurationError

raise ConfigurationError(
    "Invalid API key format",
    config_file="config.yaml",
    field="ai.api_key",
    details={"expected": "string", "actual": "null"}
)
```

**Attributes:**
- `message`: Error message
- `config_file`: Configuration file path
- `field`: Configuration field that caused the error
- `details`: Additional error details

#### StorageError

Raised when storage operations fail.

```python
from qa_agent.core.exceptions import StorageError

raise StorageError(
    "Failed to write file",
    file_path="/path/to/file.json",
    operation="write",
    details={"error": "Permission denied"}
)
```

**Attributes:**
- `message`: Error message
- `file_path`: File path involved in the operation
- `operation`: Operation that failed (read, write, delete, etc.)
- `details`: Additional error details

#### GenerationError

Raised when test generation fails.

```python
from qa_agent.core.exceptions import GenerationError

raise GenerationError(
    "Failed to generate test cases",
    requirement_id="REQ-001",
    provider="openai",
    details={"error": "Rate limit exceeded"}
)
```

**Attributes:**
- `message`: Error message
- `requirement_id`: ID of requirement being processed
- `provider`: AI provider being used
- `details`: Additional error details

#### LLMError

Raised for LLM-related errors.

```python
from qa_agent.core.exceptions import LLMError

raise LLMError(
    "Model not available",
    provider="openai",
    model="gpt-4",
    details={"status_code": 503}
)
```

**Attributes:**
- `message`: Error message
- `provider`: AI provider (kiro, openai, etc.)
- `model`: Model name
- `details`: Additional error details

#### RateLimitError

Raised when rate limit is exceeded.

```python
from qa_agent.core.exceptions import RateLimitError

raise RateLimitError(
    "Rate limit exceeded",
    provider="openai",
    retry_after=60,
    details={"limit": "3 requests per minute"}
)
```

**Attributes:**
- `message`: Error message
- `provider`: AI provider
- `retry_after`: Seconds to wait before retrying
- `details`: Additional error details

#### APIError

Raised for API-related errors.

```python
from qa_agent.core.exceptions import APIError

raise APIError(
    "API request failed",
    provider="openai",
    status_code=500,
    details={"error": "Internal server error"}
)
```

**Attributes:**
- `message`: Error message
- `provider`: AI provider
- `status_code`: HTTP status code
- `details`: Additional error details

#### ValidationError

Raised when validation fails.

```python
from qa_agent.core.exceptions import ValidationError

raise ValidationError(
    "Field cannot be empty",
    field="filename",
    value="",
    details={"constraint": "non-empty string"}
)
```

**Attributes:**
- `message`: Error message
- `field`: Field that failed validation
- `value`: Value that failed validation
- `details`: Additional error details

#### RTMError

Raised when RTM generation fails.

```python
from qa_agent.core.exceptions import RTMError

raise RTMError(
    "Failed to export RTM",
    operation="export",
    details={"format": "csv", "error": "Permission denied"}
)
```

**Attributes:**
- `message`: Error message
- `operation`: Operation that failed (generate, export, etc.)
- `details`: Additional error details

## Logging Configuration

### Setup Logging

Configure logging at application startup:

```python
from qa_agent.core.logging_config import setup_logging

# Basic setup
setup_logging(
    log_level="INFO",
    log_to_file=True,
    log_to_console=True,
    json_format=False,
)

# CI/CD setup with JSON logs
setup_logging(
    log_level="DEBUG",
    log_to_file=True,
    log_file=Path("output/logs/qa_agent.log"),
    log_to_console=True,
    json_format=True,  # JSON format for CI/CD parsing
)
```

**Parameters:**
- `log_level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `log_to_file`: Whether to log to file (default: True)
- `log_file`: Path to log file (default: output/logs/qa_agent.log)
- `log_to_console`: Whether to log to console (default: True)
- `json_format`: Whether to use JSON format for logs (default: False)

### Get Logger

Get a logger with optional context:

```python
from qa_agent.core.logging_config import get_logger

# Basic logger
logger = get_logger(__name__)

# Logger with context
logger = get_logger(__name__, context={"component": "parser", "version": "1.0"})

# Use logger
logger.info("Processing requirements", extra={"extra_fields": {"count": 10}})
```

### Log Levels

The system supports standard Python logging levels:

- **DEBUG**: Detailed information for diagnosing problems
- **INFO**: Confirmation that things are working as expected
- **WARNING**: Indication that something unexpected happened
- **ERROR**: A serious problem that prevented a function from completing
- **CRITICAL**: A very serious error that may prevent the program from continuing

### Structured Logging

Logs can include structured data for better analysis:

```python
logger.info(
    "Requirements parsed successfully",
    extra={
        "extra_fields": {
            "source": "requirements.md",
            "count": 25,
            "duration_seconds": 1.5,
        }
    }
)
```

### JSON Log Format

When `json_format=True`, logs are output in JSON format:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "level": "INFO",
  "logger": "qa_agent.parsers.markdown_parser",
  "module": "markdown_parser",
  "function": "parse",
  "line": 42,
  "message": "Requirements parsed successfully",
  "source": "requirements.md",
  "count": 25,
  "duration_seconds": 1.5
}
```

This format is ideal for CI/CD systems and log aggregation tools.

### Helper Functions

#### Log Operation Start

```python
from qa_agent.core.logging_config import log_operation_start

log_operation_start(
    logger,
    "parse_requirements",
    source="requirements.md",
    format="markdown"
)
```

#### Log Operation Complete

```python
from qa_agent.core.logging_config import log_operation_complete

log_operation_complete(
    logger,
    "parse_requirements",
    duration=1.5,
    requirements_count=25
)
```

#### Log Operation Failed

```python
from qa_agent.core.logging_config import log_operation_failed

try:
    # Some operation
    pass
except Exception as e:
    log_operation_failed(
        logger,
        "parse_requirements",
        error=e,
        duration=0.5,
        source="requirements.md"
    )
```

#### Log Exception

```python
from qa_agent.core.logging_config import log_exception

try:
    # Some operation
    pass
except Exception as e:
    log_exception(
        logger,
        exception=e,
        message="Failed to parse requirements",
        level=logging.ERROR,
        source="requirements.md"
    )
```

## Error Handling Patterns

### Try-Catch with Specific Exceptions

```python
from qa_agent.core.exceptions import ParsingError, StorageError
from qa_agent.parsers.markdown_parser import MarkdownParser

try:
    parser = MarkdownParser()
    requirements = parser.parse_file("requirements.md")
except ParsingError as e:
    logger.error(f"Parsing failed: {e.message}")
    logger.debug(f"Details: {e.details}")
    # Handle parsing error
except StorageError as e:
    logger.error(f"Storage failed: {e.message}")
    # Handle storage error
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    # Handle unexpected error
```

### Graceful Degradation

```python
from qa_agent.core.exceptions import LLMError

try:
    # Try primary AI provider
    test_cases = await generator.generate(requirements)
except LLMError as e:
    logger.warning(f"Primary provider failed: {e.message}")
    logger.info("Falling back to alternative provider")
    # Fall back to alternative provider
    test_cases = await fallback_generator.generate(requirements)
```

### Retry Logic

```python
import asyncio
from qa_agent.core.exceptions import RateLimitError

max_retries = 3
retry_delay = 1.0

for attempt in range(max_retries):
    try:
        result = await llm_client.generate(prompt)
        break
    except RateLimitError as e:
        if attempt < max_retries - 1:
            delay = retry_delay * (2 ** attempt)
            logger.warning(
                f"Rate limit exceeded (attempt {attempt + 1}/{max_retries}). "
                f"Retrying in {delay:.1f} seconds..."
            )
            await asyncio.sleep(delay)
        else:
            logger.error(f"Rate limit exceeded after {max_retries} attempts")
            raise
```

## CLI Error Handling

The CLI provides user-friendly error messages:

```bash
$ qa-agent parse requirements.md

# Parsing error
Parsing Error: Markdown content cannot be empty
Details: {'content_length': 0}

# Storage error
Storage Error: Failed to write file: /path/to/file.json
Details: {'operation': 'write', 'error': 'Permission denied'}

# Configuration error
Configuration Error: Invalid API key format
Details: {'config_file': 'config.yaml', 'field': 'ai.api_key'}
```

## CI/CD Integration

### JSON Logs for Parsing

Enable JSON logs for CI/CD systems:

```bash
qa-agent parse requirements.md --json-logs --log-level DEBUG
```

This outputs structured JSON logs that can be parsed by CI/CD tools:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "level": "ERROR",
  "logger": "qa_agent.parsers.markdown_parser",
  "message": "Parsing failed",
  "error_type": "ParsingError",
  "source": "requirements.md",
  "line_number": 42
}
```

### Exit Codes

The CLI uses standard exit codes:

- `0`: Success
- `1`: Error (parsing, storage, configuration, etc.)

## Best Practices

### 1. Use Specific Exceptions

Always use the most specific exception type:

```python
# Good
raise ParsingError("Invalid syntax", source="file.md", line_number=42)

# Bad
raise Exception("Invalid syntax")
```

### 2. Provide Context

Include relevant context in error messages:

```python
# Good
raise StorageError(
    "Failed to write file",
    file_path="/path/to/file.json",
    operation="write",
    details={"error": "Permission denied", "user": "qa_agent"}
)

# Bad
raise StorageError("Failed to write file")
```

### 3. Log at Appropriate Levels

Use appropriate log levels:

```python
# DEBUG: Detailed diagnostic information
logger.debug(f"Parsing line {line_num}: {line}")

# INFO: Confirmation of expected behavior
logger.info(f"Successfully parsed {count} requirements")

# WARNING: Unexpected but recoverable situation
logger.warning(f"No headings found in document")

# ERROR: Serious problem that prevented completion
logger.error(f"Failed to parse requirements: {error}")

# CRITICAL: Very serious error
logger.critical(f"System configuration invalid, cannot start")
```

### 4. Include Structured Data

Add structured data to logs for better analysis:

```python
logger.info(
    "Test generation complete",
    extra={
        "extra_fields": {
            "requirements_count": 25,
            "test_cases_generated": 75,
            "duration_seconds": 45.2,
            "provider": "openai",
            "model": "gpt-4"
        }
    }
)
```

### 5. Handle Errors Gracefully

Always handle errors gracefully and provide helpful messages:

```python
try:
    requirements = parser.parse_file(file_path)
except FileNotFoundError:
    logger.error(f"File not found: {file_path}")
    console.print(f"[red]Error:[/red] File not found: {file_path}")
    console.print("[yellow]Tip:[/yellow] Check the file path and try again")
    sys.exit(1)
except ParsingError as e:
    logger.error(f"Parsing failed: {e.message}", extra={"extra_fields": e.details})
    console.print(f"[red]Parsing Error:[/red] {e.message}")
    if e.line_number:
        console.print(f"[dim]Line {e.line_number}[/dim]")
    sys.exit(1)
```

## Testing Error Handling

Test error handling with pytest:

```python
import pytest
from qa_agent.core.exceptions import ParsingError
from qa_agent.parsers.markdown_parser import MarkdownParser

def test_parse_empty_content():
    """Test parsing empty content raises ParsingError."""
    parser = MarkdownParser()
    
    with pytest.raises(ParsingError) as exc_info:
        parser.parse("")
    
    assert "cannot be empty" in str(exc_info.value)
    assert exc_info.value.details["content_length"] == 0
```

## Troubleshooting

### Common Issues

#### 1. Logs not appearing

**Problem:** Logs are not being written to file or console.

**Solution:** Ensure logging is initialized:

```python
from qa_agent.core.logging_config import setup_logging

setup_logging(log_level="INFO", log_to_file=True, log_to_console=True)
```

#### 2. JSON logs not formatted correctly

**Problem:** JSON logs are not valid JSON.

**Solution:** Ensure `json_format=True` is set:

```python
setup_logging(json_format=True)
```

#### 3. Too many logs

**Problem:** Too much log output.

**Solution:** Increase log level:

```python
setup_logging(log_level="WARNING")  # Only WARNING, ERROR, CRITICAL
```

#### 4. Missing error details

**Problem:** Error messages don't include enough context.

**Solution:** Use custom exceptions with details:

```python
raise ParsingError(
    "Invalid syntax",
    source="file.md",
    line_number=42,
    details={"column": 10, "expected": "heading", "actual": "text"}
)
```

## Summary

The QA Agent's error handling and logging system provides:

✅ **Custom exception classes** for different error types  
✅ **Descriptive error messages** with context and details  
✅ **Structured logging** with JSON format support  
✅ **Multiple log levels** (DEBUG, INFO, WARNING, ERROR)  
✅ **Console and file logging** support  
✅ **Graceful degradation** when optional components fail  
✅ **CI/CD integration** with JSON logs and exit codes  
✅ **Helper functions** for common logging patterns  
✅ **Comprehensive testing** of error scenarios  

This system ensures that errors are handled gracefully, logged comprehensively, and provide actionable information for debugging and monitoring.
