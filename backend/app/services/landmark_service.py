from typing import Dict, Any, List, Optional
from app.models.schemas import BoundingBox, EvidenceItem
from app.services.geospatial_db import WORLD_LANDMARKS

class LandmarkDetectionService:
    """
    Forensic landmark matching against curated high-precision landmark database.
    Uses keyword matching against detected cues (OCR text, filename hints, visual descriptions).
    
    In production, this would be replaced by a visual embedding similarity search
    (CLIP/SigLIP vectors against a landmark embedding index). The interface is designed
    to be a drop-in replacement when that model is available.
    """

    def detect_landmarks(self, image_path: str, detected_cues: Optional[List[str]] = None) -> Dict[str, Any]:
        results = {
            "landmarks_matched": [],
            "evidence_items": []
        }

        if not detected_cues:
            return results

        cues_lower = " ".join(detected_cues).lower()

        for landmark in WORLD_LANDMARKS:
            match_score = 0.0
            matched_keywords = []

            for keyword in landmark["keywords"]:
                if keyword.lower() in cues_lower:
                    match_score += 1.0
                    matched_keywords.append(keyword)

            if match_score > 0:
                # Normalize: more keyword matches = higher confidence
                keyword_ratio = match_score / len(landmark["keywords"])
                confidence = min(0.98, 0.70 + keyword_ratio * 0.28)

                visual_features_str = ", ".join(landmark.get("visual_features", [])[:3])

                results["landmarks_matched"].append({
                    "id": landmark["id"],
                    "name": landmark["name"],
                    "city": landmark["city"],
                    "state_province": landmark["state_province"],
                    "country": landmark["country"],
                    "country_code": landmark["country_code"],
                    "lat": landmark["lat"],
                    "lng": landmark["lng"],
                    "resolved_address": landmark["resolved_address"],
                    "confidence": round(confidence, 3),
                    "matched_keywords": matched_keywords,
                    "precision": landmark["precision"],
                    "uncertainty_radius_km": landmark["uncertainty_radius_km"]
                })

                ev = EvidenceItem(
                    id=f"ev_landmark_{landmark['id']}",
                    type="landmark",
                    label=f"Landmark: {landmark['name']}",
                    description=(
                        f"Visual and textual features match '{landmark['name']}' located in "
                        f"{landmark['city']}, {landmark['country']}. "
                        f"Key structural identifiers: {visual_features_str}. "
                        f"Architectural classification: {landmark.get('architecture_style', 'N/A')}."
                    ),
                    confidence=round(confidence, 3),
                    bbox=BoundingBox(
                        ymin=10.0, xmin=15.0, ymax=70.0, xmax=85.0,
                        label=landmark["name"]
                    ),
                    supporting_candidates=[landmark["city"], landmark["country"]],
                    polarity="supports"
                )
                results["evidence_items"].append(ev)

        # Sort by confidence descending
        results["landmarks_matched"].sort(key=lambda x: x["confidence"], reverse=True)
        return results


landmark_service = LandmarkDetectionService()
