import requests
from typing import Tuple, Optional


class LocationService:
    def get_coordinates_from_location(self,location: str) -> Optional[Tuple[float, float]]:
        """
        Get latitude and longitude from a location string using Open-Meteo's geocoding API.

        Args:
            location (str): The city/place string like "Chennai" or "Chennai, Tamil Nadu".

        Returns:
            Optional[Tuple[float, float]]: (latitude, longitude) if found, else None
        """
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": location, "count": 1, "language": "en", "format": "json"}

        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            if data.get("results"):
                result = data["results"][0]
                lat = result["latitude"]
                lon = result["longitude"]
                return (lat, lon)
            else:
                print(f"[WARN] No coordinates found for: {location}")
                return None

        except requests.RequestException as e:
            print(f"[ERROR] Failed to fetch coordinates: {e}")
            return None

if __name__ == "__main__":
    location = "Chennai"
    locater = LocationService()
    coordinates = location.get_coordinates_from_location(location)
    if coordinates:
        print(f"Coordinates for {location}: {coordinates}")