"""
GeoForensics AI — OpenStreetMap Nominatim Live Geocoding Service.
Provides 100% free, global street-level geocoding, address resolution,
and micro-location verification with zero API keys required.
"""

import json
import re
import time
import urllib.parse
import urllib.request
from typing import Dict, Any, List, Optional

def sanitize_query(query: str) -> str:
    """Strips conversational noise and filler words that cause OSM Nominatim search misses."""
    if not query:
        return ""
    q = query.strip()
    # Remove conversational phrases
    patterns = [
        r"\b(?:near(?:\s+the)?|in\s+the\s+vicinity\s+of|vicinity\s+of|around|close\s+to)\b",
        r"\b(?:area|district\s+area|region|corridor|vicinity)\b",
        r"\b(?:residential\s+street|unpaved\s+(?:dirt\s+)?track|unpaved\s+road|dirt\s+track|dirt\s+road)\b",
        r"\b(?:street\s+scene|panoramic\s+view|scenic\s+view|landscape\s+of)\b",
    ]
    for pat in patterns:
        q = re.sub(pat, " ", q, flags=re.IGNORECASE)
    # Clean up excess whitespace and commas
    q = re.sub(r",\s*,+", ",", q)
    q = re.sub(r"\s+", " ", q)
    q = re.sub(r"^\s*,\s*|\s*,\s*$", "", q)
    return q.strip()

