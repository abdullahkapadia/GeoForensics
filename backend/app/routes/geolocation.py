"""
GeoForensics AI — API Routes for geolocation analysis.
"""

import os
import uuid
import shutil
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.pipeline import run_analysis_pipeline
from app.models.schemas import GeolocationResult

router = APIRouter(prefix="/api/v1", tags=["geolocation"])

# In-memory analysis store (replace with DB in production)
_analysis_store: dict[str, GeolocationResult] = {}


def _validate_extension(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in settings.ALLOWED_EXTENSIONS


@router.post("/images/upload")
async def upload_image(
    file: UploadFile = File(...),
    cues: Optional[str] = Form(None)
):
    """
    Upload an image for forensic geolocation analysis.
    
    - `file`: Image file (JPG, JPEG, PNG, WEBP)
    - `cues`: Optional comma-separated textual hints about the image content
    
    Returns analysis_id for polling results.
    """
    if not file.filename or not _validate_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Read file and check size
    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum: {settings.MAX_UPLOAD_SIZE_MB} MB"
        )

    image_id = uuid.uuid4().hex
    analysis_id = uuid.uuid4().hex
    ext = file.filename.rsplit(".", 1)[-1].lower()
    saved_filename = f"{image_id}.{ext}"
    saved_path = str(settings.UPLOAD_DIR / saved_filename)

    with open(saved_path, "wb") as f:
        f.write(content)

    # Parse optional cues
    detected_cues = []
    if cues:
        detected_cues = [c.strip() for c in cues.split(",") if c.strip()]

    # Run synchronous pipeline (for production, dispatch to background worker)
    try:
        result = run_analysis_pipeline(
            image_path=saved_path,
            filename=file.filename,
            image_id=image_id,
            analysis_id=analysis_id,
            detected_cues=detected_cues
        )
        _analysis_store[analysis_id] = result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    return JSONResponse(content={
        "analysis_id": analysis_id,
        "image_id": image_id,
        "status": result.status,
        "message": "Analysis complete."
    })


@router.get("/geolocation/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Get full geolocation analysis result."""
    result = _analysis_store.get(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return result.model_dump()


@router.get("/geolocation/{analysis_id}/evidence")
async def get_evidence(analysis_id: str):
    """Get all evidence items for an analysis."""
    result = _analysis_store.get(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return {"evidence": [e.model_dump() for e in result.evidence_items]}


@router.get("/geolocation/{analysis_id}/candidates")
async def get_candidates(analysis_id: str):
    """Get ranked candidate locations."""
    result = _analysis_store.get(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return {"candidates": [c.model_dump() for c in result.candidates]}


@router.get("/geolocation/{analysis_id}/map")
async def get_map_data(analysis_id: str):
    """Get map-specific data for rendering."""
    result = _analysis_store.get(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    map_data = {
        "precision": result.precision,
        "confidence_score": result.confidence_score,
        "confidence_level": result.confidence_level,
        "resolved_address": result.resolved_address,
        "uncertainty_radius_km": result.uncertainty_radius_km,
        "markers": []
    }

    for cand in result.candidates:
        map_data["markers"].append({
            "id": cand.id,
            "name": cand.name,
            "lat": cand.lat,
            "lng": cand.lng,
            "score": cand.score,
            "precision_level": cand.precision_level,
            "uncertainty_radius_km": cand.uncertainty_radius_km,
            "resolved_address": cand.resolved_address,
            "is_top": cand.id == (result.top_prediction.id if result.top_prediction else None)
        })

    return map_data


@router.get("/geolocation/{analysis_id}/report")
async def get_report(analysis_id: str):
    """Get forensic explanation report."""
    result = _analysis_store.get(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    return {
        "analysis_id": analysis_id,
        "prediction": {
            "location": result.top_prediction.name if result.top_prediction else "Unknown",
            "city": result.top_prediction.city if result.top_prediction else "",
            "country": result.top_prediction.country if result.top_prediction else "",
            "lat": result.top_prediction.lat if result.top_prediction else None,
            "lng": result.top_prediction.lng if result.top_prediction else None,
            "resolved_address": result.resolved_address
        },
        "confidence_score": result.confidence_score,
        "confidence_level": result.confidence_level,
        "precision": result.precision,
        "resolution_level": result.resolution_level,
        "why_this_location": result.why_this_location,
        "contradictions": result.contradictions,
        "evidence_count": len(result.evidence_items),
        "contradiction_count": len(result.contradictions),
        "reliability": result.reliability.model_dump(),
        "timeline": [t.model_dump() for t in result.timeline]
    }
