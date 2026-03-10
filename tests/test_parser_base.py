"""Tests for parser base classes and plugin architecture."""

import pytest
from pathlib import Path
from typing import List

from qa_agent.models.base import Requirement, RequirementType, ValidationResult
from qa_agent.parsers.base import (
    RequirementParser,
    ParserRegistry,
    get_global_registry,
    register_parser,
)


class MockParser(RequirementParser):
    """Mock parser for testing."""

    name = "mock"
    supported_extensions = [".mock", ".test"]
    description = "Mock parser for testing"

    def parse(self, input_data: str | Path) -> List[Requirement]:
        """Mock parse implementation."""
        if isinstance(input_data, Path):
            if not input_data.exists():
                raise FileNotFoundError(f"File not found: {input_data}")
            with open(input_data, "r") as f:
                content = f.read()
        else:
            content = input_data

        return [
            Requirement(
                id="MOCK-001",
                type=RequirementType.FUNCTIONAL,
                content=content,
                source="mock",
            )
        ]

    def validate(self, input_data: str | Path) -> ValidationResult:
        """Mock validate implementation."""
        if isinstance(input_data, Path):
            if not input_data.exists():
                return ValidationResult(
                    is_valid=False, errors=[f"File not found: {input_data}"]
                )
            return ValidationResult(is_valid=True)

        if not input_data or not input_data.strip():
            return ValidationResult(is_valid=False, errors=["Content is empty"])

        return ValidationResult(is_valid=True)


class AnotherMockParser(RequirementParser):
    """Another mock parser for testing."""

    name = "another_mock"
    supported_extensions = [".another"]
    description = "Another mock parser"

    def parse(self, input_data: str | Path) -> List[Requirement]:
        return []

    def validate(self, input_data: str | Path) -> ValidationResult:
        return ValidationResult(is_valid=True)


class TestRequirementParser:
    """Tests for RequirementParser base class."""

    def test_parser_has_metadata(self):
        """Test that parser has required metadata."""
        parser = MockParser()
        assert parser.name == "mock"
        assert parser.supported_extensions == [".mock", ".test"]
        assert parser.description == "Mock parser for testing"

    def test_supports_file(self):
        """Test supports_file method."""
        parser = MockParser()

        assert parser.supports_file(Path("test.mock"))
        assert parser.supports_file(Path("test.test"))
        assert not parser.supports_file(Path("test.txt"))
        assert not parser.supports_file(Path("test.md"))

    def test_supports_file_case_insensitive(self):
        """Test that file extension matching is case-insensitive."""
        parser = MockParser()

        assert parser.supports_file(Path("test.MOCK"))
        assert parser.supports_file(Path("test.Mock"))
        assert parser.supports_file(Path("test.TEST"))

    def test_get_metadata(self):
        """Test get_metadata method."""
        parser = MockParser()
        metadata = parser.get_metadata()

        assert metadata["name"] == "mock"
        assert metadata["supported_extensions"] == [".mock", ".test"]
        assert metadata["description"] == "Mock parser for testing"

    def test_parse_string_content(self):
        """Test parsing string content."""
        parser = MockParser()
        requirements = parser.parse("Test content")

        assert len(requirements) == 1
        assert requirements[0].content == "Test content"

    def test_validate_string_content(self):
        """Test validating string content."""
        parser = MockParser()

        # Valid content
        result = parser.validate("Test content")
        assert result.is_valid
        assert len(result.errors) == 0

        # Empty content
        result = parser.validate("")
        assert not result.is_valid
        assert len(result.errors) > 0


