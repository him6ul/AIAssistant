#!/bin/bash
# Script to run tests when code changes are made
# This can be called by Cursor or other tools after making changes

set -e

echo "🧪 Running tests after code changes..."
echo "======================================"
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "⚠️  pytest is not installed. Installing test dependencies..."
    pip install -r requirements.txt
fi

# Run unit tests (fast)
echo "📋 Running unit tests..."
pytest tests/ -m unit -v --tb=short

TEST_EXIT_CODE=$?

echo ""
echo "======================================"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed (exit code: $TEST_EXIT_CODE)"
    exit $TEST_EXIT_CODE
fi

