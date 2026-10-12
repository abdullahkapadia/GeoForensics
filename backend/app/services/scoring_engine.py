"""
Evidence Graph Builder & Candidate Scoring Engine.

This module constructs the forensic evidence graph from all pipeline outputs,
generates candidate locations, and applies the weighted scoring model.
"""

import uuid
from typing import Dict, Any, List, Optional, Tuple
from app.models.schemas import (
    EvidenceItem, EvidenceGraph, EvidenceGraphNode, EvidenceGraphEdge,
    CandidateLocation, ScoreBreakdown, PrecisionLevel
)
from app.services.geospatial_db import (
    CITIES_DB, WORLD_LANDMARKS, COUNTRY_PROFILES,
    calculate_distance_km, find_nearest_city
)
from app.core.config import settings


def _confidence_level(score: float) -> str:
    if score >= 90:
        return "Very High"
    elif score >= 75:
        return "High"
    elif score >= 50:
        return "Moderate"
    elif score >= 30:
        return "Low"
    return "Insufficient"


def _precision_level(score: float, has_exact_coords: bool) -> PrecisionLevel:
    if has_exact_coords and score >= settings.CONFIDENCE_EXACT_THRESHOLD * 100:
        return "exact"
    elif score >= settings.CONFIDENCE_PROBABLE_THRESHOLD * 100:
        return "probable"
    elif score >= settings.CONFIDENCE_APPROXIMATE_THRESHOLD * 100:
        return "approximate"
    elif score >= settings.CONFIDENCE_REGIONAL_THRESHOLD * 100:
        return "regional"
    return "unknown"


def build_evidence_graph(
    evidence_items: List[EvidenceItem],
    candidate_names: List[str]
) -> EvidenceGraph:
    """Constructs a directed evidence graph connecting evidence nodes to candidate location nodes."""
    nodes: List[EvidenceGraphNode] = []
    edges: List[EvidenceGraphEdge] = []

    # Root image node
    nodes.append(EvidenceGraphNode(
        id="node_image",
        label="Uploaded Image",
        type="Image"
    ))

    # Candidate nodes
    for cname in candidate_names:
        cid = f"node_cand_{cname.lower().replace(' ', '_')}"
        nodes.append(EvidenceGraphNode(
            id=cid,
            label=cname,
            type="Candidate Location"
        ))

    # Evidence nodes + edges
    for ev in evidence_items:
        ntype_map = {
            "exif_gps": "Metadata",
            "exif_metadata": "Metadata",
            "ocr_text": "OCR Text",
            "street_name": "Road Feature",
            "business_name": "OCR Text",
            "phone_code": "OCR Text",
            "vehicle_plate": "Object",
            "road_marking": "Road Feature",
            "traffic_sign": "Road Feature",
            "landmark": "Landmark",
            "architecture": "Architecture",
            "vegetation_climate": "Geographic Feature",
            "terrain": "Geographic Feature",
            "sky_sun": "Geographic Feature",
            "visual_similarity": "Landmark",
            "utility_pole": "Object",
            "geographic_feature": "Geographic Feature",
        }
        node_type = ntype_map.get(ev.type, "Object")

        nodes.append(EvidenceGraphNode(
            id=f"node_{ev.id}",
            label=ev.label,
            type=node_type,
            confidence=ev.confidence
        ))

        # Edge from image → evidence
        edges.append(EvidenceGraphEdge(
            source="node_image",
            target=f"node_{ev.id}",
            relation="DERIVED_FROM",
            weight=ev.confidence
        ))

        # Edges from evidence → supporting candidates
        for sup in ev.supporting_candidates:
            cid = f"node_cand_{sup.lower().replace(' ', '_')}"
            relation = "STRONGLY_SUPPORTS" if ev.confidence >= 0.85 else (
                "SUPPORTS" if ev.confidence >= 0.65 else "WEAKLY_SUPPORTS"
            )
            edges.append(EvidenceGraphEdge(
                source=f"node_{ev.id}",
                target=cid,
                relation=relation,
                weight=ev.confidence,
                notes=ev.description[:80]
            ))

        # Edges from evidence → contradicting candidates
        for con in ev.contradicts_candidates:
            cid = f"node_cand_{con.lower().replace(' ', '_')}"
            edges.append(EvidenceGraphEdge(
                source=f"node_{ev.id}",
                target=cid,
                relation="CONTRADICTS",
                weight=ev.confidence
            ))

    return EvidenceGraph(nodes=nodes, edges=edges)


