"""Example demonstrating batch generation with progress tracking."""

import asyncio
from qa_agent.config.loader import AIConfig
from qa_agent.generators.manual_test_generator import ManualTestGenerator
from qa_agent.llm.client import LLMClient
from qa_agent.models.base import Requirement, RequirementType


def create_sample_requirements(count: int) -> list[Requirement]:
    """Create sample requirements for testing."""
    requirements = []
    
    features = [
        "User Login",
        "User Registration",
        "Password Reset",
        "Profile Management",
        "Data Export",
        "Search Functionality",
        "Notification System",
        "Payment Processing",
        "Report Generation",
        "Admin Dashboard",
    ]
    
    for i in range(count):
        feature = features[i % len(features)]
        requirements.append(
            Requirement(
                id=f"REQ-{i+1:03d}",
                type=RequirementType.FUNCTIONAL,
                content=f"""
                {feature} Feature:
                As a user, I want to {feature.lower()},
                so that I can manage my account effectively.
                
                Acceptance Criteria:
                - User can access the {feature.lower()} interface
                - System validates all inputs
                - Success confirmation is displayed
                - Errors are handled gracefully
                """,
                source="requirements.md",
            )
        )
    
    return requirements


async def example_parallel_generation():
    """Demonstrate parallel generation with progress tracking."""
    print("=" * 70)
    print("Example 1: Parallel Generation with Progress Tracking")
    print("=" * 70)
    
    # Create sample requirements
    requirements = create_sample_requirements(10)
    
    # Configure AI client
    ai_config = AIConfig(
        provider="openai",
        api_key="your-api-key-here",  # Replace with actual key
        model="gpt-4",
        temperature=0.7,
        max_tokens=2000,
    )
    
    # Create LLM client and generator with custom concurrency
    llm_client = LLMClient(ai_config)
    generator = ManualTestGenerator(llm_client, max_concurrent=3)
    
    # Progress tracking
    def progress_callback(completed, total, req_id):
        percentage = (completed / total) * 100
        print(f"Progress: {completed}/{total} ({percentage:.1f}%) - Completed {req_id}")
    
    print(f"\nGenerating tests for {len(requirements)} requirements...")
    print(f"Max concurrent requests: {generator.max_concurrent}\n")
    
    try:
        test_artifacts = await generator.generate(
            requirements=requirements,
            include_positive=True,
            include_negative=True,
            include_edge_cases=True,
            progress_callback=progress_callback,
        )
        
        print(f"\n✓ Successfully generated {len(test_artifacts)} test cases")
        print(f"  Average: {len(test_artifacts) / len(requirements):.1f} tests per requirement")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")


async def example_batch_generation():
    """Demonstrate batch generation for large requirement sets."""
    print("\n" + "=" * 70)
    print("Example 2: Batch Generation for Large Requirement Sets")
    print("=" * 70)
    
    # Create a larger set of requirements
    requirements = create_sample_requirements(25)
    
    # Configure AI client
    ai_config = AIConfig(
        provider="openai",
        api_key="your-api-key-here",  # Replace with actual key
        model="gpt-4",
        temperature=0.7,
        max_tokens=2000,
    )
    
    # Create LLM client and generator
    llm_client = LLMClient(ai_config)
    generator = ManualTestGenerator(llm_client, max_concurrent=5)
    
    # Batch progress tracking
    def batch_progress_callback(completed_batches, total_batches):
        percentage = (completed_batches / total_batches) * 100
        print(f"Batch Progress: {completed_batches}/{total_batches} ({percentage:.1f}%)")
    
    print(f"\nGenerating tests for {len(requirements)} requirements in batches...")
    print(f"Batch size: 5 requirements per batch\n")
    
    try:
        test_artifacts = await generator.generate_batch(
            requirements=requirements,
            batch_size=5,
            include_positive=True,
            include_negative=True,
            include_edge_cases=True,
            progress_callback=batch_progress_callback,
        )
        
        print(f"\n✓ Successfully generated {len(test_artifacts)} test cases")
        print(f"  Average: {len(test_artifacts) / len(requirements):.1f} tests per requirement")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")


async def example_partial_failure_handling():
    """Demonstrate graceful handling of partial failures."""
    print("\n" + "=" * 70)
    print("Example 3: Graceful Handling of Partial Failures")
    print("=" * 70)
    
    requirements = create_sample_requirements(5)
    
    # Configure AI client
    ai_config = AIConfig(
        provider="openai",
        api_key="your-api-key-here",  # Replace with actual key
        model="gpt-4",
        temperature=0.7,
        max_tokens=2000,
    )
    
    llm_client = LLMClient(ai_config)
    generator = ManualTestGenerator(llm_client, max_concurrent=2)
    
    # Track both successes and failures
    successes = []
    failures = []
    
    def progress_callback(completed, total, req_id):
        # In real scenario, you'd check if generation succeeded
        print(f"Processed {req_id} ({completed}/{total})")
    
    print(f"\nGenerating tests for {len(requirements)} requirements...")
    print("Note: System continues even if some requirements fail\n")
    
    try:
        test_artifacts = await generator.generate(
            requirements=requirements,
            include_positive=True,
            include_negative=False,
            include_edge_cases=False,
            progress_callback=progress_callback,
        )
        
        print(f"\n✓ Generated {len(test_artifacts)} test cases")
        print(f"  Success rate: {len(test_artifacts) / len(requirements) * 100:.1f}%")
        
    except Exception as e:
        print(f"\n✗ All requirements failed: {str(e)}")


async def example_custom_concurrency():
    """Demonstrate custom concurrency configuration."""
    print("\n" + "=" * 70)
    print("Example 4: Custom Concurrency Configuration")
    print("=" * 70)
    
    requirements = create_sample_requirements(8)
    
    # Configure AI client
    ai_config = AIConfig(
        provider="openai",
        api_key="your-api-key-here",  # Replace with actual key
        model="gpt-4",
        temperature=0.7,
        max_tokens=2000,
    )
    
    llm_client = LLMClient(ai_config)
    
    # Test different concurrency levels
    concurrency_levels = [1, 2, 4]
    
    for max_concurrent in concurrency_levels:
        print(f"\nTesting with max_concurrent={max_concurrent}...")
        
        generator = ManualTestGenerator(llm_client, max_concurrent=max_concurrent)
        
        try:
            import time
            start = time.time()
            
            test_artifacts = await generator.generate(
                requirements=requirements[:4],  # Use subset for demo
                include_positive=True,
                include_negative=False,
                include_edge_cases=False,
            )
            
            duration = time.time() - start
            
            print(f"  ✓ Generated {len(test_artifacts)} tests in {duration:.2f}s")
            print(f"    Throughput: {len(test_artifacts) / duration:.2f} tests/second")
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")


async def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Manual Test Generator - Batch Generation Examples")
    print("=" * 70)
    print("\nNote: These examples require a valid OpenAI API key.")
    print("Set OPENAI_API_KEY environment variable or update the code.\n")
    
    # Run examples
    await example_parallel_generation()
    await example_batch_generation()
    await example_partial_failure_handling()
    await example_custom_concurrency()
    
    print("\n" + "=" * 70)
    print("Examples Complete")
    print("=" * 70)


if __name__ == "__main__":
    # Run the async examples
    asyncio.run(main())
