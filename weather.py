"""
Weather API Integration
Fetches weather data for golf course location and date
"""

import requests
from datetime import datetime, timedelta
import json


class WeatherService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
        
    def get_weather_for_round(self, location, round_date):
        """
        Get weather conditions for the golf round
        Returns dict with temperature, wind, precipitation
        """
        # Check if round date is in the past or future
        days_diff = (round_date.date() - datetime.now().date()).days
        
        if abs(days_diff) <= 1:
            # Current or yesterday/tomorrow - use current weather
            return self._get_current_weather(location)
        elif days_diff < -5:
            # More than 5 days ago - use historical (requires paid API)
            # For free tier, we'll use current weather as approximation
            return self._get_current_weather(location)
        else:
            # Future date - use forecast
            return self._get_forecast_weather(location, days_diff)
    
    def _get_current_weather(self, location):
        """Get current weather conditions"""
        try:
            url = f"{self.base_url}/weather"
            params = {
                'q': location,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'temperature': data['main']['temp'],
                'wind_speed': data['wind']['speed'] * 3.6,  # Convert m/s to km/h
                'wind_gust': data['wind'].get('gust', 0) * 3.6,
                'precipitation': data.get('rain', {}).get('1h', 0),
                'description': data['weather'][0]['description'],
                'humidity': data['main']['humidity']
            }
        except Exception as e:
            print(f"Weather API error: {e}")
            # Return default conditions if API fails
            return self._get_default_weather()
    
    def _get_forecast_weather(self, location, days_ahead):
        """Get forecast weather (up to 5 days)"""
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'q': location,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Find forecast closest to the round date
            # Forecast is in 3-hour intervals
            target_index = min(days_ahead * 8, len(data['list']) - 1)
            forecast = data['list'][target_index]
            
            return {
                'temperature': forecast['main']['temp'],
                'wind_speed': forecast['wind']['speed'] * 3.6,
                'wind_gust': forecast['wind'].get('gust', 0) * 3.6,
                'precipitation': forecast.get('rain', {}).get('3h', 0) / 3,  # Per hour
                'description': forecast['weather'][0]['description'],
                'humidity': forecast['main']['humidity']
            }
        except Exception as e:
            print(f"Weather forecast error: {e}")
            return self._get_default_weather()
    
    def _get_default_weather(self):
        """Return default weather conditions if API fails"""
        return {
            'temperature': 20.0,
            'wind_speed': 10.0,
            'wind_gust': 15.0,
            'precipitation': 0.0,
            'description': 'unknown',
            'humidity': 60
        }
    
    def get_weather_difficulty_factor(self, weather_data):
        """
        Calculate weather difficulty factor for handicap adjustment
        Returns multiplier (1.0 = normal, >1.0 = harder conditions)
        """
        factor = 1.0
        
        # Wind adjustment
        wind = weather_data['wind_speed']
        if wind > 30:  # Strong wind
            factor += 0.15
        elif wind > 20:  # Moderate wind
            factor += 0.08
        elif wind > 15:  # Light wind
            factor += 0.03
        
        # Temperature adjustment
        temp = weather_data['temperature']
        if temp < 5:  # Very cold
            factor += 0.10
        elif temp < 10:  # Cold
            factor += 0.05
        elif temp > 35:  # Very hot
            factor += 0.08
        elif temp > 30:  # Hot
            factor += 0.04
        
        # Rain adjustment
        rain = weather_data['precipitation']
        if rain > 5:  # Heavy rain
            factor += 0.20
        elif rain > 2:  # Moderate rain
            factor += 0.10
        elif rain > 0.5:  # Light rain
            factor += 0.05
        
        return round(factor, 2)


if __name__ == "__main__":
    # Test the weather service
    # You'll need to add your API key to test
    api_key = "YOUR_API_KEY"  # Get from openweathermap.org
    
    service = WeatherService(api_key)
    location = "Warringah, Sydney, NSW, Australia"
    round_date = datetime(2025, 12, 5)
    
    weather = service.get_weather_for_round(location, round_date)
    print("Weather Conditions:")
    print(f"  Temperature: {weather['temperature']}°C")
    print(f"  Wind: {weather['wind_speed']} km/h (gusts: {weather['wind_gust']} km/h)")
    print(f"  Rain: {weather['precipitation']} mm/h")
    print(f"  Description: {weather['description']}")
    print(f"  Humidity: {weather['humidity']}%")
    
    difficulty = service.get_weather_difficulty_factor(weather)
    print(f"\nWeather Difficulty Factor: {difficulty}x")
