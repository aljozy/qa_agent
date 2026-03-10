"""Workflow orchestrator for end-to-end QA Agent pipeline."""

import logging
from pathlib import Path
from typing import Callable, List, Optional

from qa_agent.analysis.rtm_generator import RTMEntry, RTMGenerator
from qa_agent.config import Config
from qa_agent.generators.manual_test_generator import ManualTestGenerator
from qa_agent.llm.client import LLMClient, LLMError
from qa_agent.models.base import Requirement, TestArtifact
from qa_agent.parsers.markdown_parser import MarkdownParser
from qa_agent.storage.file_storage import FileStorage

logger = logging.getLogger(__name__)


class WorkflowError(Exception):
    """Base exception for workflow errors."""

    pass


class WorkflowOrchestrator:
    """
    Orchestrates the end-to-end workflow for the QA Agent.
    
    The orchestrator coordinates the following pipeline:
    1. Parse requirements from markdown
    2. Store requirements to JSON
    3. Generate test cases using AI
    4. Generate RTM mapping requirements to tests
    
    Provides progress tracking, error handling, and graceful degradation.
    """

    def __init__(self, config: Config):
        """
        Initialize the workflow orchestrator.
        
        Args:
            config: Configuration for the QA Agent
        """
        self.config = config
        
        # Initialize components
        self.parser = MarkdownParser()
        self.storage = FileStorage(config.output.directory / "requirements")
        self.rtm_generator = RTMGenerator()
        
        # LLM client and generator will be initialized when needed
        self._llm_client: Optional[LLMClient] = None
        self._test_generator: Optional[ManualTestGenerator] = None
        
        logger.info("Initialized WorkflowOrchestrator")

    @property
    def llm_client(self) -> LLMClient:
        """Lazy initialization of LLM client."""
        if self._llm_client is None:
            self._llm_client = LLMClient(self.config.ai)
        return self._llm_client

    @property
    def test_generator(self) -> ManualTestGenerator:
        """Lazy initialization of test generator."""
        if self._test_generator is None:
            self._test_generator = ManualTestGenerator(self.llm_client)
        return self._test_generator

    async def run_full_pipeline(
        self,
        input_file: Path,
        include_positive: bool = True,
        include_negative: bool = True,
        include_edge_cases: bool = True,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> dict:
        """
        Run the complete pipeline from parsing to RTM generation.
        
        Args:
            input_file: Path to the markdown requirements file
            include_positive: Whether to generate positive test scenarios
            include_negative: Whether to generate negative test scenarios
            include_edge_cases: Whether to generate edge case scenarios
            progress_callback: Optional callback function(stage, completed, total)
                             called to report progress
            
        Returns:
            Dictionary containing:
                - requirements: List of parsed requirements
                - test_artifacts: List of generated test artifacts
                - rtm_entries: List of RTM entries
                - coverage_percentage: Coverage percentage
                - requirements_file: Path to saved requirements file
                - tests_file: Path to saved test artifacts file
                - rtm_file: Path to saved RTM file
                
        Raises:
            WorkflowError: If any step in the pipeline fails
        """
        logger.info(f"Starting full pipeline for: {input_file}")
        
        try:
            # Step 1: Parse requirements
            logger.info("Step 1/4: Parsing requirements")
            if progress_callback:
                progress_callback("parse", 0, 4)
            
            requirements = await self.parse_requirements(input_file)
            
            if progress_callback:
                progress_callback("parse", 1, 4)
            
            logger.info(f"Parsed {len(requirements)} requirements")
            
            # Step 2: Store requirements
            logger.info("Step 2/4: Storing requirements")
            if progress_callback:
                progress_callback("store", 1, 4)
            
            requirements_file = await self.store_requirements(
                requirements, input_file.stem
            )
            
            if progress_callback:
                progress_callback("store", 2, 4)
            
            logger.info(f"Stored requirements to: {requirements_file}")
            
            # Step 3: Generate test cases
            logger.info("Step 3/4: Generating test cases")
            if progress_callback:
                progress_callback("generate", 2, 4)
            
            test_artifacts = await self.generate_tests(
                requirements,
                include_positive=include_positive,
                include_negative=include_negative,
                include_edge_cases=include_edge_cases,
            )
            
            if progress_callback:
                progress_callback("generate", 3, 4)
            
            logger.info(f"Generated {len(test_artifacts)} test cases")
            
            # Store test artifacts
            tests_file = await self.store_test_artifacts(
                test_artifacts, f"{input_file.stem}_tests"
            )
            logger.info(f"Stored test artifacts to: {tests_file}")
            
            # Step 4: Generate RTM
            logger.info("Step 4/4: Generating RTM")
            if progress_callback:
                progress_callback("rtm", 3, 4)
            
            rtm_entries, coverage_pct = await self.generate_rtm(
                requirements, test_artifacts
            )
            
            if progress_callback:
                progress_callback("rtm", 4, 4)
            
            logger.info(f"Generated RTM with {coverage_pct:.1f}% coverage")
            
            # Store RTM
            rtm_file = await self.store_rtm(rtm_entries)
            logger.info(f"Stored RTM to: {rtm_file}")
            
            # Return results
            result = {
                "requirements": requirements,
                "test_artifacts": test_artifacts,
                "rtm_entries": rtm_entries,
                "coverage_percentage": coverage_pct,
                "requirements_file": requirements_file,
                "tests_file": tests_file,
                "rtm_file": rtm_file,
            }
            
            logger.info("Pipeline completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise WorkflowError(f"Pipeline execution failed: {str(e)}") from e

    async def parse_requirements(self, input_file: Path) -> List[Requirement]:
        """
        Parse requirements from a markdown file.
        
        Args:
            input_file: Path to the markdown file
            
        Returns:
            List of parsed requirements
            
        Raises:
            WorkflowError: If parsing fails
        """
        try:
            logger.debug(f"Parsing requirements from: {input_file}")
            
            # Validate file exists
            if not input_file.exists():
                raise WorkflowError(f"Input file not found: {input_file}")
            
            # Parse requirements
            requirements = self.parser.parse_file(input_file)
            
            if not requirements:
                logger.warning("No requirements found in the document")
                raise WorkflowError(
                    "No requirements found in the document. "
                    "Please ensure the markdown file contains requirements."
                )
            
            logger.debug(f"Successfully parsed {len(requirements)} requirements")
            return requirements
            
        except WorkflowError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse requirements: {str(e)}")
            raise WorkflowError(f"Failed to parse requirements: {str(e)}") from e

    async def store_requirements(
        self, requirements: List[Requirement], filename: str
    ) -> Path:
        """
        Store requirements to JSON file.
        
        Args:
            requirements: List of requirements to store
            filename: Base filename (without extension)
            
        Returns:
            Path to the saved file
            
        Raises:
            WorkflowError: If storage fails
        """
        try:
            logger.debug(f"Storing {len(requirements)} requirements")
            
            # Ensure output directory exists
            self.config.ensure_output_directory()
            
            # Save requirements
            output_path = self.storage.save(requirements, filename)
            
            logger.debug(f"Successfully stored requirements to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to store requirements: {str(e)}")
            raise WorkflowError(f"Failed to store requirements: {str(e)}") from e

    async def generate_tests(
        self,
        requirements: List[Requirement],
        include_positive: bool = True,
        include_negative: bool = True,
        include_edge_cases: bool = True,
    ) -> List[TestArtifact]:
        """
        Generate test cases from requirements.
        
        Args:
            requirements: List of requirements to generate tests for
            include_positive: Whether to generate positive scenarios
            include_negative: Whether to generate negative scenarios
            include_edge_cases: Whether to generate edge case scenarios
            
        Returns:
            List of generated test artifacts
            
        Raises:
            WorkflowError: If test generation fails
        """
        try:
            logger.debug(
                f"Generating tests for {len(requirements)} requirements "
                f"(positive={include_positive}, negative={include_negative}, "
                f"edge_cases={include_edge_cases})"
            )
            
            # Generate test cases
            test_artifacts = await self.test_generator.generate(
                requirements=requirements,
                include_positive=include_positive,
                include_negative=include_negative,
                include_edge_cases=include_edge_cases,
            )
            
            if not test_artifacts:
                logger.warning("No test cases were generated")
                raise WorkflowError(
                    "No test cases were generated. "
                    "This may indicate an issue with the AI provider or requirements."
                )
            
            logger.debug(f"Successfully generated {len(test_artifacts)} test cases")
            return test_artifacts
            
        except LLMError as e:
            logger.error(f"LLM error during test generation: {str(e)}")
            raise WorkflowError(f"Test generation failed: {str(e)}") from e
        except WorkflowError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate tests: {str(e)}")
            raise WorkflowError(f"Failed to generate tests: {str(e)}") from e

    async def store_test_artifacts(
        self, test_artifacts: List[TestArtifact], filename: str
    ) -> Path:
        """
        Store test artifacts to JSON file.
        
        Args:
            test_artifacts: List of test artifacts to store
            filename: Base filename (without extension)
            
        Returns:
            Path to the saved file
            
        Raises:
            WorkflowError: If storage fails
        """
        try:
            import json
            
            logger.debug(f"Storing {len(test_artifacts)} test artifacts")
            
            # Ensure output directory exists
            tests_dir = self.config.output.directory / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            
            # Save test artifacts
            output_path = tests_dir / f"{filename}.json"
            
            with open(output_path, "w", encoding="utf-8") as f:
                artifacts_data = [
                    artifact.model_dump(mode="json") for artifact in test_artifacts
                ]
                json.dump(artifacts_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Successfully stored test artifacts to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to store test artifacts: {str(e)}")
            raise WorkflowError(f"Failed to store test artifacts: {str(e)}") from e

    async def generate_rtm(
        self, requirements: List[Requirement], test_artifacts: List[TestArtifact]
    ) -> tuple[List[RTMEntry], float]:
        """
        Generate Requirement Traceability Matrix.
        
        Args:
            requirements: List of requirements
            test_artifacts: List of test artifacts
            
        Returns:
            Tuple of (RTM entries, coverage percentage)
            
        Raises:
            WorkflowError: If RTM generation fails
        """
        try:
            logger.debug(
                f"Generating RTM for {len(requirements)} requirements "
                f"and {len(test_artifacts)} test artifacts"
            )
            
            # Generate RTM
            rtm_entries = self.rtm_generator.generate(requirements, test_artifacts)
            
            # Calculate coverage
            coverage_pct = self.rtm_generator.calculate_coverage_percentage(
                requirements, test_artifacts
            )
            
            logger.debug(
                f"Successfully generated RTM with {len(rtm_entries)} entries "
                f"({coverage_pct:.1f}% coverage)"
            )
            
            return rtm_entries, coverage_pct
            
        except Exception as e:
            logger.error(f"Failed to generate RTM: {str(e)}")
            raise WorkflowError(f"Failed to generate RTM: {str(e)}") from e

    async def store_rtm(self, rtm_entries: List[RTMEntry]) -> Path:
        """
        Store RTM to CSV file.
        
        Args:
            rtm_entries: List of RTM entries to store
            
        Returns:
            Path to the saved file
            
        Raises:
            WorkflowError: If storage fails
        """
        try:
            logger.debug(f"Storing RTM with {len(rtm_entries)} entries")
            
            # Ensure output directory exists
            rtm_dir = self.config.output.directory / "rtm"
            rtm_dir.mkdir(parents=True, exist_ok=True)
            
            # Save RTM
            output_path = rtm_dir / "rtm.csv"
            self.rtm_generator.export_to_csv(rtm_entries, output_path)
            
            logger.debug(f"Successfully stored RTM to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to store RTM: {str(e)}")
            raise WorkflowError(f"Failed to store RTM: {str(e)}") from e
