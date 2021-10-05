from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import requests
from django.conf import settings
from django.core.cache import cache


@dataclass
class Location:
    """Location dataclass"""

    latitude: float
    longitude: float

    def __str__(self):
        return f'{self.latitude},{self.longitude}'


class Weather(object):
    """Weather integration class which gets, caches and provides current and
    forecast weather for a specific location.

    Args:
        object (Location): The location (latitude & longitude) to get weather
        data for.
    """

    def __init__(self, location: Location) -> None:
        self.location = location
        self.config = settings.INTEGRATIONS['weather']
        self.cache_prefix = f'{self.__module__}.{self.__class__.__name__}'

    def _build_url(self) -> str:
        base_url, api_key = self.config['url'], self.config['api_key']
        return f'{base_url}?lat={self.location.latitude}&lon={self.location.longitude}&exclude=minutely,hourly&units=metric&appid={api_key}'

    def _get_weather_data(self) -> dict:
        cache_key = f'{self.cache_prefix}._get_weather_data:{self.location}'
        cache_result = cache.get(cache_key)
        if cache_result:
            return cache_result
        else:
            url = self._build_url()
            response = requests.get(url)
            response.raise_for_status()
            weather_data = response.json()
            if weather_data:
                cache.set(cache_key, weather_data)
                return weather_data

    @property
    def current(self) -> Optional[dict]:
        weather_data = self._get_weather_data()
        if weather_data is not None:
            current_weather_data = weather_data['current']
            try:
                return {
                    'humidity': current_weather_data['humidity'],
                    'rain': current_weather_data['weather'][0]['main'] == 'Rain',
                    'temperature': current_weather_data['temp'],
                }
            except (KeyError, IndexError):
                return None

    @property
    def forecast(self) -> Optional[list]:
        weather_data = self._get_weather_data()
        if weather_data is not None:
            forecast_weather_data = weather_data['daily']
            parsed_forecast_weather_data = []
            for forecast in forecast_weather_data:
                try:
                    parsed_forecast_weather_data.append(
                        {
                            'date': datetime.fromtimestamp(forecast['dt']).strftime(
                                '%Y-%m-%d'
                            ),
                            'humidity': forecast.get('humidity', None),
                            'rain': forecast.get('rain', 0) > 0.2,
                            'temperature': {
                                'maximum': forecast['temp']['max'],
                                'minimum': forecast['temp']['min'],
                            },
                        }
                    )
                except (KeyError, IndexError):
                    return None
            return parsed_forecast_weather_data
