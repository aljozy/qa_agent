#!/usr/bin/env python3
"""Verify that the QA Agent setup is correct."""

import sys
from pathlib import Path


def check_directory_structure() -> bool:
    """Check that all required directories exist."""
    print("Checking directory structure...")
    required_dirs = [
        "qa_agent",
        "qa_agent/parsers",
        "qa_agent/generators",
        "qa_agent/vector_store",
        "qa_agent/rag",
        "qa_agent/mcp",
        "qa_agent/config",
        "qa_agent/models",
        "qa_agent/analysis",
        "tests",
    ]

    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ✗ {dir_path} - MISSING")
            all_exist = False

    return all_exist


def check_files() -> bool:
    """Check that all required files exist."""
    print("\nChecking required files...")
    required_files = [
        "pyproject.toml",
        "README.md",
        ".env.example",
        ".gitignore",
        ".pre-commit-config.yaml",
        "requirements.txt",
        "requirements-dev.txt",
        "docker-compose.yml",
        "Makefile",
        "qa_agent/__init__.py",
        "qa_agent/cli.py",
        "tests/__init__.py",
        "tests/conftest.py",
        "tests/test_setup.py",
    ]

    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists() and path.is_file():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} - MISSING")
            all_exist = False

    return all_exist


def check_imports() -> bool:
    """Check that the package can be imported."""
    print("\nChecking package imports...")
    try:
        import qa_agent

        print(f"  ✓ qa_agent (version {qa_agent.__version__})")

        modules = [
            "qa_agent.parsers",
            "qa_agent.generators",
            "qa_agent.vector_store",
            "qa_agent.rag",
            "qa_agent.mcp",
            "qa_agent.config",
            "qa_agent.models",
            "qa_agent.analysis",
        ]

        for module in modules:
            __import__(module)
            print(f"  ✓ {module}")

        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def main() -> int:
    """Run all verification checks."""
    print("=" * 60)
    print("QA Agent Setup Verification")
    print("=" * 60)

    checks = [
        ("Directory Structure", check_directory_structure),
        ("Required Files", check_files),
        ("Package Imports", check_imports),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} check failed with error: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    all_passed = True
    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name}: {status}")
        if not result:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n✓ All checks passed! Setup is complete.")
        return 0
    else:
        print("\n✗ Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
