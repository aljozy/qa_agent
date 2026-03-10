"""Manual test case generator implementation."""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional

from qa_agent.llm.client import LLMClient, LLMError
from qa_agent.models.base import Requirement, TestArtifact, TestType

logger = logging.getLogger(__name__)


class ManualTestGenerator:
    """
    Generator for creating manual test cases from requirements.
    
    This generator uses an LLM to create comprehensive manual test cases
    covering positive scenarios, negative scenarios, and edge cases.
    Each test case includes test ID, description, preconditions, steps,
    expected results, and links to source requirements.
    
    Supports batch generation with parallel processing, progress tracking,
    and graceful handling of partial failures.
    """

    def __init__(self, llm_client: LLMClient, max_concurrent: int = 5):
        """
        Initialize the manual test generator.
        
        Args:
            llm_client: LLM client for generating test cases
            max_concurrent: Maximum number of concurrent LLM requests (default: 5)
        """
        self.llm_client = llm_client
        self.max_concurrent = max_concurrent
        logger.info(f"Initialized ManualTestGenerator with max_concurrent={max_concurrent}")

    async def generate(
        self,
        requirements: List[Requirement],
        include_positive: bool = True,
        include_negative: bool = True,
        include_edge_cases: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> List[TestArtifact]:
        """
        Generate manual test cases from requirements.
        
        Processes requirements in parallel with configurable concurrency limit.
        Tracks progress and handles partial failures gracefully.
        
        Args:
            requirements: List of requirements to generate tests for
            include_positive: Whether to generate positive test scenarios
            include_negative: Whether to generate negative test scenarios
            include_edge_cases: Whether to generate edge case scenarios
            progress_callback: Optional callback function(completed, total, requirement_id)
                             called after each requirement is processed
            
        Returns:
            List of generated test artifacts
            
        Raises:
            LLMError: If test generation fails for all requirements
        """
        if not requirements:
            logger.warning("No requirements provided for test generation")
            return []

        logger.info(
            f"Generating manual test cases for {len(requirements)} requirements "
            f"(positive={include_positive}, negative={include_negative}, "
            f"edge_cases={include_edge_cases}, max_concurrent={self.max_concurrent})"
        )

        # Use semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Track progress
        completed = 0
        total = len(requirements)
        failed_requirements = []
        
        async def process_requirement(requirement: Requirement) -> List[TestArtifact]:
            """Process a single requirement with semaphore."""
            nonlocal completed
            
            async with semaphore:
                try:
                    artifacts = await self._generate_for_requirement(
                        requirement,
                        include_positive=include_positive,
                        include_negative=include_negative,
                        include_edge_cases=include_edge_cases,
                    )
                    
                    completed += 1
                    logger.debug(
                        f"Generated {len(artifacts)} test cases for requirement {requirement.id} "
                        f"({completed}/{total})"
                    )
                    
                    # Call progress callback if provided
                    if progress_callback:
                        try:
                            progress_callback(completed, total, requirement.id)
                        except Exception as e:
                            logger.warning(f"Progress callback failed: {str(e)}")
                    
                    return artifacts
                    
                except Exception as e:
                    completed += 1
                    failed_requirements.append((requirement.id, str(e)))
                    logger.error(
                        f"Failed to generate tests for requirement {requirement.id}: {str(e)} "
                        f"({completed}/{total})"
                    )
                    
                    # Call progress callback even on failure
                    if progress_callback:
                        try:
                            progress_callback(completed, total, requirement.id)
                        except Exception as callback_error:
                            logger.warning(f"Progress callback failed: {str(callback_error)}")
                    
                    return []
        
        # Process all requirements in parallel with concurrency limit
        tasks = [process_requirement(req) for req in requirements]
        results = await asyncio.gather(*tasks)
        
        # Flatten results
        all_artifacts = [artifact for artifacts in results for artifact in artifacts]
        
        # Log summary
        success_count = len(requirements) - len(failed_requirements)
        logger.info(
            f"Batch generation complete: {success_count}/{total} requirements succeeded, "
            f"generated {len(all_artifacts)} total test cases"
        )
        
        if failed_requirements:
            logger.warning(
                f"Failed requirements: {', '.join(req_id for req_id, _ in failed_requirements)}"
            )
            
            # If all requirements failed, raise an error
            if len(failed_requirements) == total:
                error_summary = "; ".join(
                    f"{req_id}: {error}" for req_id, error in failed_requirements[:3]
                )
                raise LLMError(
                    f"Failed to generate tests for all {total} requirements. "
                    f"Sample errors: {error_summary}"
                )
        
        return all_artifacts

    async def _generate_for_requirement(
        self,
        requirement: Requirement,
        include_positive: bool,
        include_negative: bool,
        include_edge_cases: bool,
    ) -> List[TestArtifact]:
        """
        Generate test cases for a single requirement.
        
        Args:
            requirement: The requirement to generate tests for
            include_positive: Whether to generate positive scenarios
            include_negative: Whether to generate negative scenarios
            include_edge_cases: Whether to generate edge case scenarios
            
        Returns:
            List of test artifacts for this requirement
        """
        artifacts = []

        # Generate positive test cases
        if include_positive:
            positive_tests = await self._generate_positive_tests(requirement)
            artifacts.extend(positive_tests)

        # Generate negative test cases
        if include_negative:
            negative_tests = await self._generate_negative_tests(requirement)
            artifacts.extend(negative_tests)

        # Generate edge case test cases
        if include_edge_cases:
            edge_case_tests = await self._generate_edge_case_tests(requirement)
            artifacts.extend(edge_case_tests)

        return artifacts

    async def _generate_positive_tests(
        self, requirement: Requirement
    ) -> List[TestArtifact]:
        """
        Generate positive test scenarios for a requirement.
        
        Args:
            requirement: The requirement to generate tests for
            
        Returns:
            List of positive test artifacts
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_positive_test_prompt(requirement)

        try:
            response = await self.llm_client.generate(user_prompt, system_prompt)
            test_cases = self._parse_llm_response(response, requirement, "positive")
            return test_cases
        except LLMError as e:
            logger.error(f"Failed to generate positive tests: {str(e)}")
            raise

    async def _generate_negative_tests(
        self, requirement: Requirement
    ) -> List[TestArtifact]:
        """
        Generate negative test scenarios for a requirement.
        
        Args:
            requirement: The requirement to generate tests for
            
        Returns:
            List of negative test artifacts
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_negative_test_prompt(requirement)

        try:
            response = await self.llm_client.generate(user_prompt, system_prompt)
            test_cases = self._parse_llm_response(response, requirement, "negative")
            return test_cases
        except LLMError as e:
            logger.error(f"Failed to generate negative tests: {str(e)}")
            raise

    async def _generate_edge_case_tests(
        self, requirement: Requirement
    ) -> List[TestArtifact]:
        """
        Generate edge case test scenarios for a requirement.
        
        Args:
            requirement: The requirement to generate tests for
            
        Returns:
            List of edge case test artifacts
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_edge_case_test_prompt(requirement)

        try:
            response = await self.llm_client.generate(user_prompt, system_prompt)
            test_cases = self._parse_llm_response(response, requirement, "edge_case")
            return test_cases
        except LLMError as e:
            logger.error(f"Failed to generate edge case tests: {str(e)}")
            raise

    def _build_system_prompt(self) -> str:
        """
        Build the system prompt for test case generation.
        
        Returns:
            System prompt string
        """
        return """You are an expert QA engineer specializing in manual test case design.
Your task is to generate comprehensive, well-structured manual test cases.

Each test case must include:
1. test_id: A unique identifier (e.g., TC001, TC002)
2. description: A clear, concise description of what is being tested
3. preconditions: List of conditions that must be met before executing the test
4. steps: Numbered list of actions to perform
5. expected_results: List of expected outcomes for each step or overall

Format your response as a JSON array of test cases. Example:
[
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
      "Welcome message is displayed",
      "User session is created"
    ]
  }
]

