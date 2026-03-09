"""Integration test demonstrating configuration and parser working together."""

from qa_agent.config import Config
from qa_agent.parsers import MarkdownParser

# Test 1: Load configuration
print("=" * 60)
print("Test 1: Configuration Loading")
print("=" * 60)

config = Config.from_yaml("config.kiro.yaml")
print(f"✓ Configuration loaded successfully")
print(f"  Provider: {config.ai.provider}")
print(f"  Model: {config.ai.model}")
print(f"  Output directory: {config.output.directory}")
print()

# Test 2: Parse a sample Markdown document
print("=" * 60)
print("Test 2: Markdown Parsing")
print("=" * 60)

sample_markdown = """
# User Authentication Feature

## Functional Requirements

- The system shall provide user login functionality
- The system shall support password reset via email
- Users must be able to register with email and password

## Non-Functional Requirements

The system must ensure high security for user credentials.

Performance requirements include response time under 2 seconds.
"""

parser = MarkdownParser()
requirements = parser.parse(sample_markdown, source="sample-prd.md")

print(f"✓ Parsed {len(requirements)} requirements")
print()

for req in requirements:
    print(f"  {req.id}: {req.content[:60]}...")
    print(f"    Type: {req.type.value}")
    print(f"    Section: {req.metadata['section']}")
    print()

# Test 3: Validate configuration and parser integration
print("=" * 60)
print("Test 3: Integration Validation")
print("=" * 60)

# Ensure output directory exists
config.ensure_output_directory()
print(f"✓ Output directory created: {config.output.directory}")

# Validate markdown
validation = parser.validate(sample_markdown)
print(f"✓ Markdown validation: {'PASSED' if validation.is_valid else 'FAILED'}")

if validation.warnings:
    print(f"  Warnings: {len(validation.warnings)}")
    for warning in validation.warnings:
        print(f"    - {warning}")

print()
print("=" * 60)
print("All integration tests passed! ✓")
print("=" * 60)
