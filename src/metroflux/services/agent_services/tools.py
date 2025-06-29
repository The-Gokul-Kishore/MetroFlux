from langchain_tavily import TavilySearch

from langchain_core.tools import tool
import requests

search = TavilySearch(max_results=3)


@tool
def weather_current(lat: float, lon: float) -> dict:
    """
    Returns only current weather data.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "timezone": "auto",
    }
    return requests.get(url, params=params).json()


@tool
def weather_future(lat: float, lon: float, days: int = 7) -> dict:
    """
    Returns only future forecast (hourly + daily).
    only up to 16 days in future
    """
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


@tool
def weather_past(lat: float, lon: float, start_date: str, end_date: str) -> dict:
    """
    Returns historical reanalysis (hourly) from start_date to end_date.
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
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
    lat: float, lon: float, start_date: str = None, end_date: str = None
) -> dict:
    """
    Returns:
      • Just current if no dates.
      • Future if start_date ≥ today.
      • Past if end_date ≤ today.
      • Both if range spans before and after today.
      only 16days to future but till 1940AD in past
    """
    from datetime import date

    today = date.today().isoformat()
    result = {}

    # 1. No dates → current only
    if not start_date and not end_date:
        result["current"] = weather_current(lat, lon)
        return result

    # 2. Future forecast
    if not start_date or start_date > today:
        result["future"] = weather_future(lat, lon)

    # 3. Historical data
    hist_start = start_date if start_date else today
    hist_end = min(end_date, today) if end_date else today
    if hist_start <= hist_end:
        result["past"] = weather_past(lat, lon, hist_start, hist_end)

    return result

tool_list = [search, weather_current, weather_future, weather_past, weather_summary]