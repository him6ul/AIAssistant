"""
Network detection and status management.
Detects network connectivity and determines if online services are available.
"""

import asyncio
import aiohttp
from typing import Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NetworkMonitor:
    """
    Monitors network connectivity and determines if online services are available.
    """
    
    def __init__(
        self,
        check_interval: int = 30,
        timeout: int = 5,
        retry_attempts: int = 3,
        test_urls: Optional[list] = None
    ):
        """
        Initialize network monitor.
        
        Args:
            check_interval: Seconds between network checks
            timeout: Timeout for network requests in seconds
            retry_attempts: Number of retry attempts
            test_urls: List of URLs to test connectivity (defaults to common services)
        """
        self.check_interval = check_interval
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.test_urls = test_urls or [
            "https://www.google.com",
            "https://api.openai.com",
            "https://graph.microsoft.com"
        ]
        self._is_online: Optional[bool] = None
        self._last_check: Optional[float] = None
        self._monitoring = False
    
    async def check_connectivity(self) -> bool:
        """
        Check if network connectivity is available.
        
        Returns:
            True if online, False otherwise
        """
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            for url in self.test_urls:
                for attempt in range(self.retry_attempts):
                    try:
                        async with session.get(url) as response:
                            if response.status < 500:
                                logger.debug(f"Network check successful: {url}")
                                return True
                    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                        logger.debug(f"Network check failed (attempt {attempt + 1}/{self.retry_attempts}): {url} - {e}")
                        if attempt < self.retry_attempts - 1:
                            await asyncio.sleep(1)
                        continue
        
        logger.warning("All network connectivity checks failed")
        return False
    
    async def is_online(self, force_check: bool = False) -> bool:
        """
        Get current online status, with caching.
        
        Args:
            force_check: Force a new network check
        
        Returns:
            True if online, False otherwise
        """
        import time
        
        current_time = time.time()
        
        # Return cached result if recent and not forcing check
        if not force_check and self._is_online is not None and self._last_check:
            time_since_check = current_time - self._last_check
            if time_since_check < self.check_interval:
                return self._is_online
        
        # Perform new check
        self._is_online = await self.check_connectivity()
        self._last_check = current_time
        
        status = "ONLINE" if self._is_online else "OFFLINE"
        logger.info(f"Network status: {status}")
        
        return self._is_online
    
    async def start_monitoring(self):
        """
        Start continuous network monitoring in the background.
        """
        if self._monitoring:
            logger.warning("Network monitoring already started")
            return
        
        self._monitoring = True
        logger.info("Starting network monitoring")
        
        while self._monitoring:
            await self.is_online(force_check=True)
            await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """
        Stop network monitoring.
        """
        self._monitoring = False
        logger.info("Stopped network monitoring")
    
    def get_status(self) -> dict:
        """
        Get current network status information.
        
        Returns:
            Dictionary with status information
        """
        return {
            "is_online": self._is_online,
            "last_check": self._last_check,
            "monitoring": self._monitoring
        }


# Global network monitor instance
_network_monitor: Optional[NetworkMonitor] = None


def get_network_monitor() -> NetworkMonitor:
    """
    Get or create the global network monitor instance.
    
    Returns:
        NetworkMonitor instance
    """
    global _network_monitor
    if _network_monitor is None:
        _network_monitor = NetworkMonitor()
    return _network_monitor

