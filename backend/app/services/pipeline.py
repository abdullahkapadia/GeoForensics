"""
GeoForensics AI — Main Analysis Pipeline Orchestrator.

Coordinates all forensic analysis stages in sequence, collecting evidence,
generating candidates, scoring, and producing the final GeolocationResult.
"""

import os
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from app.models.schemas import (
    GeolocationResult, InvestigationTimelineStep,
    ReliabilityReport, HistoricalReport, EvidenceItem
)
from app.services.exif_service import extract_exif_data
from app.services.ocr_service import ocr_service
from app.services.visual_scene_service import visual_scene_service
from app.services.object_detection_service import object_detection_service
from app.services.architecture_service import architecture_service
from app.services.landmark_service import landmark_service
from app.services.reliability_service import reliability_service
from app.services.google_maps_service import google_maps_service
from app.services.gemini_vision_service import gemini_vision_service
from app.services.scoring_engine import (
    build_evidence_graph, generate_candidates,
    determine_resolution_level, generate_why_explanation,
    generate_contradictions
)


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _step(num: int, title: str, status: str, detail: str, dur: float = 0) -> InvestigationTimelineStep:
    return InvestigationTimelineStep(
        step_number=num,
        title=title,
        status=status,
        duration_ms=round(dur, 1),
        detail=detail,
        timestamp=_ts()
    )


