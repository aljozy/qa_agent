"""Parser factory for selecting and creating parser instances."""

from pathlib import Path
from typing import Dict, List, Optional

from qa_agent.parsers.base import ParserRegistry, RequirementParser, get_global_registry


class ParserFactory:
    """Factory for creating parser instances based on input type or configuration.
    
    This class provides methods to select the appropriate parser based on:
    - File extension
    - Explicit parser name
    - Configuration settings
    """

    def __init__(self, registry: Optional[ParserRegistry] = None):
        """Initialize the parser factory.
        
        Args:
            registry: Optional ParserRegistry to use. If None, uses the global registry.
        """
        self.registry = registry or get_global_registry()

    def create_parser(self, parser_name: str) -> RequirementParser:
        """Create a parser instance by name.
        
        Args:
            parser_name: Name of the parser to create
        
        Returns:
            Instance of the requested parser
        
        Raises:
            KeyError: If parser is not registered
        """
        return self.registry.get_parser(parser_name)

    def create_parser_for_file(self, file_path: str | Path) -> RequirementParser:
        """Create a parser instance for the given file.
        
        Args:
            file_path: Path to the file
        
        Returns:
            Parser instance that supports the file extension
        
        Raises:
            ValueError: If no parser supports the file extension
        """
        file_path = Path(file_path)
        parser = self.registry.get_parser_for_file(file_path)

        if parser is None:
            supported_exts = self.registry.get_supported_extensions()
            raise ValueError(
                f"No parser found for file extension '{file_path.suffix}'. "
                f"Supported extensions: {supported_exts}"
            )

        return parser

    def get_available_parsers(self) -> List[Dict[str, any]]:
        """Get information about all available parsers.
        
        Returns:
            List of dictionaries containing parser metadata
        """
        return self.registry.list_parsers()

    def get_supported_extensions(self) -> List[str]:
        """Get all supported file extensions.
        
        Returns:
            List of supported file extensions
        """
        return self.registry.get_supported_extensions()

    def supports_file(self, file_path: str | Path) -> bool:
        """Check if any parser supports the given file.
        
        Args:
            file_path: Path to the file to check
        
        Returns:
            True if a parser supports the file extension, False otherwise
        """
        file_path = Path(file_path)
        return self.registry.get_parser_for_file(file_path) is not None


def create_parser_from_config(
    config: Dict[str, any], registry: Optional[ParserRegistry] = None
) -> RequirementParser:
    """Create a parser based on configuration settings.
    
    This function supports configuration-based parser activation as specified
    in Requirement 15.4 and 15.5.
    
    Args:
        config: Configuration dictionary with parser settings.
                Expected format:
                {
                    "parser": "parser_name",  # Required
                    "options": {...}          # Optional parser-specific options
                }
        registry: Optional ParserRegistry to use. If None, uses the global registry.
    
    Returns:
        Instance of the configured parser
    
    Raises:
        ValueError: If configuration is invalid
        KeyError: If specified parser is not registered
    """
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a dictionary")

    if "parser" not in config:
        raise ValueError("Configuration must specify a 'parser' field")

    parser_name = config["parser"]
    factory = ParserFactory(registry)

    return factory.create_parser(parser_name)


def auto_detect_parser(
    input_data: str | Path, registry: Optional[ParserRegistry] = None
) -> RequirementParser:
    """Automatically detect and create the appropriate parser.
    
    Args:
        input_data: Either a file path or content string
        registry: Optional ParserRegistry to use. If None, uses the global registry.
    
    Returns:
        Parser instance appropriate for the input
    
    Raises:
        ValueError: If no suitable parser can be determined
    """
    factory = ParserFactory(registry)

    # If it's a Path or looks like a file path, use file extension
    if isinstance(input_data, Path):
        return factory.create_parser_for_file(input_data)

    if isinstance(input_data, str):
        # Try to interpret as a file path
        try:
            path = Path(input_data)
            if path.exists() and path.is_file():
                return factory.create_parser_for_file(path)
        except (OSError, ValueError):
            # Not a valid file path, treat as content
            pass

        # For content strings, we need heuristics or default parser
        # This is a simple heuristic - can be enhanced
        if input_data.strip().startswith("#"):
            # Looks like Markdown
            return factory.create_parser("markdown")

    raise ValueError(
        "Could not auto-detect parser for input. "
        "Please specify parser explicitly or provide a file path."
    )
