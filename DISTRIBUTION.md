# Distribution Guide

This guide explains how to build, package, and distribute the AI-Powered QA Agent.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Building the Package](#building-the-package)
- [Testing the Distribution](#testing-the-distribution)
- [Publishing to PyPI](#publishing-to-pypi)
- [Version Management](#version-management)
- [Distribution Checklist](#distribution-checklist)

## Prerequisites

### Required Tools

Install the required build and distribution tools:

```bash
pip install --upgrade pip
pip install build twine wheel setuptools
```

### PyPI Account

1. Create an account at [PyPI](https://pypi.org/account/register/)
2. Create an account at [TestPyPI](https://test.pypi.org/account/register/) for testing
3. Generate API tokens for both accounts:
   - PyPI: https://pypi.org/manage/account/token/
   - TestPyPI: https://test.pypi.org/manage/account/token/

### Configure PyPI Credentials

Create or update `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR-API-TOKEN-HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TESTPYPI-TOKEN-HERE
```

Set appropriate permissions:

```bash
chmod 600 ~/.pypirc
```

## Building the Package

### 1. Clean Previous Builds

Remove any previous build artifacts:

```bash
rm -rf build/ dist/ *.egg-info
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### 2. Update Version Information

Before building, ensure version is updated in:

1. `qa_agent/__init__.py`:
   ```python
   __version__ = "0.1.0"
   ```

2. `pyproject.toml`:
   ```toml
   [project]
   version = "0.1.0"
   ```

3. `CHANGELOG.md`:
   - Add release notes for the new version
   - Update the release date

### 3. Build Source and Wheel Distributions

Build both source distribution (`.tar.gz`) and wheel (`.whl`):

```bash
python -m build
```

This creates:
- `dist/qa-agent-0.1.0.tar.gz` (source distribution)
- `dist/qa_agent-0.1.0-py3-none-any.whl` (wheel distribution)

### 4. Verify Build Contents

Check what files are included in the distribution:

```bash
# For source distribution
tar -tzf dist/qa-agent-0.1.0.tar.gz

# For wheel
unzip -l dist/qa_agent-0.1.0-py3-none-any.whl
```

Ensure all necessary files are included:
- ✅ Python source files (`qa_agent/`)
- ✅ README.md
- ✅ LICENSE
- ✅ CHANGELOG.md
- ✅ requirements.txt
- ✅ Example files (`examples/`)
- ✅ Documentation (`docs/`)
- ✅ Configuration examples

## Testing the Distribution

### 1. Test with TestPyPI

Upload to TestPyPI first to verify everything works:

```bash
python -m twine upload --repository testpypi dist/*
```

### 2. Install from TestPyPI

Test installation in a clean virtual environment:

```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ qa-agent

# Verify installation
qa-agent --version
qa-agent --help

# Test basic functionality
qa-agent parse examples/example_prd.md --output test_output

# Deactivate and remove test environment
deactivate
rm -rf test_env test_output
```

### 3. Local Installation Test

Test installation from local files:

```bash
# Create test environment
python -m venv local_test_env
source local_test_env/bin/activate

# Install from wheel
pip install dist/qa_agent-0.1.0-py3-none-any.whl

# Or install from source distribution
pip install dist/qa-agent-0.1.0.tar.gz

# Test functionality
qa-agent --version

# Clean up
deactivate
rm -rf local_test_env
```

## Publishing to PyPI

### 1. Final Checks

Before publishing to production PyPI:

- ✅ All tests pass: `pytest`
- ✅ Code quality checks pass: `ruff check qa_agent tests`
- ✅ Type checks pass: `mypy qa_agent`
- ✅ Documentation is up to date
- ✅ CHANGELOG.md is updated
- ✅ Version numbers are consistent
- ✅ TestPyPI installation works
- ✅ Git repository is clean and committed

### 2. Create Git Tag

Tag the release in git:

```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

### 3. Upload to PyPI

Upload the distribution to production PyPI:

```bash
python -m twine upload dist/*
```

### 4. Verify Publication

Check that the package is available:

```bash
# View on PyPI
open https://pypi.org/project/qa-agent/

# Install from PyPI
pip install qa-agent

# Verify version
qa-agent --version
```

## Version Management

### Semantic Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Incompatible API changes
- **MINOR** (0.X.0): New features, backward compatible
- **PATCH** (0.0.X): Bug fixes, backward compatible

### Version Update Process

1. **Decide version number** based on changes:
   - Breaking changes → increment MAJOR
   - New features → increment MINOR
   - Bug fixes → increment PATCH

2. **Update version in code**:
   ```bash
   # Update qa_agent/__init__.py
   __version__ = "0.2.0"
   
   # Update pyproject.toml
   version = "0.2.0"
   ```

3. **Update CHANGELOG.md**:
   - Add new version section
   - List all changes under appropriate categories
   - Set release date

4. **Commit changes**:
   ```bash
   git add qa_agent/__init__.py pyproject.toml CHANGELOG.md
   git commit -m "Bump version to 0.2.0"
   ```

5. **Create and push tag**:
   ```bash
   git tag -a v0.2.0 -m "Release version 0.2.0"
   git push origin main
   git push origin v0.2.0
   ```

## Distribution Checklist

Use this checklist before each release:

### Pre-Release

- [ ] All tests pass (`pytest`)
- [ ] Code quality checks pass (`ruff check`, `black --check`, `mypy`)
- [ ] Documentation is updated
- [ ] CHANGELOG.md has release notes
- [ ] Version updated in `__init__.py` and `pyproject.toml`
- [ ] README.md examples work
- [ ] Example files are up to date
- [ ] Git repository is clean (no uncommitted changes)

### Build

- [ ] Clean previous builds (`rm -rf build/ dist/ *.egg-info`)
- [ ] Build distributions (`python -m build`)
- [ ] Verify build contents (check tar.gz and .whl)
- [ ] Check package metadata (`twine check dist/*`)

### Test

- [ ] Upload to TestPyPI
- [ ] Install from TestPyPI in clean environment
- [ ] Run basic functionality tests
- [ ] Verify CLI commands work
- [ ] Check version output

### Release

- [ ] Create git tag (`git tag -a vX.Y.Z`)
- [ ] Push tag to repository
- [ ] Upload to PyPI (`twine upload dist/*`)
- [ ] Verify package on PyPI
- [ ] Test installation from PyPI
- [ ] Create GitHub release with notes

### Post-Release

- [ ] Announce release (if applicable)
- [ ] Update documentation site (if applicable)
- [ ] Close milestone (if using GitHub milestones)
- [ ] Plan next version

## Troubleshooting

### Common Issues

#### Issue: "File already exists" on PyPI

**Solution**: You cannot re-upload the same version. Increment the version number.

#### Issue: Missing files in distribution

**Solution**: Check `MANIFEST.in` and ensure all necessary files are included.

#### Issue: Import errors after installation

**Solution**: Verify package structure and ensure `__init__.py` files exist in all packages.

#### Issue: Dependencies not installing

**Solution**: Check `pyproject.toml` dependencies section and version constraints.

### Validation Commands

```bash
# Check package metadata
twine check dist/*

# Verify package contents
tar -tzf dist/qa-agent-*.tar.gz | grep -E "(README|LICENSE|CHANGELOG)"

# Test import after installation
python -c "import qa_agent; print(qa_agent.__version__)"

# Verify CLI entry point
which qa-agent
qa-agent --version
```

## Automation

### GitHub Actions (Future)

Consider automating releases with GitHub Actions:

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install build twine
      - name: Build package
        run: python -m build
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

## Resources

- [Python Packaging User Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Twine Documentation](https://twine.readthedocs.io/)