def generate_candidates(
    evidence_items: List[EvidenceItem],
    exif_data: Dict[str, Any],
    landmark_results: Dict[str, Any],
    ocr_results: Dict[str, Any],
    gemini_results: Optional[Dict[str, Any]] = None
) -> List[CandidateLocation]:
    """
    Generates ranked candidate locations from accumulated evidence.
    Uses a multi-signal weighted scoring model.
    """
    candidate_pool: Dict[str, Dict[str, Any]] = {}

    # --- Source 0: Gemini Multimodal Vision AI ---
    if gemini_results and gemini_results.get("location_prediction"):
        pred = gemini_results["location_prediction"]
        if pred.get("name"):
            lat = float(pred.get("lat", 0.0) or 0.0)
            lng = float(pred.get("lng", 0.0) or 0.0)
            conf = float(pred.get("confidence", 0.90) or 0.90)
            key = f"gemini_{pred.get('name', 'target')}"
            candidate_pool[key] = {
                "name": pred.get("name"),
                "city": pred.get("city", ""),
                "state_province": pred.get("state_province", ""),
                "country": pred.get("country", ""),
                "country_code": pred.get("country_code", ""),
                "lat": lat,
                "lng": lng,
                "has_exact_coords": abs(lat) > 0.01 or abs(lng) > 0.01,
                "resolved_address": pred.get("resolved_address", ""),
                "sources": {"landmark": conf, "visual_similarity": conf, "ocr": conf},
                "supporting_ev": [e.id for e in gemini_results.get("evidence_items", [])],
                "contradicting_ev": [],
                "rationale": gemini_results.get("why_this_location", [f"Identified by Gemini 3.1 Flash vision analysis"]),
                "place_type": "ai_multimodal_vision",
                "base_confidence": conf,
                "precision_level": pred.get("precision_level", "probable"),
                "uncertainty_radius_km": float(pred.get("uncertainty_radius_km", 5.0) or 5.0)
            }

        for alt in gemini_results.get("alternative_candidates", []):
            if alt.get("name"):
                lat = float(alt.get("lat", 0.0) or 0.0)
                lng = float(alt.get("lng", 0.0) or 0.0)
                conf = float(alt.get("confidence", 0.50) or 0.50)
                key = f"gemini_alt_{alt.get('name')}"
                candidate_pool[key] = {
                    "name": alt.get("name"),
                    "city": alt.get("city", ""),
                    "state_province": alt.get("state_province", ""),
                    "country": alt.get("country", ""),
                    "country_code": alt.get("country_code", ""),
                    "lat": lat,
                    "lng": lng,
                    "has_exact_coords": abs(lat) > 0.01 or abs(lng) > 0.01,
                    "resolved_address": "",
                    "sources": {"landmark": conf, "visual_similarity": conf},
                    "supporting_ev": [],
                    "contradicting_ev": [],
                    "rationale": [f"Alternative candidate suggested by Gemini multimodal analysis"],
                    "place_type": "ai_alternative",
                    "base_confidence": conf,
                    "precision_level": alt.get("precision_level", "probable"),
                    "uncertainty_radius_km": float(alt.get("uncertainty_radius_km", 25.0) or 25.0)
                }

    # --- Source 1: EXIF GPS (Level 1) ---
    if exif_data.get("has_gps") and exif_data.get("gps"):
        gps = exif_data["gps"]
        lat, lng = gps["latitude"], gps["longitude"]
        nearest_city, dist = find_nearest_city(lat, lng)
        city_name = nearest_city["city"] if nearest_city else "Unknown"
        country = nearest_city["country"] if nearest_city else "Unknown"
        country_code = nearest_city["country_code"] if nearest_city else "XX"
        state = nearest_city.get("state", "")

        key = f"exif_{city_name}"
        candidate_pool[key] = {
            "name": f"EXIF GPS — {city_name}",
            "city": city_name,
            "state_province": state,
            "country": country,
            "country_code": country_code,
            "lat": lat,
            "lng": lng,
            "has_exact_coords": True,
            "resolved_address": gps.get("resolved_address"),
            "sources": {"exif": 1.0},
            "supporting_ev": [],
            "contradicting_ev": [],
            "rationale": [f"GPS coordinates embedded in EXIF metadata: ({lat}, {lng})"],
            "place_type": "coordinate"
        }

    # --- Source 2: Landmark matches (Level 2–4) ---
    for lmk in landmark_results.get("landmarks_matched", []):
        key = f"lmk_{lmk['id']}"
        candidate_pool[key] = {
            "name": lmk["name"],
            "city": lmk["city"],
            "state_province": lmk["state_province"],
            "country": lmk["country"],
            "country_code": lmk["country_code"],
            "lat": lmk["lat"],
            "lng": lmk["lng"],
            "has_exact_coords": lmk["precision"] == "exact",
            "resolved_address": lmk["resolved_address"],
            "sources": {"landmark": lmk["confidence"]},
            "supporting_ev": [f"ev_landmark_{lmk['id']}"],
            "contradicting_ev": [],
            "rationale": [f"Landmark '{lmk['name']}' identified with {lmk['confidence']*100:.0f}% confidence"],
            "place_type": "landmark",
            "uncertainty_radius_km": lmk.get("uncertainty_radius_km", 0.1)
        }

    # --- Source 3: OCR city mentions (Level 3) ---
    for place in ocr_results.get("potential_places", []):
        city_match = next((c for c in CITIES_DB if c["city"].lower() == place.lower()), None)
        if city_match:
            key = f"ocr_{city_match['city']}"
            if key not in candidate_pool:
                candidate_pool[key] = {
                    "name": f"OCR Text — {city_match['city']}",
                    "city": city_match["city"],
                    "state_province": city_match["state"],
                    "country": city_match["country"],
                    "country_code": city_match["country_code"],
                    "lat": city_match["lat"],
                    "lng": city_match["lng"],
                    "has_exact_coords": False,
                    "resolved_address": None,
                    "sources": {"ocr": 0.85},
                    "supporting_ev": [],
                    "contradicting_ev": [],
                    "rationale": [f"Toponym '{city_match['city']}' detected in visible text"],
                    "place_type": "city",
                    "uncertainty_radius_km": city_match["radius_km"]
                }
            else:
                candidate_pool[key]["sources"]["ocr"] = 0.85

    # If no candidates generated, fall back to evidence-derived country-level
    if not candidate_pool:
        # Collect country mentions from evidence
        country_mentions: Dict[str, int] = {}
        for ev in evidence_items:
            for sup in ev.supporting_candidates:
                sup_lower = sup.lower()
                for code, profile in COUNTRY_PROFILES.items():
                    if profile["name"].lower() == sup_lower or sup_lower == code.lower():
                        country_mentions[code] = country_mentions.get(code, 0) + 1

        if country_mentions:
            top_code = max(country_mentions, key=country_mentions.get)
            profile = COUNTRY_PROFILES[top_code]
            key = f"country_{top_code}"
            candidate_pool[key] = {
                "name": profile["name"],
                "city": "",
                "state_province": "",
                "country": profile["name"],
                "country_code": top_code,
                "lat": profile["default_lat"],
                "lng": profile["default_lng"],
                "has_exact_coords": False,
                "resolved_address": None,
                "sources": {"environment": 0.5},
                "supporting_ev": [],
                "contradicting_ev": [],
                "rationale": [f"Multiple visual cues consistent with {profile['name']}"],
                "place_type": "country",
                "uncertainty_radius_km": 500.0
            }

    # --- Score each candidate ---
    scored_candidates: List[CandidateLocation] = []

    for key, cand in candidate_pool.items():
        sources = cand["sources"]
        supporting_ev_ids = list(cand.get("supporting_ev", []))
        contradicting_ev_ids = list(cand.get("contradicting_ev", []))

        # Collect matching evidence
        for ev in evidence_items:
            cand_lower_names = [
                cand["city"].lower(),
                cand["country"].lower(),
                cand["name"].lower()
            ]
            for sup in ev.supporting_candidates:
                if sup.lower() in cand_lower_names:
                    if ev.id not in supporting_ev_ids:
                        supporting_ev_ids.append(ev.id)
                        # Add source type score
                        type_key_map = {
                            "ocr_text": "ocr", "street_name": "ocr", "business_name": "ocr",
                            "phone_code": "ocr",
                            "landmark": "landmark", "visual_similarity": "visual_similarity",
                            "architecture": "architecture",
                            "road_marking": "geospatial", "traffic_sign": "geospatial",
                            "utility_pole": "geospatial",
                            "vegetation_climate": "environment", "terrain": "environment",
                            "sky_sun": "environment", "geographic_feature": "environment",
                            "exif_gps": "exif", "exif_metadata": "exif",
                        }
                        skey = type_key_map.get(ev.type, "environment")
                        sources[skey] = max(sources.get(skey, 0), ev.confidence)

            for con in ev.contradicts_candidates:
                if con.lower() in cand_lower_names and ev.id not in contradicting_ev_ids:
                    contradicting_ev_ids.append(ev.id)

        # Weighted score computation
        breakdown = ScoreBreakdown(
            ocr=sources.get("ocr", 0.0) * settings.WEIGHT_OCR,
            landmark=sources.get("landmark", 0.0) * settings.WEIGHT_LANDMARK,
            visual_similarity=sources.get("visual_similarity", 0.0) * settings.WEIGHT_VISUAL_SIMILARITY,
            geospatial=sources.get("geospatial", 0.0) * settings.WEIGHT_GEOSPATIAL,
            architecture=sources.get("architecture", 0.0) * settings.WEIGHT_ARCHITECTURE,
            environment=sources.get("environment", 0.0) * settings.WEIGHT_ENVIRONMENT,
            exif=sources.get("exif", 0.0) * settings.WEIGHT_EXIF_GPS,
            contradiction_penalty=len(contradicting_ev_ids) * -0.08
        )

        raw_score = (
            breakdown.ocr
            + breakdown.landmark
            + breakdown.visual_similarity
            + breakdown.geospatial
            + breakdown.architecture
            + breakdown.environment
            + breakdown.exif
            + breakdown.contradiction_penalty
        )

        # Determine normalized score based on candidate source
        place_type = cand.get("place_type")
        evidence_count = len(supporting_ev_ids)
        contradiction_count = len(contradicting_ev_ids)

        if place_type == "ai_multimodal_vision":
            base_conf = float(cand.get("base_confidence", 0.90) or 0.90)
            evidence_bonus = min(0.08, evidence_count * 0.015)
            penalty = contradiction_count * 0.15
            ai_score = (base_conf + evidence_bonus - penalty) * 100
            if cand.get("has_exact_coords") and cand.get("precision_level") == "exact":
                ai_score = max(ai_score, 94.0)
            normalized = min(99.0, max(50.0, ai_score))
            precision = cand.get("precision_level") or _precision_level(normalized, cand.get("has_exact_coords", False))

        elif place_type == "ai_alternative":
            base_conf = float(cand.get("base_confidence", 0.55) or 0.55)
            evidence_bonus = min(0.06, evidence_count * 0.015)
            penalty = contradiction_count * 0.15
            ai_score = (base_conf + evidence_bonus - penalty) * 100
            normalized = min(80.0, max(25.0, ai_score))
            precision = cand.get("precision_level") or _precision_level(normalized, cand.get("has_exact_coords", False))

        elif place_type == "country":
            # Generic country fallback: capped at 15% so it NEVER outranks specific places
            evidence_bonus = min(0.05, evidence_count * 0.01)
            normalized = min(15.0, max(5.0, (raw_score + evidence_bonus) * 100))
            precision = "country"

        elif place_type == "coordinate":
            # Direct EXIF GPS
            normalized = 99.0
            precision = "exact"

        else:
            evidence_bonus = min(0.15, evidence_count * 0.02)
            normalized = min(99.0, max(1.0, (raw_score + evidence_bonus) * 100))
            has_exact = cand.get("has_exact_coords", False)
            precision = _precision_level(normalized, has_exact)

        uncertainty = cand.get("uncertainty_radius_km")
        if uncertainty is None:
            if precision == "exact":
                uncertainty = 0.1
            elif precision == "probable":
                uncertainty = 5.0
            elif precision == "approximate":
                uncertainty = 25.0
            elif precision == "regional":
                uncertainty = 200.0
            else:
                uncertainty = 1000.0

        scored_candidates.append(CandidateLocation(
            id=f"cand_{uuid.uuid4().hex[:8]}",
            name=cand["name"],
            city=cand["city"],
            state_province=cand["state_province"],
            country=cand["country"],
            country_code=cand["country_code"],
            lat=cand["lat"],
            lng=cand["lng"],
            score=round(normalized, 1),
            precision_level=precision,
            uncertainty_radius_km=round(uncertainty, 2),
            supporting_evidence_ids=supporting_ev_ids,
            contradicting_evidence_ids=contradicting_ev_ids,
            score_breakdown=breakdown,
            rationale=cand.get("rationale", []),
            resolved_address=cand.get("resolved_address"),
            place_type=cand.get("place_type")
        ))

    # If we have specific candidates (villages, streets, cities, landmarks), filter out generic country fallback
    has_specific = any(c.place_type != "country" for c in scored_candidates)
    if has_specific:
        scored_candidates = [c for c in scored_candidates if c.place_type != "country"]

    # Sort by score descending
    scored_candidates.sort(key=lambda c: c.score, reverse=True)
    return scored_candidates