def run_analysis_pipeline(
    image_path: str,
    filename: str,
    image_id: str,
    analysis_id: str,
    detected_cues: Optional[List[str]] = None
) -> GeolocationResult:
    """
    Executes the full forensic geolocation pipeline:
    
    1. Image Preprocessing
    2. EXIF / Metadata Extraction
    3. OCR & Linguistic Analysis
    4. Visual Scene Understanding
    5. Object Detection & Road Infrastructure
    6. Architecture Forensic Analysis
    7. Landmark Detection
    8. Reliability Assessment
    9. Candidate Location Generation
    10. Evidence Graph Construction
    11. Candidate Scoring & Ranking
    12. Exact Location Resolution
    """
    timeline: List[InvestigationTimelineStep] = []
    all_evidence: List[EvidenceItem] = []
    cues = list(detected_cues or [])

    # Also extract cues from filename
    fname_lower = filename.lower().replace("_", " ").replace("-", " ")
    cues.append(fname_lower)

    # === STAGE 1: Image Preprocessing ===
    t0 = time.time()
    timeline.append(_step(1, "Image Preprocessing", "COMPLETED",
        f"Image loaded: {filename}", (time.time() - t0) * 1000))

    # === STAGE 2: EXIF / Metadata Extraction ===
    t0 = time.time()
    exif_data = extract_exif_data(image_path)
    dur = (time.time() - t0) * 1000

    exif_detail = "No EXIF metadata found."
    if exif_data.get("has_gps"):
        gps = exif_data["gps"]
        exif_detail = f"GPS found: ({gps['latitude']}, {gps['longitude']})"
        # Add EXIF GPS evidence
        from app.models.schemas import BoundingBox
        all_evidence.append(EvidenceItem(
            id="ev_exif_gps",
            type="exif_gps",
            label="EXIF GPS Coordinates",
            description=f"Embedded GPS metadata: latitude {gps['latitude']}, longitude {gps['longitude']}. Nearest city: {gps.get('nearest_city', 'N/A')}.",
            confidence=0.98,
            bbox=None,
            supporting_candidates=[gps.get("nearest_city", ""), gps.get("nearest_country", "")],
            polarity="supports"
        ))
    elif exif_data.get("has_exif"):
        exif_detail = "EXIF found but no GPS coordinates."
        cam = exif_data.get("camera", {})
        if cam.get("make") or cam.get("model"):
            all_evidence.append(EvidenceItem(
                id="ev_exif_camera",
                type="exif_metadata",
                label=f"Camera: {cam.get('make', '')} {cam.get('model', '')}",
                description=f"Image captured with {cam.get('make', 'Unknown')} {cam.get('model', 'Unknown')} camera.",
                confidence=0.60,
                bbox=None,
                supporting_candidates=[],
                polarity="neutral"
            ))

    timeline.append(_step(2, "Metadata Extraction", "COMPLETED", exif_detail, dur))

    # === STAGE 3: OCR & Linguistic Analysis ===
    t0 = time.time()
    ocr_results = ocr_service.analyze_image(image_path, cues)
    dur = (time.time() - t0) * 1000

    ocr_detail = f"Raw text: {len(ocr_results.get('raw_text', ''))} chars. Places: {ocr_results.get('potential_places', [])}. Scripts: {ocr_results.get('scripts', [])}."
    all_evidence.extend(ocr_results.get("evidence_items", []))
    timeline.append(_step(3, "OCR & Linguistic Analysis", "COMPLETED", ocr_detail, dur))

    # === STAGE 4: Visual Scene Understanding ===
    t0 = time.time()
    scene_results = visual_scene_service.analyze_scene(image_path)
    dur = (time.time() - t0) * 1000

    scene_detail = f"Environment: {scene_results.get('environment_type', 'N/A')}. Vegetation index: {scene_results.get('vegetation_index', 0)}. Sky fraction: {scene_results.get('sky_fraction', 0)}."
    all_evidence.extend(scene_results.get("evidence_items", []))
    timeline.append(_step(4, "Visual Scene Understanding", "COMPLETED", scene_detail, dur))

    # === STAGE 5: Object Detection & Road Infrastructure ===
    t0 = time.time()
    obj_results = object_detection_service.analyze_objects(image_path, cues)
    dur = (time.time() - t0) * 1000

    obj_detail = f"Road markings: {obj_results.get('road_marking_type', 'N/A')}. Driving side: {obj_results.get('driving_side_detected', 'N/A')}."
    all_evidence.extend(obj_results.get("evidence_items", []))
    timeline.append(_step(5, "Object Detection & Road Infrastructure", "COMPLETED", obj_detail, dur))

    # === STAGE 6: Architecture Forensic Analysis ===
    t0 = time.time()
    arch_results = architecture_service.analyze_architecture(image_path, cues)
    dur = (time.time() - t0) * 1000

    arch_detail = f"Style: {arch_results.get('style_detected', 'Not determined')}."
    all_evidence.extend(arch_results.get("evidence_items", []))
    timeline.append(_step(6, "Architecture Forensic Analysis", "COMPLETED", arch_detail, dur))

    # === STAGE 7: Landmark Detection ===
    t0 = time.time()
    lmk_results = landmark_service.detect_landmarks(image_path, cues)
    dur = (time.time() - t0) * 1000

    lmk_names = [l["name"] for l in lmk_results.get("landmarks_matched", [])]
    lmk_detail = f"Landmarks matched: {lmk_names if lmk_names else 'None'}."
    all_evidence.extend(lmk_results.get("evidence_items", []))
    timeline.append(_step(7, "Landmark Detection", "COMPLETED", lmk_detail, dur))

    # === STAGE 8: Gemini Multimodal AI Vision & Geolocation ===
    gemini_results = {}
    if gemini_vision_service.is_configured():
        t0 = time.time()
        gemini_results = gemini_vision_service.analyze_image(image_path, cues)
        dur = (time.time() - t0) * 1000
        if gemini_results.get("enabled") and not gemini_results.get("error"):
            pred = gemini_results.get("location_prediction") or {}
            pred_name = pred.get("name", "Identified Location")
            gemini_detail = f"Gemini 3.1 Flash identified '{pred_name}' ({pred.get('country', '')}). Extracted {len(gemini_results.get('evidence_items', []))} AI visual cues."
            all_evidence.extend(gemini_results.get("evidence_items", []))
            timeline.append(_step(8, "Gemini Multimodal AI Vision", "COMPLETED", gemini_detail, dur))
        else:
            timeline.append(_step(8, "Gemini Multimodal AI Vision", "SKIPPED", "Offline fallback active.", dur))

    # === STAGE 9: Reliability Assessment ===
    t0 = time.time()
    rel_results = reliability_service.analyze_reliability(image_path, exif_data)
    dur = (time.time() - t0) * 1000

    rel_detail = f"Reliability: {rel_results['status']} ({rel_results['score']:.0%}). {'; '.join(rel_results['reasons'][:2])}"
    timeline.append(_step(9, "Reliability Assessment", "COMPLETED", rel_detail, dur))

    # === STAGE 10: Candidate Location Generation ===
    t0 = time.time()
    candidates = generate_candidates(all_evidence, exif_data, lmk_results, ocr_results, gemini_results=gemini_results)
    dur = (time.time() - t0) * 1000

    cand_detail = f"{len(candidates)} candidate location(s) generated."
    timeline.append(_step(10, "Candidate Location Generation", "COMPLETED", cand_detail, dur))

    # === STAGE 10: Evidence Graph Construction ===
    t0 = time.time()
    cand_names = list(set(
        [c.city for c in candidates if c.city] +
        [c.country for c in candidates if c.country] +
        [c.name for c in candidates]
    ))
    evidence_graph = build_evidence_graph(all_evidence, cand_names)
    dur = (time.time() - t0) * 1000

    graph_detail = f"Graph: {len(evidence_graph.nodes)} nodes, {len(evidence_graph.edges)} edges."
    timeline.append(_step(10, "Evidence Graph Construction", "COMPLETED", graph_detail, dur))

    # === STAGE 11: Candidate Scoring & Ranking ===
    t0 = time.time()
    # Already scored during generation; this stage confirms ranking
    dur = (time.time() - t0) * 1000
    score_detail = f"Top candidate: {candidates[0].name} ({candidates[0].score}%)" if candidates else "No candidates."
    timeline.append(_step(11, "Candidate Scoring & Ranking", "COMPLETED", score_detail, dur))

    # === STAGE 12: Exact Location Resolution ===
    t0 = time.time()
    top = candidates[0] if candidates else None

    resolution_level = determine_resolution_level(
        exif_data,
        lmk_results.get("landmarks_matched", []),
        ocr_results.get("potential_places", []),
        top
    )

    why_explanation = generate_why_explanation(top, all_evidence) if top else ["Insufficient evidence for geolocation."]
    contradictions = generate_contradictions(candidates, all_evidence)

    # Enrich with Google Maps if configured
    if top and google_maps_service.is_configured():
        g_res = google_maps_service.reverse_geocode(top.lat, top.lng)
        if g_res and g_res.get("formatted_address"):
            top.resolved_address = g_res["formatted_address"]
            if g_res.get("city") and not top.city:
                top.city = g_res["city"]
            if g_res.get("country") and not top.country:
                top.country = g_res["country"]
            loc_detail = f"Resolution: {resolution_level}. Google Maps resolved address: {top.resolved_address}."
        else:
            loc_detail = f"Resolution: {resolution_level}."
    else:
        loc_detail = f"Resolution: {resolution_level}."

    dur = (time.time() - t0) * 1000
    timeline.append(_step(12, "Exact Location Resolution", "COMPLETED", loc_detail, dur))

    # === Build Final Result ===
    confidence_score = top.score if top else 0.0
    from app.services.scoring_engine import _confidence_level
    conf_level = _confidence_level(confidence_score)
    precision = top.precision_level if top else "unknown"

    result = GeolocationResult(
        analysis_id=analysis_id,
        image_id=image_id,
        filename=filename,
        status="COMPLETED",
        top_prediction=top,
        precision=precision,
        confidence_score=confidence_score,
        confidence_level=conf_level,
        uncertainty_radius_km=top.uncertainty_radius_km if top else None,
        resolved_address=top.resolved_address if top else None,
        candidates=candidates,
        evidence_items=all_evidence,
        evidence_graph=evidence_graph,
        timeline=timeline,
        raw_metadata=exif_data,
        reliability=ReliabilityReport(**rel_results),
        historical=HistoricalReport(),
        why_this_location=why_explanation,
        contradictions=contradictions,
        resolution_level=resolution_level
    )

    return result
