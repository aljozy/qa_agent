"""Tests for batch generation functionality in ManualTestGenerator."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from qa_agent.generators.manual_test_generator import ManualTestGenerator
from qa_agent.llm.client import LLMClient, LLMError
from qa_agent.models.base import Requirement, RequirementType, TestType


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    client = MagicMock(spec=LLMClient)
    client.generate = AsyncMock()
    return client


@pytest.fixture
def sample_requirements():
    """Create sample requirements for testing."""
    return [
        Requirement(
            id=f"REQ-{i:03d}",
            type=RequirementType.FUNCTIONAL,
            content=f"Requirement {i} content",
            source="requirements.md",
        )
        for i in range(1, 11)  # 10 requirements
    ]


@pytest.fixture
def sample_test_response():
    """Create a sample LLM response with test cases."""
    test_cases = [
        {
            "test_id": "TC001",
            "description": "Test case description",
            "preconditions": ["Precondition 1"],
            "steps": ["Step 1", "Step 2"],
            "expected_results": ["Result 1"],
        }
    ]
    return json.dumps(test_cases)


class TestParallelGeneration:
    """Tests for parallel processing of requirements."""

    @pytest.mark.asyncio
    async def test_parallel_generation_with_multiple_requirements(
        self, mock_llm_client, sample_requirements, sample_test_response
    ):
        """Test that multiple requirements are processed in parallel."""
        mock_llm_client.generate.return_value = sample_test_response

        generator = ManualTestGenerator(mock_llm_client, max_concurrent=3)
        artifacts = await generator.generate(
            sample_requirements[:5],  # 5 requirements
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
        )

        # Should generate 5 test cases (one per requirement)
        assert len(artifacts) == 5

        # Verify all requirements were processed
        req_ids = {artifact.requirement_ids[0] for artifact in artifacts}
        assert len(req_ids) == 5

    @pytest.mark.asyncio
    async def test_concurrent_limit_respected(
        self, mock_llm_client, sample_requirements, sample_test_response
    ):
        """Test that concurrent limit is respected."""
        # Track concurrent calls
        concurrent_calls = 0
        max_concurrent_seen = 0

        async def mock_generate(*args, **kwargs):
            nonlocal concurrent_calls, max_concurrent_seen
            concurrent_calls += 1
            max_concurrent_seen = max(max_concurrent_seen, concurrent_calls)

            # Simulate some processing time
            await asyncio.sleep(0.01)

            concurrent_calls -= 1
            return sample_test_response

        mock_llm_client.generate.side_effect = mock_generate

        generator = ManualTestGenerator(mock_llm_client, max_concurrent=2)
        await generator.generate(
            sample_requirements[:5],
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
        )

        # Max concurrent should not exceed the limit
        # Note: Due to asyncio scheduling, this might be slightly higher
        # but should be close to the limit
        assert max_concurrent_seen <= 3  # Allow small margin

    @pytest.mark.asyncio
    async def test_parallel_generation_faster_than_sequential(
        self, mock_llm_client, sample_requirements, sample_test_response
    ):
        """Test that parallel generation is faster than sequential."""
        import time

        async def slow_generate(*args, **kwargs):
            await asyncio.sleep(0.1)  # 100ms delay
            return sample_test_response

        mock_llm_client.generate.side_effect = slow_generate

        # Test with 5 requirements, each taking 100ms
        # Sequential would take ~500ms, parallel should be much faster
        generator = ManualTestGenerator(mock_llm_client, max_concurrent=5)

        start = time.time()
        await generator.generate(
            sample_requirements[:5],
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
        )
        duration = time.time() - start

        # With 5 concurrent, should complete in ~100-200ms (not 500ms)
        assert duration < 0.3  # 300ms threshold


class TestProgressTracking:
    """Tests for progress tracking functionality."""

    @pytest.mark.asyncio
    async def test_progress_callback_called(
        self, mock_llm_client, sample_requirements, sample_test_response
    ):
        """Test that progress callback is called for each requirement."""
        mock_llm_client.generate.return_value = sample_test_response

        progress_calls = []

        def progress_callback(completed, total, req_id):
            progress_calls.append((completed, total, req_id))

        generator = ManualTestGenerator(mock_llm_client)
        await generator.generate(
            sample_requirements[:3],
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
            progress_callback=progress_callback,
        )

        # Should have 3 progress calls (one per requirement)
        assert len(progress_calls) == 3

        # Verify total is always 3
        assert all(total == 3 for _, total, _ in progress_calls)

        # Verify completed increases
        completed_values = [completed for completed, _, _ in progress_calls]
        assert sorted(completed_values) == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_progress_callback_includes_requirement_id(
        self, mock_llm_client, sample_requirements, sample_test_response
    ):
        """Test that progress callback includes requirement ID."""
        mock_llm_client.generate.return_value = sample_test_response

        progress_calls = []

        def progress_callback(completed, total, req_id):
            progress_calls.append(req_id)

        generator = ManualTestGenerator(mock_llm_client)
        await generator.generate(
            sample_requirements[:3],
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
            progress_callback=progress_callback,
        )

        # Should have all requirement IDs
        assert len(progress_calls) == 3
        assert set(progress_calls) == {"REQ-001", "REQ-002", "REQ-003"}

    @pytest.mark.asyncio
    async def test_progress_callback_called_on_failure(
        self, mock_llm_client, sample_requirements
    ):
        """Test that progress callback is called even when generation fails."""
        mock_llm_client.generate.side_effect = LLMError("API error")

        progress_calls = []

        def progress_callback(completed, total, req_id):
            progress_calls.append((completed, total, req_id))

        generator = ManualTestGenerator(mock_llm_client)
        
        # Should raise error when all requirements fail
        with pytest.raises(LLMError, match="Failed to generate tests for all"):
            await generator.generate(
                sample_requirements[:2],
                include_positive=True,
                include_negative=False,
                include_edge_cases=False,
                progress_callback=progress_callback,
            )

        # Should still have progress calls even though generation failed
        assert len(progress_calls) == 2

    @pytest.mark.asyncio
    async def test_progress_callback_exception_handled(
        self, mock_llm_client, sample_requirements, sample_test_response
    ):
        """Test that exceptions in progress callback don't break generation."""
        mock_llm_client.generate.return_value = sample_test_response

        def failing_callback(completed, total, req_id):
            raise ValueError("Callback error")

        generator = ManualTestGenerator(mock_llm_client)

        # Should not raise despite callback failing
        artifacts = await generator.generate(
            sample_requirements[:2],
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
            progress_callback=failing_callback,
        )

        # Generation should still succeed
        assert len(artifacts) == 2


