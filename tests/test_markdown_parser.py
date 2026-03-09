"""Tests for Markdown parser."""

from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from qa_agent.models.base import RequirementType
from qa_agent.parsers import MarkdownParser


class TestMarkdownParser:
    """Tests for MarkdownParser class."""

    def test_parse_simple_markdown(self) -> None:
        """Test parsing simple Markdown document."""
        content = """
# User Authentication

## Requirements

- The system shall provide user login functionality
- The system shall support password reset
- Users can register with email and password
"""
        parser = MarkdownParser()
        requirements = parser.parse(content)

        assert len(requirements) == 3
        assert all(req.type == RequirementType.FUNCTIONAL for req in requirements)
        assert requirements[0].content == "The system shall provide user login functionality"
        assert requirements[1].content == "The system shall support password reset"
        assert requirements[2].content == "Users can register with email and password"

    def test_parse_with_headings(self) -> None:
        """Test that headings are preserved in metadata."""
        content = """
# Main Feature

## Sub Feature

- Requirement under sub feature
"""
        parser = MarkdownParser()
        requirements = parser.parse(content)

        assert len(requirements) == 1
        assert requirements[0].metadata["section"] == "Sub Feature"
        assert requirements[0].metadata["heading_level"] == 2

    def test_parse_numbered_list(self) -> None:
        """Test parsing numbered lists."""
        content = """
# Requirements

1. First requirement
2. Second requirement
3. Third requirement
"""
        parser = MarkdownParser()
        requirements = parser.parse(content)

        assert len(requirements) == 3
        assert requirements[0].content == "First requirement"
        assert requirements[1].content == "Second requirement"
        assert requirements[2].content == "Third requirement"

    def test_parse_paragraphs(self) -> None:
        """Test parsing paragraph requirements."""
        content = """
# Overview

The system must provide authentication capabilities.

The application will support multiple user roles.
"""
        parser = MarkdownParser()
        requirements = parser.parse(content)

        # Paragraphs separated by blank lines are combined into one requirement per section
        assert len(requirements) >= 1
        assert "authentication" in requirements[0].content.lower()
        # Both paragraphs should be in the content
        assert "user roles" in requirements[0].content.lower() or (
            len(requirements) > 1 and "user roles" in requirements[1].content.lower()
        )

    def test_parse_mixed_content(self) -> None:
        """Test parsing mixed bullets and paragraphs."""
        content = """
# Feature

The system shall provide core functionality.

- Bullet requirement one
- Bullet requirement two

Another paragraph requirement.
"""
        parser = MarkdownParser()
        requirements = parser.parse(content)

        assert len(requirements) == 4

    def test_parse_multiline_bullet(self) -> None:
        """Test parsing multi-line bullet points."""
        content = """
# Requirements

- This is a long requirement
  that spans multiple lines
  and should be combined
"""
        parser = MarkdownParser()
        requirements = parser.parse(content)

        assert len(requirements) == 1
        assert "multiple lines" in requirements[0].content
        assert "combined" in requirements[0].content

    def test_requirement_id_generation(self) -> None:
        """Test that requirement IDs are generated automatically."""
        content = """
# Requirements

- First requirement
- Second requirement
- Third requirement
"""
        parser = MarkdownParser()
        requirements = parser.parse(content)

        assert requirements[0].id == "REQ-0001"
        assert requirements[1].id == "REQ-0002"
        assert requirements[2].id == "REQ-0003"

    def test_classify_functional_requirements(self) -> None:
        """Test classification of functional requirements."""
        content = """
# Requirements

- The system shall process payments
- Users must be able to view their profile
- The application will send notifications
"""
        parser = MarkdownParser()
        requirements = parser.parse(content)

        assert all(req.type == RequirementType.FUNCTIONAL for req in requirements)

    def test_hierarchy_preservation(self) -> None:
        """Test that document hierarchy is preserved."""
        content = """
# Level 1

## Level 2

### Level 3

- Requirement at level 3
"""
        parser = MarkdownParser()
        requirements = parser.parse(content)

        assert len(requirements) == 1
        assert requirements[0].metadata["heading_level"] == 3
        assert "Level 3" in requirements[0].metadata["hierarchy"]

    def test_parse_empty_content(self) -> None:
        """Test that empty content raises error."""
        parser = MarkdownParser()

        with pytest.raises(ValueError, match="Markdown content cannot be empty"):
            parser.parse("")

        with pytest.raises(ValueError, match="Markdown content cannot be empty"):
            parser.parse("   ")

    def test_validate_valid_markdown(self) -> None:
        """Test validation of valid Markdown."""
        content = """
# Heading

- Requirement one
- Requirement two
"""
        parser = MarkdownParser()
        result = parser.validate(content)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_empty_content(self) -> None:
        """Test validation of empty content."""
        parser = MarkdownParser()
        result = parser.validate("")

        assert result.is_valid is False
        assert "empty" in result.errors[0].lower()

    def test_validate_no_headings(self) -> None:
        """Test validation warns about missing headings."""
        content = "Just some text without headings"
        parser = MarkdownParser()
        result = parser.validate(content)

        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert "headings" in result.warnings[0].lower()

    def test_validate_short_document(self) -> None:
        """Test validation warns about short documents."""
        content = "# Title"
        parser = MarkdownParser()
        result = parser.validate(content)

        assert result.is_valid is True
        assert any("short" in w.lower() for w in result.warnings)

    def test_parse_file_success(self) -> None:
        """Test parsing from file."""
        content = """
# Requirements

- Requirement from file
"""
        with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            parser = MarkdownParser()
            requirements = parser.parse_file(temp_path)

            assert len(requirements) == 1
            assert requirements[0].content == "Requirement from file"
            assert str(temp_path) in requirements[0].source
        finally:
            Path(temp_path).unlink()

    def test_parse_file_not_found(self) -> None:
        """Test parsing non-existent file."""
        parser = MarkdownParser()

        with pytest.raises(FileNotFoundError, match="File not found"):
            parser.parse_file("nonexistent.md")

    def test_parse_file_invalid_path(self) -> None:
        """Test parsing with directory path."""
        parser = MarkdownParser()

        with pytest.raises(ValueError, match="Path is not a file"):
            parser.parse_file("/tmp")

    def test_skip_code_blocks(self) -> None:
        """Test that code blocks are skipped."""
        content = """
# Requirements

- Real requirement

```python
# This is code, not a requirement
def example():
    pass
```

- Another real requirement
"""
        parser = MarkdownParser()
        requirements = parser.parse(content)

        # Should only get the two bullet points, not the code
        assert len(requirements) == 2
        assert "Real requirement" in requirements[0].content
        assert "Another real requirement" in requirements[1].content

    def test_different_bullet_styles(self) -> None:
        """Test parsing different bullet point styles."""
        content = """
# Requirements

- Dash bullet
* Asterisk bullet
+ Plus bullet
"""
        parser = MarkdownParser()
        requirements = parser.parse(content)

        assert len(requirements) == 3
        assert requirements[0].content == "Dash bullet"
        assert requirements[1].content == "Asterisk bullet"
        assert requirements[2].content == "Plus bullet"

    def test_source_tracking(self) -> None:
        """Test that source is tracked correctly."""
        content = """
# Requirements

- Test requirement
"""
        parser = MarkdownParser()
        requirements = parser.parse(content, source="test-doc.md")

        assert requirements[0].source == "test-doc.md"

    def test_metadata_structure(self) -> None:
        """Test that metadata contains expected fields."""
        content = """
# Main Section

## Subsection

- Requirement with metadata
"""
        parser = MarkdownParser()
        requirements = parser.parse(content)

        assert "section" in requirements[0].metadata
        assert "heading_level" in requirements[0].metadata
        assert "hierarchy" in requirements[0].metadata
        assert requirements[0].metadata["section"] == "Subsection"
        assert requirements[0].metadata["heading_level"] == 2
