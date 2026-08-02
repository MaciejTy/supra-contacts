"""Weather lookups backed by OpenStreetMap Nominatim and Open-Meteo.

Both APIs are free and rate-limited, so every result is cached. Cache keys are
derived from the city name rather than the contact, which means a hundred
contacts living in five cities cost five API calls instead of a hundred.
"""

import logging

import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Nominatim's usage policy requires a descriptive User-Agent identifying the app.
USER_AGENT = "supra-contacts/1.0 (recruitment task)"

REQUEST_TIMEOUT = 5

GEOCODE_CACHE_TTL = 60 * 60 * 24 * 30  # coordinates do not change
WEATHER_CACHE_TTL = 60 * 30  # weather does

# A city that cannot be resolved is cached too, otherwise a single typo in a
# contact's city costs one Nominatim request per page load forever. The TTL is
# short so a genuine API outage does not blacklist a real city for a month.
UNRESOLVED = "unresolved"
UNRESOLVED_CACHE_TTL = 60 * 60


def _cache_key(prefix, city):
    """Normalise the city name so 'Warszawa' and 'warszawa' share one entry."""
    return f"{prefix}:{city.strip().lower()}"


def _cache_get(key):
    """Read from the cache, treating an unavailable cache as a miss.

    Caching is an optimisation; a broken Redis should slow the weather column
    down, not take it out.
    """
    try:
        return cache.get(key)
    except Exception:
        logger.warning("Cache read failed for the key %r", key, exc_info=True)
        return None


def _cache_set(key, value, ttl):
    try:
        cache.set(key, value, ttl)
    except Exception:
        logger.warning("Cache write failed for the key %r", key, exc_info=True)


def geocode_city(city):
    """Return (latitude, longitude) for a city name, or None if it cannot be resolved."""
    key = _cache_key("geo", city)
    cached = _cache_get(key)
    if cached == UNRESOLVED:
        return None
    if cached is not None:
        return cached

    try:
        response = requests.get(
            NOMINATIM_URL,
            params={"q": city, "format": "json", "limit": 1},
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        results = response.json()
    except (requests.RequestException, ValueError):
        logger.warning("Geocoding failed for the city %r", city)
        return None

    if not results:
        _cache_set(key, UNRESOLVED, UNRESOLVED_CACHE_TTL)
        return None

    try:
        coordinates = (float(results[0]["lat"]), float(results[0]["lon"]))
    except (KeyError, TypeError, ValueError):
        logger.warning("Unexpected geocoding payload for the city %r", city)
        return None

    _cache_set(key, coordinates, GEOCODE_CACHE_TTL)
    return coordinates


def get_weather(city):
    """Return current weather for a city as a dict, or None when unavailable."""
    key = _cache_key("weather", city)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    coordinates = geocode_city(city)
    if coordinates is None:
        return None
    latitude, longitude = coordinates

    try:
        response = requests.get(
            OPEN_METEO_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                # current_weather=true does not include humidity,
                # so the fields required by the task are requested explicity
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        current = response.json()["current"]
    except (requests.RequestException, ValueError, KeyError):
        logger.warning("Weather lookup failed for the city %r", city)
        return None

    weather = {
        "temperature": current["temperature_2m"],
        "humidity": current["relative_humidity_2m"],
        "wind_speed": current["wind_speed_10m"],
    }
    _cache_set(key, weather, WEATHER_CACHE_TTL)
    return weather