class NominatimService:
    sanitize_query = staticmethod(sanitize_query)

    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org"
        self.user_agent = "GeoForensicsAI/2.0 (forensic-osint-intelligence; contact=intel@geoforensics.local)"
        self.last_query_time = 0.0
        self.cache: Dict[str, Any] = {}

    def _rate_limit(self):
        """Respect Nominatim 1 query per second usage policy."""
        elapsed = time.time() - self.last_query_time
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)
        self.last_query_time = time.time()

    def search_structured(
        self,
        street: Optional[str] = None,
        city: Optional[str] = None,
        county: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        postalcode: Optional[str] = None,
        amenity: Optional[str] = None,
        country_code: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Executes strict structured geocoding against OpenStreetMap.
        Bypasses freeform text parsing ambiguity and directly anchors to administrative and physical entities.
        """
        params: Dict[str, str] = {
            "format": "jsonv2",
            "addressdetails": "1",
            "limit": "5"
        }
        if street and len(street.strip()) > 2:
            params["street"] = sanitize_query(street)
        if city and len(city.strip()) > 2:
            params["city"] = sanitize_query(city)
        if county and len(county.strip()) > 2:
            params["county"] = sanitize_query(county)
        if state and len(state.strip()) > 2:
            params["state"] = sanitize_query(state)
        if country and len(country.strip()) > 2:
            params["country"] = sanitize_query(country)
        if postalcode and len(postalcode.strip()) > 2:
            params["postalcode"] = postalcode.strip()
        if amenity and len(amenity.strip()) > 2:
            params["amenity"] = amenity.strip()
        if country_code:
            params["countrycodes"] = country_code.lower()

        # Must have at least one significant geographic parameter
        sig_keys = [k for k in ["street", "city", "county", "state", "postalcode", "amenity"] if k in params]
        if not sig_keys:
            return None

        cache_key = f"struct_{json.dumps(params, sort_keys=True)}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        self._rate_limit()
        url = f"{self.base_url}/search?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            if data and len(data) > 0:
                def _entity_priority(item: Dict[str, Any]) -> int:
                    cat = item.get("category", "")
                    typ = item.get("type", "")
                    if cat in ["amenity", "building", "historic", "tourism", "highway", "shop", "leisure"]:
                        return 10
                    if cat == "place" and typ in ["suburb", "neighbourhood", "town", "city", "village", "hamlet"]:
                        return 8
                    if cat == "place":
                        return 6
                    if cat == "boundary" and typ in ["administrative", "political"]:
                        return 1
                    return 5

                sorted_data = sorted(data, key=lambda x: (_entity_priority(x), float(x.get("importance", 0.0) or 0.0)), reverse=True)
                best = sorted_data[0]
                addr = best.get("address", {})

                result = {
                    "name": best.get("name") or (params.get("street") or params.get("city") or "Structured Match"),
                    "display_name": best.get("display_name"),
                    "lat": float(best.get("lat")),
                    "lng": float(best.get("lon")),
                    "category": best.get("category"),
                    "type": best.get("type"),
                    "importance": best.get("importance", 0.5),
                    "road": addr.get("road"),
                    "suburb": addr.get("suburb") or addr.get("neighbourhood"),
                    "city": addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality"),
                    "state": addr.get("state"),
                    "country": addr.get("country"),
                    "country_code": addr.get("country_code", "").upper(),
                    "postcode": addr.get("postcode")
                }
                self.cache[cache_key] = result
                return result
        except Exception as e:
            print(f"[NominatimService] Structured search notice: {e}")

        return None

    def search_street(self, query: str, country_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Search for exact street, intersection, landmark, or business name globally.
        Returns exact lat, lng, and formatted address.
        """
        if not query or len(query.strip()) < 2:
            return None

        clean_query = query.strip()
        cache_key = f"search_{clean_query}_{country_code or ''}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Multi-attempt query ladder (raw query -> sanitized query -> component query)
        candidate_queries = [clean_query]
        sanitized = sanitize_query(clean_query)
        if sanitized and sanitized.lower() != clean_query.lower():
            candidate_queries.append(sanitized)

        # If query has comma-separated parts, try stripping filler components
        parts = [p.strip() for p in clean_query.split(",") if p.strip()]
        if len(parts) >= 3:
            candidate_queries.append(f"{parts[0]}, {parts[-1]}")

        for q_attempt in candidate_queries:
            self._rate_limit()
            params = {
                "q": q_attempt,
                "format": "jsonv2",
                "addressdetails": "1",
                "limit": "4"
            }
            if country_code:
                params["countrycodes"] = country_code.lower()

            url = f"{self.base_url}/search?{urllib.parse.urlencode(params)}"

            try:
                req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
                with urllib.request.urlopen(req, timeout=6) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

                if data and len(data) > 0:
                    def _entity_priority(item: Dict[str, Any]) -> int:
                        cat = item.get("category", "")
                        typ = item.get("type", "")
                        if cat in ["amenity", "building", "historic", "tourism", "highway", "shop", "leisure"]:
                            return 10
                        if cat == "place" and typ in ["suburb", "neighbourhood", "town", "city", "village", "hamlet"]:
                            return 8
                        if cat == "place":
                            return 6
                        if cat == "boundary" and typ in ["administrative", "political"]:
                            return 1
                        return 5

                    sorted_data = sorted(data, key=lambda x: (_entity_priority(x), float(x.get("importance", 0.0) or 0.0)), reverse=True)
                    best = sorted_data[0]
                    addr = best.get("address", {})

                    result = {
                        "name": best.get("name") or q_attempt,
                        "display_name": best.get("display_name"),
                        "lat": float(best.get("lat")),
                        "lng": float(best.get("lon")),
                        "category": best.get("category"),
                        "type": best.get("type"),
                        "importance": best.get("importance", 0.5),
                        "road": addr.get("road"),
                        "suburb": addr.get("suburb") or addr.get("neighbourhood"),
                        "city": addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality"),
                        "state": addr.get("state"),
                        "country": addr.get("country"),
                        "country_code": addr.get("country_code", "").upper(),
                        "postcode": addr.get("postcode")
                    }
                    self.cache[cache_key] = result
                    return result
            except Exception as e:
                print(f"[NominatimService] Search notice for '{q_attempt}': {e}")

        return None

    def reverse_geocode(self, lat: float, lng: float) -> Optional[Dict[str, Any]]:
        """
        Reverse geocodes coordinates to exact street number, road, city, and country.
        """
        cache_key = f"rev_{lat:.5f}_{lng:.5f}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        self._rate_limit()

        params = {
            "lat": str(lat),
            "lon": str(lng),
            "format": "jsonv2",
            "addressdetails": "1",
            "zoom": "18"
        }
        url = f"{self.base_url}/reverse?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            if data and "address" in data:
                addr = data["address"]
                result = {
                    "display_name": data.get("display_name"),
                    "road": addr.get("road"),
                    "house_number": addr.get("house_number"),
                    "suburb": addr.get("suburb") or addr.get("neighbourhood"),
                    "city": addr.get("city") or addr.get("town") or addr.get("village") or addr.get("municipality"),
                    "state": addr.get("state"),
                    "country": addr.get("country"),
                    "country_code": addr.get("country_code", "").upper(),
                    "postcode": addr.get("postcode")
                }
                self.cache[cache_key] = result
                return result
        except Exception as e:
            print(f"[NominatimService] Reverse geocode notice: {e}")

        return None

nominatim_service = NominatimService()
