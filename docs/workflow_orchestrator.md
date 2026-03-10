# Workflow Orchestrator

The `WorkflowOrchestrator` coordinates the end-to-end pipeline for the QA Agent, managing the flow from requirement parsing to RTM generation.

## Overview

The orchestrator provides a high-level interface for executing the complete QA Agent workflow:

1. **Parse** requirements from markdown
2. **Store** requirements to JSON
3. **Generate** test cases using AI
4. **Generate** RTM mapping requirements to tests

## Features

- **End-to-end pipeline execution** with a single method call
- **Progress tracking** with customizable callbacks
- **Error handling** with descriptive error messages
- **Graceful degradation** when components fail
- **Lazy initialization** of expensive resources (LLM client)
- **Structured logging** throughout the pipeline

## Usage

### Basic Usage

```python
import asyncio
from pathlib import Path
from qa_agent.config import Config
from qa_agent.core import WorkflowOrchestrator

async def main():
    # Load configuration
    config = Config.from_yaml("config.yaml")
    
    # Create orchestrator
    orchestrator = WorkflowOrchestrator(config)
    
    # Run full pipeline
    result = await orchestrator.run_full_pipeline(
        input_file=Path("requirements.md"),
        include_positive=True,
        include_negative=True,
        include_edge_cases=True,
    )
    
    print(f"Generated {len(result['test_artifacts'])} test cases")
    print(f"Coverage: {result['coverage_percentage']:.1f}%")

asyncio.run(main())
```

### With Progress Tracking

```python
def progress_callback(stage: str, completed: int, total: int):
    """Custom progress callback."""
    percentage = (completed / total) * 100
    print(f"[{stage}] {completed}/{total} ({percentage:.0f}%)")

result = await orchestrator.run_full_pipeline(
    input_file=Path("requirements.md"),
    progress_callback=progress_callback,
)
```

### Individual Steps

You can also execute individual steps of the pipeline:

```python
# Step 1: Parse requirements
requirements = await orchestrator.parse_requirements(
    Path("requirements.md")
)

# Step 2: Store requirements
req_file = await orchestrator.store_requirements(
    requirements, "my_requirements"
)

# Step 3: Generate tests
test_artifacts = await orchestrator.generate_tests(
    requirements,
    include_positive=True,
    include_negative=True,
    include_edge_cases=True,
)

# Step 4: Store test artifacts
tests_file = await orchestrator.store_test_artifacts(
    test_artifacts, "my_tests"
)

# Step 5: Generate RTM
rtm_entries, coverage = await orchestrator.generate_rtm(
    requirements, test_artifacts
)

# Step 6: Store RTM
rtm_file = await orchestrator.store_rtm(rtm_entries)
```

## API Reference

### WorkflowOrchestrator

#### Constructor

```python
WorkflowOrchestrator(config: Config)
```

**Parameters:**
- `config`: Configuration object containing AI provider settings and output paths

#### Methods

##### run_full_pipeline

```python
async def run_full_pipeline(
    input_file: Path,
    include_positive: bool = True,
    include_negative: bool = True,
    include_edge_cases: bool = True,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
) -> dict
```

Execute the complete pipeline from parsing to RTM generation.

**Parameters:**
- `input_file`: Path to the markdown requirements file
- `include_positive`: Whether to generate positive test scenarios (default: True)
- `include_negative`: Whether to generate negative test scenarios (default: True)
- `include_edge_cases`: Whether to generate edge case scenarios (default: True)
- `progress_callback`: Optional callback function(stage, completed, total)

**Returns:**
Dictionary containing:
- `requirements`: List of parsed requirements
- `test_artifacts`: List of generated test artifacts
- `rtm_entries`: List of RTM entries
- `coverage_percentage`: Coverage percentage
- `requirements_file`: Path to saved requirements file
- `tests_file`: Path to saved test artifacts file
- `rtm_file`: Path to saved RTM file

**Raises:**
- `WorkflowError`: If any step in the pipeline fails

##### parse_requirements

```python
async def parse_requirements(input_file: Path) -> List[Requirement]
```

Parse requirements from a markdown file.

**Parameters:**
- `input_file`: Path to the markdown file

**Returns:**
- List of parsed requirements

**Raises:**
- `WorkflowError`: If parsing fails

##### store_requirements

```python
async def store_requirements(
    requirements: List[Requirement],
    filename: str
) -> Path
```

Store requirements to JSON file.

**Parameters:**
- `requirements`: List of requirements to store
- `filename`: Base filename (without extension)

**Returns:**
- Path to the saved file

**Raises:**
- `WorkflowError`: If storage fails

##### generate_tests

```python
async def generate_tests(
    requirements: List[Requirement],
    include_positive: bool = True,
    include_negative: bool = True,
    include_edge_cases: bool = True,
) -> List[TestArtifact]
```

