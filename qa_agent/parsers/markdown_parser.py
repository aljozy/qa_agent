"""Markdown parser for extracting requirements from Markdown documents."""

import re
from pathlib import Path
from typing import List, Optional

from qa_agent.models.base import Requirement, RequirementType, ValidationResult
from qa_agent.parsers.base import RequirementParser


class MarkdownParser(RequirementParser):
    """Parser for Markdown PRD documents."""

    # Parser metadata
    name = "markdown"
    supported_extensions = [".md", ".markdown"]
    description = "Parser for Markdown requirement documents"

    # Keywords for classifying requirements
    FUNCTIONAL_KEYWORDS = [
        "shall",
        "must",
        "will",
        "should",
        "can",
        "feature",
        "function",
        "capability",
        "user can",
        "system shall",
        "application will",
    ]

    NON_FUNCTIONAL_KEYWORDS = [
        "performance",
        "scalability",
        "security",
        "reliability",
        "availability",
        "maintainability",
        "usability",
        "response time",
        "throughput",
        "latency",
    ]

    def __init__(self) -> None:
        """Initialize the Markdown parser."""
        self.requirement_counter = 0

    def parse(self, input_data: str | Path, source: str = "markdown") -> List[Requirement]:
        """
        Parse Markdown content and extract requirements.

        Args:
            input_data: Either Markdown content string or Path to a Markdown file
            source: Source identifier for the document (used when input_data is a string)

        Returns:
            List of parsed requirements

        Raises:
            ValueError: If content is empty or invalid
            FileNotFoundError: If input_data is a Path that doesn't exist
        """
        # Handle Path input
        if isinstance(input_data, Path):
            return self.parse_file(input_data)
        
        # Handle string input
        content = input_data
        if not content or not content.strip():
            raise ValueError("Markdown content cannot be empty")

        requirements: List[Requirement] = []
        lines = content.split("\n")

        # Filter out code blocks first
        filtered_lines = []
        in_code_block = False
        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if not in_code_block:
                filtered_lines.append(line)

        current_section: List[str] = []
        current_heading = ""
        heading_level = 0

        for line in filtered_lines:
            # Check if line is a heading
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)

            if heading_match:
                # Process previous section before starting new one
                if current_section:
                    reqs = self._extract_requirements_from_section(
                        current_section, current_heading, heading_level, source
                    )
                    requirements.extend(reqs)

                # Start new section
                heading_level = len(heading_match.group(1))
                current_heading = heading_match.group(2).strip()
                current_section = []
            else:
                # Add line to current section
                if line.strip():
                    current_section.append(line)

        # Process final section
        if current_section:
            reqs = self._extract_requirements_from_section(
                current_section, current_heading, heading_level, source
            )
            requirements.extend(reqs)

        return requirements

    def _extract_requirements_from_section(
        self, lines: List[str], heading: str, level: int, source: str
    ) -> List[Requirement]:
        """
        Extract requirements from a section of the document.

        Args:
            lines: Lines in the section
            heading: Section heading
            level: Heading level (1-6)
            source: Source identifier

        Returns:
            List of requirements extracted from the section
        """
        requirements: List[Requirement] = []

        # Extract bullet points
        bullet_requirements = self._extract_bullet_points(lines)

        # Extract paragraphs (excluding lines that are part of bullets)
        paragraph_requirements = self._extract_paragraphs_excluding_bullets(lines)

        # Combine all requirements
        all_requirements = bullet_requirements + paragraph_requirements

        # Create Requirement objects
        for req_text in all_requirements:
            if not req_text.strip():
                continue

            self.requirement_counter += 1
            req_type = self._classify_requirement(req_text)

            requirement = Requirement(
                id=f"REQ-{self.requirement_counter:04d}",
                type=req_type,
                content=req_text.strip(),
                source=source,
                metadata={
                    "section": heading,
                    "heading_level": level,
                    "hierarchy": self._build_hierarchy(heading, level),
                },
            )
            requirements.append(requirement)

        return requirements

    def _extract_bullet_points(self, lines: List[str]) -> List[str]:
        """
        Extract bullet points from lines.

        Args:
            lines: Lines to extract from

        Returns:
            List of bullet point texts
        """
        bullet_points: List[str] = []
        current_bullet = ""
        in_bullet = False

        for line in lines:
            # Match bullet points (-, *, +, or numbered lists)
            bullet_match = re.match(r"^[\s]*[-*+]\s+(.+)$", line)
            numbered_match = re.match(r"^[\s]*\d+\.\s+(.+)$", line)

            if bullet_match or numbered_match:
                # Save previous bullet if exists
                if current_bullet:
                    bullet_points.append(current_bullet)

                # Start new bullet
                text = bullet_match.group(1) if bullet_match else numbered_match.group(1)
                current_bullet = text.strip()
                in_bullet = True
            elif in_bullet and line.strip() and not line.strip().startswith("#"):
                # Continuation of current bullet (indented line)
                if re.match(r"^\s{2,}", line):  # At least 2 spaces indent
                    current_bullet += " " + line.strip()
                else:
                    # Not indented enough, end current bullet
                    if current_bullet:
                        bullet_points.append(current_bullet)
                    current_bullet = ""
                    in_bullet = False
            elif not line.strip():
                # Empty line ends bullet
                if current_bullet:
                    bullet_points.append(current_bullet)
                current_bullet = ""
                in_bullet = False

        # Add final bullet
        if current_bullet:
            bullet_points.append(current_bullet)

        return bullet_points

    def _extract_paragraphs_excluding_bullets(self, lines: List[str]) -> List[str]:
        """
        Extract paragraphs from lines, excluding bullet points and their continuations.

        Args:
            lines: Lines to extract from

        Returns:
            List of paragraph texts
        """
        paragraphs: List[str] = []
        current_paragraph = ""
        skip_next_lines = False

        for i, line in enumerate(lines):
            # Skip bullet points and numbered lists
            if re.match(r"^[\s]*[-*+]\s+", line) or re.match(r"^[\s]*\d+\.\s+", line):
                # Save current paragraph if exists
                if current_paragraph:
                    paragraphs.append(current_paragraph.strip())
                    current_paragraph = ""
                skip_next_lines = True
                continue

            # Check if this is a continuation of a bullet (indented)
            if skip_next_lines and re.match(r"^\s{2,}", line):
                continue

            # Empty line
            if not line.strip():
                if current_paragraph:
                    paragraphs.append(current_paragraph.strip())
                    current_paragraph = ""
                skip_next_lines = False
                continue

            # Regular paragraph line
            skip_next_lines = False
            current_paragraph += " " + line.strip() if current_paragraph else line.strip()

        # Add final paragraph
        if current_paragraph:
            paragraphs.append(current_paragraph.strip())

        return paragraphs

    def _classify_requirement(self, text: str) -> RequirementType:
        """
        Classify requirement as functional or non-functional.

        Args:
            text: Requirement text

        Returns:
            RequirementType classification
        """
        text_lower = text.lower()

        # Check for non-functional keywords first (more specific)
        for keyword in self.NON_FUNCTIONAL_KEYWORDS:
            if keyword in text_lower:
                return RequirementType.FUNCTIONAL  # Using FUNCTIONAL as default type

        # Check for functional keywords
        for keyword in self.FUNCTIONAL_KEYWORDS:
            if keyword in text_lower:
                return RequirementType.FUNCTIONAL

        # Default to functional
        return RequirementType.FUNCTIONAL

    def _build_hierarchy(self, heading: str, level: int) -> str:
        """
        Build hierarchy string for the requirement.

        Args:
            heading: Section heading
            level: Heading level

        Returns:
            Hierarchy string
        """
        return f"Level {level}: {heading}"

    def validate(self, input_data: str | Path) -> ValidationResult:
        """
        Validate Markdown content before parsing.

        Args:
            input_data: Either Markdown content string or Path to a Markdown file

        Returns:
            ValidationResult with validation status and messages
        """
        # Handle Path input
        if isinstance(input_data, Path):
            if not input_data.exists():
                return ValidationResult(
                    is_valid=False,
                    errors=[f"File not found: {input_data}"],
                    warnings=[]
                )
            if not input_data.is_file():
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Path is not a file: {input_data}"],
                    warnings=[]
                )
            try:
                with open(input_data, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Failed to read file: {input_data}\nError: {str(e)}"],
                    warnings=[]
                )
        else:
            content = input_data
        
        errors: List[str] = []
        warnings: List[str] = []

        # Check if content is empty
        if not content or not content.strip():
            errors.append("Markdown content is empty")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Check for at least one heading
        if not re.search(r"^#{1,6}\s+.+$", content, re.MULTILINE):
            warnings.append("No headings found in document")

        # Check for at least some content
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        if len(lines) < 3:
            warnings.append("Document appears to be very short")

        # Validation passed
        return ValidationResult(
            is_valid=True,
            errors=errors,
            warnings=warnings,
            metadata={"line_count": len(content.split("\n"))},
        )

    def parse_file(self, file_path: str | Path) -> List[Requirement]:
        """
        Parse a Markdown file and extract requirements.

        Args:
            file_path: Path to the Markdown file

        Returns:
            List of parsed requirements

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a valid Markdown file
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        # Read file content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            raise ValueError(f"Failed to read file: {file_path}\nError: {str(e)}") from e

        # Validate content
        validation = self.validate(content)
        if not validation.is_valid:
            raise ValueError(
                f"Invalid Markdown file: {file_path}\n"
                f"Errors: {', '.join(validation.errors)}"
            )

        # Parse content
        return self.parse(content, source=str(file_path))
