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

# Tokens directory path
TOKENS_DIR = 'tokens'

class GoogleCalendarService:
    def __init__(self):
        if not os.path.exists(TOKENS_DIR):
            os.makedirs(TOKENS_DIR)

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

    def _get_token_path(self, user_id: str) -> str:
        return os.path.join(TOKENS_DIR, f"{user_id}.json")

    def _get_credentials(self, user_id: str) -> Optional[Credentials]:
        """Load credentials for a specific user."""
        token_path = self._get_token_path(user_id)
        creds = None
        
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception as e:
                print(f"[CALENDAR] Error loading token for {user_id}: {e}")
                return None
            
        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"[CALENDAR] Token refresh failed for {user_id}: {e}")
                creds = None
                
        return creds

    def _build_service(self, user_id: str):
        """Builds the service for a specific user on demand."""
        creds = self._get_credentials(user_id)
        if creds and creds.valid:
            return build('calendar', 'v3', credentials=creds)
        return None

    def is_authenticated(self, user_id: str) -> bool:
        """Check if user is authenticated."""
        creds = self._get_credentials(user_id)
        return creds is not None and creds.valid

    def get_auth_url(self, user_id: str) -> str:
        """Generate Google OAuth URL for frontend redirect with user_id in state."""
        flow = Flow.from_client_config(
            self._get_client_config(),
            scopes=SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        # Pass user_id as state so we know who authorized it on callback
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=user_id  
        )
        return auth_url

    def handle_callback(self, code: str, state: str) -> bool:
        """Exchange authorization code for tokens and save for the user (state)."""
        user_id = state
        log_file = os.path.join(os.getcwd(), 'auth_debug.log')
        
        try:
            with open(log_file, 'a') as f:
                f.write(f"[{datetime.datetime.now()}] [Start] handle_callback for user: {user_id}\n")
                
            flow = Flow.from_client_config(
                self._get_client_config(),
                scopes=SCOPES,
                redirect_uri=settings.GOOGLE_REDIRECT_URI,
                state=state
            )
            flow.fetch_token(code=code)
            creds = flow.credentials
            
            # Save token
            token_path = self._get_token_path(user_id)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
            
            with open(log_file, 'a') as f:
                f.write(f"[{datetime.datetime.now()}] [Success] Token saved to {token_path}\n")
                
            return True
        except Exception as e:
            with open(log_file, 'a') as f:
                f.write(f"[{datetime.datetime.now()}] [Error] Token exchange failed: {e}\n")
            print(f"[CALENDAR] Token exchange failed: {e}")
            return False

    def list_events(self, user_id: str, time_min=None, time_max=None, max_results=10):
        """Lists events for a specific user."""
        service = self._build_service(user_id)
        if not service:
            print(f"[CALENDAR] No service for {user_id}")
            return []

        if not time_min:
            time_min = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])

    def create_event(self, user_id: str, summary: str, start_time: str, end_time: str, description: str = ""):
        """Creates an event for a specific user."""
        service = self._build_service(user_id)
        if not service:
            raise Exception("User not authenticated")

        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC', 
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'UTC',
            },
        }
        event = service.events().insert(calendarId='primary', body=event).execute()
        return event

    def check_availability(self, user_id: str, start_time: datetime.datetime, end_time: datetime.datetime) -> bool:
        """
        Simple boolean check if a slot is free.
        """
        time_min = start_time.isoformat() + 'Z'
        time_max = end_time.isoformat() + 'Z'
        
        events = self.list_events(user_id, time_min=time_min, time_max=time_max)
        return len(events) == 0

calendar_service = GoogleCalendarService()
