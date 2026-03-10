"""Example demonstrating the WorkflowOrchestrator for end-to-end pipeline execution."""

import asyncio
from pathlib import Path

from qa_agent.config import Config
from qa_agent.core import WorkflowOrchestrator


async def main():
    """Run the workflow orchestrator example."""
    
    # Load configuration
    config = Config()
    
    # Override output directory for this example
    config.output.directory = Path("output/orchestrator_example")
    
    # Create orchestrator
    orchestrator = WorkflowOrchestrator(config)
    
    # Define input file
    input_file = Path("examples/sample_requirements.md")
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        print("Please create a sample requirements markdown file first.")
        return
    
    print("=" * 60)
    print("Workflow Orchestrator Example")
    print("=" * 60)
    print()
    
    # Define progress callback
    def progress_callback(stage: str, completed: int, total: int):
        """Print progress updates."""
        percentage = (completed / total) * 100
        print(f"[{stage.upper()}] Progress: {completed}/{total} ({percentage:.0f}%)")
    
    try:
        print(f"Input file: {input_file}")
        print(f"Output directory: {config.output.directory}")
        print()
        
        # Run the full pipeline
        print("Starting pipeline...")
        print()
        
        result = await orchestrator.run_full_pipeline(
            input_file=input_file,
            include_positive=True,
            include_negative=True,
            include_edge_cases=True,
            progress_callback=progress_callback,
        )
        
        print()
        print("=" * 60)
        print("Pipeline Results")
        print("=" * 60)
        print()
        print(f"Requirements parsed: {len(result['requirements'])}")
        print(f"Test cases generated: {len(result['test_artifacts'])}")
        print(f"RTM entries: {len(result['rtm_entries'])}")
        print(f"Coverage: {result['coverage_percentage']:.1f}%")
        print()
        print("Output files:")
        print(f"  Requirements: {result['requirements_file']}")
        print(f"  Tests: {result['tests_file']}")
        print(f"  RTM: {result['rtm_file']}")
        print()
        print("=" * 60)
        print("Pipeline completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print("Pipeline Failed")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
