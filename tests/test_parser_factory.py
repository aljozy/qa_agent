"""Tests for parser factory and configuration-based parser selection."""

import pytest
from pathlib import Path
from typing import List

from qa_agent.models.base import Requirement, RequirementType, ValidationResult
from qa_agent.parsers.base import RequirementParser, ParserRegistry
from qa_agent.parsers.factory import (
    ParserFactory,
    auto_detect_parser,
    create_parser_from_config,
)


class TestParser1(RequirementParser):
    """Test parser 1."""

    name = "test1"
    supported_extensions = [".t1"]
    description = "Test parser 1"

    def parse(self, input_data: str | Path) -> List[Requirement]:
        return [
            Requirement(
                id="T1-001",
                type=RequirementType.FUNCTIONAL,
                content="Test 1",
                source="test1",
            )
        ]

    def validate(self, input_data: str | Path) -> ValidationResult:
        return ValidationResult(is_valid=True)


class TestParser2(RequirementParser):
    """Test parser 2."""

    name = "test2"
    supported_extensions = [".t2"]
    description = "Test parser 2"

    def parse(self, input_data: str | Path) -> List[Requirement]:
        return [
            Requirement(
                id="T2-001",
                type=RequirementType.FUNCTIONAL,
                content="Test 2",
                source="test2",
            )
        ]

    def validate(self, input_data: str | Path) -> ValidationResult:
        return ValidationResult(is_valid=True)


class MarkdownTestParser(RequirementParser):
    """Mock markdown parser for testing."""

    name = "markdown"
    supported_extensions = [".md"]
    description = "Markdown parser"

    def parse(self, input_data: str | Path) -> List[Requirement]:
        return []

    def validate(self, input_data: str | Path) -> ValidationResult:
        return ValidationResult(is_valid=True)


@pytest.fixture
def test_registry():
    """Create a test registry with test parsers."""
    registry = ParserRegistry()
    registry.register(TestParser1)
    registry.register(TestParser2)
    registry.register(MarkdownTestParser)
    return registry


class TestParserFactory:
    """Tests for ParserFactory."""

    def test_create_parser_by_name(self, test_registry):
        """Test creating a parser by name."""
        factory = ParserFactory(test_registry)

        parser = factory.create_parser("test1")

        assert isinstance(parser, TestParser1)
        assert parser.name == "test1"

    def test_create_parser_nonexistent_raises_error(self, test_registry):
        """Test that creating a non-existent parser raises an error."""
        factory = ParserFactory(test_registry)

        with pytest.raises(KeyError, match="not registered"):
            factory.create_parser("nonexistent")

    def test_create_parser_for_file(self, test_registry):
        """Test creating a parser for a file."""
        factory = ParserFactory(test_registry)

        parser = factory.create_parser_for_file(Path("test.t1"))

        assert isinstance(parser, TestParser1)

    def test_create_parser_for_file_string_path(self, test_registry):
        """Test creating a parser for a file using string path."""
        factory = ParserFactory(test_registry)

        parser = factory.create_parser_for_file("test.t2")

        assert isinstance(parser, TestParser2)

    def test_create_parser_for_file_no_match_raises_error(self, test_registry):
        """Test that creating a parser for unsupported file raises an error."""
        factory = ParserFactory(test_registry)

        with pytest.raises(ValueError, match="No parser found"):
            factory.create_parser_for_file(Path("test.unknown"))

    def test_get_available_parsers(self, test_registry):
        """Test getting available parsers."""
        factory = ParserFactory(test_registry)

        parsers = factory.get_available_parsers()

        assert len(parsers) == 3
        parser_names = [p["name"] for p in parsers]
        assert "test1" in parser_names
        assert "test2" in parser_names
        assert "markdown" in parser_names

    def test_get_supported_extensions(self, test_registry):
        """Test getting supported extensions."""
        factory = ParserFactory(test_registry)

        extensions = factory.get_supported_extensions()

        assert ".t1" in extensions
        assert ".t2" in extensions
        assert ".md" in extensions

    def test_supports_file(self, test_registry):
        """Test checking if a file is supported."""
        factory = ParserFactory(test_registry)

        assert factory.supports_file(Path("test.t1"))
        assert factory.supports_file(Path("test.t2"))
        assert factory.supports_file(Path("test.md"))
        assert not factory.supports_file(Path("test.txt"))

    def test_supports_file_string_path(self, test_registry):
        """Test checking if a file is supported using string path."""
        factory = ParserFactory(test_registry)

        assert factory.supports_file("test.t1")
        assert not factory.supports_file("test.unknown")

    def test_factory_uses_global_registry_by_default(self):
        """Test that factory uses global registry when none provided."""
        factory = ParserFactory()

        # Should not raise an error
        assert factory.registry is not None


