"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def sample_config() -> dict:
    """Provide a sample configuration for testing."""
    return {
        "ai_model": {
            "model_name": "gpt-4-turbo-preview",
            "temperature": 0.7,
            "max_tokens": 4096,
        },
        "vector_store": {
            "host": "localhost",
            "port": 6333,
            "collection_name": "test_requirements",
        },
        "output": {
            "directory": "./test_output",
            "format": "json",
        },
    }
