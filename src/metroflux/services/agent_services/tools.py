from datetime import date

# from langchain_tavily import TavilySearch
from langchain_core.tools import tool
import requests

# search = TavilySearch(max_results=3)


def _weather_current(lat: float, lon: float) -> dict:
    """
    Returns only current weather data.
    """
    print("executing weather_current")
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "timezone": "auto",
    }
    return requests.get(url, params=params).json()


def _weather_future(lat: float, lon: float, days: int = 7) -> dict:
    """
    Returns only future forecast (hourly + daily).
    only up to 16 days in future
    """
    print("executing weather_future")
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation",
        "daily": "temperature_2m_max,precipitation_sum",
        "forecast_days": days,
        "timezone": "auto",
    }
    return requests.get(url, params=params).json()


def _weather_past(lat: float, lon: float, start_date: str, end_date: str) -> dict:
    """
    Returns historical reanalysis (hourly) from start_date to end_date.
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    print("executing weather_past")
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,precipitation",
        "timezone": "auto",
    }
    return requests.get(url, params=params).json()


@tool
def weather_summary(
    lat: float, lon: float, start_date: date = None, end_date: date = None
) -> dict:
    """
    Smart wrapper that chooses the right combination of:
    - weather_current
    - weather_past
    - weather_future
    Based on date range.

    Parameters:
    - start_date and end_date are Python `date` objects.
    """
    print("executing weather_summary")
    result = {}
    today = date.today()

    # Case 1: No dates → current only
    if not start_date and not end_date:
        result["current"] = _weather_current(lat, lon)
        return result

    # Case 2: Future only
    if start_date and start_date >= today:
        future_days = (end_date - start_date).days + 1 if end_date else 7
        future_days = min(future_days, 16)  # Max limit
        result["future"] = _weather_future(lat, lon, days=future_days)

    # Case 3: Past only
    if end_date and end_date < today:
        hist_start = start_date if start_date else today
        hist_end = end_date
        result["past"] = _weather_past(
            lat, lon, start_date=hist_start.isoformat(), end_date=hist_end.isoformat()
        )

    # Case 4: Spanning today
    if start_date and end_date and start_date < today and end_date > today:
        # Past: from start to today
        result["past"] = _weather_past(
            lat, lon, start_date=start_date.isoformat(), end_date=today.isoformat()
        )
        # Future: from tomorrow to end_date
        future_days = min((end_date - today).days, 16)
        result["future"] = _weather_future(lat, lon, days=future_days)

    return result
weather_current = tool(_weather_current)
weather_future = tool(_weather_future)
weather_past = tool(_weather_past)
tool_list = [ weather_current, weather_future, weather_past, weather_summary]