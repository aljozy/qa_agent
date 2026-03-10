# Jira User Story Parser

The Jira Parser is a component of the AI-Powered QA Agent that parses Jira-style user stories and extracts structured requirements for test generation.

## Features

- **Story Parsing**: Extracts title, user story (role, goal, benefit), and acceptance criteria
- **Multiple Formats**: Supports various bullet styles (-, *, •) and numbered lists (1., 2., etc.)
- **Validation**: Validates story format before parsing with descriptive error messages
- **Testable Items**: Each acceptance criterion is extracted as a separate testable requirement
- **Metadata**: Generates requirement IDs and tracks relationships between stories and criteria

## Supported Format

The parser expects user stories in the following format:

```
Title: <story title>

As a <role>, I want [to] <goal> [so that <benefit>]

Acceptance Criteria:
- <criterion 1>
- <criterion 2>
...
```

### Format Variations

The parser is flexible and supports:

- **Optional "to"**: "I want to log in" or "I want log in"
- **Optional benefit**: The "so that" clause is optional
- **Case insensitive**: Keywords like "Title:", "As a", "Acceptance Criteria:" are case-insensitive
- **Alternative headers**: "AC:" instead of "Acceptance Criteria:"
- **Multiple bullet styles**: 
  - Dashes: `- criterion`
  - Asterisks: `* criterion`
  - Bullets: `• criterion`
  - Numbers: `1. criterion`, `2. criterion`

## Usage

### Basic Usage

```python
from qa_agent.parsers.jira_parser import JiraParser

# Create parser instance
parser = JiraParser()

# Parse from string
story = """Title: User Login

As a user, I want to log in to the system so that I can access my account

Acceptance Criteria:
- Valid credentials should be accepted
- Invalid credentials should be rejected
- Account locked after 3 failed attempts
"""

requirements = parser.parse(story)

# First requirement is the main story
main_story = requirements[0]
print(f"Story ID: {main_story.id}")
print(f"Title: {main_story.metadata['title']}")
print(f"Role: {main_story.metadata['role']}")
print(f"Goal: {main_story.metadata['goal']}")

# Remaining requirements are acceptance criteria
for ac in requirements[1:]:
    print(f"AC {ac.metadata['criterion_number']}: {ac.content}")
```

### Parse from File

```python
from pathlib import Path

# Parse from file
story_file = Path("user_stories/login.jira")
requirements = parser.parse(story_file)
```

### Validation

```python
# Validate before parsing
result = parser.validate(story)

if result.is_valid:
    requirements = parser.parse(story)
else:
    print("Validation errors:")
    for error in result.errors:
        print(f"  - {error}")
```

### Using with Parser Registry

```python
from qa_agent.parsers.base import register_parser, get_global_registry

# Register the parser
register_parser(JiraParser)

# Get registry
registry = get_global_registry()

# Get parser by name
parser = registry.get_parser("jira")

# Get parser for file extension
parser = registry.get_parser_for_file(Path("story.jira"))
```

## Output Structure

The parser returns a list of `Requirement` objects:

### Main Story Requirement

```python
Requirement(
    id="STORY-USER-LOGIN",
    type=RequirementType.USER_STORY,
    content="<full story text>",
    metadata={
        "title": "User Login",
        "user_story": {...},
        "role": "user",
        "goal": "log in to the system",
        "benefit": "I can access my account",
        "acceptance_criteria_count": 3
    },
    source="<file path or 'string_input'>"
)
```

### Acceptance Criterion Requirement

```python
Requirement(
    id="STORY-USER-LOGIN-AC1",
    type=RequirementType.USER_STORY,
    content="Valid credentials should be accepted",
    metadata={
        "parent_story_id": "STORY-USER-LOGIN",
        "criterion_number": 1,
        "is_acceptance_criterion": True
    },
    source="<file path or 'string_input'>"
)
```

## Validation Rules

The parser validates the following:

1. **Title**: Must have a "Title:" field
2. **User Story**: Must have "As a <role>, I want <goal>" format
3. **Acceptance Criteria**: Must have "Acceptance Criteria:" section with at least one item
4. **Non-empty**: Content cannot be empty

### Validation Errors

Common validation errors:

- `"Story content is empty"`
- `"Missing required 'Title:' field"`
- `"Missing or malformed user story. Expected format: 'As a <role>, I want <goal> [so that <benefit>]'"`
- `"Missing 'Acceptance Criteria:' section"`
- `"Acceptance Criteria section is empty or has no valid items"`

### Validation Warnings

- `"Only one acceptance criterion found. Consider adding more."`

## Examples

### Example 1: Complete Story

```
Title: Password Reset

As a user, I want to reset my password so that I can regain access to my account

Acceptance Criteria:
1. User should receive reset email
2. Reset link should expire after 24 hours
3. New password must meet complexity requirements
```

**Output**: 4 requirements (1 story + 3 acceptance criteria)

### Example 2: Story Without Benefit

```
Title: View Dashboard

As a user, I want to view my dashboard

Acceptance Criteria:
- Dashboard displays recent activity
- Dashboard shows account summary
```

**Output**: 3 requirements (1 story + 2 acceptance criteria)

### Example 3: Alternative Format

```
title: User Profile Update

as a user, i want to update my profile

AC:
* Update name and email
* Upload profile picture
* Save changes
```

**Output**: 4 requirements (1 story + 3 acceptance criteria)

## File Extensions

The parser supports the following file extensions:

- `.jira`
- `.txt`
- `.story`

## Requirements Mapping

The Jira parser implements the following requirements from the specification:

- **Requirement 1.1**: Extract story title, description, and acceptance criteria
- **Requirement 1.2**: Parse each criterion as a separate testable item
- **Requirement 1.3**: Return descriptive error messages for malformed stories

## Testing

The parser includes comprehensive unit tests covering:

- Valid story parsing
- Multiple format variations
- Malformed story handling
- Validation logic
- File parsing
- Integration with parser registry

Run tests with:

```bash
pytest tests/test_jira_parser.py -v
```

## See Also

- [Parser Plugin Architecture](parser_plugin_architecture.md)
- [Base Parser Interface](../qa_agent/parsers/base.py)
- [Example Stories](../examples/jira_stories/)
- [Demo Script](../examples/jira_parser_demo.py)
