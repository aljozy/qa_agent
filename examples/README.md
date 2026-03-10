# QA Agent Examples

This directory contains example files demonstrating how to use the QA Agent.

## Table of Contents

- [Example Files](#example-files)
- [Quick Start](#quick-start)
- [Example Workflows](#example-workflows)
- [Python API Examples](#python-api-examples)
- [Configuration Examples](#configuration-examples)

---

## Example Files

### Input Examples

#### `example_prd.md`
A complete Product Requirements Document for a User Authentication System.

**Contents**:
- 7 functional and non-functional requirements
- Detailed acceptance criteria
- API endpoint specifications
- Data models
- Testing requirements

**Use this to**:
- Learn how to structure requirements documents
- See what information the parser extracts
- Test the full pipeline

#### `sample_requirements.md`
A simpler requirements document for quick testing.

**Use this to**:
- Quick testing and experimentation
- Learning the basic Markdown format
- Running fast iterations

### Configuration Examples

#### `example_config.yaml`
Comprehensive configuration file with all available options and detailed comments.

**Features**:
- All configuration parameters documented
- Multiple example configurations for different use cases
- Environment variable usage examples
- Best practices and recommendations

**Use this to**:
- Understand all configuration options
- Create custom configurations
- Learn about different AI providers and models

### Output Examples

#### `example_output_requirements.json`
Example of parsed requirements in JSON format.

**Shows**:
- Structured requirement objects
- Extracted acceptance criteria
- Metadata and source information
- Requirement types and priorities

#### `example_output_tests.json`
Example of generated test cases in JSON format.

**Shows**:
- Manual test case structure
- Positive, negative, and edge case scenarios
- Test steps with expected results
- Test data and tags

#### `example_output_rtm.csv`
Example of a Requirement Traceability Matrix.

**Shows**:
- Requirement to test case mapping
- Coverage status and percentages
- Uncovered requirements

---

## Quick Start

### 1. Run the Full Pipeline

Process the example PRD through the complete workflow:

```bash
qa-agent run examples/example_prd.md --output output
```

This will:
1. Parse the requirements from `example_prd.md`
2. Generate test cases (positive, negative, edge cases)
3. Create an RTM with coverage metrics

**Output**:
- `output/requirements/example_prd.json` - Parsed requirements
- `output/tests/example_prd_tests.json` - Generated test cases
- `output/rtm/rtm.csv` - Requirement traceability matrix

### 2. Parse Requirements Only

```bash
qa-agent parse examples/example_prd.md --output output/requirements
```

### 3. Generate Test Cases

```bash
qa-agent generate output/requirements/example_prd.json \
  --output output/tests \
  --config config.kiro.yaml
```

### 4. Generate RTM

```bash
qa-agent rtm \
  output/requirements/example_prd.json \
  output/tests/example_prd_tests.json \
  --output output/rtm
```

---

## Example Workflows

### Workflow 1: Development Iteration

Fast iteration during development:

```bash
# Use fast model for quick feedback
qa-agent run examples/sample_requirements.md \
  --output dev_output \
  --config config.kiro.yaml
```

### Workflow 2: Production Quality

Generate high-quality test cases for production:

```bash
# Create custom config with quality model
cat > config_production.yaml << EOF
ai:
  provider: "kiro"
  model: "quality"
  temperature: 0.7
  max_tokens: 3000
output:
  directory: "production_output"
EOF

# Run with production config
qa-agent run examples/example_prd.md \
  --config config_production.yaml
```

### Workflow 3: Selective Test Generation

Generate only specific types of test scenarios:

```bash
# Parse requirements
qa-agent parse examples/example_prd.md --output output/requirements

# Generate only positive test cases
qa-agent generate output/requirements/example_prd.json \
  --output output/tests \
  --positive \
  --no-negative \
  --no-edge-cases
```

### Workflow 4: CI/CD Integration

Automated test generation in CI/CD:

```bash
# Run with JSON logging for CI/CD parsing
qa-agent parse examples/example_prd.md \
  --output output/requirements \
  --json-logs \
  --log-level INFO

# Check exit code
if [ $? -eq 0 ]; then
  echo "Parsing successful"
else
  echo "Parsing failed"
  exit 1
fi
```

---

## Python API Examples

### Example 1: Basic Usage

```python
import asyncio
from pathlib import Path
from qa_agent.config import Config
from qa_agent.parsers.markdown_parser import MarkdownParser
from qa_agent.generators.manual_test_generator import ManualTestGenerator
from qa_agent.llm.client import LLMClient

async def main():
    # Load configuration
    config = Config.from_yaml(Path("config.yaml"))
    
    # Parse requirements
    parser = MarkdownParser()
    requirements = parser.parse_file(Path("examples/example_prd.md"))
    print(f"Parsed {len(requirements)} requirements")
    
    # Generate test cases
    llm_client = LLMClient(config.ai)
    generator = ManualTestGenerator(llm_client)
    
    test_artifacts = await generator.generate(
        requirements=requirements,
        include_positive=True,
        include_negative=True,
        include_edge_cases=True
    )
    
    print(f"Generated {len(test_artifacts)} test cases")
    
    # Print summary
    for artifact in test_artifacts[:3]:  # First 3
        print(f"\n{artifact.id}: {artifact.title}")
        print(f"  Type: {artifact.scenario_type}")
        print(f"  Steps: {len(artifact.test_steps)}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Example 2: Custom Configuration

```python
from qa_agent.config import Config, AIConfig, OutputConfig

# Create custom configuration
config = Config(
    ai=AIConfig(
        provider="kiro",
        model="balanced",
        temperature=0.5,
        max_tokens=2000
    ),
    output=OutputConfig(
        directory="custom_output"
    )
)

# Ensure output directory exists
config.ensure_output_directory()

print(f"Using provider: {config.ai.provider}")
print(f"Output directory: {config.output.directory}")
```

### Example 3: Progress Tracking

```python
import asyncio
from qa_agent.generators.manual_test_generator import ManualTestGenerator
from qa_agent.llm.client import LLMClient
from qa_agent.config import Config

async def main():
    config = Config()
    llm_client = LLMClient(config.ai)
    generator = ManualTestGenerator(llm_client)
    
    # Define progress callback
    def progress_callback(completed: int, total: int, req_id: str):
        percentage = (completed / total) * 100
        print(f"Progress: {completed}/{total} ({percentage:.1f}%) - Last: {req_id}")
    
    # Generate with progress tracking
    test_artifacts = await generator.generate(
        requirements=requirements,
        progress_callback=progress_callback
    )
    
    print(f"\nCompleted! Generated {len(test_artifacts)} test cases")

asyncio.run(main())
```

### Example 4: RTM Generation

```python
from pathlib import Path
from qa_agent.analysis.rtm_generator import RTMGenerator

# Assume requirements and test_artifacts are loaded

# Generate RTM
rtm_generator = RTMGenerator()
rtm_entries = rtm_generator.generate(requirements, test_artifacts)

# Calculate coverage
coverage = rtm_generator.calculate_coverage_percentage(
    requirements, 
    test_artifacts
)

print(f"Overall Coverage: {coverage:.1f}%")

# Identify gaps
uncovered = rtm_generator.identify_uncovered_requirements(
    requirements, 
    test_artifacts
)

if uncovered:
    print(f"\nUncovered Requirements ({len(uncovered)}):")
    for req in uncovered:
        print(f"  - {req.id}: {req.title}")

# Export to CSV
rtm_generator.export_to_csv(rtm_entries, Path("output/rtm.csv"))
print("\nRTM exported to output/rtm.csv")
```

### Example 5: Error Handling

```python
from qa_agent.core.exceptions import (
    ConfigurationError,
    ParsingError,
    LLMError,
    StorageError
)

try:
    # Load configuration
    config = Config.from_yaml("config.yaml")
    
    # Parse requirements
    parser = MarkdownParser()
    requirements = parser.parse_file("requirements.md")
    
    # Generate tests
    llm_client = LLMClient(config.ai)
    generator = ManualTestGenerator(llm_client)
    test_artifacts = await generator.generate(requirements)
    
except ConfigurationError as e:
    print(f"Configuration error: {e.message}")
    if e.details:
        print(f"Details: {e.details}")
    
except ParsingError as e:
    print(f"Parsing error: {e.message}")
    print(f"Check your requirements document format")
    
except LLMError as e:
    print(f"LLM error: {e.message}")
    print(f"Provider: {e.provider}, Model: {e.model}")
    
except StorageError as e:
    print(f"Storage error: {e.message}")
    
except Exception as e:
    print(f"Unexpected error: {str(e)}")
```

---

## Configuration Examples

### Example 1: Kiro Fast (Development)

```yaml
ai:
  provider: "kiro"
  model: "fast"
  temperature: 0.5
  max_tokens: 1000

output:
  directory: "dev_output"
```

**Use case**: Quick iterations during development

### Example 2: Kiro Quality (Production)

```yaml
ai:
  provider: "kiro"
  model: "quality"
  temperature: 0.7
  max_tokens: 2000

output:
  directory: "output"
```

**Use case**: High-quality test generation for production

### Example 3: OpenAI GPT-4

```yaml
ai:
  provider: "openai"
  api_key: "${OPENAI_API_KEY}"
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 2000

output:
  directory: "output"
```

**Use case**: Maximum quality using OpenAI's GPT-4

### Example 4: Deterministic Output

```yaml
ai:
  provider: "kiro"
  model: "balanced"
  temperature: 0.0  # Completely deterministic
  max_tokens: 2000

output:
  directory: "test_output"
```

**Use case**: Reproducible outputs for testing

---

## Running the Examples

### Prerequisites

1. Install QA Agent:
```bash
pip install -e ".[dev]"
```

2. Create a configuration file:
```bash
cp config.kiro.yaml config.yaml
```

### Run Examples

```bash
# Example 1: Full pipeline with example PRD
qa-agent run examples/example_prd.md --output output

# Example 2: Parse only
qa-agent parse examples/sample_requirements.md --output output/requirements

# Example 3: Generate with custom config
qa-agent generate output/requirements/sample_requirements.json \
  --config examples/example_config.yaml \
  --output output/tests

# Example 4: Run Python examples
python examples/manual_test_generator_example.py
python examples/rtm_generator_example.py
python examples/workflow_orchestrator_example.py
```

---

## Viewing Output

### Requirements (JSON)

```bash
# Pretty print JSON
cat output/requirements/example_prd.json | python -m json.tool

# Count requirements
cat output/requirements/example_prd.json | python -c "import json, sys; print(len(json.load(sys.stdin)))"
```

### Test Cases (JSON)

```bash
# Pretty print
cat output/tests/example_prd_tests.json | python -m json.tool

# Count test cases
cat output/tests/example_prd_tests.json | python -c "import json, sys; print(len(json.load(sys.stdin)))"

# Filter by scenario type
cat output/tests/example_prd_tests.json | python -c "
import json, sys
tests = json.load(sys.stdin)
positive = [t for t in tests if t['scenario_type'] == 'positive']
print(f'Positive tests: {len(positive)}')
"
```

### RTM (CSV)

```bash
# View in terminal
cat output/rtm/rtm.csv

# View with column formatting
column -t -s, output/rtm/rtm.csv | less -S

# Open in spreadsheet application
open output/rtm/rtm.csv  # macOS
xdg-open output/rtm/rtm.csv  # Linux
```

---

## Next Steps

1. **Explore the Documentation**:
   - [README](../README.md) - Main documentation
   - [API Reference](../docs/api_reference.md) - API documentation
   - [Configuration Guide](../docs/configuration.md) - Configuration options
   - [CLI Usage](../docs/cli_usage.md) - CLI commands

2. **Try Your Own Requirements**:
   - Create a Markdown requirements document
   - Run it through the pipeline
   - Review the generated test cases

3. **Customize Configuration**:
   - Experiment with different models
   - Adjust temperature and max_tokens
   - Try different AI providers

4. **Integrate into Your Workflow**:
   - Add to CI/CD pipeline
   - Create custom scripts
   - Build on the Python API

---

## Troubleshooting

### Issue: No test cases generated

**Solution**: Check that your requirements have acceptance criteria:

```markdown
## REQ-001: Feature Name

Description here.

**Acceptance Criteria**:
- Criterion 1
- Criterion 2
```

### Issue: Configuration not found

**Solution**: Specify the full path:

```bash
qa-agent run examples/example_prd.md --config /full/path/to/config.yaml
```

### Issue: API key error (OpenAI)

**Solution**: Set environment variable:

```bash
export OPENAI_API_KEY="sk-..."
qa-agent run examples/example_prd.md --provider openai
```

---

## Contributing Examples

Have a useful example? Contributions are welcome!

1. Create your example file
2. Add documentation to this README
3. Test the example
4. Submit a pull request

---

## See Also

- [Main README](../README.md)
- [API Reference](../docs/api_reference.md)
- [CLI Usage Guide](../docs/cli_usage.md)
- [Configuration Guide](../docs/configuration.md)
