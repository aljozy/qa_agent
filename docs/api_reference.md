# API Reference

This document provides comprehensive API documentation for the QA Agent's public classes and methods.

## Table of Contents

- [Configuration](#configuration)
- [Parsers](#parsers)
- [Generators](#generators)
- [Analysis](#analysis)
- [Storage](#storage)
- [LLM Client](#llm-client)
- [Models](#models)
- [Exceptions](#exceptions)

---

## Configuration

### Config

The main configuration class for QA Agent.

**Module**: `qa_agent.config`

#### Class Definition

```python
from qa_agent.config import Config

config = Config()
```

#### Methods

##### `Config.from_yaml(file_path: Path) -> Config`

Load configuration from a YAML file.

**Parameters**:
- `file_path` (Path): Path to the YAML configuration file

**Returns**:
- `Config`: Configuration object

**Raises**:
- `ConfigurationError`: If the file is invalid or cannot be read

**Example**:
```python
from pathlib import Path
from qa_agent.config import Config

config = Config.from_yaml(Path("config.yaml"))
print(f"Provider: {config.ai.provider}")
print(f"Model: {config.ai.model}")
```

##### `ensure_output_directory() -> None`

Create the output directory if it doesn't exist.

**Example**:
```python
config = Config()
config.output.directory = "custom_output"
config.ensure_output_directory()
```

#### Attributes

##### `ai: AIConfig`

AI model configuration.

**Properties**:
- `provider` (str): AI provider ("kiro" or "openai")
- `model` (str): Model name
- `temperature` (float): Temperature for generation (0.0-2.0)
- `max_tokens` (int): Maximum tokens per generation
- `api_key` (Optional[str]): API key (for OpenAI)

##### `output: OutputConfig`

Output configuration.

**Properties**:
- `directory` (str): Base output directory path

---

## Parsers

### BaseParser

Abstract base class for all requirement parsers.

**Module**: `qa_agent.parsers.base`

#### Class Definition

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from qa_agent.models.base import Requirement

class BaseParser(ABC):
    @abstractmethod
    def parse_file(self, file_path: Path) -> List[Requirement]:
        """Parse a file and return a list of requirements."""
        pass
```

### MarkdownParser

Parser for Markdown requirement documents.

**Module**: `qa_agent.parsers.markdown_parser`

#### Class Definition

```python
from qa_agent.parsers.markdown_parser import MarkdownParser

parser = MarkdownParser()
```

#### Methods

##### `parse_file(file_path: Path) -> List[Requirement]`

Parse a Markdown file and extract structured requirements.

**Parameters**:
- `file_path` (Path): Path to the Markdown file

**Returns**:
- `List[Requirement]`: List of parsed requirement objects

**Raises**:
- `ParsingError`: If the file cannot be parsed or is invalid

**Example**:
```python
from pathlib import Path
from qa_agent.parsers.markdown_parser import MarkdownParser

parser = MarkdownParser()
requirements = parser.parse_file(Path("requirements.md"))

for req in requirements:
    print(f"{req.id}: {req.title}")
    print(f"  Type: {req.type}")
    print(f"  Criteria: {len(req.acceptance_criteria)}")
```

##### `parse_text(text: str) -> List[Requirement]`

Parse Markdown text and extract structured requirements.

**Parameters**:
- `text` (str): Markdown text content

**Returns**:
- `List[Requirement]`: List of parsed requirement objects

**Example**:
```python
markdown_text = """
# Requirements

## REQ-001: User Login

Users must be able to log in.

**Acceptance Criteria**:
- Valid credentials accepted
- Invalid credentials rejected
"""

parser = MarkdownParser()
requirements = parser.parse_text(markdown_text)
```

---

## Generators

### ManualTestGenerator

Generator for manual test cases using AI.

**Module**: `qa_agent.generators.manual_test_generator`

#### Class Definition

```python
from qa_agent.generators.manual_test_generator import ManualTestGenerator
from qa_agent.llm.client import LLMClient
from qa_agent.config import Config

config = Config()
llm_client = LLMClient(config.ai)
generator = ManualTestGenerator(llm_client)
```

#### Methods

##### `async generate(requirements: List[Requirement], include_positive: bool = True, include_negative: bool = True, include_edge_cases: bool = True, progress_callback: Optional[Callable] = None) -> List[TestArtifact]`

Generate manual test cases from requirements.

**Parameters**:
- `requirements` (List[Requirement]): List of requirements to generate tests for
- `include_positive` (bool): Generate positive test scenarios (default: True)
- `include_negative` (bool): Generate negative test scenarios (default: True)
- `include_edge_cases` (bool): Generate edge case scenarios (default: True)
- `progress_callback` (Optional[Callable]): Callback function for progress updates

**Returns**:
- `List[TestArtifact]`: List of generated test artifacts

**Raises**:
- `LLMError`: If AI generation fails

**Example**:
```python
import asyncio
from qa_agent.generators.manual_test_generator import ManualTestGenerator
from qa_agent.llm.client import LLMClient
from qa_agent.config import Config

async def generate_tests():
    config = Config.from_yaml("config.yaml")
    llm_client = LLMClient(config.ai)
    generator = ManualTestGenerator(llm_client)
    
    # Assume requirements are already loaded
    test_artifacts = await generator.generate(
        requirements=requirements,
        include_positive=True,
        include_negative=True,
        include_edge_cases=True
    )
    
    print(f"Generated {len(test_artifacts)} test cases")
    return test_artifacts

# Run async function
test_artifacts = asyncio.run(generate_tests())
```

##### `async generate_for_requirement(requirement: Requirement, include_positive: bool = True, include_negative: bool = True, include_edge_cases: bool = True) -> List[TestArtifact]`

Generate test cases for a single requirement.

**Parameters**:
- `requirement` (Requirement): Requirement to generate tests for
- `include_positive` (bool): Generate positive scenarios
- `include_negative` (bool): Generate negative scenarios
- `include_edge_cases` (bool): Generate edge case scenarios

**Returns**:
- `List[TestArtifact]`: List of generated test artifacts

**Example**:
```python
import asyncio

async def generate_single():
    # Assume requirement is already loaded
    test_artifacts = await generator.generate_for_requirement(
        requirement=requirement,
        include_positive=True,
        include_negative=False,
        include_edge_cases=False
    )
    return test_artifacts

test_artifacts = asyncio.run(generate_single())
```

---

## Analysis

### RTMGenerator

Generator for Requirement Traceability Matrix.

**Module**: `qa_agent.analysis.rtm_generator`

#### Class Definition

```python
from qa_agent.analysis.rtm_generator import RTMGenerator

rtm_generator = RTMGenerator()
```

#### Methods

##### `generate(requirements: List[Requirement], test_artifacts: List[TestArtifact]) -> List[RTMEntry]`

Generate RTM entries mapping requirements to test cases.

**Parameters**:
- `requirements` (List[Requirement]): List of requirements
- `test_artifacts` (List[TestArtifact]): List of test artifacts

**Returns**:
- `List[RTMEntry]`: List of RTM entries

**Example**:
```python
from qa_agent.analysis.rtm_generator import RTMGenerator

rtm_generator = RTMGenerator()
rtm_entries = rtm_generator.generate(requirements, test_artifacts)

for entry in rtm_entries:
    print(f"{entry.requirement_id}: {entry.test_count} tests")
```

##### `calculate_coverage_percentage(requirements: List[Requirement], test_artifacts: List[TestArtifact]) -> float`

Calculate overall test coverage percentage.

**Parameters**:
- `requirements` (List[Requirement]): List of requirements
- `test_artifacts` (List[TestArtifact]): List of test artifacts

**Returns**:
- `float`: Coverage percentage (0.0 to 100.0)

**Example**:
```python
coverage = rtm_generator.calculate_coverage_percentage(
    requirements, 
    test_artifacts
)
print(f"Coverage: {coverage:.1f}%")
```

##### `identify_uncovered_requirements(requirements: List[Requirement], test_artifacts: List[TestArtifact]) -> List[Requirement]`

Identify requirements with no test coverage.

**Parameters**:
- `requirements` (List[Requirement]): List of requirements
- `test_artifacts` (List[TestArtifact]): List of test artifacts

**Returns**:
- `List[Requirement]`: List of uncovered requirements

**Example**:
```python
uncovered = rtm_generator.identify_uncovered_requirements(
    requirements, 
    test_artifacts
)

if uncovered:
    print(f"Warning: {len(uncovered)} requirements have no coverage:")
    for req in uncovered:
        print(f"  - {req.id}: {req.title}")
```

##### `export_to_csv(rtm_entries: List[RTMEntry], output_path: Path) -> None`

Export RTM to CSV format.

**Parameters**:
- `rtm_entries` (List[RTMEntry]): List of RTM entries
- `output_path` (Path): Path to output CSV file

**Example**:
```python
from pathlib import Path

rtm_generator.export_to_csv(
    rtm_entries, 
    Path("output/rtm.csv")
)
```

---

## Storage

### FileStorage

File-based storage for requirements and test artifacts.

**Module**: `qa_agent.storage.file_storage`

#### Class Definition

```python
from pathlib import Path
from qa_agent.storage.file_storage import FileStorage

storage = FileStorage(Path("output"))
```

#### Methods

##### `save(requirements: List[Requirement], filename: str) -> Path`

Save requirements to a JSON file.

**Parameters**:
- `requirements` (List[Requirement]): List of requirements to save
- `filename` (str): Base filename (without extension)

**Returns**:
- `Path`: Path to the saved file

**Raises**:
- `StorageError`: If saving fails

**Example**:
```python
from pathlib import Path
from qa_agent.storage.file_storage import FileStorage

storage = FileStorage(Path("output/requirements"))
output_path = storage.save(requirements, "my_requirements")
print(f"Saved to: {output_path}")
```

##### `load(filename: str) -> List[Requirement]`

Load requirements from a JSON file.

**Parameters**:
- `filename` (str): Filename (with or without .json extension)

**Returns**:
- `List[Requirement]`: List of loaded requirements

**Raises**:
- `StorageError`: If loading fails

**Example**:
```python
storage = FileStorage(Path("output/requirements"))
requirements = storage.load("my_requirements.json")
print(f"Loaded {len(requirements)} requirements")
```

---

## LLM Client

### LLMClient

Client for interacting with AI language models.

**Module**: `qa_agent.llm.client`

#### Class Definition

```python
from qa_agent.llm.client import LLMClient
from qa_agent.config import AIConfig

ai_config = AIConfig(
    provider="kiro",
    model="auto",
    temperature=0.7,
    max_tokens=2000
)
client = LLMClient(ai_config)
```

#### Methods

##### `async generate(prompt: str, system_prompt: Optional[str] = None) -> str`

Generate text using the configured AI model.

**Parameters**:
- `prompt` (str): User prompt
- `system_prompt` (Optional[str]): System prompt for context

**Returns**:
- `str`: Generated text

**Raises**:
- `LLMError`: If generation fails

**Example**:
```python
import asyncio
from qa_agent.llm.client import LLMClient
from qa_agent.config import Config

async def generate_text():
    config = Config()
    client = LLMClient(config.ai)
    
    response = await client.generate(
        prompt="Generate a test case for user login",
        system_prompt="You are a QA engineer creating test cases"
    )
    
    return response

result = asyncio.run(generate_text())
print(result)
```

---

## Models

### Requirement

Data model for a requirement.

**Module**: `qa_agent.models.base`

#### Class Definition

```python
from qa_agent.models.base import Requirement

requirement = Requirement(
    id="REQ-001",
    title="User Login",
    description="Users must be able to log in",
    type="functional",
    priority="high",
    source="requirements.md",
    acceptance_criteria=["Valid credentials accepted"],
    metadata={}
)
```

#### Attributes

- `id` (str): Unique requirement identifier
- `title` (str): Requirement title
- `description` (str): Detailed description
- `type` (str): Requirement type ("functional", "non-functional")
- `priority` (str): Priority level ("low", "medium", "high", "critical")
- `source` (str): Source document
- `acceptance_criteria` (List[str]): List of acceptance criteria
- `metadata` (Dict[str, Any]): Additional metadata

### TestArtifact

Data model for a test artifact.

**Module**: `qa_agent.models.base`

#### Class Definition

```python
from qa_agent.models.base import TestArtifact, TestStep

test_artifact = TestArtifact(
    id="TC-001",
    requirement_id="REQ-001",
    title="Test User Login",
    description="Verify user can log in",
    type="manual",
    scenario_type="positive",
    priority="high",
    preconditions=["User is registered"],
    test_steps=[
        TestStep(
            step_number=1,
            action="Enter credentials",
            expected_result="Credentials accepted"
        )
    ],
    expected_results=["User is logged in"],
    test_data={},
    tags=["login", "authentication"]
)
```

#### Attributes

- `id` (str): Unique test case identifier
- `requirement_id` (str): Associated requirement ID
- `title` (str): Test case title
- `description` (str): Test case description
- `type` (str): Test type ("manual", "automation")
- `scenario_type` (str): Scenario type ("positive", "negative", "edge_case")
- `priority` (str): Priority level
- `preconditions` (List[str]): Test preconditions
- `test_steps` (List[TestStep]): List of test steps
- `expected_results` (List[str]): Expected outcomes
- `test_data` (Dict[str, Any]): Test data
- `tags` (List[str]): Test tags

### TestStep

Data model for a test step.

**Module**: `qa_agent.models.base`

#### Attributes

- `step_number` (int): Step sequence number
- `action` (str): Action to perform
- `expected_result` (str): Expected result of the action

### RTMEntry

Data model for an RTM entry.

**Module**: `qa_agent.models.base`

#### Attributes

- `requirement_id` (str): Requirement identifier
- `requirement_title` (str): Requirement title
- `requirement_type` (str): Requirement type
- `priority` (str): Priority level
- `test_case_ids` (List[str]): Associated test case IDs
- `test_count` (int): Number of test cases
- `coverage_status` (str): Coverage status ("Covered", "Not Covered", "Partial")
- `coverage_percentage` (str): Coverage percentage string

---

## Exceptions

### ConfigurationError

Raised when configuration is invalid or cannot be loaded.

**Module**: `qa_agent.core.exceptions`

**Attributes**:
- `message` (str): Error message
- `details` (Optional[str]): Additional details

**Example**:
```python
from qa_agent.core.exceptions import ConfigurationError

try:
    config = Config.from_yaml("invalid.yaml")
except ConfigurationError as e:
    print(f"Configuration error: {e.message}")
    if e.details:
        print(f"Details: {e.details}")
```

### ParsingError

Raised when requirement parsing fails.

**Module**: `qa_agent.core.exceptions`

**Attributes**:
- `message` (str): Error message
- `details` (Optional[str]): Additional details

**Example**:
```python
from qa_agent.core.exceptions import ParsingError

try:
    requirements = parser.parse_file("invalid.md")
except ParsingError as e:
    print(f"Parsing error: {e.message}")
```

### LLMError

Raised when LLM generation fails.

**Module**: `qa_agent.core.exceptions`

**Attributes**:
- `message` (str): Error message
- `provider` (str): AI provider name
- `model` (str): Model name

**Example**:
```python
from qa_agent.core.exceptions import LLMError

try:
    response = await client.generate(prompt)
except LLMError as e:
    print(f"LLM error: {e.message}")
    print(f"Provider: {e.provider}, Model: {e.model}")
```

### StorageError

Raised when file storage operations fail.

**Module**: `qa_agent.core.exceptions`

**Attributes**:
- `message` (str): Error message
- `details` (Optional[str]): Additional details

**Example**:
```python
from qa_agent.core.exceptions import StorageError

try:
    storage.save(requirements, "output")
except StorageError as e:
    print(f"Storage error: {e.message}")
```

---

## Complete Example

Here's a complete example showing how to use the API:

```python
import asyncio
from pathlib import Path
from qa_agent.config import Config
from qa_agent.parsers.markdown_parser import MarkdownParser
from qa_agent.generators.manual_test_generator import ManualTestGenerator
from qa_agent.analysis.rtm_generator import RTMGenerator
from qa_agent.llm.client import LLMClient
from qa_agent.storage.file_storage import FileStorage

async def main():
    # 1. Load configuration
    config = Config.from_yaml(Path("config.yaml"))
    print(f"Using provider: {config.ai.provider}")
    
    # 2. Parse requirements
    parser = MarkdownParser()
    requirements = parser.parse_file(Path("requirements.md"))
    print(f"Parsed {len(requirements)} requirements")
    
    # 3. Save parsed requirements
    req_storage = FileStorage(Path("output/requirements"))
    req_storage.save(requirements, "requirements")
    
    # 4. Generate test cases
    llm_client = LLMClient(config.ai)
    generator = ManualTestGenerator(llm_client)
    
    test_artifacts = await generator.generate(
        requirements=requirements,
        include_positive=True,
        include_negative=True,
        include_edge_cases=True
    )
    print(f"Generated {len(test_artifacts)} test cases")
    
    # 5. Generate RTM
    rtm_generator = RTMGenerator()
    rtm_entries = rtm_generator.generate(requirements, test_artifacts)
    coverage = rtm_generator.calculate_coverage_percentage(
        requirements, 
        test_artifacts
    )
    
    print(f"Coverage: {coverage:.1f}%")
    
    # 6. Export RTM
    rtm_generator.export_to_csv(
        rtm_entries, 
        Path("output/rtm/rtm.csv")
    )
    
    print("Pipeline complete!")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## See Also

- [CLI Usage Guide](cli_usage.md)
- [Configuration Guide](configuration.md)
- [Parser Plugin Architecture](parser_plugin_architecture.md)
- [Workflow Orchestrator](workflow_orchestrator.md)
