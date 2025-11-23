#!/bin/bash
# Verify tests script - can be called after code changes

set -e

echo "🔍 Verifying Tests After Code Changes"
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
    echo "❌ pytest is not installed. Installing test dependencies..."
    pip install -r requirements.txt
fi

echo "📋 Running all unit tests..."
echo ""

# Run unit tests
pytest tests/ -m unit -v --tb=short

echo ""
echo "✅ All unit tests passed!"
echo ""
echo "💡 To run full test suite with coverage:"
echo "   ./scripts/run_tests.sh"

