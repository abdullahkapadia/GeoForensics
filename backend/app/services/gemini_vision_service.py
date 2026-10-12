"""
GeoForensics AI — Gemini Multimodal Vision & Street-Level OSINT Geolocation Service.
Uses Google Gemini 3.1 Flash with GeoGuessr infrastructure forensics and live
OpenStreetMap Nominatim verification to achieve world-class street-level precision.
"""

import base64
import json
import mimetypes
import time
import urllib.error
import urllib.request
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.models.schemas import EvidenceItem, BoundingBox
from app.services.nominatim_service import nominatim_service

class GeminiVisionService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""
        self.model_name = "gemini-3.1-flash-lite"

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def analyze_image(self, image_path: str, user_cues: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze image using Google Gemini 3.1 Flash for forensic street-level geolocation.
        Cross-references with live OpenStreetMap Nominatim for exact street pin resolution.
        """
        if not self.is_configured():
            return {"enabled": False, "evidence_items": [], "candidates": []}

        try:
            with open(image_path, "rb") as f:
                image_bytes = f.read()

            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type:
                mime_type = "image/jpeg"

            b64_data = base64.b64encode(image_bytes).decode("utf-8")
            cues_text = f"User contextual clues: {', '.join(user_cues)}." if user_cues else ""

            prompt = f"""You are an elite, world-champion forensic geolocation and OSINT intelligence operative (combining the visual meta-recognition of Rainbolt with the rigorous investigative methodology of Bellingcat).
Your mission is to geolocate this image with MAXIMUM PINPOINT ACCURACY anywhere on Earth.
{cues_text}

CRITICAL RULES:
1. NEVER output a generic whole-country guess like "India", "USA", or "France". Even for unpaved rural tracks, farmlands, mountain peaks, or isolated trees, you MUST triangulate to the specific District, Sub-district/Tehsil, Village/Town, National/State Highway corridor, or geographic feature.
2. Formulate OpenStreetMap search queries as CLEAN CONCISE NOUN PHRASES (e.g. "Bohra Masjid, Dahod", "Dahod, Gujarat", "Station Road, Dahod"). NEVER include conversational filler words like "near", "vicinity", "area", "dirt track", "street scene".

Conduct an exhaustive forensic investigation using this multi-modal intelligence rubric:
1. INFRASTRUCTURE & UTILITY GRID TAXONOMY:
   - Utility poles: Concrete poles with rectangular/circular hole patterns (distinctive to Indian rural electrification, Poland, Brazil), wooden poles, metal tubular posts, transformer mounts, insulators, aerial line configurations.
   - Road surface & markings: Asphalt quality, unpaved red laterite dirt track, crushed limestone, painted kerbs/curbs (e.g., black-and-yellow, red-and-white), dashed vs solid center lines.
   - Traffic infrastructure: Left-Hand Drive (LHD - India, UK, Japan, Australia, SA) vs Right-Hand Drive (RHD), delineator post styles, guardrail profiles, milestone paint codes (yellow-white = National Highway, green-white = State Highway).
   - Vehicles: Model popularity (e.g. Hero Splendor, Mahindra Bolero, tuk-tuks, Kei cars), commercial plate colors (yellow rear, green EV, white private), and EXACT vehicle registration prefix codes (e.g. GJ for Gujarat, GJ-20 for Dahod, MH for Maharashtra, DL for Delhi, UP for Uttar Pradesh, RJ for Rajasthan).

2. BOTANY, BIOME, SOIL & SOLAR CHRONOLOCATION:
   - Specific flora: Tree & crop species (e.g. Prosopis cineraria / Khejri in Thar/Rajasthan, Acacia nilotica, Neem, Banyan, Mustard fields, Rice paddies, Olive groves, Canary date palms, Washingtonia palms, Pine varieties).
   - Soil & geology: Soil hue (red laterite, black cotton regur, arid sandy loam, grey alluvial silt), exposed rock stratum.
   - Solar angle & azimuth: Shadow projection angle confirming hemisphere and cardinal orientation.
   - Topography: Mountain silhouettes, hill ranges, alluvial plains.

3. LINGUISTIC, SCRIPT & ARCHITECTURAL MOTIFS:
   - Visible text, signage, banners, shop names, phone prefixes, multilingual scripts (Devanagari, Gujarati, Bengali, Latin, Arabic, Cyrillic, Kanji).
   - Architectural styles: Religious structures (Dawoodi Bohra Fatimid minarets, Rajput jali, Dravidian gopuram, Islamic dome, Gothic spire), brickwork, balcony railings, window grilles.

4. OSM TARGET SEARCH QUERIES:
   - 3 clean, concise search queries ordered from specific POI to municipality (e.g. ["Landmark Name, City, State", "City/Town, State, Country", "District, State, Country"]).

Respond STRICTLY in valid JSON matching this exact schema:
{{
  "location_prediction": {{
    "name": "Specific village, street, landmark, or localized site name (NEVER just a country)",
    "street_name": "Specific road, street, or highway number if identifiable",
    "city": "Village, town, or city name",
    "state_province": "State, province, or administrative region",
    "country": "Country name",
    "country_code": "2-letter ISO country code (e.g. IN, JP, US, FR, DE)",
    "lat": 0.0,
    "lng": 0.0,
    "confidence": 0.95,
    "precision_level": "exact" | "probable" | "approximate",
    "uncertainty_radius_km": 0.5,
    "resolved_address": "Specific address or regional descriptor"
  }},
  "search_queries": [
    "Specific site, District, State",
    "Town, State, Country",
    "District, State, Country"
  ],
  "alternative_candidates": [
    {{
      "name": "Alternative plausible sub-region or adjacent district",
      "city": "City or Village",
      "state_province": "State",
      "country": "Country",
      "country_code": "ISO",
      "lat": 0.0,
      "lng": 0.0,
      "confidence": 0.60,
      "precision_level": "probable",
      "uncertainty_radius_km": 15.0
    }}
  ],
  "forensic_evidence": [
    {{
      "type": "Road Infrastructure" | "Signage/OCR" | "Architecture" | "Vegetation & Climate" | "Vehicle & Plates" | "Utility Pole & Grid" | "Cultural",
      "label": "Observed diagnostic feature",
      "description": "Exhaustive forensic rationale explaining how this feature confirms the location",
      "confidence": 0.94,
      "polarity": "supports" | "contradicts" | "neutral"
    }}
  ],
  "why_this_location": [
    "Key forensic proof point 1",
    "Key forensic proof point 2",
    "Key forensic proof point 3"
  ],
  "potential_contradictions": [
    "Discarded alternatives and specific visual reasons why other states/countries are impossible"
  ]
}}"""

            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": b64_data
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.1
                }
            }

            models_to_try = [self.model_name, "gemini-flash-latest"]
            resp_data = None
            last_err = None

            for m_name in models_to_try:
                if resp_data and resp_data.get("candidates"):
                    break
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m_name}:generateContent?key={self.api_key}"
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                for retry_attempt in range(3):
                    try:
                        with urllib.request.urlopen(req, timeout=45) as resp:
                            resp_data = json.loads(resp.read().decode("utf-8"))
                            if resp_data and resp_data.get("candidates"):
                                break
                    except Exception as req_err:
                        last_err = req_err
                        time.sleep(1.5 * (retry_attempt + 1))

            if not resp_data or not resp_data.get("candidates"):
                raise last_err or RuntimeError("No response from Gemini API models")

            candidates_data = resp_data.get("candidates", [])
            first_candidate = candidates_data[0]
            text_part = first_candidate.get("content", {}).get("parts", [{}])[0].get("text", "")

            # Resilient JSON extraction and repair
            clean_text = text_part.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            elif clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()

            first_brace = clean_text.find("{")
            last_brace = clean_text.rfind("}")
            if first_brace != -1 and last_brace != -1:
                clean_text = clean_text[first_brace:last_brace + 1]

            try:
                parsed = json.loads(clean_text)
            except Exception:
                import re
                repaired = re.sub(r",\s*([}\]])", r"\1", clean_text)
                parsed = json.loads(repaired)

            loc_pred = parsed.get("location_prediction") or {}

            # --- Multi-Tier High-Precision OpenStreetMap Geocoding Ladder ---
            search_queries = parsed.get("search_queries", [])
            country_code = loc_pred.get("country_code")
            city_target = loc_pred.get("city")
            state_target = loc_pred.get("state_province")
            country_target = loc_pred.get("country", "")

            def _is_geographically_consistent(match_obj: Optional[Dict[str, Any]]) -> bool:
                if not match_obj:
                    return False
                m_display = (match_obj.get("display_name") or "").lower()
                m_city = (match_obj.get("city") or match_obj.get("suburb") or "").lower()
                m_state = (match_obj.get("state") or "").lower()

                # If target city is specified, require it to match the returned location
                if city_target and len(city_target.strip()) > 2:
                    c_clean = city_target.strip().lower()
                    if c_clean in m_city or c_clean in m_display:
                        return True
                    return False

                # If only state is specified, verify state consistency
                if state_target and len(state_target.strip()) > 2:
                    s_clean = state_target.strip().lower()
                    return s_clean in m_state or s_clean in m_display

                return True

            osm_match = None

            # Tier 0: Direct Micro-POI Search within target city (Specific Name + City)
            if loc_pred.get("name") and city_target:
                clean_name = nominatim_service.sanitize_query(loc_pred["name"])
                clean_city = nominatim_service.sanitize_query(city_target)
                if clean_name and clean_city and clean_name.lower() != clean_city.lower():
                    cand_match = nominatim_service.search_street(f"{clean_name}, {clean_city}", country_code=country_code)
                    if cand_match and _is_geographically_consistent(cand_match):
                        osm_match = cand_match

            # Tier 1: Try AI-formulated clean OSM search queries with city consistency check
            if not osm_match:
                for query in search_queries:
                    if query and len(query.strip()) > 3:
                        cand_match = nominatim_service.search_street(query, country_code=country_code)
                        if cand_match and _is_geographically_consistent(cand_match):
                            osm_match = cand_match
                            break

            # Tier 2: Strict Structured Geocoding directly anchoring to physical town/city node
            if not osm_match and city_target:
                cand_match = nominatim_service.search_structured(
                    street=loc_pred.get("street_name"),
                    city=city_target,
                    state=state_target,
                    country=country_target,
                    country_code=country_code
                )
                if cand_match:
                    osm_match = cand_match

            # Tier 3: City/Village + State + Country
            if not osm_match and city_target and state_target:
                q = f"{city_target}, {state_target}, {country_target}"
                cand_match = nominatim_service.search_street(q, country_code=country_code)
                if cand_match:
                    osm_match = cand_match

            # Tier 4: Specific Landmark Name + State + Country (only if consistent)
            if not osm_match and loc_pred.get("name") and state_target:
                q = f"{loc_pred['name']}, {state_target}, {country_target}"
                cand_match = nominatim_service.search_street(q, country_code=country_code)
                if cand_match and _is_geographically_consistent(cand_match):
                    osm_match = cand_match

            # Tier 5: Street name + City
            if not osm_match and loc_pred.get("street_name") and city_target:
                q = f"{loc_pred['street_name']}, {city_target}"
                osm_match = nominatim_service.search_street(q, country_code=country_code)

            if osm_match:
                # Snap prediction to verified real-world physical node
                loc_pred["lat"] = osm_match["lat"]
                loc_pred["lng"] = osm_match["lng"]
                loc_pred["precision_level"] = "exact" if osm_match.get("road") else "probable"
                loc_pred["uncertainty_radius_km"] = 0.05 if osm_match.get("road") else 1.0
                if osm_match.get("display_name"):
                    loc_pred["resolved_address"] = osm_match["display_name"]
                if osm_match.get("city") and not loc_pred.get("city"):
                    loc_pred["city"] = osm_match["city"]
                parsed["why_this_location"].insert(
                    0,
                    f"Geospatial Verification: Coordinates snapped to OpenStreetMap physical entity '{osm_match.get('name', 'location')}' ({osm_match['lat']:.5f}, {osm_match['lng']:.5f})."
                )

            # Tier 6: If coordinates are still 0 or missing, cascade to district/state search
            lat_val = float(loc_pred.get("lat", 0.0) or 0.0)
            lng_val = float(loc_pred.get("lng", 0.0) or 0.0)
            if abs(lat_val) < 0.001 and abs(lng_val) < 0.001:
                district_target = loc_pred.get("city") or loc_pred.get("state_province")
                if district_target:
                    q = f"{district_target}, {loc_pred.get('country', '')}"
                    match = nominatim_service.search_street(q, country_code=country_code)
                    if match and match.get("lat") and match.get("lng"):
                        loc_pred["lat"] = match["lat"]
                        loc_pred["lng"] = match["lng"]
                        loc_pred["resolved_address"] = match.get("display_name", "")
                        loc_pred["precision_level"] = "probable"
                        loc_pred["uncertainty_radius_km"] = 15.0

            # Tier 7: Country profile coordinate fallback so pin never goes to (0, 0)
            lat_val = float(loc_pred.get("lat", 0.0) or 0.0)
            lng_val = float(loc_pred.get("lng", 0.0) or 0.0)
            if abs(lat_val) < 0.001 and abs(lng_val) < 0.001 and country_code:
                from app.services.geospatial_db import COUNTRY_PROFILES
                profile = COUNTRY_PROFILES.get(country_code.upper())
                if profile:
                    loc_pred["lat"] = profile["default_lat"]
                    loc_pred["lng"] = profile["default_lng"]
                    loc_pred["resolved_address"] = f"{profile['name']} (Regional corridor)"
                    loc_pred["precision_level"] = "regional"
                    loc_pred["uncertainty_radius_km"] = 50.0

            # If we have lat/lng but no resolved address, reverse geocode to real street address
            lat_final = float(loc_pred.get("lat", 0.0) or 0.0)
            lng_final = float(loc_pred.get("lng", 0.0) or 0.0)
            if abs(lat_final) > 0.001 and not loc_pred.get("resolved_address"):
                rev = nominatim_service.reverse_geocode(lat_final, lng_final)
                if rev and rev.get("display_name"):
                    loc_pred["resolved_address"] = rev["display_name"]

            # Map forensic evidence into strongly-typed EvidenceItem objects
            TYPE_MAPPING = {
                "Signage/OCR": "ocr_text",
                "Vehicle & Plates": "vehicle_plate",
                "Road Infrastructure": "road_marking",
                "Utility Pole & Grid": "utility_pole",
                "Architecture": "architecture",
                "Vegetation & Climate": "vegetation_climate",
                "Cultural": "visual_similarity"
            }

            evidence_items = []
            for idx, item in enumerate(parsed.get("forensic_evidence", [])):
                raw_type = item.get("type", "Forensics")
                ev_type = TYPE_MAPPING.get(raw_type, "ai_multimodal_vision")
                evidence_items.append(
                    EvidenceItem(
                        id=f"gemini_ev_{idx+1}",
                        type=ev_type,
                        label=f"{raw_type}: {item.get('label', 'Visual Cue')}",
                        description=item.get("description", ""),
                        confidence=float(item.get("confidence", 0.92)),
                        polarity=item.get("polarity", "supports") if item.get("polarity") in ["supports", "contradicts", "neutral"] else "supports",
                        supporting_candidates=[loc_pred.get("name", "Target Location"), loc_pred.get("city", "")],
                        contradicts_candidates=[]
                    )
                )

            return {
                "enabled": True,
                "parsed": parsed,
                "evidence_items": evidence_items,
                "location_prediction": loc_pred,
                "alternative_candidates": parsed.get("alternative_candidates", []),
                "why_this_location": parsed.get("why_this_location", []),
                "potential_contradictions": parsed.get("potential_contradictions", [])
            }

        except Exception as e:
            print(f"[GeminiVisionService] Error analyzing image: {e}")
            return {
                "enabled": True,
                "error": str(e),
                "evidence_items": [],
                "candidates": []
            }

gemini_vision_service = GeminiVisionService()
