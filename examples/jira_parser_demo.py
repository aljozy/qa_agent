"""Demo script showing how to use the Jira parser."""

from pathlib import Path
from qa_agent.parsers.jira_parser import JiraParser
from qa_agent.parsers.base import register_parser, get_global_registry

def main():
    """Demonstrate Jira parser usage."""
    
    # Create parser instance
    parser = JiraParser()
    
    print("=" * 70)
    print("Jira Parser Demo")
    print("=" * 70)
    print()
    
    # Example 1: Parse from string
    print("Example 1: Parsing from string")
    print("-" * 70)
    
    story_text = """Title: User Registration

As a new user, I want to register for an account so that I can use the system

Acceptance Criteria:
- Email address should be validated
- Password must meet security requirements
- Confirmation email should be sent
"""
    
    requirements = parser.parse(story_text)
    print(f"Parsed {len(requirements)} requirements:")
    print()
    
    for req in requirements:
        print(f"  ID: {req.id}")
        print(f"  Type: {req.type}")
        print(f"  Content: {req.content[:60]}...")
        if req.metadata.get("is_acceptance_criterion"):
            print(f"  Parent Story: {req.metadata['parent_story_id']}")
        print()
    
    # Example 2: Parse from file
    print("\nExample 2: Parsing from file")
    print("-" * 70)
    
    story_file = Path("examples/jira_stories/user_login.jira")
    if story_file.exists():
        requirements = parser.parse(story_file)
        
        main_story = requirements[0]
        print(f"Story: {main_story.metadata['title']}")
        print(f"Role: {main_story.metadata['role']}")
        print(f"Goal: {main_story.metadata['goal']}")
        print(f"Benefit: {main_story.metadata['benefit']}")
        print(f"\nAcceptance Criteria ({len(requirements) - 1}):")
        
        for idx, req in enumerate(requirements[1:], 1):
            print(f"  {idx}. {req.content}")
    else:
        print(f"File not found: {story_file}")
    
    # Example 3: Validation
    print("\n\nExample 3: Validation")
    print("-" * 70)
    
    valid_story = """Title: Valid Story

As a user, I want something

Acceptance Criteria:
- Criterion 1
"""
    
    invalid_story = """Title: Invalid Story

Missing user story format

Acceptance Criteria:
- Criterion 1
"""
    
    result = parser.validate(valid_story)
    print(f"Valid story validation: {result.is_valid}")
    
    result = parser.validate(invalid_story)
    print(f"Invalid story validation: {result.is_valid}")
    if result.errors:
        print(f"Errors: {result.errors}")
    
    # Example 4: Using with registry
    print("\n\nExample 4: Using with parser registry")
    print("-" * 70)
    
    # Register parser
    register_parser(JiraParser)
    
    # Get registry
    registry = get_global_registry()
    
    # Get parser by name
    jira_parser = registry.get_parser("jira")
    print(f"Retrieved parser: {jira_parser.name}")
    
    # Get parser for file
    test_file = Path("story.jira")
    parser_for_file = registry.get_parser_for_file(test_file)
    if parser_for_file:
        print(f"Parser for .jira files: {parser_for_file.name}")
    
    # List all parsers
    print(f"\nRegistered parsers: {[p['name'] for p in registry.list_parsers()]}")
    
    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
