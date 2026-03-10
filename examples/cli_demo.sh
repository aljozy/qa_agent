#!/bin/bash
# CLI Demo Script for QA Agent

echo "=== QA Agent CLI Demo ==="
echo ""

# Show version
echo "1. Show version:"
python3 -m qa_agent.cli --version
echo ""

# Parse requirements
echo "2. Parse requirements from markdown:"
python3 -m qa_agent.cli parse examples/sample_requirements.md
echo ""

# Note: The generate and rtm commands require an LLM provider to be configured
echo "3. To generate test cases (requires OpenAI API key or Kiro):"
echo "   python3 -m qa_agent.cli generate output/requirements/sample_requirements.json --provider openai"
echo ""

echo "4. To generate RTM:"
echo "   python3 -m qa_agent.cli rtm output/requirements/sample_requirements.json output/tests/sample_requirements_tests.json"
echo ""

echo "5. To run the full pipeline:"
echo "   python3 -m qa_agent.cli run examples/sample_requirements.md --provider openai"
echo ""

echo "=== Demo Complete ==="
