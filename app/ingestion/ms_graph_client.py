"""
Microsoft Graph API client for Office 365 integration.
"""

import os
from typing import Optional, Dict, Any, List
from msal import ConfidentialClientApplication
import httpx
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MSGraphClient:
    """
    Microsoft Graph API client for authentication and API calls.
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tenant_id: str,
        redirect_uri: str = "http://localhost:8000/auth/callback"
    ):
        """
        Initialize Microsoft Graph client.
        
        Args:
            client_id: Azure AD application client ID
            client_secret: Azure AD application client secret
            tenant_id: Azure AD tenant ID
            redirect_uri: OAuth redirect URI
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.redirect_uri = redirect_uri
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
        
        # Initialize MSAL app
        self.app = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=self.authority
        )
        
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None
    
    def get_auth_url(self, scopes: List[str] = None) -> str:
        """
        Get authorization URL for user consent.
        
        Args:
            scopes: OAuth scopes (defaults to common Graph scopes)
        
        Returns:
            Authorization URL
        """
        if scopes is None:
            scopes = [
                "https://graph.microsoft.com/Mail.Read",
                "https://graph.microsoft.com/Notes.Read",
                "https://graph.microsoft.com/User.Read"
            ]
        
        auth_url = self.app.get_authorization_request_url(
            scopes=scopes,
            redirect_uri=self.redirect_uri
        )
        
        return auth_url[0]  # Returns tuple (url, state)
    
    def acquire_token_by_authorization_code(self, code: str, scopes: List[str] = None) -> Dict[str, Any]:
        """
        Acquire access token using authorization code.
        
        Args:
            code: Authorization code from callback
            scopes: OAuth scopes
        
        Returns:
            Token response
        """
        if scopes is None:
            scopes = [
                "https://graph.microsoft.com/Mail.Read",
                "https://graph.microsoft.com/Notes.Read",
                "https://graph.microsoft.com/User.Read"
            ]
        
        result = self.app.acquire_token_by_authorization_code(
            code=code,
            scopes=scopes,
            redirect_uri=self.redirect_uri
        )
        
        if "access_token" in result:
            self._access_token = result["access_token"]
            self._token_expires_at = result.get("expires_in", 3600) + self._get_current_time()
            logger.info("Access token acquired successfully")
        else:
            logger.error(f"Failed to acquire token: {result.get('error_description', 'Unknown error')}")
        
        return result
    
    def acquire_token_client_credentials(self, scopes: List[str] = None) -> Dict[str, Any]:
        """
        Acquire access token using client credentials (app-only).
        
        Args:
            scopes: OAuth scopes
        
        Returns:
            Token response
        """
        if scopes is None:
            scopes = [
                "https://graph.microsoft.com/Mail.Read",
                "https://graph.microsoft.com/Notes.Read"
            ]
        
        result = self.app.acquire_token_for_client(scopes=scopes)
        
        if "access_token" in result:
            self._access_token = result["access_token"]
            self._token_expires_at = result.get("expires_in", 3600) + self._get_current_time()
            logger.info("Client credentials token acquired successfully")
        else:
            logger.error(f"Failed to acquire token: {result.get('error_description', 'Unknown error')}")
        
        return result
    
    def get_access_token(self) -> Optional[str]:
        """
        Get current access token, refreshing if necessary.
        
        Returns:
            Access token or None
        """
        import time
        
        # Check if token is expired or missing
        if not self._access_token or (self._token_expires_at and time.time() >= self._token_expires_at - 60):
            logger.info("Token expired or missing, acquiring new token")
            self.acquire_token_client_credentials()
        
        return self._access_token
    
    async def make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make a request to Microsoft Graph API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (relative to graph_endpoint)
            params: Query parameters
            json_data: JSON body data
        
        Returns:
            Response JSON
        """
        token = self.get_access_token()
        if not token:
            raise Exception("No access token available")
        
        url = f"{self.graph_endpoint}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    def _get_current_time(self) -> float:
        """Get current Unix timestamp."""
        import time
        return time.time()


# Global client instance
_graph_client: Optional[MSGraphClient] = None


def get_graph_client() -> MSGraphClient:
    """
    Get or create the global Microsoft Graph client instance.
    
    Returns:
        MSGraphClient instance
    """
    global _graph_client
    if _graph_client is None:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        client_id = os.getenv("MS_CLIENT_ID", "")
        client_secret = os.getenv("MS_CLIENT_SECRET", "")
        tenant_id = os.getenv("MS_TENANT_ID", "")
        
        # Check if credentials are configured
        if not client_id or not client_secret or not tenant_id or tenant_id == "your_azure_tenant_id_here":
            logger.warning("Microsoft Graph credentials not configured. O365 features will be disabled.")
            return None
        
        try:
            _graph_client = MSGraphClient(
                client_id=client_id,
                client_secret=client_secret,
                tenant_id=tenant_id,
                redirect_uri=os.getenv("MS_REDIRECT_URI", "http://localhost:8000/auth/callback")
            )
        except Exception as e:
            logger.error(f"Failed to initialize Microsoft Graph client: {e}")
            return None
    return _graph_client

