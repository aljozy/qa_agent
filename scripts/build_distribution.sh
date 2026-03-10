#!/bin/bash
# Build distribution packages for QA Agent

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}QA Agent Distribution Builder${NC}"
echo -e "${BLUE}========================================${NC}"

# Step 1: Verify distribution readiness
echo -e "\n${BLUE}Step 1: Verifying distribution readiness...${NC}"
if python scripts/verify_distribution.py; then
    echo -e "${GREEN}✓ Verification passed${NC}"
else
    echo -e "${RED}✗ Verification failed. Please fix issues before building.${NC}"
    exit 1
fi

# Step 2: Clean previous builds
echo -e "\n${BLUE}Step 2: Cleaning previous builds...${NC}"
rm -rf build/ dist/ *.egg-info
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo -e "${GREEN}✓ Cleaned build artifacts${NC}"

# Step 3: Run tests
echo -e "\n${BLUE}Step 3: Running tests...${NC}"
if pytest --quiet; then
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${RED}✗ Tests failed. Please fix before building.${NC}"
    exit 1
fi

# Step 4: Check code quality
echo -e "\n${BLUE}Step 4: Checking code quality...${NC}"
if ruff check qa_agent tests --quiet; then
    echo -e "${GREEN}✓ Code quality checks passed${NC}"
else
    echo -e "${YELLOW}⚠ Code quality issues found (continuing anyway)${NC}"
fi

# Step 5: Build distributions
echo -e "\n${BLUE}Step 5: Building distributions...${NC}"
python -m build
echo -e "${GREEN}✓ Built distributions${NC}"

# Step 6: Check distributions
echo -e "\n${BLUE}Step 6: Checking distributions...${NC}"
if python -m twine check dist/*; then
    echo -e "${GREEN}✓ Distribution checks passed${NC}"
else
    echo -e "${RED}✗ Distribution checks failed${NC}"
    exit 1
fi

# Step 7: List built files
echo -e "\n${BLUE}Step 7: Built files:${NC}"
ls -lh dist/

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Build completed successfully!${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "\nNext steps:"
echo -e "  1. Test installation: ${YELLOW}pip install dist/*.whl${NC}"
echo -e "  2. Upload to TestPyPI: ${YELLOW}twine upload --repository testpypi dist/*${NC}"
echo -e "  3. Upload to PyPI: ${YELLOW}twine upload dist/*${NC}"
