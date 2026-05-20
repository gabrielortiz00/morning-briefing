import os
import requests


def get_assignments():
    url = os.environ.get('COLLEGE_DASHBOARD_URL', '').rstrip('/')
    api_key = os.environ.get('COLLEGE_DASHBOARD_API_KEY')
    if not url or not api_key:
        return []
    try:
        resp = requests.get(
            f'{url}/api/briefing',
            headers={'X-Briefing-Key': api_key},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get('assignments', [])
    except Exception as e:
        print(f'Assignments error: {e}')
        return []
