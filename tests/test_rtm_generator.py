"""Tests for RTM generator."""

import csv
import tempfile
from pathlib import Path

import pytest

from qa_agent.analysis.rtm_generator import RTMEntry, RTMGenerator
from qa_agent.models.base import Requirement, RequirementType, TestArtifact, TestType


@pytest.fixture
def sample_requirements():
    """Create sample requirements for testing."""
    return [
        Requirement(
            id="REQ-001",
            type=RequirementType.FUNCTIONAL,
            content="User shall be able to log in with valid credentials",
            source="requirements.md",
        ),
        Requirement(
            id="REQ-002",
            type=RequirementType.FUNCTIONAL,
            content="System shall validate email format",
            source="requirements.md",
        ),
        Requirement(
            id="REQ-003",
            type=RequirementType.FUNCTIONAL,
            content="User shall be able to reset password",
            source="requirements.md",
        ),
    ]


@pytest.fixture
def sample_test_artifacts():
    """Create sample test artifacts for testing."""
    return [
        TestArtifact(
            id="TEST-001",
            type=TestType.MANUAL,
            content="Test login with valid credentials",
            requirement_ids=["REQ-001"],
            metadata={"test_id": "TC001"},
        ),
        TestArtifact(
            id="TEST-002",
            type=TestType.MANUAL,
            content="Test login with invalid credentials",
            requirement_ids=["REQ-001"],
            metadata={"test_id": "TC002"},
        ),
        TestArtifact(
            id="TEST-003",
            type=TestType.MANUAL,
            content="Test email validation",
            requirement_ids=["REQ-002"],
            metadata={"test_id": "TC003"},
        ),
    ]


@pytest.fixture
def rtm_generator():
    """Create RTM generator instance."""
    return RTMGenerator()


class TestRTMEntry:
    """Tests for RTMEntry class."""

    def test_rtm_entry_creation(self):
        """Test creating an RTM entry."""
        entry = RTMEntry(
            requirement_id="REQ-001",
            requirement_description="Test requirement",
            test_ids=["TC001", "TC002"],
            coverage_status="Covered",
        )

        assert entry.requirement_id == "REQ-001"
        assert entry.requirement_description == "Test requirement"
        assert entry.test_ids == ["TC001", "TC002"]
        assert entry.coverage_status == "Covered"

    def test_rtm_entry_to_dict(self):
        """Test converting RTM entry to dictionary."""
        entry = RTMEntry(
            requirement_id="REQ-001",
            requirement_description="Test requirement",
            test_ids=["TC001", "TC002"],
            coverage_status="Covered",
        )

        result = entry.to_dict()

        assert result["Requirement ID"] == "REQ-001"
        assert result["Requirement Description"] == "Test requirement"
        assert result["Test IDs"] == "TC001, TC002"
        assert result["Coverage Status"] == "Covered"

    def test_rtm_entry_to_dict_no_tests(self):
        """Test converting RTM entry with no tests to dictionary."""
        entry = RTMEntry(
            requirement_id="REQ-001",
            requirement_description="Test requirement",
            test_ids=[],
            coverage_status="Not Covered",
        )

        result = entry.to_dict()

        assert result["Test IDs"] == "None"
        assert result["Coverage Status"] == "Not Covered"


