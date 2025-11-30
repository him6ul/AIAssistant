"""
Google Calendar connector implementation.
"""

import os
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
from app.utils.logger import get_logger

# Load environment variables
load_dotenv(override=True)

logger = get_logger(__name__)

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


class GoogleCalendarConnector:
    """
    Google Calendar connector to fetch meetings and events.
    """
    
    def __init__(
        self,
        credentials_file: Optional[str] = None,
        token_file: Optional[str] = None,
    ):
        """
        Initialize Google Calendar connector.
        
        Args:
            credentials_file: Path to OAuth2 credentials JSON file
            token_file: Path to store/load OAuth2 token
        """
        # Get path from .env file or use default
        # If path from .env is relative, resolve it relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        
        # Get credentials file path from .env or use default
        env_credentials_file = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_FILE")
        if credentials_file:
            # Explicitly provided path takes precedence
            self.credentials_file = credentials_file
        elif env_credentials_file:
            # Use path from .env file
            creds_path = Path(env_credentials_file)
            if creds_path.is_absolute():
                self.credentials_file = str(creds_path)
            else:
                # Resolve relative path from project root
                self.credentials_file = str(project_root / creds_path)
        else:
            # Default path relative to project root
            self.credentials_file = str(project_root / "config" / "google_calendar_credentials.json")
        
        # Get token file path from .env or use default
        env_token_file = os.getenv("GOOGLE_CALENDAR_TOKEN_FILE")
        if token_file:
            # Explicitly provided path takes precedence
            self.token_file = token_file
        elif env_token_file:
            # Use path from .env file
            token_path = Path(env_token_file)
            if token_path.is_absolute():
                self.token_file = str(token_path)
            else:
                # Resolve relative path from project root
                self.token_file = str(project_root / token_path)
        else:
            # Default path relative to project root
            self.token_file = str(project_root / "config" / "google_calendar_token.pickle")
        
        logger.debug(f"Google Calendar credentials file: {self.credentials_file}")
        logger.debug(f"Google Calendar token file: {self.token_file}")
        self.service = None
        self._credentials = None
    
    def _get_credentials(self) -> Optional[Credentials]:
        """Get valid user credentials from storage or OAuth flow."""
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                logger.warning(f"Error loading token file: {e}")
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed Google Calendar credentials")
                except Exception as e:
                    logger.error(f"Error refreshing credentials: {e}")
                    creds = None
            else:
                if not os.path.exists(self.credentials_file):
                    logger.warning(
                        f"Google Calendar credentials file not found: {self.credentials_file}\n"
                        "Please download OAuth2 credentials from Google Cloud Console and save to this path."
                    )
                    return None
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    logger.info("Obtained new Google Calendar credentials")
                except Exception as e:
                    logger.error(f"Error obtaining credentials: {e}")
                    return None
            
            # Save credentials for next run
            if creds:
                try:
                    os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
                    with open(self.token_file, 'wb') as token:
                        pickle.dump(creds, token)
                    logger.info(f"Saved credentials to {self.token_file}")
                except Exception as e:
                    logger.warning(f"Error saving credentials: {e}")
        
        return creds
    
    async def connect(self) -> bool:
        """Connect to Google Calendar API."""
        try:
            logger.info("🔌 GOOGLE CALENDAR CONNECTOR: Starting connection...")
            
            # Run credential loading in executor (it may do file I/O and network calls)
            loop = asyncio.get_event_loop()
            creds = await loop.run_in_executor(None, self._get_credentials)
            
            if not creds:
                logger.error("❌ Failed to obtain Google Calendar credentials")
                return False
            
            # Build service in executor as well
            def _build_service():
                return build('calendar', 'v3', credentials=creds)
            
            self._credentials = creds
            self.service = await loop.run_in_executor(None, _build_service)
            logger.info("✅ Google Calendar connector connected successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Error connecting to Google Calendar: {e}", exc_info=True)
            return False
    
    def is_connected(self) -> bool:
        """Check if connector is connected."""
        return self.service is not None
    
    async def get_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_results: int = 50,
        calendar_id: str = 'primary'
    ) -> List[Dict[str, Any]]:
        """
        Get events from Google Calendar.
        
        Args:
            start_time: Start time for event query (default: now)
            end_time: End time for event query (default: end of today)
            max_results: Maximum number of events to return
            calendar_id: Calendar ID (default: 'primary')
        
        Returns:
            List of event dictionaries
        """
        if not self.service:
            logger.error("Google Calendar service not initialized")
            return []
        
        try:
            # Default to today if not specified
            if not start_time:
                start_time = datetime.utcnow()
            if not end_time:
                # Default to end of today
                end_time = datetime.utcnow().replace(hour=23, minute=59, second=59)
            
            # Format times for API
            time_min = start_time.isoformat() + 'Z'
            time_max = end_time.isoformat() + 'Z'
            
            logger.info(f"📅 Fetching events from {start_time} to {end_time}")
            
            # Run synchronous Google API call in executor
            loop = asyncio.get_event_loop()
            
            def _fetch_events():
                return self.service.events().list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
            
            events_result = await loop.run_in_executor(None, _fetch_events)
            events = events_result.get('items', [])
            logger.info(f"✅ Found {len(events)} events")
            
            return events
        except HttpError as e:
            logger.error(f"❌ Error fetching events: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching events: {e}", exc_info=True)
            return []
    
    async def get_today_events(self, calendar_id: str = 'primary') -> List[Dict[str, Any]]:
        """
        Get all events for today.
        
        Args:
            calendar_id: Calendar ID (default: 'primary')
        
        Returns:
            List of event dictionaries for today
        """
        now = datetime.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        return await self.get_events(
            start_time=start_of_day,
            end_time=end_of_day,
            calendar_id=calendar_id
        )
    
    async def get_remaining_today_events(self, calendar_id: str = 'primary') -> List[Dict[str, Any]]:
        """
        Get remaining events for today (events that haven't ended yet).
        
        Args:
            calendar_id: Calendar ID (default: 'primary')
        
        Returns:
            List of remaining event dictionaries for today
        """
        now = datetime.utcnow()
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        events = await self.get_events(
            start_time=now,
            end_time=end_of_day,
            calendar_id=calendar_id
        )
        
        # Filter out events that have already ended
        remaining = []
        for event in events:
            end = event.get('end', {})
            
            # Parse end time
            if 'dateTime' in end:
                try:
                    event_end_str = end['dateTime'].replace('Z', '+00:00')
                    event_end = datetime.fromisoformat(event_end_str)
                    # Convert to UTC naive for comparison
                    if event_end.tzinfo:
                        event_end = event_end.replace(tzinfo=None)
                except Exception as e:
                    logger.warning(f"Error parsing event end time: {e}")
                    continue
            elif 'date' in end:
                try:
                    event_end = datetime.fromisoformat(end['date'] + 'T23:59:59+00:00')
                    if event_end.tzinfo:
                        event_end = event_end.replace(tzinfo=None)
                except Exception as e:
                    logger.warning(f"Error parsing event end date: {e}")
                    continue
            else:
                # If no end time, assume it's still active
                remaining.append(event)
                continue
            
            # Check if event hasn't ended yet
            if event_end > now:
                remaining.append(event)
        
        return remaining
    
    def format_event(self, event: Dict[str, Any]) -> str:
        """
        Format an event for display.
        
        Args:
            event: Event dictionary from Google Calendar API
        
        Returns:
            Formatted string representation of the event
        """
        summary = event.get('summary', 'No title')
        start = event.get('start', {})
        end = event.get('end', {})
        location = event.get('location', '')
        
        # Parse start time
        if 'dateTime' in start:
            start_time = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(end.get('dateTime', start['dateTime']).replace('Z', '+00:00'))
            time_str = start_time.strftime('%I:%M %p')
            if start_time.date() == end_time.date():
                end_time_str = end_time.strftime('%I:%M %p')
                time_display = f"{time_str} to {end_time_str}"
            else:
                time_display = f"{time_str} (ends {end_time.strftime('%I:%M %p on %B %d')})"
        elif 'date' in start:
            time_display = "All day"
        else:
            time_display = "Time TBD"
        
        location_str = f" at {location}" if location else ""
        
        return f"{summary} at {time_display}{location_str}"