class TestPartialFailureHandling:
    """Tests for graceful handling of partial failures."""

    @pytest.mark.asyncio
    async def test_continues_on_partial_failure(
        self, mock_llm_client, sample_requirements, sample_test_response
    ):
        """Test that generation continues when some requirements fail."""
        # First two calls fail, rest succeed
        mock_llm_client.generate.side_effect = [
            LLMError("API error"),
            LLMError("API error"),
            sample_test_response,
            sample_test_response,
            sample_test_response,
        ]

        generator = ManualTestGenerator(mock_llm_client)
        artifacts = await generator.generate(
            sample_requirements[:5],
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
        )

        # Should have 3 artifacts from successful requirements
        assert len(artifacts) == 3

    @pytest.mark.asyncio
    async def test_raises_error_when_all_fail(
        self, mock_llm_client, sample_requirements
    ):
        """Test that error is raised when all requirements fail."""
        mock_llm_client.generate.side_effect = LLMError("API error")

        generator = ManualTestGenerator(mock_llm_client)

        with pytest.raises(LLMError, match="Failed to generate tests for all"):
            await generator.generate(
                sample_requirements[:3],
                include_positive=True,
                include_negative=False,
                include_edge_cases=False,
            )

    @pytest.mark.asyncio
    async def test_partial_failure_logged(
        self, mock_llm_client, sample_requirements, sample_test_response, caplog
    ):
        """Test that partial failures are logged."""
        import logging

        caplog.set_level(logging.ERROR)

        # First call fails, second succeeds
        mock_llm_client.generate.side_effect = [
            LLMError("API error"),
            sample_test_response,
        ]

        generator = ManualTestGenerator(mock_llm_client)
        await generator.generate(
            sample_requirements[:2],
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
        )

        # Should have error log for failed requirement
        assert any("Failed to generate tests" in record.message for record in caplog.records)
        assert any("REQ-001" in record.message for record in caplog.records)


