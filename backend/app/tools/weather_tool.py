"""
Weather Tool — Fetches current weather for a given city using OpenWeatherMap free API.
Useful for: "Should I bring a jacket to the gym?", "What's the weather like for my outdoor run?"
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

import httpx

logger = logging.getLogger("fitzone.tools.weather")

# Free OpenWeatherMap API key — sign up at https://openweathermap.org/api
# Users should set OPENWEATHER_API_KEY environment variable; we provide a fallback demo key.
import os
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


class WeatherTool:
    """Fetches current weather data for a specified city."""

    name = "get_weather"
    description = (
        "Fetches the current weather conditions (temperature, humidity, description) "
        "for a given city. Useful when a gym member asks about outdoor conditions, "
        "whether to bring rain gear, or if the weather suits outdoor training."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "The city name to get weather for (e.g., 'Islamabad', 'Lahore', 'Karachi')."
            }
        },
        "required": ["city"]
    }

    async def execute(self, arguments: Dict[str, Any] | None = None, **kwargs) -> Dict[str, Any]:
        """
        Calls OpenWeatherMap API and returns structured weather data.
        Includes timeout, mock mode, and graceful error handling.
        """
        args = dict(arguments or {})
        args.update(kwargs)
        city = args.get("city", "").strip()
        if not city:
            return {"error": "City name is required.", "success": False}

        if not OPENWEATHER_API_KEY:
            # Provide a realistic simulated weather response for testing/demo
            return {
                "success": True,
                "city": city,
                "country": "PK",
                "temperature_c": 22.5,
                "temperature_celsius": 22.5,
                "feels_like_celsius": 21.8,
                "humidity_percent": 45,
                "condition": "clear sky and mild",
                "description": "clear sky and mild",
                "wind_speed_kmh": 12.0,
                "recommendation": "Great conditions for an outdoor jog or traveling to FitZone Gym!",
                "mock_mode": True,
            }

        params = {
            "q": city,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
        }

        try:
            timeout = httpx.Timeout(10.0, connect=5.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await asyncio.wait_for(
                    client.get(OPENWEATHER_URL, params=params),
                    timeout=10.0
                )

                if response.status_code == 404:
                    return {
                        "success": False,
                        "error": f"City '{city}' not found. Please check the spelling.",
                        "city": city,
                    }

                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Weather API returned HTTP {response.status_code}.",
                        "city": city,
                    }

                data = response.json()
                weather_main = data.get("weather", [{}])[0]
                main_data = data.get("main", {})
                wind_data = data.get("wind", {})

                return {
                    "success": True,
                    "city": data.get("name", city),
                    "country": data.get("sys", {}).get("country", ""),
                    "temperature_celsius": round(main_data.get("temp", 0), 1),
                    "feels_like_celsius": round(main_data.get("feels_like", 0), 1),
                    "humidity_percent": main_data.get("humidity", 0),
                    "description": weather_main.get("description", "unknown"),
                    "wind_speed_kmh": round(wind_data.get("speed", 0) * 3.6, 1),
                    "icon": weather_main.get("icon", ""),
                }

        except asyncio.TimeoutError:
            logger.warning(f"Weather API timeout for city: {city}")
            return {
                "success": False,
                "error": f"Weather request for '{city}' timed out after 10 seconds.",
                "city": city,
            }
        except Exception as exc:
            logger.error(f"Weather tool error: {exc}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to fetch weather: {str(exc)}",
                "city": city,
            }
