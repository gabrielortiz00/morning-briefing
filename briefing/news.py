import os
import requests


def get_news():
    api_key = os.environ.get('NEWS_API_KEY')
    if not api_key:
        return []
    try:
        resp = requests.get(
            'https://newsapi.org/v2/top-headlines',
            params={'country': 'us', 'pageSize': 5, 'apiKey': api_key},
            timeout=10,
        )
        resp.raise_for_status()
        articles = resp.json().get('articles', [])
        return [
            {'title': a['title'], 'source': a['source']['name']}
            for a in articles
            if a.get('title') and '[Removed]' not in a['title']
        ][:5]
    except Exception as e:
        print(f'News error: {e}')
        return []