class TestRTMGenerator:
    """Tests for RTMGenerator class."""

    def test_initialization(self, rtm_generator):
        """Test RTM generator initialization."""
        assert rtm_generator is not None

    def test_generate_rtm(self, rtm_generator, sample_requirements, sample_test_artifacts):
        """Test generating RTM entries."""
        entries = rtm_generator.generate(sample_requirements, sample_test_artifacts)

        assert len(entries) == 3
        assert all(isinstance(entry, RTMEntry) for entry in entries)

        # Check first requirement (covered by 2 tests)
        req1_entry = next(e for e in entries if e.requirement_id == "REQ-001")
        assert len(req1_entry.test_ids) == 2
        assert "TC001" in req1_entry.test_ids
        assert "TC002" in req1_entry.test_ids
        assert req1_entry.coverage_status == "Covered"

        # Check second requirement (covered by 1 test)
        req2_entry = next(e for e in entries if e.requirement_id == "REQ-002")
        assert len(req2_entry.test_ids) == 1
        assert "TC003" in req2_entry.test_ids
        assert req2_entry.coverage_status == "Partial"

        # Check third requirement (not covered)
        req3_entry = next(e for e in entries if e.requirement_id == "REQ-003")
        assert len(req3_entry.test_ids) == 0
        assert req3_entry.coverage_status == "Not Covered"

    def test_generate_rtm_empty_requirements(self, rtm_generator):
        """Test generating RTM with no requirements."""
        entries = rtm_generator.generate([], [])
        assert entries == []

    def test_generate_rtm_no_tests(self, rtm_generator, sample_requirements):
        """Test generating RTM with no test artifacts."""
        entries = rtm_generator.generate(sample_requirements, [])

        assert len(entries) == 3
        assert all(entry.coverage_status == "Not Covered" for entry in entries)
        assert all(len(entry.test_ids) == 0 for entry in entries)

    def test_identify_uncovered_requirements(
        self, rtm_generator, sample_requirements, sample_test_artifacts
    ):
        """Test identifying uncovered requirements."""
        uncovered = rtm_generator.identify_uncovered_requirements(
            sample_requirements, sample_test_artifacts
        )

        assert len(uncovered) == 1
        assert uncovered[0].id == "REQ-003"

    def test_identify_uncovered_requirements_all_covered(
        self, rtm_generator, sample_requirements
    ):
        """Test identifying uncovered requirements when all are covered."""
        # Create test artifacts covering all requirements
        test_artifacts = [
            TestArtifact(
                type=TestType.MANUAL,
                content="Test 1",
                requirement_ids=["REQ-001"],
                metadata={"test_id": "TC001"},
            ),
            TestArtifact(
                type=TestType.MANUAL,
                content="Test 2",
                requirement_ids=["REQ-002"],
                metadata={"test_id": "TC002"},
            ),
            TestArtifact(
                type=TestType.MANUAL,
                content="Test 3",
                requirement_ids=["REQ-003"],
                metadata={"test_id": "TC003"},
            ),
        ]

        uncovered = rtm_generator.identify_uncovered_requirements(
            sample_requirements, test_artifacts
        )

        assert len(uncovered) == 0

    def test_identify_uncovered_requirements_none_covered(
        self, rtm_generator, sample_requirements
    ):
        """Test identifying uncovered requirements when none are covered."""
        uncovered = rtm_generator.identify_uncovered_requirements(
            sample_requirements, []
        )

        assert len(uncovered) == 3
        assert set(req.id for req in uncovered) == {"REQ-001", "REQ-002", "REQ-003"}

    def test_calculate_coverage_percentage(
        self, rtm_generator, sample_requirements, sample_test_artifacts
    ):
        """Test calculating coverage percentage."""
        percentage = rtm_generator.calculate_coverage_percentage(
            sample_requirements, sample_test_artifacts
        )

        # 2 out of 3 requirements are covered
        assert percentage == pytest.approx(66.67, rel=0.01)

    def test_calculate_coverage_percentage_full_coverage(
        self, rtm_generator, sample_requirements
    ):
        """Test calculating coverage percentage with full coverage."""
        # Create test artifacts covering all requirements
        test_artifacts = [
            TestArtifact(
                type=TestType.MANUAL,
                content="Test 1",
                requirement_ids=["REQ-001"],
                metadata={"test_id": "TC001"},
            ),
            TestArtifact(
                type=TestType.MANUAL,
                content="Test 2",
                requirement_ids=["REQ-002"],
                metadata={"test_id": "TC002"},
            ),
            TestArtifact(
                type=TestType.MANUAL,
                content="Test 3",
                requirement_ids=["REQ-003"],
                metadata={"test_id": "TC003"},
            ),
        ]

        percentage = rtm_generator.calculate_coverage_percentage(
            sample_requirements, test_artifacts
        )

        assert percentage == 100.0

    def test_calculate_coverage_percentage_no_coverage(
        self, rtm_generator, sample_requirements
    ):
        """Test calculating coverage percentage with no coverage."""
        percentage = rtm_generator.calculate_coverage_percentage(
            sample_requirements, []
        )

        assert percentage == 0.0

    def test_calculate_coverage_percentage_empty_requirements(self, rtm_generator):
        """Test calculating coverage percentage with no requirements."""
        percentage = rtm_generator.calculate_coverage_percentage([], [])
        assert percentage == 0.0

    def test_export_to_csv(self, rtm_generator, sample_requirements, sample_test_artifacts):
        """Test exporting RTM to CSV."""
        entries = rtm_generator.generate(sample_requirements, sample_test_artifacts)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "rtm.csv"
            rtm_generator.export_to_csv(entries, output_path)

            # Verify file was created
            assert output_path.exists()

            # Verify CSV content
            with open(output_path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)

                assert len(rows) == 3

                # Check header
                assert reader.fieldnames == [
                    "Requirement ID",
                    "Requirement Description",
                    "Test IDs",
                    "Coverage Status",
                ]

                # Check first row (REQ-001)
                req1_row = next(r for r in rows if r["Requirement ID"] == "REQ-001")
                assert "TC001" in req1_row["Test IDs"]
                assert "TC002" in req1_row["Test IDs"]
                assert req1_row["Coverage Status"] == "Covered"

                # Check uncovered requirement (REQ-003)
                req3_row = next(r for r in rows if r["Requirement ID"] == "REQ-003")
                assert req3_row["Test IDs"] == "None"
                assert req3_row["Coverage Status"] == "Not Covered"

    def test_export_to_csv_creates_directory(self, rtm_generator):
        """Test that export creates parent directories if they don't exist."""
        entries = [
            RTMEntry(
                requirement_id="REQ-001",
                requirement_description="Test requirement",
                test_ids=["TC001"],
                coverage_status="Partial",
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "nested" / "rtm.csv"
            rtm_generator.export_to_csv(entries, output_path)

            assert output_path.exists()
            assert output_path.parent.exists()

    def test_export_to_csv_empty_entries(self, rtm_generator):
        """Test exporting empty RTM entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "rtm.csv"
            rtm_generator.export_to_csv([], output_path)

            # Should not create file for empty entries
            assert not output_path.exists()

    def test_export_to_csv_invalid_path(self, rtm_generator):
        """Test exporting to invalid path raises error."""
        entries = [
            RTMEntry(
                requirement_id="REQ-001",
                requirement_description="Test requirement",
                test_ids=["TC001"],
                coverage_status="Partial",
            )
        ]

        # Try to write to a path that can't be created (e.g., root on Unix systems)
        invalid_path = Path("/invalid/path/that/cannot/be/created/rtm.csv")

        with pytest.raises(IOError):
            rtm_generator.export_to_csv(entries, invalid_path)

    def test_multiple_tests_per_requirement(self, rtm_generator):
        """Test RTM generation with multiple tests per requirement."""
        requirements = [
            Requirement(
                id="REQ-001",
                type=RequirementType.FUNCTIONAL,
                content="Test requirement",
                source="test.md",
            )
        ]

        test_artifacts = [
            TestArtifact(
                type=TestType.MANUAL,
                content="Test 1",
                requirement_ids=["REQ-001"],
                metadata={"test_id": "TC001"},
            ),
            TestArtifact(
                type=TestType.MANUAL,
                content="Test 2",
                requirement_ids=["REQ-001"],
                metadata={"test_id": "TC002"},
            ),
            TestArtifact(
                type=TestType.MANUAL,
                content="Test 3",
                requirement_ids=["REQ-001"],
                metadata={"test_id": "TC003"},
            ),
        ]

        entries = rtm_generator.generate(requirements, test_artifacts)

        assert len(entries) == 1
        assert len(entries[0].test_ids) == 3
        assert entries[0].coverage_status == "Covered"

    def test_test_covering_multiple_requirements(self, rtm_generator):
        """Test RTM generation when one test covers multiple requirements."""
        requirements = [
            Requirement(
                id="REQ-001",
                type=RequirementType.FUNCTIONAL,
                content="Requirement 1",
                source="test.md",
            ),
            Requirement(
                id="REQ-002",
                type=RequirementType.FUNCTIONAL,
                content="Requirement 2",
                source="test.md",
            ),
        ]

        test_artifacts = [
            TestArtifact(
                type=TestType.MANUAL,
                content="Test covering both requirements",
                requirement_ids=["REQ-001", "REQ-002"],
                metadata={"test_id": "TC001"},
            ),
        ]

        entries = rtm_generator.generate(requirements, test_artifacts)

        assert len(entries) == 2
        
        # Both requirements should be covered by the same test
        req1_entry = next(e for e in entries if e.requirement_id == "REQ-001")
        req2_entry = next(e for e in entries if e.requirement_id == "REQ-002")
        
        assert "TC001" in req1_entry.test_ids
        assert "TC001" in req2_entry.test_ids
        assert req1_entry.coverage_status == "Partial"
        assert req2_entry.coverage_status == "Partial"

    def test_description_extraction_long_content(self, rtm_generator):
        """Test description extraction with long requirement content."""
        long_content = "A" * 150  # Content longer than 100 characters
        
        requirements = [
            Requirement(
                id="REQ-001",
                type=RequirementType.FUNCTIONAL,
                content=long_content,
                source="test.md",
            )
        ]

        entries = rtm_generator.generate(requirements, [])

        assert len(entries) == 1
        assert len(entries[0].requirement_description) <= 104  # 100 + "..."
        assert entries[0].requirement_description.endswith("...")

    def test_description_extraction_multiline_content(self, rtm_generator):
        """Test description extraction with multiline requirement content."""
        multiline_content = "First line\nSecond line\nThird line"
        
        requirements = [
            Requirement(
                id="REQ-001",
                type=RequirementType.FUNCTIONAL,
                content=multiline_content,
                source="test.md",
            )
        ]

        entries = rtm_generator.generate(requirements, [])

        assert len(entries) == 1
        assert entries[0].requirement_description == "First line"

    def test_test_artifact_without_test_id_metadata(self, rtm_generator):
        """Test RTM generation when test artifact doesn't have test_id in metadata."""
        requirements = [
            Requirement(
                id="REQ-001",
                type=RequirementType.FUNCTIONAL,
                content="Test requirement",
                source="test.md",
            )
        ]

        test_artifacts = [
            TestArtifact(
                id="ARTIFACT-123",
                type=TestType.MANUAL,
                content="Test without test_id metadata",
                requirement_ids=["REQ-001"],
                metadata={},  # No test_id in metadata
            ),
        ]

        entries = rtm_generator.generate(requirements, test_artifacts)

        assert len(entries) == 1
        # Should use artifact ID when test_id is not in metadata
        assert "ARTIFACT-123" in entries[0].test_ids
