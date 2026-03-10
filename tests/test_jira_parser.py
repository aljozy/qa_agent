"""Tests for Jira user story parser."""

import pytest
from pathlib import Path

from qa_agent.models.base import RequirementType
from qa_agent.parsers.jira_parser import JiraParser


# Sample valid Jira story
VALID_STORY = """Title: User Login

As a user, I want to log in to the system so that I can access my account

Acceptance Criteria:
- Valid credentials should be accepted
- Invalid credentials should be rejected
- Account should be locked after 3 failed attempts
"""

# Story without benefit clause
STORY_WITHOUT_BENEFIT = """Title: View Dashboard

As a user, I want to view my dashboard

Acceptance Criteria:
- Dashboard should display recent activity
- Dashboard should show account summary
"""

# Story with numbered acceptance criteria
STORY_WITH_NUMBERED_AC = """Title: Password Reset

As a user, I want to reset my password so that I can regain access to my account

Acceptance Criteria:
1. User should receive reset email
2. Reset link should expire after 24 hours
3. New password must meet complexity requirements
"""

# Malformed story - missing title
MALFORMED_NO_TITLE = """As a user, I want to do something

Acceptance Criteria:
- Some criterion
"""

# Malformed story - missing user story
MALFORMED_NO_USER_STORY = """Title: Some Feature

Acceptance Criteria:
- Some criterion
"""

# Malformed story - missing acceptance criteria
MALFORMED_NO_AC = """Title: Some Feature

As a user, I want to do something
"""

# Empty acceptance criteria
EMPTY_AC = """Title: Some Feature

As a user, I want to do something

Acceptance Criteria:
"""


