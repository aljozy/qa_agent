"""Auto-registration of built-in parsers.

This module automatically registers all built-in parsers when imported.
"""

from qa_agent.parsers.base import register_parser
from qa_agent.parsers.markdown_parser import MarkdownParser


def register_builtin_parsers() -> None:
    """Register all built-in parsers in the global registry."""
    register_parser(MarkdownParser)


# Auto-register on import
register_builtin_parsers()