Generate test cases from requirements.

**Parameters:**
- `requirements`: List of requirements to generate tests for
- `include_positive`: Whether to generate positive scenarios
- `include_negative`: Whether to generate negative scenarios
- `include_edge_cases`: Whether to generate edge case scenarios

**Returns:**
- List of generated test artifacts

**Raises:**
- `WorkflowError`: If test generation fails

##### store_test_artifacts

```python
async def store_test_artifacts(
    test_artifacts: List[TestArtifact],
    filename: str
) -> Path
```

Store test artifacts to JSON file.

**Parameters:**
- `test_artifacts`: List of test artifacts to store
- `filename`: Base filename (without extension)

**Returns:**
- Path to the saved file

**Raises:**
- `WorkflowError`: If storage fails

##### generate_rtm

```python
async def generate_rtm(
    requirements: List[Requirement],
    test_artifacts: List[TestArtifact]
) -> tuple[List[RTMEntry], float]
```

Generate Requirement Traceability Matrix.

**Parameters:**
- `requirements`: List of requirements
- `test_artifacts`: List of test artifacts

**Returns:**
- Tuple of (RTM entries, coverage percentage)

**Raises:**
- `WorkflowError`: If RTM generation fails

##### store_rtm

```python
async def store_rtm(rtm_entries: List[RTMEntry]) -> Path
```

Store RTM to CSV file.

**Parameters:**
- `rtm_entries`: List of RTM entries to store

**Returns:**
- Path to the saved file

**Raises:**
- `WorkflowError`: If storage fails

## Error Handling

The orchestrator provides comprehensive error handling:

### WorkflowError

All workflow-related errors are wrapped in `WorkflowError` exceptions with descriptive messages.

```python
from qa_agent.core import WorkflowError

try:
    result = await orchestrator.run_full_pipeline(input_file)
except WorkflowError as e:
    print(f"Pipeline failed: {str(e)}")
    # Handle error appropriately
```

### Graceful Degradation

The orchestrator handles errors gracefully:
- Validates input files before processing
- Checks for empty results at each step
- Provides detailed error messages
- Logs all operations for debugging

## Logging

The orchestrator uses Python's logging module:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Run orchestrator (will log progress)
result = await orchestrator.run_full_pipeline(input_file)
```

Log levels:
- `DEBUG`: Detailed operation information
- `INFO`: High-level progress updates
- `WARNING`: Non-critical issues
- `ERROR`: Critical failures

## Integration with CLI

The CLI uses the orchestrator internally for the `run` command:

```bash
qa-agent run requirements.md
```

This executes:
```python
orchestrator = WorkflowOrchestrator(config)
result = await orchestrator.run_full_pipeline(input_file)
```

## Best Practices

1. **Use progress callbacks** for long-running operations
2. **Configure logging** to track pipeline execution
3. **Handle WorkflowError** exceptions appropriately
4. **Validate configuration** before creating orchestrator
5. **Use individual methods** when you need fine-grained control
6. **Use run_full_pipeline** for simple end-to-end execution

## Example: Custom Pipeline

```python
async def custom_pipeline():
    """Custom pipeline with additional processing."""
    config = Config()
    orchestrator = WorkflowOrchestrator(config)
    
    # Parse requirements
    requirements = await orchestrator.parse_requirements(
        Path("requirements.md")
    )
    
    # Filter requirements (custom logic)
    filtered_reqs = [
        req for req in requirements
        if "critical" in req.content.lower()
    ]
    
    # Generate tests only for critical requirements
    test_artifacts = await orchestrator.generate_tests(
        filtered_reqs,
        include_positive=True,
        include_negative=True,
        include_edge_cases=False,  # Skip edge cases
    )
    
    # Generate RTM
    rtm_entries, coverage = await orchestrator.generate_rtm(
        filtered_reqs, test_artifacts
    )
    
    print(f"Critical requirements coverage: {coverage:.1f}%")
```

## Troubleshooting

### "No requirements found in the document"

**Cause:** The markdown file doesn't contain parseable requirements.

**Solution:** Ensure your markdown has proper structure:
```markdown
# Requirements

## Feature 1
- Requirement 1
- Requirement 2
```

### "No test cases were generated"

**Cause:** AI provider failed or returned empty results.

**Solution:**
- Check AI provider configuration
- Verify API key is valid
- Check network connectivity
- Review logs for detailed error messages

### "Pipeline execution failed"

**Cause:** One of the pipeline steps failed.

**Solution:**
- Check the error message for specific step that failed
- Review logs for detailed information
- Verify all configuration is correct
- Ensure output directories are writable

## See Also

- [CLI Usage Guide](cli_usage.md)
- [Configuration Guide](configuration.md)
- [Manual Test Generator](manual_test_generator.md)
- [RTM Generator](rtm_generator.md)