class TestJiraParser:
    """Tests for JiraParser class."""

    def test_parser_metadata(self):
        """Test that parser has correct metadata."""
        parser = JiraParser()
        assert parser.name == "jira"
        assert ".jira" in parser.supported_extensions
        assert ".txt" in parser.supported_extensions
        assert ".story" in parser.supported_extensions
        assert "Jira" in parser.description

    def test_parse_valid_story(self):
        """Test parsing a valid user story."""
        parser = JiraParser()
        requirements = parser.parse(VALID_STORY)

        # Should return main story + 3 acceptance criteria = 4 requirements
        assert len(requirements) == 4

        # Check main story
        main_story = requirements[0]
        assert main_story.type == RequirementType.USER_STORY
        assert main_story.id.startswith("STORY-")
        assert "USER-LOGIN" in main_story.id
        assert main_story.metadata["title"] == "User Login"
        assert main_story.metadata["role"] == "user"
        assert main_story.metadata["goal"] == "log in to the system"
        assert main_story.metadata["benefit"] == "I can access my account"
        assert main_story.metadata["acceptance_criteria_count"] == 3

        # Check acceptance criteria
        for idx in range(1, 4):
            ac = requirements[idx]
            assert ac.type == RequirementType.USER_STORY
            assert ac.id == f"{main_story.id}-AC{idx}"
            assert ac.metadata["parent_story_id"] == main_story.id
            assert ac.metadata["criterion_number"] == idx
            assert ac.metadata["is_acceptance_criterion"] is True
            assert len(ac.content) > 0

    def test_parse_story_without_benefit(self):
        """Test parsing a story without benefit clause."""
        parser = JiraParser()
        requirements = parser.parse(STORY_WITHOUT_BENEFIT)

        assert len(requirements) == 3  # Main story + 2 AC

        main_story = requirements[0]
        assert main_story.metadata["role"] == "user"
        assert main_story.metadata["goal"] == "view my dashboard"
        assert main_story.metadata["benefit"] == ""

    def test_parse_story_with_numbered_ac(self):
        """Test parsing a story with numbered acceptance criteria."""
        parser = JiraParser()
        requirements = parser.parse(STORY_WITH_NUMBERED_AC)

        assert len(requirements) == 4  # Main story + 3 AC

        # Check that numbered items are parsed correctly
        ac1 = requirements[1]
        assert "reset email" in ac1.content.lower()

        ac2 = requirements[2]
        assert "24 hours" in ac2.content.lower()

        ac3 = requirements[3]
        assert "complexity requirements" in ac3.content.lower()

    def test_parse_from_file(self, tmp_path):
        """Test parsing from a file."""
        # Create a test file
        test_file = tmp_path / "story.jira"
        test_file.write_text(VALID_STORY, encoding="utf-8")

        parser = JiraParser()
        requirements = parser.parse(test_file)

        assert len(requirements) == 4
        assert requirements[0].source == str(test_file)

    def test_parse_nonexistent_file(self):
        """Test parsing a non-existent file raises error."""
        parser = JiraParser()
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/file.jira"))

    def test_parse_malformed_no_title(self):
        """Test parsing malformed story without title."""
        parser = JiraParser()
        with pytest.raises(ValueError, match="Invalid Jira story format"):
            parser.parse(MALFORMED_NO_TITLE)

    def test_parse_malformed_no_user_story(self):
        """Test parsing malformed story without user story."""
        parser = JiraParser()
        with pytest.raises(ValueError, match="Invalid Jira story format"):
            parser.parse(MALFORMED_NO_USER_STORY)

    def test_parse_malformed_no_ac(self):
        """Test parsing malformed story without acceptance criteria."""
        parser = JiraParser()
        with pytest.raises(ValueError, match="Invalid Jira story format"):
            parser.parse(MALFORMED_NO_AC)

    def test_validate_valid_story(self):
        """Test validating a valid story."""
        parser = JiraParser()
        result = parser.validate(VALID_STORY)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_story_without_benefit(self):
        """Test validating a story without benefit clause (should be valid)."""
        parser = JiraParser()
        result = parser.validate(STORY_WITHOUT_BENEFIT)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_malformed_no_title(self):
        """Test validating story without title."""
        parser = JiraParser()
        result = parser.validate(MALFORMED_NO_TITLE)

        assert not result.is_valid
        assert any("Title" in error for error in result.errors)

    def test_validate_malformed_no_user_story(self):
        """Test validating story without user story."""
        parser = JiraParser()
        result = parser.validate(MALFORMED_NO_USER_STORY)

        assert not result.is_valid
        assert any("user story" in error.lower() for error in result.errors)

    def test_validate_malformed_no_ac(self):
        """Test validating story without acceptance criteria."""
        parser = JiraParser()
        result = parser.validate(MALFORMED_NO_AC)

        assert not result.is_valid
        assert any("Acceptance Criteria" in error for error in result.errors)

    def test_validate_empty_content(self):
        """Test validating empty content."""
        parser = JiraParser()
        result = parser.validate("")

        assert not result.is_valid
        assert any("empty" in error.lower() for error in result.errors)

    def test_validate_empty_ac_section(self):
        """Test validating story with empty acceptance criteria section."""
        parser = JiraParser()
        result = parser.validate(EMPTY_AC)

        assert not result.is_valid
        assert any("empty" in error.lower() for error in result.errors)

    def test_validate_from_file(self, tmp_path):
        """Test validating from a file."""
        test_file = tmp_path / "story.jira"
        test_file.write_text(VALID_STORY, encoding="utf-8")

        parser = JiraParser()
        result = parser.validate(test_file)

        assert result.is_valid

    def test_validate_nonexistent_file(self):
        """Test validating a non-existent file."""
        parser = JiraParser()
        result = parser.validate(Path("/nonexistent/file.jira"))

        assert not result.is_valid
        assert any("not found" in error.lower() for error in result.errors)

    def test_supports_file(self):
        """Test file extension support."""
        parser = JiraParser()

        assert parser.supports_file(Path("story.jira"))
        assert parser.supports_file(Path("story.txt"))
        assert parser.supports_file(Path("story.story"))
        assert not parser.supports_file(Path("story.md"))
        assert not parser.supports_file(Path("story.json"))

    def test_get_metadata(self):
        """Test getting parser metadata."""
        parser = JiraParser()
        metadata = parser.get_metadata()

        assert metadata["name"] == "jira"
        assert ".jira" in metadata["supported_extensions"]
        assert "description" in metadata

    def test_story_id_generation(self):
        """Test that story IDs are generated correctly."""
        parser = JiraParser()
        requirements = parser.parse(VALID_STORY)

        main_story = requirements[0]
        assert main_story.id == "STORY-USER-LOGIN"

        # Check that AC IDs are based on main story ID
        assert requirements[1].id == "STORY-USER-LOGIN-AC1"
        assert requirements[2].id == "STORY-USER-LOGIN-AC2"
        assert requirements[3].id == "STORY-USER-LOGIN-AC3"

    def test_story_id_special_characters(self):
        """Test story ID generation with special characters."""
        story = """Title: User's Login & Authentication!

As a user, I want to log in

Acceptance Criteria:
- Valid credentials accepted
"""
        parser = JiraParser()
        requirements = parser.parse(story)

        # Special characters should be removed
        assert "STORY-USERS-LOGIN-AUTHENTICATION" in requirements[0].id

    def test_acceptance_criteria_content(self):
        """Test that acceptance criteria content is extracted correctly."""
        parser = JiraParser()
        requirements = parser.parse(VALID_STORY)

        # Check AC content
        ac1 = requirements[1]
        assert "Valid credentials should be accepted" == ac1.content

        ac2 = requirements[2]
        assert "Invalid credentials should be rejected" == ac2.content

        ac3 = requirements[3]
        assert "Account should be locked after 3 failed attempts" == ac3.content

    def test_case_insensitive_parsing(self):
        """Test that parsing is case-insensitive for keywords."""
        story = """title: User Login

as a user, i want to log in

acceptance criteria:
- Valid credentials accepted
"""
        parser = JiraParser()
        requirements = parser.parse(story)

        assert len(requirements) == 2
        assert requirements[0].metadata["title"] == "User Login"

    def test_alternative_ac_header(self):
        """Test parsing with 'AC:' instead of 'Acceptance Criteria:'."""
        story = """Title: User Login

As a user, I want to log in

AC:
- Valid credentials accepted
- Invalid credentials rejected
"""
        parser = JiraParser()
        requirements = parser.parse(story)

        assert len(requirements) == 3
        assert requirements[0].metadata["acceptance_criteria_count"] == 2

    def test_bullet_variations(self):
        """Test parsing with different bullet point styles."""
        story = """Title: User Login

As a user, I want to log in

Acceptance Criteria:
- Criterion with dash
* Criterion with asterisk
• Criterion with bullet
"""
        parser = JiraParser()
        requirements = parser.parse(story)

        assert len(requirements) == 4
        assert "dash" in requirements[1].content
        assert "asterisk" in requirements[2].content
        assert "bullet" in requirements[3].content

    def test_multiline_acceptance_criteria(self):
        """Test that each line is treated as a separate criterion."""
        story = """Title: User Login

As a user, I want to log in

Acceptance Criteria:
- First criterion
- Second criterion
- Third criterion
"""
        parser = JiraParser()
        requirements = parser.parse(story)

        assert len(requirements) == 4
        assert requirements[1].content == "First criterion"
        assert requirements[2].content == "Second criterion"
        assert requirements[3].content == "Third criterion"


