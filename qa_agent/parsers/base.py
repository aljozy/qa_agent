"""Base parser interface and plugin architecture for requirement parsers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Type

from qa_agent.models.base import Requirement, ValidationResult


class RequirementParser(ABC):
    """Abstract base class for requirement parsers.
    
    All parser implementations must inherit from this class and implement
    the abstract methods. This enables a plugin architecture where new
    parsers can be added without modifying the core system.
    """

    # Parser metadata - subclasses should override these
    name: str = "base_parser"
    supported_extensions: List[str] = []
    description: str = "Base requirement parser"

    @abstractmethod
    def parse(self, input_data: str | Path) -> List[Requirement]:
        """Parse input and return structured requirements.
        
        Args:
            input_data: Either a string containing the content to parse,
                       or a Path to a file to parse
        
        Returns:
            List of parsed Requirement objects
        
        Raises:
            ValueError: If input_data is invalid or cannot be parsed
            FileNotFoundError: If input_data is a Path that doesn't exist
        """
        pass

    @abstractmethod
    def validate(self, input_data: str | Path) -> ValidationResult:
        """Validate input format before parsing.
        
        Args:
            input_data: Either a string containing the content to validate,
                       or a Path to a file to validate
        
        Returns:
            ValidationResult indicating whether the input is valid,
            along with any errors or warnings
        """
        pass

    def supports_file(self, file_path: Path) -> bool:
        """Check if this parser supports the given file.
        
        Args:
            file_path: Path to the file to check
        
        Returns:
            True if this parser supports the file extension, False otherwise
        """
        if not self.supported_extensions:
            return False
        
        suffix = file_path.suffix.lower()
        return suffix in self.supported_extensions

    def get_metadata(self) -> Dict[str, any]:
        """Get parser metadata.
        
        Returns:
            Dictionary containing parser name, supported extensions, and description
        """
        return {
            "name": self.name,
            "supported_extensions": self.supported_extensions,
            "description": self.description,
        }


class ParserRegistry:
    """Registry for managing parser plugins.
    
    This class implements the plugin discovery and registration system,
    allowing parsers to be dynamically registered and retrieved based on
    file extensions or parser names.
    """

    def __init__(self):
        """Initialize the parser registry."""
        self._parsers: Dict[str, Type[RequirementParser]] = {}
        self._extension_map: Dict[str, str] = {}

    def register(self, parser_class: Type[RequirementParser]) -> None:
        """Register a parser plugin.
        
        Args:
            parser_class: The parser class to register (not an instance)
        
        Raises:
            ValueError: If parser_class is not a subclass of RequirementParser
            ValueError: If a parser with the same name is already registered
        """
        if not issubclass(parser_class, RequirementParser):
            raise ValueError(
                f"Parser class must be a subclass of RequirementParser, "
                f"got {parser_class.__name__}"
            )

        # Create a temporary instance to get metadata
        temp_instance = parser_class()
        parser_name = temp_instance.name

        if parser_name in self._parsers:
            raise ValueError(f"Parser '{parser_name}' is already registered")

        # Register the parser class
        self._parsers[parser_name] = parser_class

        # Register file extension mappings
        for ext in temp_instance.supported_extensions:
            ext_lower = ext.lower()
            if ext_lower in self._extension_map:
                # Log warning but allow override
                existing_parser = self._extension_map[ext_lower]
                print(
                    f"Warning: Extension '{ext}' was mapped to '{existing_parser}', "
                    f"now remapping to '{parser_name}'"
                )
            self._extension_map[ext_lower] = parser_name

    def unregister(self, parser_name: str) -> None:
        """Unregister a parser plugin.
        
        Args:
            parser_name: Name of the parser to unregister
        
        Raises:
            KeyError: If parser is not registered
        """
        if parser_name not in self._parsers:
            raise KeyError(f"Parser '{parser_name}' is not registered")

        # Remove extension mappings
        parser_class = self._parsers[parser_name]
        temp_instance = parser_class()
        for ext in temp_instance.supported_extensions:
            ext_lower = ext.lower()
            if self._extension_map.get(ext_lower) == parser_name:
                del self._extension_map[ext_lower]

        # Remove parser
        del self._parsers[parser_name]

    def get_parser(self, parser_name: str) -> RequirementParser:
        """Get a parser instance by name.
        
        Args:
            parser_name: Name of the parser to retrieve
        
        Returns:
            Instance of the requested parser
        
        Raises:
            KeyError: If parser is not registered
        """
        if parser_name not in self._parsers:
            raise KeyError(
                f"Parser '{parser_name}' is not registered. "
                f"Available parsers: {list(self._parsers.keys())}"
            )

        parser_class = self._parsers[parser_name]
        return parser_class()

    def get_parser_for_file(self, file_path: Path) -> Optional[RequirementParser]:
        """Get a parser instance for the given file.
        
        Args:
            file_path: Path to the file
        
        Returns:
            Parser instance that supports the file extension, or None if no parser found
        """
        suffix = file_path.suffix.lower()
        parser_name = self._extension_map.get(suffix)

        if parser_name is None:
            return None

        return self.get_parser(parser_name)

    def list_parsers(self) -> List[Dict[str, any]]:
        """List all registered parsers with their metadata.
        
        Returns:
            List of dictionaries containing parser metadata
        """
        parsers_info = []
        for parser_name, parser_class in self._parsers.items():
            temp_instance = parser_class()
            parsers_info.append(temp_instance.get_metadata())
        return parsers_info

    def is_registered(self, parser_name: str) -> bool:
        """Check if a parser is registered.
        
        Args:
            parser_name: Name of the parser to check
        
        Returns:
            True if parser is registered, False otherwise
        """
        return parser_name in self._parsers

    def get_supported_extensions(self) -> List[str]:
        """Get all supported file extensions.
        
        Returns:
            List of supported file extensions
        """
        return list(self._extension_map.keys())


# Global parser registry instance
_global_registry: Optional[ParserRegistry] = None


def get_global_registry() -> ParserRegistry:
    """Get the global parser registry instance.
    
    Returns:
        The global ParserRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ParserRegistry()
    return _global_registry


def register_parser(parser_class: Type[RequirementParser]) -> None:
    """Register a parser in the global registry.
    
    This is a convenience function for registering parsers in the global registry.
    
    Args:
        parser_class: The parser class to register
    """
    registry = get_global_registry()
    registry.register(parser_class)
