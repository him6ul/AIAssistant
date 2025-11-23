"""
Unit tests for WhatsApp connector using mocks.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from app.connectors.implementations.whatsapp_connector import WhatsAppConnector
from app.connectors.models import SourceType, UnifiedMessage


@pytest.fixture
def whatsapp_connector():
    """Create a WhatsApp connector instance for testing."""
    return WhatsAppConnector(
        api_token="test_token",
        phone_number_id="test_phone_id",
        business_account_id="test_business_id",
    )


@pytest.fixture
def mock_httpx_client():
    """Create a mock HTTPX client."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.aclose = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_whatsapp_connector_source_type(whatsapp_connector):
    """Test that connector returns correct source type."""
    assert whatsapp_connector.source_type == SourceType.WHATSAPP


@pytest.mark.asyncio
async def test_whatsapp_connector_connect_success(whatsapp_connector, mock_httpx_client):
    """Test successful connection to WhatsApp API."""
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_httpx_client.get.return_value = mock_response
    
    with patch('app.connectors.implementations.whatsapp_connector.httpx.AsyncClient', return_value=mock_httpx_client):
        result = await whatsapp_connector.connect()
        assert result is True
        assert whatsapp_connector.is_connected() is True


@pytest.mark.asyncio
async def test_whatsapp_connector_connect_failure(whatsapp_connector, mock_httpx_client):
    """Test failed connection to WhatsApp API."""
    # Mock failed response
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_httpx_client.get.return_value = mock_response
    
    with patch('app.connectors.implementations.whatsapp_connector.httpx.AsyncClient', return_value=mock_httpx_client):
        result = await whatsapp_connector.connect()
        assert result is False
        assert whatsapp_connector.is_connected() is False


@pytest.mark.asyncio
async def test_whatsapp_connector_disconnect(whatsapp_connector, mock_httpx_client):
    """Test disconnecting from WhatsApp API."""
    whatsapp_connector._client = mock_httpx_client
    whatsapp_connector._connected = True
    
    await whatsapp_connector.disconnect()
    
    assert whatsapp_connector.is_connected() is False
    mock_httpx_client.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_whatsapp_connector_send_message(whatsapp_connector, mock_httpx_client):
    """Test sending a message via WhatsApp."""
    # Setup
    whatsapp_connector._client = mock_httpx_client
    whatsapp_connector._connected = True
    
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "messages": [{"id": "test_message_id"}]
    }
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.post.return_value = mock_response
    
    # Send message
    result = await whatsapp_connector.send_message(
        content="Test message",
        to_user_id="+1234567890",
    )
    
    # Verify
    assert isinstance(result, UnifiedMessage)
    assert result.source_type == SourceType.WHATSAPP
    assert result.content == "Test message"
    mock_httpx_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_whatsapp_connector_get_capabilities(whatsapp_connector):
    """Test getting connector capabilities."""
    capabilities = whatsapp_connector.get_capabilities()
    
    assert capabilities.can_send is True
    assert capabilities.can_receive is True
    assert capabilities.supports_attachments is True
    assert capabilities.supports_read_receipts is True


@pytest.mark.asyncio
async def test_whatsapp_connector_fetch_messages_stub(whatsapp_connector):
    """Test fetching messages (stub implementation)."""
    whatsapp_connector._connected = True
    
    messages = await whatsapp_connector.fetch_messages(limit=10)
    
    # Stub implementation returns empty list
    assert isinstance(messages, list)
    assert len(messages) == 0


@pytest.mark.asyncio
async def test_whatsapp_connector_subscribe_to_events(whatsapp_connector):
    """Test subscribing to events."""
    callback = AsyncMock()
    
    await whatsapp_connector.subscribe_to_events(callback)
    
    assert len(whatsapp_connector._event_callbacks) == 1
    assert whatsapp_connector._event_callbacks[0] == callback


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