class TestJiraParserIntegration:
    """Integration tests for Jira parser."""

    def test_parser_registration(self):
        """Test that Jira parser can be registered and retrieved."""
        from qa_agent.parsers.base import ParserRegistry

        registry = ParserRegistry()
        registry.register(JiraParser)

        assert registry.is_registered("jira")

        parser = registry.get_parser("jira")
        assert isinstance(parser, JiraParser)

    def test_parser_file_detection(self):
        """Test that parser is selected for .jira files."""
        from qa_agent.parsers.base import ParserRegistry

        registry = ParserRegistry()
        registry.register(JiraParser)

        parser = registry.get_parser_for_file(Path("story.jira"))
        assert isinstance(parser, JiraParser)

    def test_end_to_end_workflow(self, tmp_path):
        """Test complete workflow from file to parsed requirements."""
        from qa_agent.parsers.base import ParserRegistry

        # Create test file
        test_file = tmp_path / "user_login.jira"
        test_file.write_text(VALID_STORY, encoding="utf-8")

        # Register parser
        registry = ParserRegistry()
        registry.register(JiraParser)

        # Get parser for file
        parser = registry.get_parser_for_file(test_file)
        assert parser is not None

        # Validate
        validation = parser.validate(test_file)
        assert validation.is_valid

        # Parse
        requirements = parser.parse(test_file)
        assert len(requirements) == 4

        # Verify structure
        main_story = requirements[0]
        assert main_story.type == RequirementType.USER_STORY
        assert main_story.metadata["acceptance_criteria_count"] == 3

        for idx in range(1, 4):
            ac = requirements[idx]
            assert ac.metadata["parent_story_id"] == main_story.id
            assert ac.metadata["is_acceptance_criterion"] is True
