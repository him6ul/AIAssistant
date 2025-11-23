#!/bin/bash
# Test runner script for AI Assistant

set -e  # Exit on error

echo "🧪 Running AI Assistant Test Suite"
echo "===================================="
echo ""

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest is not installed. Installing test dependencies..."
    pip install -r requirements.txt
fi

# Run tests with coverage
echo "🔍 Running unit tests..."
echo ""

# Run tests
pytest tests/ \
    -v \
    --tb=short \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html \
    --cov-report=xml \
    "$@"

TEST_EXIT_CODE=$?

echo ""
echo "===================================="
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
    echo ""
    echo "📊 Coverage report generated in:"
    echo "   - HTML: htmlcov/index.html"
    echo "   - XML:  coverage.xml"
else
    echo "❌ Some tests failed (exit code: $TEST_EXIT_CODE)"
    exit $TEST_EXIT_CODE
fi