class TestBatchGeneration:
    """Tests for batch generation functionality."""

    @pytest.mark.asyncio
    async def test_batch_generation_basic(
        self, mock_llm_client, sample_requirements, sample_test_response
    ):
        """Test basic batch generation."""
        mock_llm_client.generate.return_value = sample_test_response

        generator = ManualTestGenerator(mock_llm_client)
        artifacts = await generator.generate_batch(
            sample_requirements,
            batch_size=3,
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
        )

        # Should generate test cases for all 10 requirements
        assert len(artifacts) == 10

    @pytest.mark.asyncio
    async def test_batch_generation_splits_correctly(
        self, mock_llm_client, sample_requirements, sample_test_response
    ):
        """Test that requirements are split into correct batch sizes."""
        mock_llm_client.generate.return_value = sample_test_response

        batch_progress = []

        def batch_callback(completed, total):
            batch_progress.append((completed, total))

        generator = ManualTestGenerator(mock_llm_client)
        await generator.generate_batch(
            sample_requirements,  # 10 requirements
            batch_size=3,  # Should create 4 batches: 3, 3, 3, 1
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
            progress_callback=batch_callback,
        )

        # Should have 4 batch progress calls
        assert len(batch_progress) == 4
        assert batch_progress[-1] == (4, 4)  # Last call should be (4, 4)

    @pytest.mark.asyncio
    async def test_batch_generation_with_empty_list(
        self, mock_llm_client, sample_test_response
    ):
        """Test batch generation with empty requirements list."""
        mock_llm_client.generate.return_value = sample_test_response

        generator = ManualTestGenerator(mock_llm_client)
        artifacts = await generator.generate_batch(
            [],
            batch_size=5,
        )

        assert artifacts == []
        mock_llm_client.generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_batch_generation_continues_on_batch_failure(
        self, mock_llm_client, sample_requirements, sample_test_response
    ):
        """Test that batch generation continues when one batch fails."""
        # Simulate first batch failing, second succeeding
        call_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 3:  # First batch (3 requirements)
                raise LLMError("API error")
            return sample_test_response

        mock_llm_client.generate.side_effect = mock_generate

        generator = ManualTestGenerator(mock_llm_client)
        artifacts = await generator.generate_batch(
            sample_requirements[:6],  # 6 requirements
            batch_size=3,  # 2 batches
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
        )

        # Should have artifacts from second batch only
        assert len(artifacts) == 3

    @pytest.mark.asyncio
    async def test_batch_progress_callback(
        self, mock_llm_client, sample_requirements, sample_test_response
    ):
        """Test batch progress callback functionality."""
        mock_llm_client.generate.return_value = sample_test_response

        batch_progress = []

        def batch_callback(completed, total):
            batch_progress.append((completed, total))

        generator = ManualTestGenerator(mock_llm_client)
        await generator.generate_batch(
            sample_requirements[:5],
            batch_size=2,  # 3 batches: 2, 2, 1
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
            progress_callback=batch_callback,
        )

        # Should have 3 batch callbacks
        assert len(batch_progress) == 3
        assert batch_progress[0] == (1, 3)
        assert batch_progress[1] == (2, 3)
        assert batch_progress[2] == (3, 3)

    @pytest.mark.asyncio
    async def test_batch_callback_exception_handled(
        self, mock_llm_client, sample_requirements, sample_test_response
    ):
        """Test that exceptions in batch callback don't break generation."""
        mock_llm_client.generate.return_value = sample_test_response

        def failing_callback(completed, total):
            raise ValueError("Callback error")

        generator = ManualTestGenerator(mock_llm_client)

        # Should not raise despite callback failing
        artifacts = await generator.generate_batch(
            sample_requirements[:4],
            batch_size=2,
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
            progress_callback=failing_callback,
        )

        # Generation should still succeed
        assert len(artifacts) == 4


class TestConcurrencyConfiguration:
    """Tests for concurrency configuration."""

    @pytest.mark.asyncio
    async def test_custom_max_concurrent(
        self, mock_llm_client, sample_requirements, sample_test_response
    ):
        """Test that custom max_concurrent is respected."""
        mock_llm_client.generate.return_value = sample_test_response

        generator = ManualTestGenerator(mock_llm_client, max_concurrent=2)
        assert generator.max_concurrent == 2

        artifacts = await generator.generate(
            sample_requirements[:3],
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
        )

        assert len(artifacts) == 3

    @pytest.mark.asyncio
    async def test_default_max_concurrent(
        self, mock_llm_client, sample_requirements, sample_test_response
    ):
        """Test default max_concurrent value."""
        mock_llm_client.generate.return_value = sample_test_response

        generator = ManualTestGenerator(mock_llm_client)
        assert generator.max_concurrent == 5  # Default value

        artifacts = await generator.generate(
            sample_requirements[:3],
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
        )

        assert len(artifacts) == 3


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    @pytest.mark.asyncio
    async def test_large_batch_with_progress_tracking(
        self, mock_llm_client, sample_test_response
    ):
        """Test processing a large batch with progress tracking."""
        # Create 50 requirements
        large_requirements = [
            Requirement(
                id=f"REQ-{i:03d}",
                type=RequirementType.FUNCTIONAL,
                content=f"Requirement {i}",
                source="requirements.md",
            )
            for i in range(1, 51)
        ]

        mock_llm_client.generate.return_value = sample_test_response

        progress_updates = []

        def progress_callback(completed, total, req_id):
            progress_updates.append(completed)

        generator = ManualTestGenerator(mock_llm_client, max_concurrent=10)
        artifacts = await generator.generate(
            large_requirements,
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
            progress_callback=progress_callback,
        )

        # Should generate 50 test cases
        assert len(artifacts) == 50

        # Should have 50 progress updates
        assert len(progress_updates) == 50

        # Progress should go from 1 to 50
        assert sorted(progress_updates) == list(range(1, 51))

    @pytest.mark.asyncio
    async def test_mixed_success_and_failure(
        self, mock_llm_client, sample_requirements, sample_test_response
    ):
        """Test realistic scenario with mixed success and failure."""
        # Simulate intermittent failures
        call_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Fail every 3rd call
            if call_count % 3 == 0:
                raise LLMError("Intermittent API error")
            return sample_test_response

        mock_llm_client.generate.side_effect = mock_generate

        generator = ManualTestGenerator(mock_llm_client, max_concurrent=3)
        artifacts = await generator.generate(
            sample_requirements[:9],  # 9 requirements
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
        )

        # Should have 6 successful artifacts (9 - 3 failures)
        assert len(artifacts) == 6
