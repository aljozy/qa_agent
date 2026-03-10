# RTM Generator Documentation

## Overview

The RTM (Requirement Traceability Matrix) Generator creates a comprehensive mapping between requirements and test cases, helping teams track test coverage and identify gaps in their testing strategy.

## Features

- **Requirement-to-Test Mapping**: Creates a matrix linking each requirement to its associated test cases
- **Coverage Analysis**: Identifies requirements with no test coverage
- **Coverage Percentage Calculation**: Computes overall test coverage metrics
- **CSV Export**: Exports RTM to CSV format for easy sharing and reporting
- **Coverage Status Classification**: Categorizes requirements as "Covered", "Partial", or "Not Covered"

## Usage

### Basic Usage

```python
from qa_agent.analysis.rtm_generator import RTMGenerator
from qa_agent.models.base import Requirement, TestArtifact

# Initialize the generator
rtm_generator = RTMGenerator()

# Generate RTM entries
rtm_entries = rtm_generator.generate(requirements, test_artifacts)

# Export to CSV
from pathlib import Path
output_path = Path("output/rtm.csv")
rtm_generator.export_to_csv(rtm_entries, output_path)
```

### Identifying Uncovered Requirements

```python
# Find requirements with no test coverage
uncovered = rtm_generator.identify_uncovered_requirements(
    requirements, 
    test_artifacts
)

print(f"Found {len(uncovered)} uncovered requirements:")
for req in uncovered:
    print(f"  - {req.id}: {req.content}")
```

### Calculating Coverage Percentage

```python
# Calculate overall coverage percentage
coverage = rtm_generator.calculate_coverage_percentage(
    requirements,
    test_artifacts
)

print(f"Overall test coverage: {coverage:.1f}%")
```

## RTM Entry Structure

Each RTM entry contains:

- **Requirement ID**: Unique identifier for the requirement
- **Requirement Description**: Brief description extracted from requirement content
- **Test IDs**: List of test case IDs that cover this requirement
- **Coverage Status**: One of:
  - `"Covered"`: 2 or more test cases
  - `"Partial"`: Exactly 1 test case
  - `"Not Covered"`: No test cases

## Coverage Status Logic

The RTM generator uses the following logic to determine coverage status:

| Test Cases | Status |
|-----------|--------|
| 0 | Not Covered |
| 1 | Partial |
| 2+ | Covered |

This encourages comprehensive testing with multiple test scenarios (positive, negative, edge cases) per requirement.

## CSV Export Format

The exported CSV file contains the following columns:

| Column | Description |
|--------|-------------|
| Requirement ID | Unique identifier for the requirement |
| Requirement Description | First line or first 100 characters of requirement content |
| Test IDs | Comma-separated list of test case IDs (or "None" if no coverage) |
| Coverage Status | Coverage status (Covered, Partial, Not Covered) |

### Example CSV Output

```csv
Requirement ID,Requirement Description,Test IDs,Coverage Status
REQ-001,User shall be able to log in with valid credentials,"TC001, TC002, TC003",Covered
REQ-002,System shall validate email format,"TC004, TC005",Covered
REQ-003,User shall be able to reset password,TC006,Partial
REQ-004,System shall lock account after failed attempts,None,Not Covered
```

## API Reference

### RTMGenerator

#### `generate(requirements, test_artifacts) -> List[RTMEntry]`

Generate RTM entries mapping requirements to test cases.

**Parameters:**
- `requirements` (List[Requirement]): List of requirements to trace
- `test_artifacts` (List[TestArtifact]): List of test artifacts

**Returns:**
- List[RTMEntry]: List of RTM entries

**Example:**
```python
rtm_entries = rtm_generator.generate(requirements, test_artifacts)
```

#### `identify_uncovered_requirements(requirements, test_artifacts) -> List[Requirement]`

Identify requirements with no associated test cases.

**Parameters:**
- `requirements` (List[Requirement]): List of requirements to check
- `test_artifacts` (List[TestArtifact]): List of test artifacts

**Returns:**
- List[Requirement]: List of uncovered requirements

**Example:**
```python
uncovered = rtm_generator.identify_uncovered_requirements(
    requirements, 
    test_artifacts
)
```

#### `calculate_coverage_percentage(requirements, test_artifacts) -> float`

Calculate overall coverage percentage.

