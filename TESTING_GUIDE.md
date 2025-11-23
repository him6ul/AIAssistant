# Testing Guide

This document describes the testing strategy and how to run tests for the AI Assistant.

## Test Structure

Tests are organized in the `tests/` directory:

```
tests/
├── __init__.py
├── test_email_importance_checker.py    # Tests for email importance detection
├── test_email_notification_monitor.py  # Tests for email monitoring
├── test_localization.py                # Tests for localization utilities
├── test_gmail_connector.py             # Tests for Gmail connector
└── test_outlook_connector.py           # Tests for Outlook connector
```

## Test Categories

Tests are marked with pytest markers:

- **`@pytest.mark.unit`**: Fast, isolated unit tests (no external dependencies)
- **`@pytest.mark.integration`**: Integration tests (may require external services)
- **`@pytest.mark.slow`**: Slow tests that may take longer to run
- **`@pytest.mark.email`**: Email-related tests
- **`@pytest.mark.connector`**: Connector tests
- **`@pytest.mark.monitor`**: Email monitor tests

## Running Tests

### Run All Tests

```bash
# Full test suite with coverage
./scripts/run_tests.sh

# Or using pytest directly
pytest tests/ -v
```

### Run Quick Tests (Unit Tests Only)

```bash
# Fast unit tests only
./scripts/run_tests_quick.sh

# Or using pytest directly
pytest tests/ -m unit -v
```

### Run Specific Test Files

```bash
# Run tests for email importance checker
pytest tests/test_email_importance_checker.py -v

# Run tests for email monitor
pytest tests/test_email_notification_monitor.py -v

# Run tests for localization
pytest tests/test_localization.py -v
```

### Run Tests by Marker

```bash
# Run only email-related tests
pytest tests/ -m email -v

# Run only connector tests
pytest tests/ -m connector -v

# Run only monitor tests
pytest tests/ -m monitor -v
```

### Run with Coverage

```bash
# Generate coverage report
pytest tests/ --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Test Coverage

The test suite covers:

### ✅ EmailImportanceChecker
- Heuristic importance detection (flags, priority, keywords)
- LLM-based importance detection
- Error handling
- Edge cases (empty subjects, invalid responses)

### ✅ EmailNotificationMonitor
- Initialization
- Notification history loading/saving
- Email filtering (time window, already notified)
- Importance checking integration
- Notification sending
- Monitor start/stop

### ✅ Localization
- Message loading from file
- Variable substitution
- Missing key handling
- File parsing

### ✅ GmailConnector
- Connection/disconnection
- Email fetching
- Importance detection from headers
- Error handling

### ✅ OutlookConnector
- Connection/disconnection
- Email fetching via Graph API
- Importance detection
- Email conversion

## Writing New Tests

### Test Template

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
@pytest.mark.unit
async def test_feature_name():
    """Test description."""
    # Arrange
    # Act
    # Assert
    pass
```

### Best Practices

1. **Use fixtures** for common setup
2. **Mock external dependencies** (APIs, file system, etc.)
3. **Test edge cases** (empty inputs, errors, boundaries)
4. **Use descriptive test names** that explain what is being tested
5. **Keep tests isolated** - each test should be independent
6. **Use parametrize** for testing multiple inputs

### Example: Adding a New Test

```python
@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.email
async def test_new_feature():
    """Test new feature functionality."""
    # Arrange
    with patch('module.dependency') as mock_dep:
        mock_dep.return_value = "expected_value"
        
        # Act
        result = await function_under_test()
        
        # Assert
        assert result == "expected_result"
        mock_dep.assert_called_once()
```

## Continuous Integration

Tests are automatically run on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

See `.github/workflows/tests.yml` for CI configuration.

## Pre-commit Testing

To run tests before committing:

```bash
# Add to .git/hooks/pre-commit (or use pre-commit framework)
#!/bin/bash
./scripts/run_tests_quick.sh
```

Or use the pre-commit hook:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

## Troubleshooting

### Tests Fail with Import Errors

```bash
# Make sure you're in the project root
cd /path/to/AI_Assistant

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Tests Timeout

Some tests may timeout if they're waiting for external services. Use mocks instead:

```python
with patch('external.service') as mock_service:
    mock_service.return_value = AsyncMock(return_value="result")
    # Your test code
```

### Coverage Not Working

```bash
# Install coverage tools
pip install pytest-cov

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Test Data

Test data is created using fixtures and mocks. No real API credentials or external services are required for unit tests.

For integration tests that need real services, use environment variables or test credentials stored securely.

## Coverage Goals

- **Target**: 80%+ code coverage
- **Critical paths**: 90%+ coverage
- **New code**: 100% coverage required

View current coverage:
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

## Contributing

When adding new features:

1. ✅ Write tests first (TDD approach)
2. ✅ Ensure all tests pass
3. ✅ Maintain or improve coverage
4. ✅ Update this guide if needed

