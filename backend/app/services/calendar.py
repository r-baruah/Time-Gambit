import datetime
from typing import List, Dict, Optional
import os.path
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.config import settings

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Token file path
TOKEN_FILE = 'token.json'

class GoogleCalendarService:
    def __init__(self):
        self.creds = None
        self.service = None
        self._try_load_existing_token()

    def _get_client_config(self):
        """Returns the OAuth client configuration."""
        return {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "project_id": "hackathon-agent",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
            }
        }

    def _try_load_existing_token(self):
        """Try to load existing token from file."""
        if os.path.exists(TOKEN_FILE):
            self.creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            
            # Refresh if expired
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                    self._save_token()
                except Exception as e:
                    print(f"[CALENDAR] Token refresh failed: {e}")
                    self.creds = None
                    
            if self.creds and self.creds.valid:
                self.service = build('calendar', 'v3', credentials=self.creds)

    def _save_token(self):
        """Save credentials to token file."""
        with open(TOKEN_FILE, 'w') as token:
            token.write(self.creds.to_json())

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.creds is not None and self.creds.valid

    def get_auth_url(self) -> str:
        """Generate Google OAuth URL for frontend redirect."""
        flow = Flow.from_client_config(
            self._get_client_config(),
            scopes=SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return auth_url

    def handle_callback(self, code: str) -> bool:
        """Exchange authorization code for tokens."""
        try:
            flow = Flow.from_client_config(
                self._get_client_config(),
                scopes=SCOPES,
                redirect_uri=settings.GOOGLE_REDIRECT_URI
            )
            flow.fetch_token(code=code)
            self.creds = flow.credentials
            self._save_token()
            self.service = build('calendar', 'v3', credentials=self.creds)
            return True
        except Exception as e:
            print(f"[CALENDAR] Token exchange failed: {e}")
            return False

    def list_events(self, time_min=None, time_max=None, max_results=10):
        """Lists events."""
        if not time_min:
            time_min = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            
        events_result = self.service.events().list(
            calendarId='primary', 
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])

    def create_event(self, summary: str, start_time: str, end_time: str, description: str = ""):
        """Creates an event."""
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC', # adjust as needed or pass in
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'UTC',
            },
        }
        event = self.service.events().insert(calendarId='primary', body=event).execute()
        return event

    def check_availability(self, start_time: datetime.datetime, end_time: datetime.datetime) -> bool:
        """
        Simple boolean check if a slot is free.
        """
        time_min = start_time.isoformat() + 'Z'
        time_max = end_time.isoformat() + 'Z'
        
        events = self.list_events(time_min=time_min, time_max=time_max)
        return len(events) == 0

calendar_service = GoogleCalendarService()