**Parameters:**
- `requirements` (List[Requirement]): List of requirements
- `test_artifacts` (List[TestArtifact]): List of test artifacts

**Returns:**
- float: Coverage percentage (0.0 to 100.0)

**Example:**
```python
coverage = rtm_generator.calculate_coverage_percentage(
    requirements,
    test_artifacts
)
print(f"Coverage: {coverage:.1f}%")
```

#### `export_to_csv(rtm_entries, output_path) -> None`

Export RTM to CSV format.

**Parameters:**
- `rtm_entries` (List[RTMEntry]): List of RTM entries to export
- `output_path` (Path): Path to output CSV file

**Raises:**
- IOError: If file cannot be written

**Example:**
```python
from pathlib import Path
output_path = Path("output/rtm.csv")
rtm_generator.export_to_csv(rtm_entries, output_path)
```

### RTMEntry

#### Attributes

- `requirement_id` (str): Unique identifier for the requirement
- `requirement_description` (str): Description of the requirement
- `test_ids` (List[str]): List of test artifact IDs
- `coverage_status` (str): Coverage status

#### `to_dict() -> Dict[str, str]`

Convert entry to dictionary format suitable for CSV export.

**Returns:**
- Dict[str, str]: Dictionary with keys: "Requirement ID", "Requirement Description", "Test IDs", "Coverage Status"

## Complete Example

See `examples/rtm_generator_example.py` for a complete working example:

```bash
# Run the example
python examples/rtm_generator_example.py
```

This example demonstrates:
- Creating sample requirements and test artifacts
- Generating RTM entries
- Identifying uncovered requirements
- Calculating coverage percentage
- Exporting to CSV
- Displaying coverage summary

## Integration with Test Generators

The RTM generator works seamlessly with test generators like `ManualTestGenerator`:

```python
from qa_agent.generators.manual_test_generator import ManualTestGenerator
from qa_agent.analysis.rtm_generator import RTMGenerator
from qa_agent.llm.client import LLMClient

# Generate test cases
llm_client = LLMClient(provider="openai", api_key="your-key")
test_generator = ManualTestGenerator(llm_client)
test_artifacts = await test_generator.generate(requirements)

# Generate RTM
rtm_generator = RTMGenerator()
rtm_entries = rtm_generator.generate(requirements, test_artifacts)

# Export results
rtm_generator.export_to_csv(rtm_entries, Path("output/rtm.csv"))
```

## Best Practices

1. **Regular RTM Generation**: Generate RTM after each test generation cycle to track coverage progress
2. **Address Gaps Early**: Prioritize generating tests for uncovered requirements
3. **Aim for "Covered" Status**: Ensure each requirement has multiple test scenarios (positive, negative, edge cases)
4. **Version Control**: Commit RTM CSV files to version control to track coverage over time
5. **CI/CD Integration**: Include RTM generation in CI/CD pipelines to enforce coverage thresholds

## Troubleshooting

### Empty RTM Entries

**Problem**: RTM entries show no test coverage even though tests exist.

**Solution**: Ensure test artifacts have `requirement_ids` populated correctly:

```python
test_artifact = TestArtifact(
    type=TestType.MANUAL,
    content="Test content",
    requirement_ids=["REQ-001"],  # Must match requirement IDs
    metadata={"test_id": "TC001"}
)
```

### Missing Test IDs in CSV

**Problem**: CSV shows artifact IDs instead of test IDs.

**Solution**: Include `test_id` in test artifact metadata:

```python
test_artifact = TestArtifact(
    type=TestType.MANUAL,
    content="Test content",
    requirement_ids=["REQ-001"],
    metadata={"test_id": "TC001"}  # Add this
)
```

### Truncated Descriptions

**Problem**: Requirement descriptions are truncated in RTM.

**Solution**: This is by design to keep CSV readable. Descriptions are limited to 100 characters. For full content, refer to the original requirement objects.

## Requirements Traceability

The RTM generator satisfies the following requirements from the specification:

- **Requirement 7.1**: Create matrix mapping requirements to test cases
- **Requirement 7.2**: Identify requirements with no associated test cases
- **Requirement 7.3**: Calculate coverage percentage for each requirement category
- **Requirement 7.4**: Export RTM in CSV format
- **Requirement 7.5**: Include requirement ID, description, test case IDs, and coverage status