def determine_resolution_level(
    exif_data: Dict[str, Any],
    landmarks: List[Dict],
    ocr_places: List[str],
    top_candidate: Optional[CandidateLocation]
) -> str:
    """Determines the hierarchical resolution level achieved."""
    if exif_data.get("has_gps"):
        return "LEVEL 1 — GPS Metadata"
    if landmarks:
        best = landmarks[0]
        if best.get("precision") == "exact" and best.get("confidence", 0) >= 0.85:
            return "LEVEL 2 — Unique Landmark Identification"
    if ocr_places:
        return "LEVEL 3 — OCR + Geographic Search"
    if landmarks:
        return "LEVEL 4 — Visual Landmark Matching"
    if top_candidate and top_candidate.precision_level in ("probable", "approximate"):
        return "LEVEL 5 — Geospatial Feature Matching"
    if top_candidate and top_candidate.city:
        return "LEVEL 6 — City/Region Geolocation Model"
    return "LEVEL 7 — Country-level Prediction"


def generate_why_explanation(
    top_candidate: CandidateLocation,
    evidence_items: List[EvidenceItem]
) -> List[str]:
    """Generates human-readable forensic explanation for the top prediction."""
    reasons = []
    for ev_id in top_candidate.supporting_evidence_ids:
        ev = next((e for e in evidence_items if e.id == ev_id), None)
        if ev:
            reasons.append(f"{ev.label} — {ev.description[:120]}")
    if not top_candidate.contradicting_evidence_ids:
        reasons.append("No major contradictory evidence found.")
    else:
        reasons.append(f"{len(top_candidate.contradicting_evidence_ids)} contradicting signal(s) detected.")
    return reasons


def generate_contradictions(
    candidates: List[CandidateLocation],
    evidence_items: List[EvidenceItem]
) -> List[str]:
    """Identifies and explains contradictions across candidates."""
    contradictions = []
    for cand in candidates:
        for ev_id in cand.contradicting_evidence_ids:
            ev = next((e for e in evidence_items if e.id == ev_id), None)
            if ev:
                contradictions.append(
                    f"Evidence '{ev.label}' contradicts candidate '{cand.name}': {ev.description[:100]}"
                )
    return contradictions
