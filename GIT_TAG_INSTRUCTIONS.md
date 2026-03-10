# Git Tag Instructions for v1.0.0-mvp Release

## Creating the Release Tag

To create the v1.0.0-mvp release tag, follow these steps:

### 1. Ensure All Changes Are Committed

```bash
# Check status
git status

# Add any uncommitted changes
git add .

# Commit with release message
git commit -m "Release v1.0.0-mvp: Initial MVP release with Markdown parsing and manual test generation"
```

### 2. Create Annotated Tag

```bash
# Create annotated tag with release message
git tag -a v1.0.0-mvp -m "Release v1.0.0-mvp

AI-Powered QA Agent MVP Release

Features:
- Markdown requirements parser
- AI-powered manual test case generation
- Requirement Traceability Matrix (RTM)
- Multi-provider AI support (Kiro/OpenAI)
- CLI interface with parse, generate, rtm, and run commands
- Comprehensive documentation and examples

See RELEASE_NOTES_v1.0.0-mvp.md for full details."
```

### 3. Verify Tag

```bash
# List tags
git tag -l

# Show tag details
git show v1.0.0-mvp
```

### 4. Push Tag to Remote

```bash
# Push the tag to remote repository
git push origin v1.0.0-mvp

# Or push all tags
git push --tags
```

### 5. Create GitHub Release (Optional)

If using GitHub, create a release from the tag:

1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Select tag: `v1.0.0-mvp`
4. Release title: `v1.0.0-mvp - AI-Powered QA Agent MVP`
5. Description: Copy content from `RELEASE_NOTES_v1.0.0-mvp.md`
6. Attach any release artifacts (optional)
7. Check "This is a pre-release" (since it's an MVP)
8. Click "Publish release"

## Tag Naming Convention

This project follows semantic versioning with pre-release identifiers:

- **Major.Minor.Patch**: `1.0.0`
- **Pre-release identifier**: `-mvp`, `-alpha`, `-beta`, `-rc1`
- **Full version**: `1.0.0-mvp`

### Future Tags

- `v1.0.0-mvp` - Initial MVP release (current)
- `v1.1.0` - Jira parser addition
- `v1.2.0` - OpenAPI parser + API test generator
- `v1.3.0` - Vector store + RAG
- `v1.4.0` - Coverage analyzer
- `v1.5.0` - MCP integrations
- `v2.0.0` - Major version with breaking changes

## Deleting a Tag (If Needed)

If you need to delete a tag:

```bash
# Delete local tag
git tag -d v1.0.0-mvp

# Delete remote tag
git push origin --delete v1.0.0-mvp
```

## Verifying Release

After tagging, verify the release:

```bash
# Check version in code
python -c "from qa_agent import __version__; print(__version__)"
# Should output: 1.0.0-mvp

# Check CLI version
qa-agent --version
# Should output: qa-agent version 1.0.0-mvp

# List all tags
git tag -l -n9
```

## Release Checklist

Before creating the tag, ensure:

- ✅ All tests pass: `pytest`
- ✅ Code is formatted: `black qa_agent tests`
- ✅ Code is linted: `ruff check qa_agent tests`
- ✅ Type checking passes: `mypy qa_agent`
- ✅ Documentation is updated
- ✅ CHANGELOG.md is updated
- ✅ Version numbers are updated in:
  - `qa_agent/__init__.py`
  - `pyproject.toml`
- ✅ Release notes are created: `RELEASE_NOTES_v1.0.0-mvp.md`
- ✅ All changes are committed
- ✅ Working directory is clean

## Post-Release Tasks

After creating the release:

1. Announce the release (if applicable)
2. Update documentation website (if applicable)
3. Notify users/stakeholders
4. Monitor for issues
5. Begin work on next version (v1.1.0)

## Questions?

If you have questions about the release process, refer to:
- [Semantic Versioning](https://semver.org/)
- [Git Tagging Documentation](https://git-scm.com/book/en/v2/Git-Basics-Tagging)
- [GitHub Releases Documentation](https://docs.github.com/en/repositories/releasing-projects-on-github)
