# Quick Deploy Reference

Fast reference for building and deploying the QA Agent package.

## Prerequisites

```bash
pip install build twine wheel setuptools
```

## Quick Commands

### Verify Ready
```bash
python3 scripts/verify_distribution.py
```

### Build Package
```bash
bash scripts/build_distribution.sh
```

### Or Build Manually
```bash
rm -rf build/ dist/ *.egg-info
python3 -m build
python3 -m twine check dist/*
```

### Test Locally
```bash
pip install dist/*.whl
qa-agent --version
```

### Upload to TestPyPI
```bash
python3 -m twine upload --repository testpypi dist/*
```

### Upload to PyPI
```bash
python3 -m twine upload dist/*
```

## Version Update

```bash
# 1. Update version in files
# - qa_agent/__init__.py: __version__ = "0.2.0"
# - pyproject.toml: version = "0.2.0"
# - CHANGELOG.md: Add release notes

# 2. Commit and tag
git add qa_agent/__init__.py pyproject.toml CHANGELOG.md
git commit -m "Bump version to 0.2.0"
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin main
git push origin v0.2.0
```

## Files to Update Before Release

- [ ] `qa_agent/__init__.py` - Update `__version__`
- [ ] `pyproject.toml` - Update `version`
- [ ] `CHANGELOG.md` - Add release notes
- [ ] Run tests: `pytest`
- [ ] Run verification: `python3 scripts/verify_distribution.py`

## Distribution Files

After build, you'll have:
- `dist/qa-agent-X.Y.Z.tar.gz` - Source distribution
- `dist/qa_agent-X.Y.Z-py3-none-any.whl` - Wheel distribution

## Troubleshooting

**Build fails?**
```bash
pip install --upgrade build wheel setuptools
```

**Version mismatch?**
```bash
python3 scripts/verify_distribution.py
```

**Import errors?**
```bash
pip install -e ".[dev]"
```

## Full Documentation

- Detailed guide: `DISTRIBUTION.md`
- Deployment guide: `docs/deployment.md`
- Changelog: `CHANGELOG.md`
