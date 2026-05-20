import os
import requests

_COMPASS = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW']

LAT = float(os.environ.get('WEATHER_LAT', '42.3398'))
LON = float(os.environ.get('WEATHER_LON', '-71.0892'))


def get_weather():
    api_key = os.environ.get('OPENWEATHERMAP_API_KEY')
    if not api_key:
        return None
    try:
        resp = requests.get(
            'https://api.openweathermap.org/data/3.0/onecall',
            params={
                'lat': LAT, 'lon': LON,
                'appid': api_key,
                'units': 'imperial',
                'exclude': 'minutely,alerts',
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        current = data['current']
        today = data['daily'][0]

        wind_deg = current.get('wind_deg', 0)
        wind_knots = round(current.get('wind_speed', 0) * 0.868976)
        gust_mph = current.get('wind_gust', 0)
        gust_knots = round(gust_mph * 0.868976) if gust_mph else None

        clouds = current.get('clouds', 0)
        if clouds < 25:
            sky = 'Clear'
        elif clouds < 50:
            sky = 'Few clouds'
        elif clouds < 75:
            sky = 'Scattered'
        else:
            sky = 'Overcast'

        visibility_m = current.get('visibility', 16093)
        visibility_miles = min(round(visibility_m * 0.000621371, 1), 10.0)

        return {
            'temp': round(current['temp']),
            'feels_like': round(current['feels_like']),
            'description': current['weather'][0]['description'].title(),
            'humidity': current['humidity'],
            'wind_speed_knots': wind_knots,
            'wind_dir': _COMPASS[round(wind_deg / 22.5) % 16],
            'wind_deg': wind_deg,
            'gust_knots': gust_knots,
            'visibility_miles': visibility_miles,
            'sky': sky,
            'high': round(today['temp']['max']),
            'low': round(today['temp']['min']),
        }
    except Exception as e:
        print(f'Weather error: {e}')
        return None
