# Parser Plugin Architecture

## Overview

The QA Agent implements a flexible plugin architecture for requirement parsers. This design allows new parsers to be added without modifying the core system, supporting the modular architecture requirements (15.1, 15.2, 15.4, 15.5).

## Architecture Components

### 1. RequirementParser (Abstract Base Class)

The `RequirementParser` class defines the interface that all parsers must implement:

```python
from qa_agent.parsers import RequirementParser

class MyParser(RequirementParser):
    # Parser metadata
    name = "my_parser"
    supported_extensions = [".ext"]
    description = "My custom parser"
    
    def parse(self, input_data: str | Path) -> List[Requirement]:
        """Parse input and return requirements."""
        pass
    
    def validate(self, input_data: str | Path) -> ValidationResult:
        """Validate input before parsing."""
        pass
```

**Key Features:**
- Abstract methods enforce consistent interface
- Metadata properties for parser discovery
- Support for both string content and file paths
- Built-in file extension checking

### 2. ParserRegistry

The `ParserRegistry` manages parser plugins and provides discovery capabilities:

```python
from qa_agent.parsers import ParserRegistry

registry = ParserRegistry()

# Register a parser
registry.register(MyParser)

# Get parser by name
parser = registry.get_parser("my_parser")

# Get parser for a file
parser = registry.get_parser_for_file(Path("requirements.ext"))

# List all parsers
parsers = registry.list_parsers()

# Get supported extensions
extensions = registry.get_supported_extensions()
```

**Key Features:**
- Dynamic parser registration
- Extension-based parser lookup
- Parser metadata queries
- Global registry singleton available

### 3. ParserFactory

The `ParserFactory` provides high-level parser creation and selection:

```python
from qa_agent.parsers import ParserFactory

factory = ParserFactory()

# Create parser by name
parser = factory.create_parser("markdown")

# Create parser for file
parser = factory.create_parser_for_file("requirements.md")

# Check if file is supported
if factory.supports_file("spec.txt"):
    parser = factory.create_parser_for_file("spec.txt")
```

**Key Features:**
- Simplified parser creation
- File extension-based selection
- Support checking
- Uses global registry by default

### 4. Configuration-Based Selection

Parsers can be selected via configuration:

```python
from qa_agent.parsers import create_parser_from_config

config = {
    "parser": "markdown",
    "options": {
        "preserve_hierarchy": True
    }
}

parser = create_parser_from_config(config)
```

**Configuration Format:**
```yaml
parser: markdown
options:
  preserve_hierarchy: true
  extract_metadata: true
```

### 5. Auto-Detection

The system can automatically detect the appropriate parser:

```python
from qa_agent.parsers import auto_detect_parser

# From file path
parser = auto_detect_parser(Path("requirements.md"))

# From content (uses heuristics)
parser = auto_detect_parser("# Requirements\n\nSome content")
```

## Creating a Custom Parser

### Step 1: Define the Parser Class

```python
from pathlib import Path
from typing import List
from qa_agent.parsers import RequirementParser
from qa_agent.models.base import Requirement, RequirementType, ValidationResult

class JSONParser(RequirementParser):
    """Parser for JSON requirement files."""
    
    name = "json"
    supported_extensions = [".json"]
    description = "JSON requirements parser"
    
    def parse(self, input_data: str | Path) -> List[Requirement]:
        """Parse JSON requirements."""
        import json
        
        # Handle file or string input
        if isinstance(input_data, Path):
            with open(input_data, "r") as f:
                data = json.load(f)
        else:
            data = json.loads(input_data)
        
        requirements = []
        for item in data.get("requirements", []):
            req = Requirement(
                id=item["id"],
                type=RequirementType[item["type"]],
                content=item["content"],
                source="json",
                metadata=item.get("metadata", {})
            )
            requirements.append(req)
        
        return requirements
    
    def validate(self, input_data: str | Path) -> ValidationResult:
        """Validate JSON format."""
        import json
        
        try:
            if isinstance(input_data, Path):
                if not input_data.exists():
                    return ValidationResult(
                        is_valid=False,
                        errors=[f"File not found: {input_data}"]
                    )
                with open(input_data, "r") as f:
                    json.load(f)
            else:
                json.loads(input_data)
            
            return ValidationResult(is_valid=True)
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Invalid JSON: {str(e)}"]
            )
```

### Step 2: Register the Parser

```python
from qa_agent.parsers import register_parser

# Register in global registry
register_parser(JSONParser)
```

Or use a custom registry:

```python
from qa_agent.parsers import ParserRegistry

registry = ParserRegistry()
registry.register(JSONParser)
```

### Step 3: Use the Parser

