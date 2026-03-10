"""Requirement parsers for various input formats."""

from qa_agent.parsers.base import (
    ParserRegistry,
    RequirementParser,
    get_global_registry,
    register_parser,
)
from qa_agent.parsers.factory import (
    ParserFactory,
    auto_detect_parser,
    create_parser_from_config,
)
from qa_agent.parsers.jira_parser import JiraParser
from qa_agent.parsers.markdown_parser import MarkdownParser
from qa_agent.parsers.openapi_parser import OpenAPIParser

__all__ = [
    "RequirementParser",
    "ParserRegistry",
    "get_global_registry",
    "register_parser",
    "ParserFactory",
    "create_parser_from_config",
    "auto_detect_parser",
    "JiraParser",
    "MarkdownParser",
    "OpenAPIParser",
]
