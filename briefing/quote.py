import requests


def get_quote():
    try:
        resp = requests.get('https://zenquotes.io/api/random', timeout=10)
        resp.raise_for_status()
        item = resp.json()[0]
        return {'text': item['q'], 'author': item['a']}
    except Exception as e:
        print(f'Quote error: {e}')
        return None