Generate 1-3 test cases per scenario type. Be specific and actionable."""

    def _build_positive_test_prompt(self, requirement: Requirement) -> str:
        """
        Build the prompt for generating positive test cases.
        
        Args:
            requirement: The requirement to generate tests for
            
        Returns:
            User prompt string
        """
        return f"""Generate positive test cases for the following requirement:

Requirement ID: {requirement.id}
Requirement Type: {requirement.type.value}
Requirement Content:
{requirement.content}

Positive test cases should verify that the system works correctly when:
- Valid inputs are provided
- Normal conditions are met
- Expected user flows are followed
- All acceptance criteria are satisfied

Generate 1-3 comprehensive positive test cases in JSON format."""

    def _build_negative_test_prompt(self, requirement: Requirement) -> str:
        """
        Build the prompt for generating negative test cases.
        
        Args:
            requirement: The requirement to generate tests for
            
        Returns:
            User prompt string
        """
        return f"""Generate negative test cases for the following requirement:

Requirement ID: {requirement.id}
Requirement Type: {requirement.type.value}
Requirement Content:
{requirement.content}

Negative test cases should verify that the system handles errors correctly when:
- Invalid inputs are provided
- Required fields are missing
- Unauthorized access is attempted
- Business rules are violated
- System constraints are exceeded

