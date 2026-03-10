"""Demonstration of the parser plugin architecture.

This example shows how to:
1. Use the built-in MarkdownParser
2. Create a custom parser plugin
3. Register parsers in the registry
4. Use the factory to select parsers automatically
5. Use configuration-based parser selection
"""

from pathlib import Path
from typing import List

from qa_agent.models.base import Requirement, RequirementType, ValidationResult
from qa_agent.parsers import (
    ParserFactory,
    ParserRegistry,
    RequirementParser,
    auto_detect_parser,
    create_parser_from_config,
    register_parser,
)


# Example 1: Create a custom parser plugin
class SimpleTextParser(RequirementParser):
    """Simple parser for plain text files with one requirement per line."""

    name = "simple_text"
    supported_extensions = [".txt", ".text"]
    description = "Simple text parser - one requirement per line"

    def parse(self, input_data: str | Path) -> List[Requirement]:
        """Parse text file with one requirement per line."""
        if isinstance(input_data, Path):
            if not input_data.exists():
                raise FileNotFoundError(f"File not found: {input_data}")
            with open(input_data, "r") as f:
                content = f.read()
        else:
            content = input_data

        requirements = []
        lines = [line.strip() for line in content.split("\n") if line.strip()]

        for idx, line in enumerate(lines, 1):
            req = Requirement(
                id=f"TXT-{idx:03d}",
                type=RequirementType.FUNCTIONAL,
                content=line,
                source="simple_text",
                metadata={"line_number": idx},
            )
            requirements.append(req)

        return requirements

    def validate(self, input_data: str | Path) -> ValidationResult:
        """Validate text input."""
        if isinstance(input_data, Path):
            if not input_data.exists():
                return ValidationResult(
                    is_valid=False, errors=[f"File not found: {input_data}"]
                )
            return ValidationResult(is_valid=True)

        if not input_data or not input_data.strip():
            return ValidationResult(is_valid=False, errors=["Content is empty"])

        return ValidationResult(is_valid=True)


def demo_basic_usage():
    """Demonstrate basic parser usage."""
    print("=" * 60)
    print("Demo 1: Basic Parser Usage")
    print("=" * 60)

    # Create a custom parser instance
    parser = SimpleTextParser()

    # Parse some content
    content = """
    User shall be able to login
    System shall validate credentials
    Application shall display error messages
    """

    requirements = parser.parse(content)

    print(f"\nParsed {len(requirements)} requirements:")
    for req in requirements:
        print(f"  - {req.id}: {req.content}")


def demo_registry():
    """Demonstrate parser registry."""
    print("\n" + "=" * 60)
    print("Demo 2: Parser Registry")
    print("=" * 60)

    # Create a registry and register our custom parser
    registry = ParserRegistry()
    registry.register(SimpleTextParser)

    print("\nRegistered parsers:")
    for parser_info in registry.list_parsers():
        print(f"  - {parser_info['name']}: {parser_info['description']}")
        print(f"    Extensions: {parser_info['supported_extensions']}")

    # Get a parser by name
    parser = registry.get_parser("simple_text")
    print(f"\nRetrieved parser: {parser.name}")

    # Get a parser for a file
    parser_for_file = registry.get_parser_for_file(Path("requirements.txt"))
    print(f"Parser for .txt file: {parser_for_file.name}")


def demo_factory():
    """Demonstrate parser factory."""
    print("\n" + "=" * 60)
    print("Demo 3: Parser Factory")
    print("=" * 60)

    # Create a registry and register parsers
    registry = ParserRegistry()
    registry.register(SimpleTextParser)

    # Create a factory
    factory = ParserFactory(registry)

    print("\nSupported extensions:")
    print(f"  {factory.get_supported_extensions()}")

    # Check if files are supported
    test_files = ["requirements.txt", "spec.md", "data.json"]
    print("\nFile support check:")
    for file in test_files:
        supported = factory.supports_file(file)
        print(f"  {file}: {'✓ Supported' if supported else '✗ Not supported'}")

    # Create parser for specific file
    parser = factory.create_parser_for_file("requirements.txt")
    print(f"\nCreated parser for .txt file: {parser.name}")


def demo_config_based_selection():
    """Demonstrate configuration-based parser selection."""
    print("\n" + "=" * 60)
    print("Demo 4: Configuration-Based Parser Selection")
    print("=" * 60)

    # Create a registry and register parsers
    registry = ParserRegistry()
    registry.register(SimpleTextParser)

    # Configuration specifying which parser to use
    config = {
        "parser": "simple_text",
        "options": {
            "some_option": "value"
        }
    }

    print(f"\nConfiguration: {config}")

    # Create parser from config
    parser = create_parser_from_config(config, registry)
    print(f"Created parser: {parser.name}")

    # Use the parser
    content = "System shall process requests\nSystem shall log errors"
    requirements = parser.parse(content)
    print(f"\nParsed {len(requirements)} requirements:")
    for req in requirements:
        print(f"  - {req.id}: {req.content}")


def demo_auto_detection():
    """Demonstrate automatic parser detection."""
    print("\n" + "=" * 60)
    print("Demo 5: Automatic Parser Detection")
    print("=" * 60)

    # Create a registry and register parsers
    from qa_agent.parsers.markdown_parser import MarkdownParser
    
    registry = ParserRegistry()
    registry.register(SimpleTextParser)
    registry.register(MarkdownParser)

    # Auto-detect parser from content
    markdown_content = "# Requirements\n\nSome requirement"
    try:
        parser = auto_detect_parser(markdown_content, registry)
        print(f"Auto-detected parser for markdown content: {parser.name}")
    except ValueError as e:
        print(f"Could not auto-detect: {e}")


def demo_plugin_extensibility():
    """Demonstrate how easy it is to extend with new parsers."""
    print("\n" + "=" * 60)
    print("Demo 6: Plugin Extensibility")
    print("=" * 60)

    # Create another custom parser
    class CSVParser(RequirementParser):
        """Parser for CSV files with requirements."""

        name = "csv"
        supported_extensions = [".csv"]
        description = "CSV parser for requirements"

        def parse(self, input_data: str | Path) -> List[Requirement]:
            # Simplified CSV parsing
            if isinstance(input_data, Path):
                with open(input_data, "r") as f:
                    content = f.read()
            else:
                content = input_data

            requirements = []
            lines = content.strip().split("\n")[1:]  # Skip header

            for idx, line in enumerate(lines, 1):
                if line.strip():
                    req = Requirement(
                        id=f"CSV-{idx:03d}",
                        type=RequirementType.FUNCTIONAL,
                        content=line,
                        source="csv",
                    )
                    requirements.append(req)

            return requirements

        def validate(self, input_data: str | Path) -> ValidationResult:
            return ValidationResult(is_valid=True)

    # Register both parsers
    registry = ParserRegistry()
    registry.register(SimpleTextParser)
    registry.register(CSVParser)

    print("\nRegistered parsers:")
    for parser_info in registry.list_parsers():
        print(f"  - {parser_info['name']}: {parser_info['description']}")

    print("\nSupported extensions:")
    print(f"  {registry.get_supported_extensions()}")

    print("\n✓ New parser added without modifying core code!")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("Parser Plugin Architecture Demonstration")
    print("=" * 60)

    demo_basic_usage()
    demo_registry()
    demo_factory()
    demo_config_based_selection()
    demo_auto_detection()
    demo_plugin_extensibility()

    print("\n" + "=" * 60)
    print("All demos completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
