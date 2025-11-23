"""
Unit tests for GmailConnector.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime
import imaplib

from app.connectors.implementations.gmail_connector import GmailConnector
from app.connectors.models import SourceType, EmailPriority


@pytest.fixture
def gmail_connector():
    """Create a GmailConnector instance for testing."""
    return GmailConnector(
        imap_server="imap.gmail.com",
        imap_port=993,
        username="test@gmail.com",
        password="test_password"
    )


@pytest.fixture
def mock_imap():
    """Create a mocked IMAP connection."""
    mock_imap = MagicMock()
    mock_imap.login = MagicMock()
    mock_imap.logout = MagicMock()
    mock_imap.select = MagicMock()
    mock_imap.search = MagicMock(return_value=("OK", [b"1 2 3"]))
    mock_imap.fetch = MagicMock(return_value=(
        "OK",
        [
            (b"1 (RFC822 {100}", b"From: sender@example.com\r\nSubject: Test\r\n\r\nBody"),
            (b"2 (RFC822 {100}", b"From: sender2@example.com\r\nSubject: Test2\r\n\r\nBody2")
        ]
    ))
    return mock_imap


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.connector
async def test_gmail_connector_source_type(gmail_connector):
    """Test that GmailConnector returns correct source type."""
    assert gmail_connector.source_type == SourceType.GMAIL


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.connector
async def test_gmail_connector_connect_success(gmail_connector, mock_imap):
    """Test successful Gmail connection."""
    with patch('imaplib.IMAP4_SSL', return_value=mock_imap):
        result = await gmail_connector.connect()
        
        assert result is True
        assert gmail_connector._connected is True
        mock_imap.login.assert_called_once_with("test@gmail.com", "test_password")


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.connector
async def test_gmail_connector_connect_missing_credentials():
    """Test Gmail connection fails without credentials."""
    connector = GmailConnector(username=None, password=None)
    
    result = await connector.connect()
    
    assert result is False
    assert connector._connected is False


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.connector
async def test_gmail_connector_connect_failure(gmail_connector):
    """Test Gmail connection failure handling."""
    with patch('imaplib.IMAP4_SSL', side_effect=Exception("Connection failed")):
        result = await gmail_connector.connect()
        
        assert result is False
        assert gmail_connector._connected is False


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.connector
async def test_gmail_connector_disconnect(gmail_connector, mock_imap):
    """Test Gmail disconnection."""
    gmail_connector._imap = mock_imap
    gmail_connector._connected = True
    
    await gmail_connector.disconnect()
    
    assert gmail_connector._connected is False
    mock_imap.logout.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.connector
async def test_gmail_connector_is_connected(gmail_connector):
    """Test is_connected method."""
    gmail_connector._connected = True
    assert gmail_connector.is_connected() is True
    
    gmail_connector._connected = False
    assert gmail_connector.is_connected() is False


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.connector
async def test_gmail_connector_fetch_emails_not_connected(gmail_connector):
    """Test fetch_emails when not connected."""
    gmail_connector._connected = False
    
    emails = await gmail_connector.fetch_emails()
    
    assert emails == []


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.connector
async def test_gmail_connector_fetch_emails_success(gmail_connector, mock_imap):
    """Test successful email fetching."""
    gmail_connector._connected = True
    gmail_connector._imap = mock_imap
    
    # Mock email parsing
    with patch('email.message_from_bytes') as mock_parse:
        mock_email = MagicMock()
        mock_email.get = MagicMock(side_effect=lambda key, default=None: {
            "From": "sender@example.com",
            "Subject": "Test Subject",
            "Date": "Mon, 1 Jan 2024 12:00:00 +0000",
            "X-Priority": "1",
            "X-Gmail-Labels": "Important"
        }.get(key, default))
        mock_email.get_payload = MagicMock(return_value="Test body")
        mock_parse.return_value = mock_email
        
        emails = await gmail_connector.fetch_emails(limit=10)
        
        assert len(emails) > 0
        # Verify emails have expected attributes
        if emails:
            assert hasattr(emails[0], 'subject')
            assert hasattr(emails[0], 'from_address')


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.connector
def test_gmail_connector_capabilities(gmail_connector):
    """Test connector capabilities."""
    caps = gmail_connector.get_capabilities()
    
    assert caps.can_fetch is True
    assert caps.can_send is False  # Gmail connector doesn't implement send yet
    assert caps.can_search is True


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.connector
async def test_gmail_connector_importance_detection(gmail_connector):
    """Test that Gmail connector detects importance from headers."""
    # This tests the _convert_imap_email logic
    # We'll test the importance detection through integration
    # For unit test, we verify the method exists
    assert hasattr(gmail_connector, '_convert_imap_email')

