"""AI-Powered QA Agent for intelligent test automation and artifact generation.

This package provides an intelligent test automation system that analyzes software
requirements from multiple sources and automatically generates comprehensive testing
artifacts using AI agent architecture, Retrieval Augmented Generation (RAG), and
Model Context Protocol (MCP) servers.

Key Features:
    - Multi-format requirement ingestion (Markdown, Jira, OpenAPI, SQL schemas)
    - Intelligent test case generation (manual and automated)
    - Requirement traceability matrix (RTM) generation
    - AI-powered test generation using Kiro or OpenAI
    - Modular plugin architecture
    - CLI and Python API interfaces

Example:
    >>> from qa_agent import __version__
    >>> print(__version__)
    0.1.0

For more information, see the documentation at:
https://github.com/qa-agent/qa-agent
"""

__version__ = "0.1.0"
__author__ = "QA Agent Team"
__email__ = "qa-agent@example.com"
__license__ = "MIT"
__copyright__ = "Copyright 2024 QA Agent Team"

# Version information tuple for programmatic access
VERSION = tuple(map(int, __version__.split(".")))

# Public API exports
__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__copyright__",
    "VERSION",
]
