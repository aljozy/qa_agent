"""Requirement Traceability Matrix (RTM) generator implementation."""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

from qa_agent.models.base import Requirement, TestArtifact

logger = logging.getLogger(__name__)


class RTMEntry:
    """Represents a single entry in the RTM."""

    def __init__(
        self,
        requirement_id: str,
        requirement_description: str,
        test_ids: List[str],
        coverage_status: str,
    ):
        """
        Initialize an RTM entry.
        
        Args:
            requirement_id: Unique identifier for the requirement
            requirement_description: Description of the requirement
            test_ids: List of test artifact IDs that cover this requirement
            coverage_status: Coverage status (e.g., "Covered", "Not Covered", "Partial")
        """
        self.requirement_id = requirement_id
        self.requirement_description = requirement_description
        self.test_ids = test_ids
        self.coverage_status = coverage_status

    def to_dict(self) -> Dict[str, str]:
        """
        Convert entry to dictionary format.
        
        Returns:
            Dictionary representation of the RTM entry
        """
        return {
            "Requirement ID": self.requirement_id,
            "Requirement Description": self.requirement_description,
            "Test IDs": ", ".join(self.test_ids) if self.test_ids else "None",
            "Coverage Status": self.coverage_status,
        }


class RTMGenerator:
    """
    Generator for creating Requirement Traceability Matrix (RTM).
    
    The RTM maps requirements to test cases, identifies coverage gaps,
    and calculates coverage percentages. Supports export to CSV format.
    """

    def __init__(self):
        """Initialize the RTM generator."""
        logger.info("Initialized RTMGenerator")

    def generate(
        self,
        requirements: List[Requirement],
        test_artifacts: List[TestArtifact],
    ) -> List[RTMEntry]:
        """
        Generate RTM entries mapping requirements to test cases.
        
        Args:
            requirements: List of requirements to trace
            test_artifacts: List of test artifacts that cover requirements
            
        Returns:
            List of RTM entries
        """
        if not requirements:
            logger.warning("No requirements provided for RTM generation")
            return []

        logger.info(
            f"Generating RTM for {len(requirements)} requirements "
            f"and {len(test_artifacts)} test artifacts"
        )

        # Build mapping of requirement ID to test IDs
        req_to_tests = self._build_requirement_test_mapping(test_artifacts)

        # Create RTM entries
        rtm_entries = []
        for requirement in requirements:
            test_ids = req_to_tests.get(requirement.id, [])
            coverage_status = self._determine_coverage_status(test_ids)
            
            # Extract description from requirement content (first line or truncated)
            description = self._extract_description(requirement)
            
            entry = RTMEntry(
                requirement_id=requirement.id,
                requirement_description=description,
                test_ids=test_ids,
                coverage_status=coverage_status,
            )
            rtm_entries.append(entry)

        # Log summary
        covered = sum(1 for entry in rtm_entries if entry.coverage_status == "Covered")
        not_covered = sum(1 for entry in rtm_entries if entry.coverage_status == "Not Covered")
        
        logger.info(
            f"RTM generation complete: {covered} covered, {not_covered} not covered, "
            f"{len(rtm_entries) - covered - not_covered} partial"
        )

        return rtm_entries

    def identify_uncovered_requirements(
        self,
        requirements: List[Requirement],
        test_artifacts: List[TestArtifact],
    ) -> List[Requirement]:
        """
        Identify requirements with no associated test cases.
        
        Args:
            requirements: List of requirements to check
            test_artifacts: List of test artifacts
            
        Returns:
            List of requirements with no test coverage
        """
        # Build set of covered requirement IDs
        covered_req_ids = set()
        for artifact in test_artifacts:
            covered_req_ids.update(artifact.requirement_ids)

        # Find uncovered requirements
        uncovered = [
            req for req in requirements
            if req.id not in covered_req_ids
        ]

        logger.info(
            f"Identified {len(uncovered)} uncovered requirements "
            f"out of {len(requirements)} total"
        )

        return uncovered

    def calculate_coverage_percentage(
        self,
        requirements: List[Requirement],
        test_artifacts: List[TestArtifact],
    ) -> float:
        """
        Calculate overall coverage percentage.
        
        Args:
            requirements: List of requirements
            test_artifacts: List of test artifacts
            
        Returns:
            Coverage percentage (0.0 to 100.0)
        """
        if not requirements:
            logger.warning("No requirements provided for coverage calculation")
            return 0.0

        # Build set of covered requirement IDs
        covered_req_ids = set()
        for artifact in test_artifacts:
            covered_req_ids.update(artifact.requirement_ids)

        # Calculate percentage
        covered_count = sum(1 for req in requirements if req.id in covered_req_ids)
        percentage = (covered_count / len(requirements)) * 100.0

        logger.info(
            f"Coverage: {covered_count}/{len(requirements)} requirements "
            f"({percentage:.1f}%)"
        )

        return percentage

    def export_to_csv(
        self,
        rtm_entries: List[RTMEntry],
        output_path: Path,
    ) -> None:
        """
        Export RTM to CSV format.
        
        Args:
            rtm_entries: List of RTM entries to export
            output_path: Path to output CSV file
            
        Raises:
            IOError: If file cannot be written
        """
        if not rtm_entries:
            logger.warning("No RTM entries to export")
            return

        logger.info(f"Exporting RTM to CSV: {output_path}")

        try:
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write CSV
            with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = [
                    "Requirement ID",
                    "Requirement Description",
                    "Test IDs",
                    "Coverage Status",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for entry in rtm_entries:
                    writer.writerow(entry.to_dict())

            logger.info(f"Successfully exported {len(rtm_entries)} RTM entries to {output_path}")

        except Exception as e:
            logger.error(f"Failed to export RTM to CSV: {str(e)}")
            raise IOError(f"Failed to write RTM to {output_path}: {str(e)}")

    def _build_requirement_test_mapping(
        self,
        test_artifacts: List[TestArtifact],
    ) -> Dict[str, List[str]]:
        """
        Build mapping of requirement IDs to test artifact IDs.
        
        Args:
            test_artifacts: List of test artifacts
            
        Returns:
            Dictionary mapping requirement ID to list of test IDs
        """
        mapping: Dict[str, List[str]] = {}

        for artifact in test_artifacts:
            # Extract test ID from metadata if available
            test_id = artifact.metadata.get("test_id", artifact.id)
            
            for req_id in artifact.requirement_ids:
                if req_id not in mapping:
                    mapping[req_id] = []
                mapping[req_id].append(test_id)

        return mapping

    def _determine_coverage_status(self, test_ids: List[str]) -> str:
        """
        Determine coverage status based on number of test cases.
        
        Args:
            test_ids: List of test IDs covering a requirement
            
        Returns:
            Coverage status string
        """
        if not test_ids:
            return "Not Covered"
        elif len(test_ids) == 1:
            return "Partial"
        else:
            return "Covered"

    def _extract_description(self, requirement: Requirement) -> str:
        """
        Extract a concise description from requirement content.
        
        Args:
            requirement: Requirement object
            
        Returns:
            Truncated description string
        """
        # Get first line or first 100 characters
        content = requirement.content.strip()
        
        # Try to get first line
        first_line = content.split("\n")[0].strip()
        
        # Truncate if too long
        max_length = 100
        if len(first_line) > max_length:
            return first_line[:max_length] + "..."
        
        return first_line
