# Testing Quick Reference

## Quick Start

```bash
# Run all tests
./scripts/run_tests.sh

# Run quick unit tests only
./scripts/run_tests_quick.sh

# Verify tests after code changes
./scripts/verify_tests.sh
```

## Test Execution Workflow

### After Making Code Changes

1. **Tests run automatically** when Cursor makes changes (via `.cursor/rules`)

2. **Or run tests manually:**
   ```bash
   ./scripts/run_tests_on_change.sh
   ```

3. **If tests pass, proceed with commit:**
   ```bash
   git add .
   git commit -m "Your commit message"
   ```

**Note:** Pre-commit hook is disabled. Tests run via Cursor, not on git commit.

### Manual Test Execution

```bash
# All tests with coverage
pytest tests/ -v --cov=app

# Specific test file
pytest tests/test_email_importance_checker.py -v

# Tests by marker
pytest tests/ -m email -v
pytest tests/ -m connector -v
```

## Test Coverage

Current test coverage includes:

- ✅ Email importance checking (heuristics + LLM)
- ✅ Email notification monitoring
- ✅ Localization utilities
- ✅ Gmail connector (mocked)
- ✅ Outlook connector (mocked)
- ✅ Email filtering and time window logic
- ✅ Notification history management

## Installing Test Dependencies

```bash
# Install all dependencies including test tools
pip install -r requirements.txt

# Or install test tools separately
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

## Troubleshooting

**Tests fail with import errors:**
- Make sure virtual environment is activated
- Run from project root directory
- Install dependencies: `pip install -r requirements.txt`

**Tests not running automatically:**
- Cursor should run tests automatically based on `.cursor/rules`
- Manually run: `./scripts/run_tests_on_change.sh`

**Pre-commit hook:**
- Disabled (tests don't run on commit)
- Tests run via Cursor when code changes are made

For detailed testing guide, see [TESTING_GUIDE.md](TESTING_GUIDE.md)