```python
from qa_agent.parsers import ParserFactory

factory = ParserFactory()

# Automatic selection by file extension
parser = factory.create_parser_for_file("requirements.json")
requirements = parser.parse("requirements.json")

# Or explicit selection
parser = factory.create_parser("json")
requirements = parser.parse('{"requirements": [...]}')
```

## Built-in Parsers

### MarkdownParser

Parses Markdown requirement documents.

**Supported Extensions:** `.md`, `.markdown`

**Features:**
- Extracts requirements from headings, bullets, and paragraphs
- Preserves document hierarchy
- Classifies functional vs non-functional requirements
- Skips code blocks

**Example:**
```python
from qa_agent.parsers import ParserFactory

factory = ParserFactory()
parser = factory.create_parser("markdown")

requirements = parser.parse("""
# User Authentication

- User shall be able to login
- System shall validate credentials
- Application shall display error messages
""")
```

## Best Practices

### 1. Parser Naming

- Use lowercase with underscores: `my_parser`
- Be descriptive: `openapi_parser` not `api`
- Avoid conflicts with existing parsers

### 2. Extension Handling

- Include the dot: `.json` not `json`
- Support common variations: `[".yaml", ".yml"]`
- Use lowercase for consistency

### 3. Error Handling

- Validate input before parsing
- Provide descriptive error messages
- Use appropriate exception types
- Return ValidationResult with details

### 4. File vs String Input

- Always support both Path and string input
- Check file existence for Path input
- Handle encoding properly (UTF-8)

### 5. Metadata

- Store useful parsing context in metadata
- Include source information
- Add parser-specific details

## Testing Custom Parsers

```python
import pytest
from pathlib import Path
from qa_agent.parsers import ParserRegistry

def test_custom_parser():
    """Test custom parser registration and usage."""
    registry = ParserRegistry()
    registry.register(MyParser)
    
    # Test registration
    assert registry.is_registered("my_parser")
    
    # Test parser retrieval
    parser = registry.get_parser("my_parser")
    assert parser.name == "my_parser"
    
    # Test file extension mapping
    parser = registry.get_parser_for_file(Path("test.ext"))
    assert isinstance(parser, MyParser)
    
    # Test parsing
    requirements = parser.parse("test content")
    assert len(requirements) > 0
    
    # Test validation
    result = parser.validate("test content")
    assert result.is_valid
```

## Integration with Configuration

Parsers can be configured via YAML:

```yaml
# config.yaml
parsers:
  markdown:
    enabled: true
    preserve_hierarchy: true
  
  json:
    enabled: true
    validate_schema: true
  
  custom:
    enabled: false
```

Load and use:

```python
from qa_agent.parsers import create_parser_from_config

config = load_config("config.yaml")
parser_config = config["parsers"]["markdown"]

if parser_config.get("enabled", True):
    parser = create_parser_from_config({
        "parser": "markdown",
        "options": parser_config
    })
```

## Advanced Features

### Custom Validation Logic

```python
def validate(self, input_data: str | Path) -> ValidationResult:
    """Custom validation with warnings."""
    errors = []
    warnings = []
    
    # Check for required fields
    if "requirement" not in content:
        errors.append("Missing 'requirement' field")
    
    # Check for optional fields
    if "priority" not in content:
        warnings.append("No priority specified")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        metadata={"checked_fields": ["requirement", "priority"]}
    )
```

### Parser Options

```python
class ConfigurableParser(RequirementParser):
    """Parser with configurable options."""
    
    def __init__(self, strict_mode=False, max_requirements=None):
        self.strict_mode = strict_mode
        self.max_requirements = max_requirements
    
    def parse(self, input_data: str | Path) -> List[Requirement]:
        requirements = self._do_parse(input_data)
        
        if self.max_requirements and len(requirements) > self.max_requirements:
            if self.strict_mode:
                raise ValueError(f"Too many requirements: {len(requirements)}")
            else:
                requirements = requirements[:self.max_requirements]
        
        return requirements
```

### Chaining Parsers

```python
def parse_multi_format(file_path: Path) -> List[Requirement]:
    """Parse file using multiple parsers."""
    factory = ParserFactory()
    
    # Try primary parser
    try:
        parser = factory.create_parser_for_file(file_path)
        return parser.parse(file_path)
    except Exception as e:
        # Fallback to alternative parser
        fallback_parser = factory.create_parser("generic")
        return fallback_parser.parse(file_path)
```

## See Also

- [Requirements Document](../requirements.md) - Requirements 15.1, 15.2, 15.4, 15.5
- [Design Document](../design.md) - Section 3.1 Requirement Parser
- [Parser Plugin Demo](../examples/parser_plugin_demo.py) - Working examples
- [API Reference](api-reference.md) - Complete API documentation
