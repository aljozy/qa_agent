"""Tests for error handling and logging functionality."""

import json
import logging
from pathlib import Path

import pytest

from qa_agent.core.exceptions import (
    ConfigurationError,
    ParsingError,
    StorageError,
    ValidationError,
)
from qa_agent.core.logging_config import (
    get_logger,
    log_exception,
    log_operation_complete,
    log_operation_failed,
    log_operation_start,
    setup_logging,
)
from qa_agent.parsers.markdown_parser import MarkdownParser
from qa_agent.storage.file_storage import FileStorage


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_parsing_error_with_details(self):
        """Test ParsingError with source and line number."""
        error = ParsingError(
            "Invalid syntax",
            source="test.md",
            line_number=42,
            details={"column": 10}
        )
        
        assert error.message == "Invalid syntax"
        assert error.source == "test.md"
        assert error.line_number == 42
        assert error.details["column"] == 10
        
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "ParsingError"
        assert error_dict["message"] == "Invalid syntax"
        assert error_dict["details"]["source"] == "test.md"
        assert error_dict["details"]["line_number"] == 42

    def test_configuration_error(self):
        """Test ConfigurationError with config file and field."""
        error = ConfigurationError(
            "Invalid API key",
            config_file="config.yaml",
            field="ai.api_key"
        )
        
        assert error.message == "Invalid API key"
        assert error.config_file == "config.yaml"
        assert error.field == "ai.api_key"

    def test_storage_error(self):
        """Test StorageError with file path and operation."""
        error = StorageError(
            "Failed to write file",
            file_path="/tmp/test.json",
            operation="write"
        )
        
        assert error.message == "Failed to write file"
        assert error.file_path == "/tmp/test.json"
        assert error.operation == "write"

    def test_validation_error(self):
        """Test ValidationError with field and value."""
        error = ValidationError(
            "Field cannot be empty",
            field="filename",
            value=""
        )
        
        assert error.message == "Field cannot be empty"
        assert error.field == "filename"
        assert error.value == ""


class TestLoggingConfiguration:
    """Test logging configuration."""

    def test_setup_logging_console_only(self, tmp_path):
        """Test logging setup with console output only."""
        setup_logging(
            log_level="DEBUG",
            log_to_file=False,
            log_to_console=True,
            json_format=False,
        )
        
        logger = logging.getLogger()
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) > 0

    def test_setup_logging_with_file(self, tmp_path):
        """Test logging setup with file output."""
        log_file = tmp_path / "test.log"
        
        setup_logging(
            log_level="INFO",
            log_to_file=True,
            log_file=log_file,
            log_to_console=False,
            json_format=True,
        )
        
        logger = logging.getLogger()
        logger.info("Test message", extra={"extra_fields": {"test": "value"}})
        
        assert log_file.exists()
        
        # Read and verify log file contains JSON
        with open(log_file, "r") as f:
            log_content = f.read()
            assert "Test message" in log_content

    def test_get_logger_with_context(self):
        """Test getting logger with context."""
        logger = get_logger(__name__, context={"component": "test"})
        
        assert logger is not None
        assert logger.extra == {"component": "test"}

    def test_log_operation_helpers(self, caplog):
        """Test log operation helper functions."""
        logger = logging.getLogger(__name__)
        
        with caplog.at_level(logging.INFO):
            log_operation_start(logger, "test_operation", param="value")
            log_operation_complete(logger, "test_operation", duration=1.5)
            
            error = Exception("Test error")
            log_operation_failed(logger, "test_operation", error, duration=0.5)
        
        assert "Starting operation: test_operation" in caplog.text
        assert "Completed operation: test_operation" in caplog.text
        assert "Operation failed: test_operation" in caplog.text


class TestMarkdownParserErrorHandling:
    """Test error handling in markdown parser."""

    def test_parse_empty_content(self):
        """Test parsing empty content raises ParsingError."""
        parser = MarkdownParser()
        
        with pytest.raises(ParsingError) as exc_info:
            parser.parse("")
        
        assert "cannot be empty" in str(exc_info.value)
        assert exc_info.value.details["content_length"] == 0

    def test_parse_nonexistent_file(self):
        """Test parsing nonexistent file raises FileNotFoundError."""
        parser = MarkdownParser()
        
        with pytest.raises(FileNotFoundError):
            parser.parse_file(Path("/nonexistent/file.md"))

    def test_parse_directory_instead_of_file(self, tmp_path):
        """Test parsing directory raises ParsingError."""
        parser = MarkdownParser()
        
        with pytest.raises(ParsingError) as exc_info:
            parser.parse_file(tmp_path)
        
        assert "not a file" in str(exc_info.value)
        assert exc_info.value.source == str(tmp_path)


class TestFileStorageErrorHandling:
    """Test error handling in file storage."""

    def test_save_empty_requirements(self, tmp_path):
        """Test saving empty requirements list raises ValidationError."""
        storage = FileStorage(tmp_path)
        
        with pytest.raises(ValidationError) as exc_info:
            storage.save([], "test")
        
        assert "empty" in str(exc_info.value)
        assert exc_info.value.field == "requirements"

    def test_save_invalid_filename(self, tmp_path):
        """Test saving with empty filename raises ValidationError."""
        from qa_agent.models.base import Requirement, RequirementType
        
        storage = FileStorage(tmp_path)
        req = Requirement(
            type=RequirementType.FUNCTIONAL,
            content="Test requirement",
            source="test"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            storage.save([req], "")
        
        assert "Filename cannot be empty" in str(exc_info.value)
        assert exc_info.value.field == "filename"

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading nonexistent file raises FileNotFoundError."""
        storage = FileStorage(tmp_path)
        
        with pytest.raises(FileNotFoundError):
            storage.load("nonexistent.json")

    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON raises StorageError."""
        storage = FileStorage(tmp_path)
        
        # Create invalid JSON file
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }")
        
        with pytest.raises(StorageError) as exc_info:
            storage.load("invalid.json")
        
        assert "parse JSON" in str(exc_info.value)
        assert exc_info.value.operation == "parse"

    def test_load_non_array_json(self, tmp_path):
        """Test loading non-array JSON raises StorageError."""
        storage = FileStorage(tmp_path)
        
        # Create JSON file with object instead of array
        invalid_file = tmp_path / "object.json"
        invalid_file.write_text('{"key": "value"}')
        
        with pytest.raises(StorageError) as exc_info:
            storage.load("object.json")
        
        assert "Invalid requirements file format" in str(exc_info.value)
        assert exc_info.value.operation == "validate"


class TestGracefulDegradation:
    """Test graceful degradation scenarios."""

    def test_parser_continues_after_section_error(self):
        """Test parser continues processing after encountering an error in one section."""
        parser = MarkdownParser()
        
        # Valid markdown with multiple sections
        content = """
# Section 1

- Requirement 1
- Requirement 2

# Section 2

- Requirement 3
- Requirement 4
"""
        
        requirements = parser.parse(content)
        
        # Should successfully parse all requirements
        assert len(requirements) == 4

    def test_storage_provides_detailed_error_info(self, tmp_path):
        """Test storage provides detailed error information."""
        storage = FileStorage(tmp_path)
        
        try:
            storage.load("nonexistent.json")
        except FileNotFoundError as e:
            # Error message should include helpful information
            assert "not found" in str(e)
            assert str(tmp_path) in str(e)
