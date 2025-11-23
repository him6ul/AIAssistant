# Automatic Test Execution

This directory contains configuration for automatic test execution when Cursor makes code changes.

## How It Works

When Cursor makes changes to the codebase, it should automatically run tests to verify the changes work correctly.

## Manual Test Execution

Run tests manually after making changes:

```bash
./scripts/run_tests_on_change.sh
```

## Test Scripts Available

- `scripts/run_tests_on_change.sh` - Quick unit tests (for after changes)
- `scripts/run_tests_quick.sh` - Quick unit tests only
- `scripts/run_tests.sh` - Full test suite with coverage
- `scripts/verify_tests.sh` - Verify tests after changes

## Configuration

The `.cursor/rules` file contains instructions for Cursor to run tests automatically.

