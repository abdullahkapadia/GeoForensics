"""
GeoForensics AI — Google Maps Platform Integration Service.
Provides live geocoding, reverse geocoding, and place details with offline fallback.
"""

import json
import urllib.parse
import urllib.request
from typing import Optional, Dict, Any
from app.core.config import settings

class GoogleMapsService:
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY.strip() if settings.GOOGLE_MAPS_API_KEY else ""

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def reverse_geocode(self, lat: float, lng: float) -> Optional[Dict[str, Any]]:
        """
        Reverse geocode latitude and longitude to a structured address.
        """
        if not self.is_configured():
            return None

        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={self.api_key}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "GeoForensicsAI/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                if data.get("status") == "OK" and data.get("results"):
                    first = data["results"][0]
                    formatted = first.get("formatted_address")
                    components = first.get("address_components", [])

                    city = ""
                    state = ""
                    country = ""
                    country_code = ""

                    for comp in components:
                        types = comp.get("types", [])
                        if "locality" in types:
                            city = comp.get("long_name", "")
                        elif "administrative_area_level_1" in types:
                            state = comp.get("long_name", "")
                        elif "country" in types:
                            country = comp.get("long_name", "")
                            country_code = comp.get("short_name", "")

                    return {
                        "formatted_address": formatted,
                        "city": city,
                        "state_province": state,
                        "country": country,
                        "country_code": country_code,
                        "place_id": first.get("place_id"),
                        "raw": first
                    }
        except Exception as e:
            # Silently fallback to offline resolution
            print(f"[GoogleMapsService] Geocoding notice: {e}")

        return None

    def search_place(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Search for a place by text query using Google Places API.
        """
        if not self.is_configured() or not query.strip():
            return None

        encoded = urllib.parse.quote(query.strip())
        url = (
            f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
            f"?input={encoded}&inputtype=textquery"
            f"&fields=formatted_address,name,geometry,place_id"
            f"&key={self.api_key}"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "GeoForensicsAI/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                if data.get("status") == "OK" and data.get("candidates"):
                    candidate = data["candidates"][0]
                    loc = candidate.get("geometry", {}).get("location", {})
                    return {
                        "name": candidate.get("name"),
                        "formatted_address": candidate.get("formatted_address"),
                        "lat": loc.get("lat"),
                        "lng": loc.get("lng"),
                        "place_id": candidate.get("place_id")
                    }
        except Exception as e:
            print(f"[GoogleMapsService] Place search notice: {e}")

        return None

google_maps_service = GoogleMapsService()
