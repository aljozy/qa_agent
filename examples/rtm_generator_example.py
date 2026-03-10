"""Example usage of the RTM generator."""

import asyncio
from pathlib import Path

from qa_agent.analysis.rtm_generator import RTMGenerator
from qa_agent.models.base import Requirement, RequirementType, TestArtifact, TestType


def main():
    """Demonstrate RTM generator usage."""
    print("RTM Generator Example")
    print("=" * 50)
    print()

    # Create sample requirements
    requirements = [
        Requirement(
            id="REQ-001",
            type=RequirementType.FUNCTIONAL,
            content="User shall be able to log in with valid credentials",
            source="requirements.md",
        ),
        Requirement(
            id="REQ-002",
            type=RequirementType.FUNCTIONAL,
            content="System shall validate email format before accepting registration",
            source="requirements.md",
        ),
        Requirement(
            id="REQ-003",
            type=RequirementType.FUNCTIONAL,
            content="User shall be able to reset password via email link",
            source="requirements.md",
        ),
        Requirement(
            id="REQ-004",
            type=RequirementType.FUNCTIONAL,
            content="System shall lock account after 5 failed login attempts",
            source="requirements.md",
        ),
    ]

    # Create sample test artifacts
    test_artifacts = [
        TestArtifact(
            type=TestType.MANUAL,
            content="Test login with valid credentials",
            requirement_ids=["REQ-001"],
            metadata={"test_id": "TC001", "scenario_type": "positive"},
        ),
        TestArtifact(
            type=TestType.MANUAL,
            content="Test login with invalid credentials",
            requirement_ids=["REQ-001"],
            metadata={"test_id": "TC002", "scenario_type": "negative"},
        ),
        TestArtifact(
            type=TestType.MANUAL,
            content="Test login with empty password",
            requirement_ids=["REQ-001"],
            metadata={"test_id": "TC003", "scenario_type": "edge_case"},
        ),
        TestArtifact(
            type=TestType.MANUAL,
            content="Test email validation with valid email",
            requirement_ids=["REQ-002"],
            metadata={"test_id": "TC004", "scenario_type": "positive"},
        ),
        TestArtifact(
            type=TestType.MANUAL,
            content="Test email validation with invalid email format",
            requirement_ids=["REQ-002"],
            metadata={"test_id": "TC005", "scenario_type": "negative"},
        ),
        TestArtifact(
            type=TestType.MANUAL,
            content="Test password reset flow",
            requirement_ids=["REQ-003"],
            metadata={"test_id": "TC006", "scenario_type": "positive"},
        ),
    ]

    print(f"Requirements: {len(requirements)}")
    print(f"Test Artifacts: {len(test_artifacts)}")
    print()

    # Initialize RTM generator
    rtm_generator = RTMGenerator()

    # Generate RTM
    print("Generating RTM...")
    rtm_entries = rtm_generator.generate(requirements, test_artifacts)
    print(f"Generated {len(rtm_entries)} RTM entries")
    print()

    # Display RTM entries
    print("RTM Entries:")
    print("-" * 100)
    for entry in rtm_entries:
        print(f"Requirement: {entry.requirement_id}")
        print(f"Description: {entry.requirement_description}")
        print(f"Test IDs: {', '.join(entry.test_ids) if entry.test_ids else 'None'}")
        print(f"Coverage: {entry.coverage_status}")
        print("-" * 100)
    print()

    # Identify uncovered requirements
    print("Identifying uncovered requirements...")
    uncovered = rtm_generator.identify_uncovered_requirements(requirements, test_artifacts)
    print(f"Uncovered requirements: {len(uncovered)}")
    if uncovered:
        for req in uncovered:
            print(f"  - {req.id}: {req.content[:60]}...")
    print()

    # Calculate coverage percentage
    print("Calculating coverage percentage...")
    coverage = rtm_generator.calculate_coverage_percentage(requirements, test_artifacts)
    print(f"Overall coverage: {coverage:.1f}%")
    print()

    # Export to CSV
    output_path = Path("output/rtm_example.csv")
    print(f"Exporting RTM to CSV: {output_path}")
    rtm_generator.export_to_csv(rtm_entries, output_path)
    print(f"RTM exported successfully!")
    print()

    # Display coverage summary
    print("Coverage Summary:")
    print("-" * 50)
    covered = sum(1 for e in rtm_entries if e.coverage_status == "Covered")
    partial = sum(1 for e in rtm_entries if e.coverage_status == "Partial")
    not_covered = sum(1 for e in rtm_entries if e.coverage_status == "Not Covered")
    
    print(f"Covered: {covered} ({covered/len(rtm_entries)*100:.1f}%)")
    print(f"Partial: {partial} ({partial/len(rtm_entries)*100:.1f}%)")
    print(f"Not Covered: {not_covered} ({not_covered/len(rtm_entries)*100:.1f}%)")
    print("-" * 50)


if __name__ == "__main__":
    main()
