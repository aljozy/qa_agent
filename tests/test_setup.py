"""Test to verify the project setup is correct."""

import qa_agent


def test_version_exists() -> None:
    """Test that the package version is defined."""
    assert hasattr(qa_agent, "__version__")
    assert isinstance(qa_agent.__version__, str)
    assert qa_agent.__version__ == "0.1.0"


def test_package_imports() -> None:
    """Test that the package can be imported."""
    import qa_agent.analysis
    import qa_agent.config
    import qa_agent.generators
    import qa_agent.mcp
    import qa_agent.models
    import qa_agent.parsers
    import qa_agent.rag
    import qa_agent.vector_store

    assert qa_agent.analysis is not None
    assert qa_agent.config is not None
    assert qa_agent.generators is not None
    assert qa_agent.mcp is not None
    assert qa_agent.models is not None
    assert qa_agent.parsers is not None
    assert qa_agent.rag is not None
    assert qa_agent.vector_store is not None