class TestCreateParserFromConfig:
    """Tests for create_parser_from_config function."""

    def test_create_parser_from_config(self, test_registry):
        """Test creating a parser from configuration."""
        config = {"parser": "test1"}

        parser = create_parser_from_config(config, test_registry)

        assert isinstance(parser, TestParser1)

    def test_create_parser_from_config_with_options(self, test_registry):
        """Test creating a parser from configuration with options."""
        config = {"parser": "test2", "options": {"some_option": "value"}}

        parser = create_parser_from_config(config, test_registry)

        assert isinstance(parser, TestParser2)

    def test_create_parser_from_config_missing_parser_field(self, test_registry):
        """Test that missing parser field raises an error."""
        config = {"options": {"some_option": "value"}}

        with pytest.raises(ValueError, match="must specify a 'parser' field"):
            create_parser_from_config(config, test_registry)

    def test_create_parser_from_config_invalid_type(self, test_registry):
        """Test that invalid config type raises an error."""
        with pytest.raises(ValueError, match="must be a dictionary"):
            create_parser_from_config("not a dict", test_registry)

    def test_create_parser_from_config_nonexistent_parser(self, test_registry):
        """Test that non-existent parser raises an error."""
        config = {"parser": "nonexistent"}

        with pytest.raises(KeyError, match="not registered"):
            create_parser_from_config(config, test_registry)


class TestAutoDetectParser:
    """Tests for auto_detect_parser function."""

    def test_auto_detect_parser_from_path(self, test_registry, tmp_path):
        """Test auto-detecting parser from file path."""
        test_file = tmp_path / "test.t1"
        test_file.write_text("test content")

        parser = auto_detect_parser(test_file, test_registry)

        assert isinstance(parser, TestParser1)

    def test_auto_detect_parser_from_string_path(self, test_registry, tmp_path):
        """Test auto-detecting parser from string file path."""
        test_file = tmp_path / "test.t2"
        test_file.write_text("test content")

        parser = auto_detect_parser(str(test_file), test_registry)

        assert isinstance(parser, TestParser2)

    def test_auto_detect_parser_from_markdown_content(self, test_registry):
        """Test auto-detecting parser from markdown content."""
        content = "# Heading\n\nSome content"

        parser = auto_detect_parser(content, test_registry)

        assert isinstance(parser, MarkdownTestParser)

    def test_auto_detect_parser_unsupported_raises_error(self, test_registry):
        """Test that unsupported input raises an error."""
        content = "Plain text without markdown"

        with pytest.raises(ValueError, match="Could not auto-detect"):
            auto_detect_parser(content, test_registry)

    def test_auto_detect_parser_nonexistent_file(self, test_registry):
        """Test auto-detecting parser for non-existent file."""
        # Should try to parse as content and fail
        with pytest.raises(ValueError, match="Could not auto-detect"):
            auto_detect_parser("nonexistent.unknown", test_registry)


class TestParserFactoryIntegration:
    """Integration tests for parser factory."""

    def test_end_to_end_config_based_parsing(self, test_registry, tmp_path):
        """Test complete workflow using configuration-based parser selection."""
        # Create test file
        test_file = tmp_path / "requirements.t1"
        test_file.write_text("Test requirement")

        # Create parser from config
        config = {"parser": "test1"}
        parser = create_parser_from_config(config, test_registry)

        # Parse file
        requirements = parser.parse(test_file)

        assert len(requirements) == 1
        assert requirements[0].id == "T1-001"

    def test_end_to_end_file_based_parsing(self, test_registry, tmp_path):
        """Test complete workflow using file extension-based parser selection."""
        # Create test file
        test_file = tmp_path / "requirements.t2"
        test_file.write_text("Test requirement")

        # Create factory and get parser for file
        factory = ParserFactory(test_registry)
        parser = factory.create_parser_for_file(test_file)

        # Parse file
        requirements = parser.parse(test_file)

        assert len(requirements) == 1
        assert requirements[0].id == "T2-001"

    def test_factory_supports_multiple_parsers(self, test_registry):
        """Test that factory can work with multiple parsers."""
        factory = ParserFactory(test_registry)

        # Get different parsers
        parser1 = factory.create_parser("test1")
        parser2 = factory.create_parser("test2")
        parser3 = factory.create_parser("markdown")

        # All should be different types
        assert type(parser1) != type(parser2)
        assert type(parser2) != type(parser3)
        assert type(parser1) != type(parser3)

    def test_factory_parser_selection_by_extension(self, test_registry):
        """Test that factory correctly selects parser by file extension."""
        factory = ParserFactory(test_registry)

        # Different extensions should get different parsers
        parser_t1 = factory.create_parser_for_file(Path("file.t1"))
        parser_t2 = factory.create_parser_for_file(Path("file.t2"))
        parser_md = factory.create_parser_for_file(Path("file.md"))

        assert isinstance(parser_t1, TestParser1)
        assert isinstance(parser_t2, TestParser2)
        assert isinstance(parser_md, MarkdownTestParser)
