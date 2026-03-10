# CLI Usage Guide

The QA Agent provides a command-line interface for parsing requirements, generating test cases, and creating requirement traceability matrices.

## Installation

```bash
pip install -e .
```

After installation, the `qa-agent` command will be available globally.

## Commands

### 1. Parse Requirements

Parse markdown requirements and save to JSON format.

```bash
qa-agent parse <input_file> [OPTIONS]
```

**Arguments:**
- `input_file`: Path to the markdown requirements file (required)

**Options:**
- `--output, -o`: Output directory for parsed requirements (default: `output/requirements`)
- `--config, -c`: Path to configuration file (optional)

**Example:**
```bash
qa-agent parse examples/sample_requirements.md
qa-agent parse requirements.md --output ./parsed
```

**Output:**
- Creates a JSON file with structured requirements
- File is named after the input file (e.g., `sample_requirements.json`)

---

### 2. Generate Test Cases

Generate manual test cases from parsed requirements using AI.

```bash
qa-agent generate <requirements_file> [OPTIONS]
```

**Arguments:**
- `requirements_file`: Path to the requirements JSON file (required)

**Options:**
- `--output, -o`: Output directory for generated test cases (default: `output/tests`)
- `--config, -c`: Path to configuration file (optional)
- `--provider, -p`: Override AI provider (`kiro` or `openai`)
- `--positive/--no-positive`: Generate positive test scenarios (default: enabled)
- `--negative/--no-negative`: Generate negative test scenarios (default: enabled)
- `--edge-cases/--no-edge-cases`: Generate edge case scenarios (default: enabled)

**Example:**
```bash
# Using default config (Kiro)
qa-agent generate output/requirements/sample_requirements.json

# Using OpenAI
qa-agent generate output/requirements/sample_requirements.json --provider openai

# Generate only positive tests
qa-agent generate output/requirements/sample_requirements.json --no-negative --no-edge-cases

# With custom config
qa-agent generate output/requirements/sample_requirements.json --config config.yaml
```

**Output:**
- Creates a JSON file with generated test cases
- File is named `<requirements_file>_tests.json`
- Displays progress during generation

---

### 3. Generate RTM

Generate a Requirement Traceability Matrix mapping requirements to test cases.

```bash
qa-agent rtm <requirements_file> <tests_file> [OPTIONS]
```

**Arguments:**
- `requirements_file`: Path to the requirements JSON file (required)
- `tests_file`: Path to the test artifacts JSON file (required)

**Options:**
- `--output, -o`: Output directory for RTM (default: `output/rtm`)
- `--config, -c`: Path to configuration file (optional)

**Example:**
```bash
qa-agent rtm \
  output/requirements/sample_requirements.json \
  output/tests/sample_requirements_tests.json

qa-agent rtm \
  output/requirements/sample_requirements.json \
  output/tests/sample_requirements_tests.json \
  --output ./rtm_reports
```

**Output:**
- Creates `rtm.csv` with requirement-to-test mapping
- Displays coverage percentage
- Lists uncovered requirements

---

### 4. Run Full Pipeline

Execute the complete workflow: parse → generate → rtm.

```bash
qa-agent run <input_file> [OPTIONS]
```

**Arguments:**
- `input_file`: Path to the markdown requirements file (required)

**Options:**
- `--output, -o`: Base output directory for all artifacts (default: `output`)
- `--config, -c`: Path to configuration file (optional)
- `--provider, -p`: Override AI provider (`kiro` or `openai`)

**Example:**
```bash
# Using default config
qa-agent run examples/sample_requirements.md

# Using OpenAI with custom output directory
qa-agent run examples/sample_requirements.md --provider openai --output ./results

# With custom config
qa-agent run examples/sample_requirements.md --config config.yaml
```

**Output:**
- `output/requirements/`: Parsed requirements JSON
- `output/tests/`: Generated test cases JSON
- `output/rtm/`: RTM CSV file
- Displays progress for each step
- Shows final summary with coverage metrics

---

## Configuration

### Configuration File

Create a YAML configuration file to customize AI provider settings:

**config.yaml:**
```yaml
ai:
  provider: "kiro"  # or "openai"
  model: "auto"     # For Kiro: auto, fast, balanced, quality
                    # For OpenAI: gpt-4, gpt-3.5-turbo, etc.
  temperature: 0.7
  max_tokens: 2000
  api_key: "${OPENAI_API_KEY}"  # Environment variable substitution

output:
  directory: "output"
```

### Default Configuration

If no config file is specified, the CLI will:
1. Look for `config.kiro.yaml` in the current directory
2. Fall back to default settings (Kiro provider with auto model)

### Environment Variables

You can use environment variable substitution in config files:

```yaml
ai:
  api_key: "${OPENAI_API_KEY}"
```

Set the environment variable:
```bash
export OPENAI_API_KEY="sk-your-api-key"
```

---

## Exit Codes

- `0`: Success
- `1`: Error (with error message displayed)

---

## Examples

### Basic Workflow

```bash
# Step 1: Parse requirements
qa-agent parse requirements.md

# Step 2: Generate test cases
qa-agent generate output/requirements/requirements.json --provider openai

# Step 3: Generate RTM
qa-agent rtm \
  output/requirements/requirements.json \
  output/tests/requirements_tests.json
```

### One-Command Pipeline

```bash
# Run everything at once
qa-agent run requirements.md --provider openai
```

### Custom Configuration

```bash
# Create config file
cat > my_config.yaml << EOF
ai:
  provider: "openai"
  model: "gpt-4"
  temperature: 0.8
  max_tokens: 3000
  api_key: "\${OPENAI_API_KEY}"
output:
  directory: "custom_output"
EOF

# Use custom config
qa-agent run requirements.md --config my_config.yaml
```

### Selective Test Generation

```bash
# Generate only positive tests
qa-agent generate output/requirements/requirements.json \
  --no-negative \
  --no-edge-cases

# Generate only negative and edge case tests
qa-agent generate output/requirements/requirements.json \
  --no-positive
```

---

## Troubleshooting

### "OpenAI provider requires an API key"

**Solution:** Set your OpenAI API key:
```bash
export OPENAI_API_KEY="sk-your-api-key"
```

Or provide it in the config file:
```yaml
ai:
  provider: "openai"
  api_key: "sk-your-api-key"
```

### "Configuration file not found"

**Solution:** Ensure the config file path is correct:
```bash
qa-agent run requirements.md --config ./config.yaml
```

### "No requirements found in the document"

**Solution:** Ensure your markdown file has proper structure with headings and content:
```markdown
# Requirements

## Feature 1

- Requirement 1
- Requirement 2
```

### Rate Limiting

If you encounter rate limiting with OpenAI:
- The CLI automatically retries with exponential backoff
- Consider reducing the number of requirements
- Use a higher tier API key with increased rate limits

---

## Tips

1. **Use the run command** for quick end-to-end execution
2. **Use individual commands** when you need more control or want to regenerate specific artifacts
3. **Save your config** in `config.kiro.yaml` to avoid specifying it every time
4. **Check the output directory** after each command to verify results
5. **Use --help** on any command to see detailed options

---

## Getting Help

```bash
# General help
qa-agent --help

# Command-specific help
qa-agent parse --help
qa-agent generate --help
qa-agent rtm --help
qa-agent run --help

# Show version
qa-agent --version
```
