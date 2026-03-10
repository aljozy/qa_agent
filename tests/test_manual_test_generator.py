"""Tests for manual test generator implementation."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from qa_agent.config.loader import AIConfig
from qa_agent.generators.manual_test_generator import ManualTestGenerator
from qa_agent.llm.client import LLMClient, LLMError
from qa_agent.models.base import Requirement, RequirementType, TestType


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    # Create a mock client without initializing the real LLMClient
    client = MagicMock(spec=LLMClient)
    client.generate = AsyncMock()
    
    return client


@pytest.fixture
def sample_requirement():
    """Create a sample requirement for testing."""
    return Requirement(
        id="REQ-001",
        type=RequirementType.FUNCTIONAL,
        content="User must be able to log in with valid credentials",
        source="requirements.md",
    )


@pytest.fixture
def sample_test_response():
    """Create a sample LLM response with test cases."""
    test_cases = [
        {
            "test_id": "TC001",
            "description": "Verify user can log in with valid credentials",
            "preconditions": [
                "User account exists in the system",
                "User has valid username and password"
            ],
            "steps": [
                "Navigate to login page",
                "Enter valid username",
                "Enter valid password",
                "Click login button"
            ],
            "expected_results": [
                "User is redirected to dashboard",
                "Welcome message is displayed"
            ]
        }
    ]
    return json.dumps(test_cases)


class TestManualTestGeneratorInitialization:
    """Tests for ManualTestGenerator initialization."""

    def test_init(self, mock_llm_client):
        """Test generator initialization."""
        generator = ManualTestGenerator(mock_llm_client)
        
        assert generator.llm_client == mock_llm_client


class TestManualTestGeneratorGenerate:
    """Tests for test case generation."""

    @pytest.mark.asyncio
    async def test_generate_empty_requirements(self, mock_llm_client):
        """Test generation with empty requirements list."""
        generator = ManualTestGenerator(mock_llm_client)
        
        artifacts = await generator.generate([])
        
        assert artifacts == []
        mock_llm_client.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_positive_tests(
        self, mock_llm_client, sample_requirement, sample_test_response
    ):
        """Test generation of positive test cases."""
        mock_llm_client.generate.return_value = sample_test_response
        
        generator = ManualTestGenerator(mock_llm_client)
        artifacts = await generator.generate(
            [sample_requirement],
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
        )
        
        assert len(artifacts) == 1
        assert artifacts[0].type == TestType.MANUAL
        assert sample_requirement.id in artifacts[0].requirement_ids
        assert "TC001" in artifacts[0].content
        assert "log in with valid credentials" in artifacts[0].content
        
        # Verify LLM was called once for positive tests
        assert mock_llm_client.generate.call_count == 1

    @pytest.mark.asyncio
    async def test_generate_negative_tests(
        self, mock_llm_client, sample_requirement, sample_test_response
    ):
        """Test generation of negative test cases."""
        mock_llm_client.generate.return_value = sample_test_response
        
        generator = ManualTestGenerator(mock_llm_client)
        artifacts = await generator.generate(
            [sample_requirement],
            include_positive=False,
            include_negative=True,
            include_edge_cases=False,
        )
        
        assert len(artifacts) == 1
        assert artifacts[0].type == TestType.MANUAL
        
        # Verify LLM was called once for negative tests
        assert mock_llm_client.generate.call_count == 1

    @pytest.mark.asyncio
    async def test_generate_edge_case_tests(
        self, mock_llm_client, sample_requirement, sample_test_response
    ):
        """Test generation of edge case test cases."""
        mock_llm_client.generate.return_value = sample_test_response
        
        generator = ManualTestGenerator(mock_llm_client)
        artifacts = await generator.generate(
            [sample_requirement],
            include_positive=False,
            include_negative=False,
            include_edge_cases=True,
        )
        
        assert len(artifacts) == 1
        assert artifacts[0].type == TestType.MANUAL
        
        # Verify LLM was called once for edge case tests
        assert mock_llm_client.generate.call_count == 1

    @pytest.mark.asyncio
    async def test_generate_all_test_types(
        self, mock_llm_client, sample_requirement, sample_test_response
    ):
        """Test generation of all test types."""
        mock_llm_client.generate.return_value = sample_test_response
        
        generator = ManualTestGenerator(mock_llm_client)
        artifacts = await generator.generate(
            [sample_requirement],
            include_positive=True,
            include_negative=True,
            include_edge_cases=True,
        )
        
        # Should generate 3 test cases (one for each type)
        assert len(artifacts) == 3
        
        # Verify LLM was called 3 times (positive, negative, edge case)
        assert mock_llm_client.generate.call_count == 3

    @pytest.mark.asyncio
    async def test_generate_multiple_requirements(
        self, mock_llm_client, sample_test_response
    ):
        """Test generation for multiple requirements."""
        requirements = [
            Requirement(
                id="REQ-001",
                type=RequirementType.FUNCTIONAL,
                content="User login requirement",
                source="requirements.md",
            ),
            Requirement(
                id="REQ-002",
                type=RequirementType.FUNCTIONAL,
                content="User logout requirement",
                source="requirements.md",
            ),
        ]
        
        mock_llm_client.generate.return_value = sample_test_response
        
        generator = ManualTestGenerator(mock_llm_client)
        artifacts = await generator.generate(
            requirements,
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
        )
        
        # Should generate 2 test cases (one per requirement)
        assert len(artifacts) == 2
        
        # Verify each requirement has a test
        req_ids = {artifact.requirement_ids[0] for artifact in artifacts}
        assert "REQ-001" in req_ids
        assert "REQ-002" in req_ids

    @pytest.mark.asyncio
    async def test_generate_handles_llm_error(
        self, mock_llm_client, sample_requirement
    ):
        """Test that generation raises error when all requirements fail."""
        mock_llm_client.generate.side_effect = LLMError("API error")
        
        generator = ManualTestGenerator(mock_llm_client)
        
        # Should raise error when all requirements fail
        with pytest.raises(LLMError, match="Failed to generate tests for all"):
            await generator.generate(
                [sample_requirement],
                include_positive=True,
                include_negative=False,
                include_edge_cases=False,
            )

    @pytest.mark.asyncio
    async def test_generate_continues_on_partial_failure(
        self, mock_llm_client, sample_test_response
    ):
        """Test that generation continues when one requirement fails."""
        requirements = [
            Requirement(
                id="REQ-001",
                type=RequirementType.FUNCTIONAL,
                content="First requirement",
                source="requirements.md",
            ),
            Requirement(
                id="REQ-002",
                type=RequirementType.FUNCTIONAL,
                content="Second requirement",
                source="requirements.md",
            ),
        ]
        
        # First call fails, second succeeds
        mock_llm_client.generate.side_effect = [
            LLMError("API error"),
            sample_test_response,
        ]
        
        generator = ManualTestGenerator(mock_llm_client)
        artifacts = await generator.generate(
            requirements,
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
        )
        
        # Should have 1 artifact from the successful requirement
        assert len(artifacts) == 1
        assert artifacts[0].requirement_ids[0] == "REQ-002"


class TestManualTestGeneratorPrompts:
    """Tests for prompt construction."""

    def test_system_prompt_structure(self, mock_llm_client):
        """Test that system prompt has correct structure."""
        generator = ManualTestGenerator(mock_llm_client)
        system_prompt = generator._build_system_prompt()
        
        assert "QA engineer" in system_prompt
        assert "test_id" in system_prompt
        assert "description" in system_prompt
        assert "preconditions" in system_prompt
        assert "steps" in system_prompt
        assert "expected_results" in system_prompt
        assert "JSON" in system_prompt

    def test_positive_test_prompt(self, mock_llm_client, sample_requirement):
        """Test positive test prompt construction."""
        generator = ManualTestGenerator(mock_llm_client)
        prompt = generator._build_positive_test_prompt(sample_requirement)
        
        assert sample_requirement.id in prompt
        assert sample_requirement.content in prompt
        assert "positive" in prompt.lower()
        assert "valid inputs" in prompt.lower()

    def test_negative_test_prompt(self, mock_llm_client, sample_requirement):
        """Test negative test prompt construction."""
        generator = ManualTestGenerator(mock_llm_client)
        prompt = generator._build_negative_test_prompt(sample_requirement)
        
        assert sample_requirement.id in prompt
        assert sample_requirement.content in prompt
        assert "negative" in prompt.lower()
        assert "invalid inputs" in prompt.lower()

    def test_edge_case_test_prompt(self, mock_llm_client, sample_requirement):
        """Test edge case test prompt construction."""
        generator = ManualTestGenerator(mock_llm_client)
        prompt = generator._build_edge_case_test_prompt(sample_requirement)
        
        assert sample_requirement.id in prompt
        assert sample_requirement.content in prompt
        assert "edge case" in prompt.lower()
        assert "boundary" in prompt.lower()


class TestManualTestGeneratorResponseParsing:
    """Tests for LLM response parsing."""

    def test_parse_valid_json_response(
        self, mock_llm_client, sample_requirement, sample_test_response
    ):
        """Test parsing of valid JSON response."""
        generator = ManualTestGenerator(mock_llm_client)
        artifacts = generator._parse_llm_response(
            sample_test_response, sample_requirement, "positive"
        )
        
        assert len(artifacts) == 1
        assert artifacts[0].type == TestType.MANUAL
        assert sample_requirement.id in artifacts[0].requirement_ids
        assert artifacts[0].metadata["scenario_type"] == "positive"

    def test_parse_json_with_markdown_code_blocks(
        self, mock_llm_client, sample_requirement, sample_test_response
    ):
        """Test parsing of JSON wrapped in markdown code blocks."""
        wrapped_response = f"```json\n{sample_test_response}\n```"
        
        generator = ManualTestGenerator(mock_llm_client)
        artifacts = generator._parse_llm_response(
            wrapped_response, sample_requirement, "positive"
        )
        
        assert len(artifacts) == 1

    def test_parse_json_with_generic_code_blocks(
        self, mock_llm_client, sample_requirement, sample_test_response
    ):
        """Test parsing of JSON wrapped in generic code blocks."""
        wrapped_response = f"```\n{sample_test_response}\n```"
        
        generator = ManualTestGenerator(mock_llm_client)
        artifacts = generator._parse_llm_response(
            wrapped_response, sample_requirement, "positive"
        )
        
        assert len(artifacts) == 1

    def test_parse_multiple_test_cases(
        self, mock_llm_client, sample_requirement
    ):
        """Test parsing of multiple test cases in one response."""
        test_cases = [
            {
                "test_id": "TC001",
                "description": "First test",
                "preconditions": ["Precondition 1"],
                "steps": ["Step 1"],
                "expected_results": ["Result 1"]
            },
            {
                "test_id": "TC002",
                "description": "Second test",
                "preconditions": ["Precondition 2"],
                "steps": ["Step 2"],
                "expected_results": ["Result 2"]
            }
        ]
        response = json.dumps(test_cases)
        
        generator = ManualTestGenerator(mock_llm_client)
        artifacts = generator._parse_llm_response(
            response, sample_requirement, "positive"
        )
        
        assert len(artifacts) == 2
        assert "TC001" in artifacts[0].content
        assert "TC002" in artifacts[1].content

    def test_parse_invalid_json_raises_error(
        self, mock_llm_client, sample_requirement
    ):
        """Test that invalid JSON raises ValueError."""
        invalid_response = "This is not JSON"
        
        generator = ManualTestGenerator(mock_llm_client)
        
        with pytest.raises(ValueError, match="Invalid JSON response"):
            generator._parse_llm_response(
                invalid_response, sample_requirement, "positive"
            )

    def test_parse_non_array_json_raises_error(
        self, mock_llm_client, sample_requirement
    ):
        """Test that non-array JSON raises ValueError."""
        non_array_response = json.dumps({"test_id": "TC001"})
        
        generator = ManualTestGenerator(mock_llm_client)
        
        with pytest.raises(ValueError, match="must be a JSON array"):
            generator._parse_llm_response(
                non_array_response, sample_requirement, "positive"
            )

    def test_parse_missing_required_fields_raises_error(
        self, mock_llm_client, sample_requirement
    ):
        """Test that missing required fields raises ValueError."""
        incomplete_test = [
            {
                "test_id": "TC001",
                "description": "Test without steps"
                # Missing preconditions, steps, expected_results
            }
        ]
        response = json.dumps(incomplete_test)
        
        generator = ManualTestGenerator(mock_llm_client)
        
        with pytest.raises(ValueError, match="Missing required fields"):
            generator._parse_llm_response(
                response, sample_requirement, "positive"
            )


class TestManualTestGeneratorArtifactCreation:
    """Tests for test artifact creation."""

    def test_create_test_artifact(self, mock_llm_client, sample_requirement):
        """Test creation of TestArtifact from test case data."""
        test_case = {
            "test_id": "TC001",
            "description": "Test description",
            "preconditions": ["Precondition 1", "Precondition 2"],
            "steps": ["Step 1", "Step 2", "Step 3"],
            "expected_results": ["Result 1", "Result 2"]
        }
        
        generator = ManualTestGenerator(mock_llm_client)
        artifact = generator._create_test_artifact(
            test_case, sample_requirement, "positive"
        )
        
        assert artifact.type == TestType.MANUAL
        assert sample_requirement.id in artifact.requirement_ids
        assert artifact.metadata["scenario_type"] == "positive"
        assert artifact.metadata["test_id"] == "TC001"
        assert "TC001" in artifact.content
        assert "Test description" in artifact.content

    def test_format_test_content(self, mock_llm_client):
        """Test formatting of test content."""
        test_case = {
            "test_id": "TC001",
            "description": "Test description",
            "preconditions": ["Precondition 1"],
            "steps": ["Step 1", "Step 2"],
            "expected_results": ["Result 1"]
        }
        
        generator = ManualTestGenerator(mock_llm_client)
        content = generator._format_test_content(test_case)
        
        assert "Test ID: TC001" in content
        assert "Description: Test description" in content
        assert "Preconditions:" in content
        assert "1. Precondition 1" in content
        assert "Test Steps:" in content
        assert "1. Step 1" in content
        assert "2. Step 2" in content
        assert "Expected Results:" in content
        assert "1. Result 1" in content

    def test_artifact_includes_requirement_link(
        self, mock_llm_client, sample_requirement
    ):
        """Test that artifact includes link to source requirement."""
        test_case = {
            "test_id": "TC001",
            "description": "Test",
            "preconditions": ["Pre"],
            "steps": ["Step"],
            "expected_results": ["Result"]
        }
        
        generator = ManualTestGenerator(mock_llm_client)
        artifact = generator._create_test_artifact(
            test_case, sample_requirement, "positive"
        )
        
        assert sample_requirement.id in artifact.requirement_ids
        assert artifact.metadata["source_requirement"] == sample_requirement.id


class TestManualTestGeneratorIntegration:
    """Integration tests for the manual test generator."""

    @pytest.mark.asyncio
    async def test_end_to_end_generation(
        self, mock_llm_client, sample_requirement, sample_test_response
    ):
        """Test end-to-end test generation flow."""
        mock_llm_client.generate.return_value = sample_test_response
        
        generator = ManualTestGenerator(mock_llm_client)
        artifacts = await generator.generate([sample_requirement])
        
        # Should generate 3 artifacts (positive, negative, edge case)
        assert len(artifacts) == 3
        
        # All artifacts should be manual tests
        assert all(a.type == TestType.MANUAL for a in artifacts)
        
        # All artifacts should link to the requirement
        assert all(sample_requirement.id in a.requirement_ids for a in artifacts)
        
        # Verify system and user prompts were used
        calls = mock_llm_client.generate.call_args_list
        assert len(calls) == 3
        
        # Each call should have user prompt and system prompt
        for call in calls:
            args, kwargs = call
            assert len(args) >= 1  # user_prompt
            assert len(args) >= 2 or 'system_prompt' in kwargs  # system_prompt
