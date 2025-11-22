"""
Location detection utility.
Uses IP geolocation to detect user's current location.
"""

import httpx
import os
from typing import Optional, Dict, Any
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Cached location to avoid repeated API calls
_cached_location: Optional[Dict[str, Any]] = None


async def get_current_location() -> Optional[str]:
    """
    Get current location using IP geolocation.
    Returns city name or None if detection fails.
    
    Returns:
        City name (e.g., "San Francisco") or None
    """
    global _cached_location
    
    # Check cache first
    if _cached_location:
        city = _cached_location.get("city")
        if city:
            logger.debug(f"Using cached location: {city}")
            return city
    
    # Try multiple free IP geolocation services
    services = [
        _get_location_from_ipapi,
        _get_location_from_ipinfo,
        _get_location_from_ipapi_co,
    ]
    
    for service in services:
        try:
            location_data = await service()
            if location_data and location_data.get("city"):
                _cached_location = location_data
                city = location_data["city"]
                logger.info(f"Detected location: {city}, {location_data.get('country', '')}")
                return city
        except Exception as e:
            logger.debug(f"Location service {service.__name__} failed: {e}")
            continue
    
    logger.warning("Could not detect location from any service")
    return None


async def _get_location_from_ipapi() -> Optional[Dict[str, Any]]:
    """Get location from ip-api.com (free, no API key required)."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://ip-api.com/json/?fields=status,message,city,country,countryCode")
            data = response.json()
            
            if data.get("status") == "success":
                return {
                    "city": data.get("city"),
                    "country": data.get("country"),
                    "country_code": data.get("countryCode")
                }
    except Exception as e:
        logger.debug(f"ip-api.com failed: {e}")
    return None


async def _get_location_from_ipinfo() -> Optional[Dict[str, Any]]:
    """Get location from ipinfo.io (free tier available)."""
    try:
        # Try with token if available, otherwise free tier
        token = os.getenv("IPINFO_TOKEN", "")
        url = f"https://ipinfo.io/json"
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        async with httpx.AsyncClient(timeout=5.0, headers=headers) as client:
            response = await client.get(url)
            data = response.json()
            
            if data.get("city"):
                return {
                    "city": data.get("city"),
                    "country": data.get("country"),
                    "country_code": data.get("country")
                }
    except Exception as e:
        logger.debug(f"ipinfo.io failed: {e}")
    return None


async def _get_location_from_ipapi_co() -> Optional[Dict[str, Any]]:
    """Get location from ipapi.co (free tier available)."""
    try:
        # Try with API key if available
        api_key = os.getenv("IPAPI_KEY", "")
        url = "https://ipapi.co/json/"
        if api_key:
            url += f"?key={api_key}"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            data = response.json()
            
            if data.get("city") and not data.get("error"):
                return {
                    "city": data.get("city"),
                    "country": data.get("country_name"),
                    "country_code": data.get("country_code")
                }
    except Exception as e:
        logger.debug(f"ipapi.co failed: {e}")
    return None


def reset_location_cache():
    """Reset cached location (useful for testing or when location changes)."""
    global _cached_location
    _cached_location = None
    logger.info("Location cache reset")

