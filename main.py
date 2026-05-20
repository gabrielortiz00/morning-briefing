import os
import requests
from datetime import datetime, timezone, date

from briefing.weather import get_weather
from briefing.whoop import get_whoop_data
from briefing.day_calendar import get_calendar_events
from briefing.news import get_news
from briefing.quote import get_quote
from briefing.tasks import get_assignments


def _recovery_color(score):
    if score is None:
        return '#888888'
    if score >= 67:
        return '#22c55e'
    if score >= 34:
        return '#f59e0b'
    return '#ef4444'


def _fmt_time(iso_str):
    if not iso_str:
        return ''
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime('%-I:%M %p')
    except Exception:
        return iso_str


def _urgency_color(days_until):
    if days_until == 0:
        return '#ef4444'
    if days_until == 1:
        return '#f59e0b'
    return '#3b82f6'


def build_html(weather, whoop, events, assignments, news, quote):
    now = datetime.now(timezone.utc)
    day_str = now.strftime('%A, %B %-d, %Y')

    # ── WHOOP section ─────────────────────────────────────────────────────────
    if whoop:
        rec_score = whoop.get('recovery_score')
        rec_color = _recovery_color(rec_score)
        rec_label = f"{rec_score}%" if rec_score is not None else 'N/A'
        sleep_h = f"{whoop.get('hours_sleep', '?')}h"
        sleep_pct = f"{round(whoop.get('sleep_performance', 0))}%" if whoop.get('sleep_performance') else 'N/A'
        hrv = f"{round(whoop.get('hrv_rmssd', 0))}ms" if whoop.get('hrv_rmssd') else 'N/A'
        rhr = f"{round(whoop.get('resting_hr', 0))}bpm" if whoop.get('resting_hr') else 'N/A'
        whoop_html = f'''
    <div style="background:white;border-radius:12px;padding:20px;margin-bottom:16px;border-left:4px solid {rec_color};">
      <h2 style="margin:0 0 14px;font-size:13px;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:0.08em;">Recovery</h2>
      <table style="border-collapse:collapse;width:100%;">
        <tr>
          <td style="padding:0 20px 0 0;white-space:nowrap;">
            <span style="font-size:32px;font-weight:800;color:{rec_color};">{rec_label}</span><br>
            <span style="font-size:11px;color:#888;">Recovery</span>
          </td>
          <td style="padding:0 20px 0 0;white-space:nowrap;">
            <span style="font-size:32px;font-weight:800;color:#111;">{sleep_h}</span><br>
            <span style="font-size:11px;color:#888;">Sleep</span>
          </td>
          <td style="padding:0 20px 0 0;white-space:nowrap;">
            <span style="font-size:32px;font-weight:800;color:#111;">{sleep_pct}</span><br>
            <span style="font-size:11px;color:#888;">Sleep Score</span>
          </td>
          <td style="padding:0 20px 0 0;white-space:nowrap;">
            <span style="font-size:32px;font-weight:800;color:#111;">{hrv}</span><br>
            <span style="font-size:11px;color:#888;">HRV</span>
          </td>
          <td style="padding:0;white-space:nowrap;">
            <span style="font-size:32px;font-weight:800;color:#111;">{rhr}</span><br>
            <span style="font-size:11px;color:#888;">Resting HR</span>
          </td>
        </tr>
      </table>
    </div>'''
    else:
        whoop_html = ''

    # ── Weather section ────────────────────────────────────────────────────────
    if weather:
        gust_str = f' · Gusts to {weather["gust_knots"]}kt' if weather.get('gust_knots') else ''
        vis_str = f'{weather["visibility_miles"]}+ mi' if weather['visibility_miles'] >= 10 else f'{weather["visibility_miles"]} mi'
        weather_html = f'''
    <div style="background:white;border-radius:12px;padding:20px;margin-bottom:16px;">
      <h2 style="margin:0 0 14px;font-size:13px;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:0.08em;">Weather — Boston, MA</h2>
      <p style="margin:0 0 4px;font-size:22px;font-weight:700;color:#111;">{weather["temp"]}°F &nbsp;·&nbsp; {weather["description"]}</p>
      <p style="margin:0 0 14px;font-size:14px;color:#555;">High {weather["high"]}° &nbsp;·&nbsp; Low {weather["low"]}° &nbsp;·&nbsp; Humidity {weather["humidity"]}%</p>
      <div style="background:#f4f4f5;border-radius:8px;padding:12px 16px;">
        <p style="margin:0;font-size:13px;color:#333;line-height:1.7;font-family:monospace;">
          <strong>PILOT BRIEF</strong><br>
          Wind &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{weather["wind_speed_knots"]}kt from {weather["wind_dir"]} ({weather["wind_deg"]}°){gust_str}<br>
          Visibility &nbsp;{vis_str}<br>
          Sky &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{weather["sky"]}
        </p>
      </div>
    </div>'''
    else:
        weather_html = ''

    # ── Calendar section ───────────────────────────────────────────────────────
    if events:
        rows = ''.join(
            f'<tr><td style="padding:8px 16px 8px 0;font-size:13px;color:#888;white-space:nowrap;">'
            f'{_fmt_time(e["start"])} – {_fmt_time(e["end"])}</td>'
            f'<td style="padding:8px 0;font-size:14px;color:#111;font-weight:500;">{e["title"]}</td></tr>'
            for e in events
        )
        calendar_html = f'''
    <div style="background:white;border-radius:12px;padding:20px;margin-bottom:16px;">
      <h2 style="margin:0 0 14px;font-size:13px;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:0.08em;">Today's Schedule</h2>
      <table style="border-collapse:collapse;width:100%;">{rows}</table>
    </div>'''
    else:
        calendar_html = ''

    # ── Assignments section ────────────────────────────────────────────────────
    if assignments:
        rows = ''
        for a in assignments:
            days = a.get('days_until', 0)
            color = _urgency_color(days)
            if days == 0:
                when = 'Today'
            elif days == 1:
                when = 'Tomorrow'
            else:
                due_dt = date.fromisoformat(a['due_date'])
                when = due_dt.strftime('%a %b %-d')
            time_str = f' &nbsp;·&nbsp; {a["due_time"]}' if a.get('due_time') else ''
            atype = a.get('type', 'assignment').title()
            rows += (
                f'<tr>'
                f'<td style="padding:8px 14px 8px 0;white-space:nowrap;">'
                f'<span style="background:{color};color:white;font-size:11px;font-weight:700;padding:2px 8px;border-radius:4px;">{when}</span>'
                f'</td>'
                f'<td style="padding:8px 0;font-size:14px;color:#111;">'
                f'<strong>{a["course_code"]}</strong> — {a["title"]}'
                f'<span style="font-size:12px;color:#888;"> &nbsp;{atype}{time_str}</span>'
                f'</td></tr>'
            )
        assignments_html = f'''
    <div style="background:white;border-radius:12px;padding:20px;margin-bottom:16px;">
      <h2 style="margin:0 0 14px;font-size:13px;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:0.08em;">Upcoming Deadlines</h2>
      <table style="border-collapse:collapse;width:100%;">{rows}</table>
    </div>'''
    else:
        assignments_html = ''

    # ── News section ───────────────────────────────────────────────────────────
    if news:
        items = ''.join(
            f'<li style="margin-bottom:8px;font-size:14px;color:#111;">'
            f'{a["title"]} <span style="color:#888;font-size:12px;">— {a["source"]}</span></li>'
            for a in news
        )
        news_html = f'''
    <div style="background:white;border-radius:12px;padding:20px;margin-bottom:16px;">
      <h2 style="margin:0 0 14px;font-size:13px;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:0.08em;">Top News</h2>
      <ul style="margin:0;padding-left:18px;">{items}</ul>
    </div>'''
    else:
        news_html = ''

    # ── Quote ──────────────────────────────────────────────────────────────────
    if quote:
        quote_html = f'''
    <div style="padding:20px;text-align:center;">
      <p style="margin:0 0 6px;font-size:15px;color:#444;font-style:italic;">"{quote["text"]}"</p>
      <p style="margin:0;font-size:13px;color:#888;">— {quote["author"]}</p>
    </div>'''
    else:
        quote_html = ''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#f4f4f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;">
  <div style="max-width:600px;margin:0 auto;padding:24px 16px;">

    <div style="margin-bottom:24px;">
      <h1 style="margin:0;font-size:26px;font-weight:800;color:#111;">Good morning, Gabriel</h1>
      <p style="margin:4px 0 0;font-size:14px;color:#888;">{day_str}</p>
    </div>

    {whoop_html}
    {weather_html}
    {calendar_html}
    {assignments_html}
    {news_html}
    {quote_html}

  </div>
</body>
</html>'''


def send_email(html, subject):
    api_key = os.environ.get('RESEND_API_KEY')
    if not api_key:
        raise RuntimeError('RESEND_API_KEY not set')
    resp = requests.post(
        'https://api.resend.com/emails',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        json={
            'from': 'morning@gabrielortiz.io',
            'to': 'gabriel@gabrielortiz.io',
            'subject': subject,
            'html': html,
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def main():
    print('Fetching data...')
    weather = get_weather()
    whoop = get_whoop_data()
    events = get_calendar_events()
    assignments = get_assignments()
    news = get_news()
    quote = get_quote()

    now = datetime.now(timezone.utc)
    subject = f"Morning Briefing — {now.strftime('%A, %B %-d')}"

    html = build_html(weather, whoop, events, assignments, news, quote)
    result = send_email(html, subject)
    print(f'Sent: {result}')


if __name__ == '__main__':
    main()
