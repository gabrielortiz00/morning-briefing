import os
import requests

_TOKEN_URL = 'https://api.prod.whoop.com/oauth/oauth2/token'
_BASE_URL = 'https://api.prod.whoop.com/developer/v1'


def _refresh_access_token():
    resp = requests.post(_TOKEN_URL, data={
        'grant_type': 'refresh_token',
        'client_id': os.environ['WHOOP_CLIENT_ID'],
        'client_secret': os.environ['WHOOP_CLIENT_SECRET'],
        'refresh_token': os.environ['WHOOP_REFRESH_TOKEN'],
        'scope': 'offline read:recovery read:sleep read:cycles read:workout read:profile',
    }, timeout=10)
    resp.raise_for_status()
    tokens = resp.json()
    return tokens['access_token'], tokens.get('refresh_token', os.environ['WHOOP_REFRESH_TOKEN'])


def get_whoop_data():
    if not all(os.environ.get(k) for k in ('WHOOP_CLIENT_ID', 'WHOOP_CLIENT_SECRET', 'WHOOP_REFRESH_TOKEN')):
        return None
    try:
        access_token, new_refresh_token = _refresh_access_token()

        # Persist new refresh token so the workflow can update the GitHub secret
        with open('.whoop_refresh_token', 'w') as f:
            f.write(new_refresh_token)

        headers = {'Authorization': f'Bearer {access_token}'}

        recovery_resp = requests.get(f'{_BASE_URL}/recovery', headers=headers,
                                     params={'limit': 1}, timeout=10)
        recovery_resp.raise_for_status()
        recovery_records = recovery_resp.json().get('records', [])

        sleep_resp = requests.get(f'{_BASE_URL}/activity/sleep', headers=headers,
                                  params={'limit': 1}, timeout=10)
        sleep_resp.raise_for_status()
        sleep_records = sleep_resp.json().get('records', [])

        result = {}

        if recovery_records:
            score = recovery_records[0].get('score', {})
            result['recovery_score'] = score.get('recovery_score')
            result['hrv_rmssd'] = score.get('hrv_rmssd_milli')
            result['resting_hr'] = score.get('resting_heart_rate')
            result['spo2'] = score.get('spo2_percentage')

        if sleep_records:
            score = sleep_records[0].get('score', {})
            result['sleep_performance'] = score.get('sleep_performance_percentage')
            result['sleep_efficiency'] = score.get('sleep_efficiency_percentage')
            stages = score.get('stage_summary', {})
            total_ms = (
                stages.get('total_light_sleep_time_milli', 0) +
                stages.get('total_slow_wave_sleep_time_milli', 0) +
                stages.get('total_rem_sleep_time_milli', 0)
            )
            result['hours_sleep'] = round(total_ms / 3_600_000, 1)

        return result or None
    except Exception as e:
        print(f'WHOOP error: {e}')
        return None
