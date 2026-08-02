"""Tests for the weather service, with external APIs mocked out."""

from unittest.mock import patch

import pytest
from django.core.cache import cache

from contacts.services import geocode_city, get_weather


@pytest.fixture(autouse=True)
def clear_cache():
    """LocMemCache persists between tests, so reset it before each one."""
    cache.clear()


@patch("contacts.services.requests.get")
def test_geocode_city_caches_result(mock_get):
    """A city is geocoded once; the second call is served from the cache."""
    mock_get.return_value.json.return_value = [{"lat": "52.23", "lon": "21.01"}]

    first = geocode_city("Warszawa")
    second = geocode_city("Warszawa")

    assert first == (52.23, 21.01)
    assert second == first
    assert mock_get.call_count == 1


@patch("contacts.services.requests.get")
def test_geocode_city_normalises_name(mock_get):
    """Different spellings of the same city share one cache entry."""
    mock_get.return_value.json.return_value = [{"lat": "52.23", "lon": "21.01"}]

    geocode_city("Warszawa")
    geocode_city("  warszawa  ")

    assert mock_get.call_count == 1


@patch("contacts.services.requests.get")
def test_get_weather_returns_none_for_unknown_city(mock_get):
    """An unresolvable city must not raise: the page still has to render."""
    mock_get.return_value.json.return_value = []

    assert get_weather("Nonexistentville") is None


@patch("contacts.services.requests.get")
def test_unresolvable_city_is_cached(mock_get):
    """A typo in a city must not cost one Nominatim call per page load."""
    mock_get.return_value.json.return_value = []

    for _ in range(3):
        assert get_weather("Nonexistentville") is None

    assert mock_get.call_count == 1


@patch("contacts.services.requests.get")
def test_broken_cache_falls_back_to_a_direct_lookup(mock_get):
    """An unreachable cache must slow the lookup down, not break it."""
    mock_get.return_value.json.side_effect = [
        [{"lat": "54.35", "lon": "18.64"}],
        {
            "current": {
                "temperature_2m": 18.2,
                "relative_humidity_2m": 70,
                "wind_speed_10m": 7.1,
            }
        },
    ]

    with patch.object(cache, "get", side_effect=ConnectionError), patch.object(
        cache, "set", side_effect=ConnectionError
    ):
        weather = get_weather("Gdańsk")

    assert weather == {"temperature": 18.2, "humidity": 70, "wind_speed": 7.1}
