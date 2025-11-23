"""
Unit tests for EmailImportanceChecker.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.monitoring.email_monitor import EmailImportanceChecker
from app.connectors.models import UnifiedEmail, SourceType, EmailPriority


@pytest.fixture
def importance_checker():
    """Create an EmailImportanceChecker instance with mocked LLM router."""
    with patch('app.monitoring.email_monitor.get_llm_router') as mock_router:
        mock_llm = MagicMock()
        mock_router.return_value = mock_llm
        checker = EmailImportanceChecker()
        checker.llm_router = mock_llm
        return checker


@pytest.fixture
def sample_email():
    """Create a sample UnifiedEmail for testing."""
    return UnifiedEmail(
        id="test_email_1",
        source_type=SourceType.GMAIL,
        source_id="123",
        subject="Test Email",
        body_text="This is a test email body",
        from_address={"email": "sender@example.com", "name": "Test Sender"},
        to_addresses=[{"email": "recipient@example.com"}],
        timestamp=datetime.utcnow(),
        is_read=False,
        is_important=False,
        priority=EmailPriority.NORMAL
    )


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.email
async def test_is_important_flag_true(importance_checker, sample_email):
    """Test that email with is_important=True is marked as important."""
    sample_email.is_important = True
    
    result = await importance_checker.is_important(sample_email)
    
    assert result is True
    # Should not call LLM if heuristic passes
    importance_checker.llm_router.generate.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.email
async def test_high_priority_email(importance_checker, sample_email):
    """Test that email with high priority is marked as important."""
    sample_email.priority = EmailPriority.HIGH
    
    result = await importance_checker.is_important(sample_email)
    
    assert result is True
    importance_checker.llm_router.generate.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.email
async def test_urgent_priority_email(importance_checker, sample_email):
    """Test that email with urgent priority is marked as important."""
    sample_email.priority = EmailPriority.URGENT
    
    result = await importance_checker.is_important(sample_email)
    
    assert result is True
    importance_checker.llm_router.generate.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.email
@pytest.mark.parametrize("keyword", [
    "urgent",
    "important",
    "action required",
    "deadline",
    "meeting",
    "asap",
    "critical",
    "priority",
    "attention",
    "response needed"
])
async def test_keyword_detection(importance_checker, sample_email, keyword):
    """Test that emails with important keywords in subject are marked as important."""
    sample_email.subject = f"This is {keyword} email"
    
    result = await importance_checker.is_important(sample_email)
    
    assert result is True
    importance_checker.llm_router.generate.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.email
async def test_keyword_case_insensitive(importance_checker, sample_email):
    """Test that keyword detection is case-insensitive."""
    sample_email.subject = "THIS IS URGENT EMAIL"
    
    result = await importance_checker.is_important(sample_email)
    
    assert result is True


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.email
async def test_llm_marks_important(importance_checker, sample_email):
    """Test that LLM can mark an email as important."""
    # No heuristic matches
    sample_email.is_important = False
    sample_email.priority = EmailPriority.NORMAL
    sample_email.subject = "Regular email"
    
    # Mock LLM response
    importance_checker.llm_router.generate = AsyncMock(return_value={
        "content": "YES"
    })
    
    result = await importance_checker.is_important(sample_email)
    
    assert result is True
    importance_checker.llm_router.generate.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.email
async def test_llm_marks_not_important(importance_checker, sample_email):
    """Test that LLM can mark an email as not important."""
    # No heuristic matches
    sample_email.is_important = False
    sample_email.priority = EmailPriority.NORMAL
    sample_email.subject = "Regular email"
    
    # Mock LLM response
    importance_checker.llm_router.generate = AsyncMock(return_value={
        "content": "NO"
    })
    
    result = await importance_checker.is_important(sample_email)
    
    assert result is False
    importance_checker.llm_router.generate.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.email
async def test_llm_response_variations(importance_checker, sample_email):
    """Test that LLM response variations are handled correctly."""
    sample_email.is_important = False
    sample_email.priority = EmailPriority.NORMAL
    sample_email.subject = "Regular email"
    
    # Test various LLM response formats
    test_cases = [
        ("YES", True),
        ("yes", True),
        ("Yes, this is important", True),
        ("NO", False),
        ("no", False),
        ("No, not important", False),
    ]
    
    for response, expected in test_cases:
        importance_checker.llm_router.generate = AsyncMock(return_value={
            "content": response
        })
        
        result = await importance_checker.is_important(sample_email)
        
        assert result == expected, f"Expected {expected} for response '{response}'"


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.email
async def test_llm_error_handling(importance_checker, sample_email):
    """Test that LLM errors are handled gracefully."""
    sample_email.is_important = False
    sample_email.priority = EmailPriority.NORMAL
    sample_email.subject = "Regular email"
    
    # Mock LLM to raise exception
    importance_checker.llm_router.generate = AsyncMock(side_effect=Exception("LLM error"))
    
    result = await importance_checker.is_important(sample_email)
    
    # Should default to not important on error
    assert result is False


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.email
async def test_llm_invalid_response(importance_checker, sample_email):
    """Test that invalid LLM responses are handled."""
    sample_email.is_important = False
    sample_email.priority = EmailPriority.NORMAL
    sample_email.subject = "Regular email"
    
    # Mock LLM to return invalid response
    importance_checker.llm_router.generate = AsyncMock(return_value={
        "invalid": "response"
    })
    
    result = await importance_checker.is_important(sample_email)
    
    assert result is False


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.email
async def test_heuristic_takes_precedence(importance_checker, sample_email):
    """Test that heuristics are checked before LLM."""
    # Set both heuristic match and prepare LLM
    sample_email.is_important = True
    importance_checker.llm_router.generate = AsyncMock()
    
    result = await importance_checker.is_important(sample_email)
    
    assert result is True
    # LLM should not be called if heuristic matches
    importance_checker.llm_router.generate.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.email
async def test_email_with_empty_subject(importance_checker, sample_email):
    """Test email with empty subject."""
    sample_email.subject = ""
    sample_email.is_important = False
    sample_email.priority = EmailPriority.NORMAL
    
    # Should fall through to LLM
    importance_checker.llm_router.generate = AsyncMock(return_value={
        "content": "NO"
    })
    
    result = await importance_checker.is_important(sample_email)
    
    assert result is False
    importance_checker.llm_router.generate.assert_called_once()

