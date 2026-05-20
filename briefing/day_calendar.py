import os
import json
from datetime import datetime, timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

_SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def get_calendar_events():
    token_json = os.environ.get('GOOGLE_CALENDAR_TOKEN')
    if not token_json:
        return []
    try:
        creds = Credentials.from_authorized_user_info(json.loads(token_json), _SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open('.google_token.json', 'w') as f:
                f.write(creds.to_json())

        service = build('calendar', 'v3', credentials=creds)
        now = datetime.now(timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = now.replace(hour=23, minute=59, second=59, microsecond=0)

        result = service.events().list(
            calendarId='primary',
            timeMin=day_start.isoformat(),
            timeMax=day_end.isoformat(),
            singleEvents=True,
            orderBy='startTime',
        ).execute()

        events = []
        for item in result.get('items', []):
            start_raw = item['start'].get('dateTime', item['start'].get('date'))
            end_raw = item['end'].get('dateTime', item['end'].get('date'))
            events.append({
                'title': item.get('summary', 'Untitled'),
                'start': start_raw,
                'end': end_raw,
                'location': item.get('location', ''),
            })
        return events
    except Exception as e:
        print(f'Calendar error: {e}')
        return []
