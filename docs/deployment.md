# Deployment Guide

This guide covers deployment and distribution of the AI-Powered QA Agent.

## Quick Start

### Verify Distribution Readiness

```bash
python3 scripts/verify_distribution.py
```

This checks:
- ✅ All required files exist
- ✅ Version consistency across files
- ✅ PyProject metadata completeness
- ✅ Example files present
- ✅ Documentation present
- ✅ Tests present

### Build Distribution

```bash
bash scripts/build_distribution.sh
```

This script:
1. Verifies distribution readiness
2. Cleans previous builds
3. Runs tests
4. Checks code quality
5. Builds source and wheel distributions
6. Validates distributions with twine

### Manual Build

If you prefer manual control:

```bash
# Clean previous builds
rm -rf build/ dist/ *.egg-info

# Build distributions
python3 -m build

# Check distributions
python3 -m twine check dist/*
```

## Distribution Files

After building, you'll have:

```
dist/
├── qa-agent-0.1.0.tar.gz          # Source distribution
└── qa_agent-0.1.0-py3-none-any.whl # Wheel distribution
```

### Source Distribution (`.tar.gz`)

Contains:
- All Python source code
- README, LICENSE, CHANGELOG
- Example files
- Documentation
- Configuration examples

### Wheel Distribution (`.whl`)

Contains:
- Compiled Python bytecode
- Package metadata
- Faster installation than source

## Installation Methods

### From PyPI (Production)

```bash
pip install qa-agent
```

### From TestPyPI (Testing)

```bash
pip install --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    qa-agent
```

### From Local Wheel

```bash
pip install dist/qa_agent-0.1.0-py3-none-any.whl
```

### From Local Source

```bash
pip install dist/qa-agent-0.1.0.tar.gz
```

### From Git Repository

```bash
pip install git+https://github.com/qa-agent/qa-agent.git
```

### Development Installation

```bash
pip install -e ".[dev]"
```

## Publishing

### To TestPyPI (Recommended First)

```bash
python3 -m twine upload --repository testpypi dist/*
```

### To PyPI (Production)

```bash
python3 -m twine upload dist/*
```

## Version Management

### Current Version

Check current version:

```bash
qa-agent --version
```

Or in Python:

```python
from qa_agent import __version__
print(__version__)  # 0.1.0
```

### Update Version

1. Update `qa_agent/__init__.py`:
   ```python
   __version__ = "0.2.0"
   ```

2. Update `pyproject.toml`:
   ```toml
   version = "0.2.0"
   ```

3. Update `CHANGELOG.md` with release notes

4. Commit and tag:
   ```bash
   git add qa_agent/__init__.py pyproject.toml CHANGELOG.md
   git commit -m "Bump version to 0.2.0"
   git tag -a v0.2.0 -m "Release version 0.2.0"
   git push origin main
   git push origin v0.2.0
   ```

## Configuration Files

### pyproject.toml

Main project configuration:
- Package metadata (name, version, description)
- Dependencies
- Optional dependencies (dev tools)
- CLI entry points
- Tool configurations (black, ruff, mypy, pytest)

### requirements.txt

Production dependencies with version constraints:
- Used for pip installations
- Includes all runtime dependencies
- Version pinning for reproducibility

### MANIFEST.in

Controls which files are included in distributions:
- Documentation files
- Example files
- Configuration templates
- Excludes build artifacts and caches

## Deployment Artifacts

### Core Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Package metadata and configuration |
| `requirements.txt` | Production dependencies |
| `MANIFEST.in` | Distribution file inclusion rules |
| `LICENSE` | MIT license text |
| `README.md` | Package documentation |
| `CHANGELOG.md` | Version history and release notes |

### Scripts

| Script | Purpose |
|--------|---------|
| `scripts/verify_distribution.py` | Verify distribution readiness |
| `scripts/build_distribution.sh` | Automated build process |

### Documentation

| File | Purpose |
|------|---------|
| `DISTRIBUTION.md` | Detailed distribution guide |
| `docs/deployment.md` | This file - deployment overview |

## Verification Checklist

Before releasing:

- [ ] All tests pass: `pytest`
- [ ] Code quality: `ruff check qa_agent tests`
- [ ] Type checks: `mypy qa_agent`
- [ ] Version updated in `__init__.py` and `pyproject.toml`
- [ ] CHANGELOG.md updated with release notes
- [ ] Distribution verification: `python3 scripts/verify_distribution.py`
- [ ] Build successful: `bash scripts/build_distribution.sh`
- [ ] Test installation from wheel
- [ ] Git repository clean and committed
- [ ] Git tag created and pushed

## Troubleshooting

### Build Fails

**Issue**: `python -m build` fails

**Solutions**:
- Ensure build tools installed: `pip install build wheel setuptools`
- Check pyproject.toml syntax
- Verify all required files exist

### Import Errors After Installation

**Issue**: Cannot import qa_agent after installation

**Solutions**:
- Check package structure has `__init__.py` files
- Verify MANIFEST.in includes all necessary files
- Reinstall in clean environment

### Version Mismatch

**Issue**: Different versions in different files

**Solutions**:
- Run verification script: `python3 scripts/verify_distribution.py`
- Update both `__init__.py` and `pyproject.toml`
- Ensure consistency before building

### Missing Files in Distribution

**Issue**: Files missing from built package

**Solutions**:
- Check MANIFEST.in includes the files
- Verify files are committed to git
- Rebuild after updating MANIFEST.in

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Publish

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install build twine
      
      - name: Verify distribution
        run: python3 scripts/verify_distribution.py
      
      - name: Build package
        run: python3 -m build
      
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install package
COPY dist/qa_agent-0.1.0-py3-none-any.whl .
RUN pip install qa_agent-0.1.0-py3-none-any.whl

# Set up configuration
COPY config.example.yaml /app/config.yaml

# Entry point
ENTRYPOINT ["qa-agent"]
CMD ["--help"]
```

### Build and Run

```bash
# Build image
docker build -t qa-agent:0.1.0 .

# Run container
docker run -v $(pwd)/requirements.md:/input.md \
           -v $(pwd)/output:/output \
           qa-agent:0.1.0 run /input.md --output /output
```

## Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [Semantic Versioning](https://semver.org/)
- [Twine Documentation](https://twine.readthedocs.io/)

## Support

For deployment issues:
- Check [DISTRIBUTION.md](../DISTRIBUTION.md) for detailed guide
- Open an issue on GitHub
- Review [troubleshooting section](#troubleshooting)
