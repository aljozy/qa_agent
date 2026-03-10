#!/usr/bin/env python3
"""Verify distribution readiness for the QA Agent package.

This script checks that all necessary files and configurations are in place
before building and distributing the package.
"""

import sys
from pathlib import Path
from typing import List, Tuple

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def check_file_exists(filepath: Path, description: str) -> bool:
    """Check if a file exists."""
    if filepath.exists():
        print(f"{GREEN}✓{RESET} {description}: {filepath}")
        return True
    else:
        print(f"{RED}✗{RESET} {description}: {filepath} (MISSING)")
        return False


def check_version_consistency() -> bool:
    """Check that version is consistent across files."""
    print(f"\n{BLUE}Checking version consistency...{RESET}")
    
    # Read version from __init__.py
    init_file = Path("qa_agent/__init__.py")
    if not init_file.exists():
        print(f"{RED}✗{RESET} Cannot find qa_agent/__init__.py")
        return False
    
    init_content = init_file.read_text()
    init_version = None
    for line in init_content.split("\n"):
        if line.startswith("__version__"):
            init_version = line.split("=")[1].strip().strip('"').strip("'")
            break
    
    # Read version from pyproject.toml
    pyproject_file = Path("pyproject.toml")
    if not pyproject_file.exists():
        print(f"{RED}✗{RESET} Cannot find pyproject.toml")
        return False
    
    pyproject_content = pyproject_file.read_text()
    pyproject_version = None
    for line in pyproject_content.split("\n"):
        if line.startswith("version"):
            pyproject_version = line.split("=")[1].strip().strip('"').strip("'")
            break
    
    if init_version and pyproject_version:
        if init_version == pyproject_version:
            print(f"{GREEN}✓{RESET} Version consistent: {init_version}")
            return True
        else:
            print(f"{RED}✗{RESET} Version mismatch:")
            print(f"  __init__.py: {init_version}")
            print(f"  pyproject.toml: {pyproject_version}")
            return False
    else:
        print(f"{RED}✗{RESET} Could not extract version from files")
        return False


def check_required_files() -> Tuple[bool, List[str]]:
    """Check that all required files exist."""
    print(f"\n{BLUE}Checking required files...{RESET}")
    
    required_files = [
        ("README.md", "README file"),
        ("LICENSE", "License file"),
        ("CHANGELOG.md", "Changelog"),
        ("pyproject.toml", "Project configuration"),
        ("requirements.txt", "Requirements file"),
        ("MANIFEST.in", "Manifest file"),
        ("qa_agent/__init__.py", "Package init file"),
        ("qa_agent/cli.py", "CLI module"),
    ]
    
    all_exist = True
    missing = []
    
    for filepath, description in required_files:
        path = Path(filepath)
        if not check_file_exists(path, description):
            all_exist = False
            missing.append(filepath)
    
    return all_exist, missing


def check_example_files() -> bool:
    """Check that example files exist."""
    print(f"\n{BLUE}Checking example files...{RESET}")
    
    examples_dir = Path("examples")
    if not examples_dir.exists():
        print(f"{RED}✗{RESET} Examples directory not found")
        return False
    
    example_files = list(examples_dir.glob("*"))
    if len(example_files) > 0:
        print(f"{GREEN}✓{RESET} Found {len(example_files)} example files")
        return True
    else:
        print(f"{YELLOW}⚠{RESET} No example files found")
        return False


def check_docs() -> bool:
    """Check that documentation exists."""
    print(f"\n{BLUE}Checking documentation...{RESET}")
    
    docs_dir = Path("docs")
    if not docs_dir.exists():
        print(f"{YELLOW}⚠{RESET} Docs directory not found")
        return False
    
    doc_files = list(docs_dir.glob("*.md"))
    if len(doc_files) > 0:
        print(f"{GREEN}✓{RESET} Found {len(doc_files)} documentation files")
        return True
    else:
        print(f"{YELLOW}⚠{RESET} No documentation files found")
        return False


def check_tests() -> bool:
    """Check that tests exist."""
    print(f"\n{BLUE}Checking tests...{RESET}")
    
    tests_dir = Path("tests")
    if not tests_dir.exists():
        print(f"{RED}✗{RESET} Tests directory not found")
        return False
    
    test_files = list(tests_dir.glob("test_*.py"))
    if len(test_files) > 0:
        print(f"{GREEN}✓{RESET} Found {len(test_files)} test files")
        return True
    else:
        print(f"{RED}✗{RESET} No test files found")
        return False


def check_pyproject_metadata() -> bool:
    """Check that pyproject.toml has required metadata."""
    print(f"\n{BLUE}Checking pyproject.toml metadata...{RESET}")
    
    pyproject_file = Path("pyproject.toml")
    if not pyproject_file.exists():
        print(f"{RED}✗{RESET} pyproject.toml not found")
        return False
    
    content = pyproject_file.read_text()
    
    required_fields = [
        ("name =", "Package name"),
        ("version =", "Version"),
        ("description =", "Description"),
        ("readme =", "README reference"),
        ("requires-python =", "Python version requirement"),
        ("license =", "License"),
        ("authors =", "Authors"),
        ("[project.urls]", "Project URLs"),
        ("[project.scripts]", "CLI entry points"),
    ]
    
    all_present = True
    for field, description in required_fields:
        if field in content:
            print(f"{GREEN}✓{RESET} {description}")
        else:
            print(f"{RED}✗{RESET} {description} (MISSING)")
            all_present = False
    
    return all_present


def main() -> int:
    """Run all verification checks."""
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}QA Agent Distribution Verification{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    checks = [
        ("Required files", check_required_files),
        ("Version consistency", check_version_consistency),
        ("PyProject metadata", check_pyproject_metadata),
        ("Example files", check_example_files),
        ("Documentation", check_docs),
        ("Tests", check_tests),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            if name == "Required files":
                result, missing = check_func()
                results.append((name, result))
            else:
                result = check_func()
                results.append((name, result))
        except Exception as e:
            print(f"{RED}✗{RESET} Error checking {name}: {e}")
            results.append((name, False))
    
    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Summary{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{status} - {name}")
    
    print(f"\n{BLUE}Results: {passed}/{total} checks passed{RESET}")
    
    if passed == total:
        print(f"\n{GREEN}✓ All checks passed! Ready for distribution.{RESET}")
        return 0
    else:
        print(f"\n{RED}✗ Some checks failed. Please fix the issues before distributing.{RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