Generate 1-3 comprehensive negative test cases in JSON format."""

    def _build_edge_case_test_prompt(self, requirement: Requirement) -> str:
        """
        Build the prompt for generating edge case test cases.
        
        Args:
            requirement: The requirement to generate tests for
            
        Returns:
            User prompt string
        """
        return f"""Generate edge case test cases for the following requirement:

Requirement ID: {requirement.id}
Requirement Type: {requirement.type.value}
Requirement Content:
{requirement.content}

Edge case test cases should verify system behavior at boundaries and unusual conditions:
- Minimum and maximum values
- Empty or null inputs
- Very large data sets
- Concurrent operations
- Unusual but valid combinations
- Boundary conditions

Generate 1-3 comprehensive edge case test cases in JSON format."""

    def _parse_llm_response(
        self, response: str, requirement: Requirement, scenario_type: str
    ) -> List[TestArtifact]:
        """
        Parse LLM response into structured TestArtifact objects.
        
        Args:
            response: Raw LLM response text
            requirement: The source requirement
            scenario_type: Type of scenario (positive, negative, edge_case)
            
        Returns:
            List of parsed test artifacts
            
        Raises:
            ValueError: If response cannot be parsed
        """
        try:
            # Try to extract JSON from the response
            # LLM might wrap JSON in markdown code blocks
            response = response.strip()
            
            # Remove markdown code blocks if present
            if response.startswith("```json"):
                response = response[7:]
            elif response.startswith("```"):
                response = response[3:]
            
            if response.endswith("```"):
                response = response[:-3]
            
            response = response.strip()
            
            # Parse JSON
            test_cases = json.loads(response)
            
            if not isinstance(test_cases, list):
                raise ValueError("Response must be a JSON array of test cases")
            
            # Convert to TestArtifact objects
            artifacts = []
            for test_case in test_cases:
                artifact = self._create_test_artifact(
                    test_case, requirement, scenario_type
                )
                artifacts.append(artifact)
            
            return artifacts
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.debug(f"Response was: {response}")
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            raise ValueError(f"Failed to parse test cases: {str(e)}")

    def _create_test_artifact(
        self, test_case: Dict[str, Any], requirement: Requirement, scenario_type: str
    ) -> TestArtifact:
        """
        Create a TestArtifact from parsed test case data.
        
        Args:
            test_case: Parsed test case dictionary
            requirement: Source requirement
            scenario_type: Type of scenario (positive, negative, edge_case)
            
        Returns:
            TestArtifact object
            
        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        required_fields = ["test_id", "description", "preconditions", "steps", "expected_results"]
        missing_fields = [field for field in required_fields if field not in test_case]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Build test content in a structured format
        content = self._format_test_content(test_case)
        
        # Create metadata
        metadata = {
            "scenario_type": scenario_type,
            "test_id": test_case["test_id"],
            "requirement_type": requirement.type.value,
            "source_requirement": requirement.id,
        }
        
        # Create and return TestArtifact
        return TestArtifact(
            type=TestType.MANUAL,
            content=content,
            requirement_ids=[requirement.id],
            metadata=metadata,
        )

    def _format_test_content(self, test_case: Dict[str, Any]) -> str:
        """
        Format test case data into a readable string.
        
        Args:
            test_case: Test case dictionary
            
        Returns:
            Formatted test content string
        """
        lines = []
        
        # Test ID and Description
        lines.append(f"Test ID: {test_case['test_id']}")
        lines.append(f"Description: {test_case['description']}")
        lines.append("")
        
        # Preconditions
        lines.append("Preconditions:")
        for i, precondition in enumerate(test_case['preconditions'], 1):
            lines.append(f"  {i}. {precondition}")
        lines.append("")
        
        # Test Steps
        lines.append("Test Steps:")
        for i, step in enumerate(test_case['steps'], 1):
            lines.append(f"  {i}. {step}")
        lines.append("")
        
        # Expected Results
        lines.append("Expected Results:")
        for i, result in enumerate(test_case['expected_results'], 1):
            lines.append(f"  {i}. {result}")
        
        return "\n".join(lines)

    async def generate_batch(
        self,
        requirements: List[Requirement],
        batch_size: int = 10,
        include_positive: bool = True,
        include_negative: bool = True,
        include_edge_cases: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[TestArtifact]:
        """
        Generate test cases in batches for better control over large requirement sets.
        
        This method processes requirements in batches, which can be useful for:
        - Rate limiting with external APIs
        - Memory management with large requirement sets
        - Checkpoint/resume capabilities
        
        Args:
            requirements: List of requirements to generate tests for
            batch_size: Number of requirements to process per batch
            include_positive: Whether to generate positive test scenarios
            include_negative: Whether to generate negative test scenarios
            include_edge_cases: Whether to generate edge case scenarios
            progress_callback: Optional callback function(completed_batches, total_batches)
                             called after each batch is processed
            
        Returns:
            List of generated test artifacts
            
        Raises:
            LLMError: If test generation fails for all requirements
        """
        if not requirements:
            logger.warning("No requirements provided for batch generation")
            return []
        
        # Split requirements into batches
        batches = [
            requirements[i:i + batch_size]
            for i in range(0, len(requirements), batch_size)
        ]
        
        total_batches = len(batches)
        logger.info(
            f"Starting batch generation: {len(requirements)} requirements "
            f"in {total_batches} batches of size {batch_size}"
        )
        
        all_artifacts = []
        completed_batches = 0
        
        for batch_num, batch in enumerate(batches, 1):
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} requirements)")
            
            try:
                # Process batch using parallel generation
                batch_artifacts = await self.generate(
                    requirements=batch,
                    include_positive=include_positive,
                    include_negative=include_negative,
                    include_edge_cases=include_edge_cases,
                )
                
                all_artifacts.extend(batch_artifacts)
                completed_batches += 1
                
                logger.info(
                    f"Batch {batch_num}/{total_batches} complete: "
                    f"generated {len(batch_artifacts)} test cases"
                )
                
                # Call progress callback if provided
                if progress_callback:
                    try:
                        progress_callback(completed_batches, total_batches)
                    except Exception as e:
                        logger.warning(f"Batch progress callback failed: {str(e)}")
                        
            except Exception as e:
                logger.error(f"Batch {batch_num}/{total_batches} failed: {str(e)}")
                # Continue with next batch
                continue
        
        logger.info(
            f"Batch generation complete: processed {completed_batches}/{total_batches} batches, "
            f"generated {len(all_artifacts)} total test cases"
        )
        
        return all_artifacts
