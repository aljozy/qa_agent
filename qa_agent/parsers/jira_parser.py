"""Jira user story parser implementation."""

import re
from pathlib import Path
from typing import List

from qa_agent.models.base import Requirement, RequirementType, ValidationResult
from qa_agent.parsers.base import RequirementParser


class JiraParser(RequirementParser):
    """Parser for Jira-style user stories.
    
    Parses user stories in Jira format, extracting:
    - Story title
    - Story description
    - Acceptance criteria (each as a separate testable item)
    
    Expected format:
        Title: <story title>
        
        As a <role>, I want <goal> [so that <benefit>]
        
        Acceptance Criteria:
        - <criterion 1>
        - <criterion 2>
        ...
    
    Alternative formats supported:
    - "AC:" or "Acceptance Criteria:" section headers
    - Numbered lists (1., 2., etc.)
    - Bullet points (-, *, •)
    """

    name = "jira"
    supported_extensions = [".jira", ".txt", ".story"]
    description = "Parser for Jira-style user stories"

    # Regex patterns for parsing
    TITLE_PATTERN = re.compile(r"^Title:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
    USER_STORY_PATTERN = re.compile(
        r"As\s+an?\s+(.+?),\s*I\s+want\s+(?:to\s+)?(.+?)(?:\s+so\s+that\s+(.+?))?(?:\n|$)",
        re.IGNORECASE | re.DOTALL,
    )
    AC_SECTION_PATTERN = re.compile(
        r"(?:Acceptance\s+Criteria|AC):\s*\n((?:[-*•\d.]\s*.+\n?)*)",
        re.IGNORECASE | re.MULTILINE,
    )
    AC_ITEM_PATTERN = re.compile(r"^[-*•]|\d+\.", re.MULTILINE)

    def parse(self, input_data: str | Path) -> List[Requirement]:
        """Parse Jira user story and return structured requirements.
        
        Args:
            input_data: Either a string containing the story content,
                       or a Path to a file containing the story
        
        Returns:
            List of Requirement objects - one for the main story and
            one for each acceptance criterion
        
        Raises:
            ValueError: If input_data is invalid or cannot be parsed
            FileNotFoundError: If input_data is a Path that doesn't exist
        """
        # Read content from file or use string directly
        if isinstance(input_data, Path):
            if not input_data.exists():
                raise FileNotFoundError(f"File not found: {input_data}")
            with open(input_data, "r", encoding="utf-8") as f:
                content = f.read()
            source = str(input_data)
        else:
            content = input_data
            source = "string_input"

        # Validate before parsing
        validation = self.validate(content)
        if not validation.is_valid:
            error_msg = "; ".join(validation.errors)
            raise ValueError(f"Invalid Jira story format: {error_msg}")

        # Extract components
        title = self._extract_title(content)
        user_story = self._extract_user_story(content)
        acceptance_criteria = self._extract_acceptance_criteria(content)

        # Create requirements list
        requirements = []

        # Create main story requirement
        story_id = self._generate_story_id(title)
        main_requirement = Requirement(
            id=story_id,
            type=RequirementType.USER_STORY,
            content=content,
            metadata={
                "title": title,
                "user_story": user_story,
                "role": user_story.get("role", ""),
                "goal": user_story.get("goal", ""),
                "benefit": user_story.get("benefit", ""),
                "acceptance_criteria_count": len(acceptance_criteria),
            },
            source=source,
        )
        requirements.append(main_requirement)

        # Create separate requirements for each acceptance criterion
        for idx, criterion in enumerate(acceptance_criteria, start=1):
            ac_id = f"{story_id}-AC{idx}"
            ac_requirement = Requirement(
                id=ac_id,
                type=RequirementType.USER_STORY,
                content=criterion,
                metadata={
                    "parent_story_id": story_id,
                    "criterion_number": idx,
                    "is_acceptance_criterion": True,
                },
                source=source,
            )
            requirements.append(ac_requirement)

        return requirements

    def validate(self, input_data: str | Path) -> ValidationResult:
        """Validate Jira user story format.
        
        Args:
            input_data: Either a string containing the story content,
                       or a Path to a file to validate
        
        Returns:
            ValidationResult indicating whether the input is valid,
            along with any errors or warnings
        """
        errors = []
        warnings = []

        # Read content from file or use string directly
        if isinstance(input_data, Path):
            if not input_data.exists():
                return ValidationResult(
                    is_valid=False,
                    errors=[f"File not found: {input_data}"],
                )
            try:
                with open(input_data, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Error reading file: {str(e)}"],
                )
        else:
            content = input_data

        # Check if content is empty
        if not content or not content.strip():
            errors.append("Story content is empty")
            return ValidationResult(is_valid=False, errors=errors)

        # Check for title
        if not self.TITLE_PATTERN.search(content):
            errors.append("Missing required 'Title:' field")

        # Check for user story format
        if not self.USER_STORY_PATTERN.search(content):
            errors.append(
                "Missing or malformed user story. Expected format: "
                "'As a <role>, I want <goal> [so that <benefit>]'"
            )

        # Check for acceptance criteria
        ac_match = self.AC_SECTION_PATTERN.search(content)
        if not ac_match:
            errors.append(
                "Missing 'Acceptance Criteria:' section. "
                "Expected format: 'Acceptance Criteria:' followed by list items"
            )
        else:
            # Validate that acceptance criteria section has items
            ac_section = ac_match.group(1)
            criteria = self._parse_list_items(ac_section)
            if not criteria or len(criteria) == 0:
                errors.append("Acceptance Criteria section is empty or has no valid items")
            elif len(criteria) == 1:
                warnings.append("Only one acceptance criterion found. Consider adding more.")

        # Determine validity
        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            metadata={"content_length": len(content)},
        )

    def _extract_title(self, content: str) -> str:
        """Extract story title from content.
        
        Args:
            content: Story content
        
        Returns:
            Story title or empty string if not found
        """
        match = self.TITLE_PATTERN.search(content)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_user_story(self, content: str) -> dict:
        """Extract user story components (role, goal, benefit).
        
        Args:
            content: Story content
        
        Returns:
            Dictionary with 'role', 'goal', and 'benefit' keys
        """
        match = self.USER_STORY_PATTERN.search(content)
        if match:
            role = match.group(1).strip()
            goal = match.group(2).strip()
            benefit = match.group(3).strip() if match.group(3) else ""
            return {
                "role": role,
                "goal": goal,
                "benefit": benefit,
            }
        return {"role": "", "goal": "", "benefit": ""}

    def _extract_acceptance_criteria(self, content: str) -> List[str]:
        """Extract acceptance criteria from content.
        
        Args:
            content: Story content
        
        Returns:
            List of acceptance criteria strings
        """
        match = self.AC_SECTION_PATTERN.search(content)
        if not match:
            return []

        ac_section = match.group(1)
        return self._parse_list_items(ac_section)

    def _parse_list_items(self, text: str) -> List[str]:
        """Parse list items from text (supports bullets, numbers, etc.).
        
        Args:
            text: Text containing list items
        
        Returns:
            List of item strings with markers removed
        """
        items = []
        lines = text.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Remove list markers (-, *, •, 1., 2., etc.)
            cleaned = re.sub(r"^[-*•]\s*", "", line)
            cleaned = re.sub(r"^\d+\.\s*", "", cleaned)

            if cleaned:
                items.append(cleaned)

        return items

    def _generate_story_id(self, title: str) -> str:
        """Generate a story ID from the title.
        
        Args:
            title: Story title
        
        Returns:
            Generated story ID (e.g., "STORY-USER-LOGIN")
        """
        # Convert title to uppercase, replace spaces with hyphens
        # Remove special characters, limit length
        clean_title = re.sub(r"[^a-zA-Z0-9\s-]", "", title)
        clean_title = re.sub(r"\s+", "-", clean_title.strip())
        clean_title = clean_title.upper()[:50]  # Limit length

        return f"STORY-{clean_title}" if clean_title else "STORY-UNTITLED"
