#!/bin/bash
# Quick test runner (unit tests only, no coverage)

set -e

echo "⚡ Running Quick Test Suite (Unit Tests Only)"
echo "=============================================="
echo ""

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run only unit tests (fast)
pytest tests/ \
    -v \
    -m "unit" \
    --tb=short \
    "$@"

