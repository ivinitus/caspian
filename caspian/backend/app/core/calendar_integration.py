import os
import datetime
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.pickle")


def get_calendar_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)
    return build("calendar", "v3", credentials=creds)


def add_event(summary, start_dt, end_dt=None, description=None):
    service = get_calendar_service()
    event = {
        "summary": summary,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": (end_dt or (start_dt + datetime.timedelta(hours=1))).isoformat(), "timeZone": "UTC"},
    }
    if description:
        event["description"] = description
    created = service.events().insert(calendarId="primary", body=event).execute()
    return created.get("htmlLink")


def list_upcoming_events(max_results=10):
    service = get_calendar_service()
    now = datetime.datetime.utcnow().isoformat() + "Z"
    events_result = service.events().list(calendarId="primary", timeMin=now,
                                          maxResults=max_results, singleEvents=True,
                                          orderBy="startTime").execute()
    return events_result.get("items", [])
