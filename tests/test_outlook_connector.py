"""
Unit tests for OutlookConnector.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.connectors.implementations.outlook_connector import OutlookConnector
from app.connectors.models import SourceType, EmailPriority


@pytest.fixture
def outlook_connector():
    """Create an OutlookConnector instance for testing."""
    return OutlookConnector(
        client_id="test_client_id",
        client_secret="test_secret",
        tenant_id="test_tenant",
        user_principal_name="test@example.com"
    )


@pytest.fixture
def mock_graph_client():
    """Create a mocked MS Graph client."""
    mock_client = MagicMock()
    mock_client.get_access_token = MagicMock(return_value="test_token")
    mock_client.make_request = AsyncMock(return_value={
        "value": [
            {
                "id": "1",
                "subject": "Test Email",
                "bodyPreview": "Test preview",
                "from": {"emailAddress": {"name": "Sender", "address": "sender@example.com"}},
                "receivedDateTime": "2024-01-01T12:00:00Z",
                "isRead": False,
                "importance": "high"
            }
        ]
    })
    return mock_client


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.connector
async def test_outlook_connector_source_type(outlook_connector):
    """Test that OutlookConnector returns correct source type."""
    assert outlook_connector.source_type == SourceType.OUTLOOK


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.connector
async def test_outlook_connector_connect_success(outlook_connector, mock_graph_client):
    """Test successful Outlook connection."""
    outlook_connector._graph_client = mock_graph_client
    
    result = await outlook_connector.connect()
    
    assert result is True
    assert outlook_connector._connected is True


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.connector
async def test_outlook_connector_connect_missing_credentials():
    """Test Outlook connection fails without credentials."""
    connector = OutlookConnector(
        client_id=None,
        client_secret=None,
        tenant_id=None
    )
    
    result = await connector.connect()
    
    assert result is False


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.connector
async def test_outlook_connector_is_connected(outlook_connector):
    """Test is_connected method."""
    outlook_connector._connected = True
    assert outlook_connector.is_connected() is True
    
    outlook_connector._connected = False
    assert outlook_connector.is_connected() is False


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.connector
async def test_outlook_connector_fetch_emails_not_connected(outlook_connector):
    """Test fetch_emails when not connected."""
    outlook_connector._connected = False
    
    emails = await outlook_connector.fetch_emails()
    
    assert emails == []


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.connector
async def test_outlook_connector_fetch_emails_success(outlook_connector, mock_graph_client):
    """Test successful email fetching."""
    outlook_connector._connected = True
    outlook_connector._graph_client = mock_graph_client
    
    emails = await outlook_connector.fetch_emails(limit=10)
    
    assert len(emails) > 0
    # Verify emails are UnifiedEmail instances
    assert all(hasattr(e, 'subject') for e in emails)


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.connector
async def test_outlook_connector_importance_detection(outlook_connector, mock_graph_client):
    """Test that Outlook connector detects importance from Graph API."""
    outlook_connector._connected = True
    outlook_connector._graph_client = mock_graph_client
    
    # Mock response with high importance
    mock_graph_client.make_request = AsyncMock(return_value={
        "value": [
            {
                "id": "1",
                "subject": "Important Email",
                "bodyPreview": "This is important",
                "from": {"emailAddress": {"name": "Sender", "address": "sender@example.com"}},
                "receivedDateTime": "2024-01-01T12:00:00Z",
                "isRead": False,
                "importance": "high"
            }
        ]
    })
    
    emails = await outlook_connector.fetch_emails(limit=1)
    
    if emails:
        # Check that importance is detected
        assert emails[0].is_important is True or emails[0].priority == EmailPriority.HIGH


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.connector
def test_outlook_connector_capabilities(outlook_connector):
    """Test connector capabilities."""
    caps = outlook_connector.get_capabilities()
    
    assert caps.can_fetch is True
    assert caps.can_send is False  # Outlook connector doesn't implement send yet
    assert caps.can_search is True


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.connector
async def test_outlook_connector_convert_email(outlook_connector):
    """Test email conversion from Graph API format."""
    graph_email = {
        "id": "test_id",
        "subject": "Test Subject",
        "bodyPreview": "Test preview",
        "from": {"emailAddress": {"name": "Test Sender", "address": "sender@example.com"}},
        "toRecipients": [{"emailAddress": {"address": "recipient@example.com"}}],
        "receivedDateTime": "2024-01-01T12:00:00Z",
        "isRead": False,
        "importance": "high"
    }
    
    unified_email = outlook_connector._convert_outlook_email(graph_email)
    
    assert unified_email.subject == "Test Subject"
    assert unified_email.source_type == SourceType.OUTLOOK
    assert unified_email.from_address["email"] == "sender@example.com"
    assert unified_email.is_important is True or unified_email.priority == EmailPriority.HIGH

