"""Example demonstrating the ManualTestGenerator usage."""

import asyncio
from qa_agent.config.loader import AIConfig
from qa_agent.generators.manual_test_generator import ManualTestGenerator
from qa_agent.llm.client import LLMClient
from qa_agent.models.base import Requirement, RequirementType


async def main():
    """Demonstrate manual test generation."""
    
    # Create a sample requirement
    requirement = Requirement(
        id="REQ-001",
        type=RequirementType.FUNCTIONAL,
        content="""
        User Login Feature:
        As a user, I want to log in to the system with my username and password,
        so that I can access my personalized dashboard.
        
        Acceptance Criteria:
        - User can enter username and password
        - System validates credentials against database
        - Valid credentials redirect to dashboard
        - Invalid credentials show error message
        - Account locks after 3 failed attempts
        """,
        source="requirements.md",
    )
    
    # Configure AI client (using OpenAI as example)
    # Note: In production, set OPENAI_API_KEY environment variable
    ai_config = AIConfig(
        provider="openai",
        api_key="your-api-key-here",  # Replace with actual key or use env var
        model="gpt-4",
        temperature=0.7,
        max_tokens=2000,
    )
    
    # Create LLM client and generator
    llm_client = LLMClient(ai_config)
    generator = ManualTestGenerator(llm_client)
    
    # Generate test cases
    print("Generating manual test cases...")
    print(f"Requirement: {requirement.id}")
    print(f"Content: {requirement.content[:100]}...")
    print()
    
    try:
        # Generate all types of test cases
        test_artifacts = await generator.generate(
            requirements=[requirement],
            include_positive=True,
            include_negative=True,
            include_edge_cases=True,
        )
        
        print(f"Generated {len(test_artifacts)} test cases:\n")
        
        # Display generated test cases
        for i, artifact in enumerate(test_artifacts, 1):
            print(f"{'='*70}")
            print(f"Test Case {i}")
            print(f"Type: {artifact.type.value}")
            print(f"Scenario: {artifact.metadata.get('scenario_type', 'unknown')}")
            print(f"Requirement Link: {artifact.requirement_ids}")
            print(f"{'='*70}")
            print(artifact.content)
            print()
            
    except Exception as e:
        print(f"Error generating tests: {str(e)}")
        print("\nNote: This example requires a valid OpenAI API key.")
        print("Set it in the code or use environment variable OPENAI_API_KEY")


if __name__ == "__main__":
    # Run the async example
    asyncio.run(main())