class TestParserRegistry:
    """Tests for ParserRegistry."""

    def test_register_parser(self):
        """Test registering a parser."""
        registry = ParserRegistry()
        registry.register(MockParser)

        assert registry.is_registered("mock")
        assert "mock" in [p["name"] for p in registry.list_parsers()]

    def test_register_duplicate_parser_raises_error(self):
        """Test that registering a duplicate parser raises an error."""
        registry = ParserRegistry()
        registry.register(MockParser)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(MockParser)

    def test_register_non_parser_class_raises_error(self):
        """Test that registering a non-parser class raises an error."""
        registry = ParserRegistry()

        class NotAParser:
            pass

        with pytest.raises(ValueError, match="must be a subclass"):
            registry.register(NotAParser)

    def test_unregister_parser(self):
        """Test unregistering a parser."""
        registry = ParserRegistry()
        registry.register(MockParser)

        assert registry.is_registered("mock")

        registry.unregister("mock")

        assert not registry.is_registered("mock")

    def test_unregister_nonexistent_parser_raises_error(self):
        """Test that unregistering a non-existent parser raises an error."""
        registry = ParserRegistry()

        with pytest.raises(KeyError, match="not registered"):
            registry.unregister("nonexistent")

    def test_get_parser(self):
        """Test getting a parser instance."""
        registry = ParserRegistry()
        registry.register(MockParser)

        parser = registry.get_parser("mock")

        assert isinstance(parser, MockParser)
        assert parser.name == "mock"

    def test_get_nonexistent_parser_raises_error(self):
        """Test that getting a non-existent parser raises an error."""
        registry = ParserRegistry()

        with pytest.raises(KeyError, match="not registered"):
            registry.get_parser("nonexistent")

    def test_get_parser_for_file(self):
        """Test getting a parser for a file."""
        registry = ParserRegistry()
        registry.register(MockParser)

        parser = registry.get_parser_for_file(Path("test.mock"))

        assert isinstance(parser, MockParser)

    def test_get_parser_for_file_no_match(self):
        """Test getting a parser for a file with no matching parser."""
        registry = ParserRegistry()
        registry.register(MockParser)

        parser = registry.get_parser_for_file(Path("test.txt"))

        assert parser is None

    def test_list_parsers(self):
        """Test listing all parsers."""
        registry = ParserRegistry()
        registry.register(MockParser)
        registry.register(AnotherMockParser)

        parsers = registry.list_parsers()

        assert len(parsers) == 2
        parser_names = [p["name"] for p in parsers]
        assert "mock" in parser_names
        assert "another_mock" in parser_names

    def test_get_supported_extensions(self):
        """Test getting supported extensions."""
        registry = ParserRegistry()
        registry.register(MockParser)
        registry.register(AnotherMockParser)

        extensions = registry.get_supported_extensions()

        assert ".mock" in extensions
        assert ".test" in extensions
        assert ".another" in extensions

    def test_extension_mapping_override_warning(self, capsys):
        """Test that overriding an extension mapping shows a warning."""
        registry = ParserRegistry()

        # Create a parser with overlapping extension
        class OverlapParser(RequirementParser):
            name = "overlap"
            supported_extensions = [".mock"]  # Same as MockParser
            description = "Overlap parser"

            def parse(self, input_data: str | Path) -> List[Requirement]:
                return []

            def validate(self, input_data: str | Path) -> ValidationResult:
                return ValidationResult(is_valid=True)

        registry.register(MockParser)
        registry.register(OverlapParser)

        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert ".mock" in captured.out

    def test_multiple_extensions_per_parser(self):
        """Test that a parser can support multiple extensions."""
        registry = ParserRegistry()
        registry.register(MockParser)

        # Both extensions should work
        parser1 = registry.get_parser_for_file(Path("test.mock"))
        parser2 = registry.get_parser_for_file(Path("test.test"))

        assert isinstance(parser1, MockParser)
        assert isinstance(parser2, MockParser)


class TestGlobalRegistry:
    """Tests for global registry functions."""

    def test_get_global_registry(self):
        """Test getting the global registry."""
        registry1 = get_global_registry()
        registry2 = get_global_registry()

        # Should return the same instance
        assert registry1 is registry2

    def test_register_parser_global(self):
        """Test registering a parser in the global registry."""
        # Note: This test may affect other tests if they use the global registry
        # In a real scenario, you might want to reset the global registry between tests

        register_parser(MockParser)
        registry = get_global_registry()

        assert registry.is_registered("mock")


class TestParserIntegration:
    """Integration tests for parser system."""

    def test_end_to_end_parser_registration_and_usage(self, tmp_path):
        """Test complete workflow of registering and using a parser."""
        # Create a test file
        test_file = tmp_path / "test.mock"
        test_file.write_text("Test requirement content")

        # Create registry and register parser
        registry = ParserRegistry()
        registry.register(MockParser)

        # Get parser for file
        parser = registry.get_parser_for_file(test_file)
        assert parser is not None

        # Validate file
        validation = parser.validate(test_file)
        assert validation.is_valid

        # Parse file
        requirements = parser.parse(test_file)
        assert len(requirements) == 1
        assert requirements[0].content == "Test requirement content"

    def test_parser_discovery_by_extension(self):
        """Test that parsers can be discovered by file extension."""
        registry = ParserRegistry()
        registry.register(MockParser)
        registry.register(AnotherMockParser)

        # Test different extensions
        mock_parser = registry.get_parser_for_file(Path("file.mock"))
        another_parser = registry.get_parser_for_file(Path("file.another"))
        no_parser = registry.get_parser_for_file(Path("file.unknown"))

        assert isinstance(mock_parser, MockParser)
        assert isinstance(another_parser, AnotherMockParser)
        assert no_parser is None
