from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

PrecisionLevel = Literal["exact", "probable", "approximate", "regional", "unknown"]

EvidenceType = Literal[
    "exif_gps",
    "exif_metadata",
    "ocr_text",
    "street_name",
    "business_name",
    "phone_code",
    "vehicle_plate",
    "road_marking",
    "traffic_sign",
    "landmark",
    "architecture",
    "vegetation_climate",
    "terrain",
    "sky_sun",
    "visual_similarity",
    "utility_pole",
    "geographic_feature",
    "ai_multimodal_vision",
    "contradiction"
]

EdgeRelation = Literal[
    "SUPPORTS",
    "STRONGLY_SUPPORTS",
    "WEAKLY_SUPPORTS",
    "CONTRADICTS",
    "MATCHES",
    "DERIVED_FROM"
]

class BoundingBox(BaseModel):
    ymin: float = Field(..., ge=0, le=100, description="Top percent")
    xmin: float = Field(..., ge=0, le=100, description="Left percent")
    ymax: float = Field(..., ge=0, le=100, description="Bottom percent")
    xmax: float = Field(..., ge=0, le=100, description="Right percent")
    label: Optional[str] = None

class EvidenceItem(BaseModel):
    id: str
    type: EvidenceType
    label: str
    description: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: Optional[BoundingBox] = None
    supporting_candidates: List[str] = []
    contradicts_candidates: List[str] = []
    polarity: Literal["supports", "contradicts", "neutral"] = "supports"
    metadata_details: Optional[Dict[str, Any]] = None

class EvidenceGraphNode(BaseModel):
    id: str
    label: str
    type: str  # e.g., "Image", "OCR Text", "Object", "Landmark", "Architecture", "Road Feature", "Geographic Feature", "Candidate Location", "Metadata"
    confidence: Optional[float] = None
    properties: Optional[Dict[str, Any]] = None

class EvidenceGraphEdge(BaseModel):
    source: str
    target: str
    relation: EdgeRelation
    weight: float = 1.0
    notes: Optional[str] = None

class EvidenceGraph(BaseModel):
    nodes: List[EvidenceGraphNode] = []
    edges: List[EvidenceGraphEdge] = []

class ScoreBreakdown(BaseModel):
    ocr: float = 0.0
    landmark: float = 0.0
    visual_similarity: float = 0.0
    geospatial: float = 0.0
    architecture: float = 0.0
    environment: float = 0.0
    exif: float = 0.0
    contradiction_penalty: float = 0.0

class CandidateLocation(BaseModel):
    id: str
    name: str
    city: str
    state_province: str
    country: str
    country_code: str
    lat: float
    lng: float
    score: float = Field(..., ge=0.0, le=100.0)
    precision_level: PrecisionLevel
    uncertainty_radius_km: Optional[float] = None
    supporting_evidence_ids: List[str] = []
    contradicting_evidence_ids: List[str] = []
    score_breakdown: ScoreBreakdown
    rationale: List[str] = []
    resolved_address: Optional[str] = None
    place_type: Optional[str] = None  # landmark, building, street, neighborhood, city, administrative, region

class ReliabilityReport(BaseModel):
    status: Literal["HIGH", "QUESTIONABLE", "MANIPULATED"]
    score: float = Field(..., ge=0.0, le=1.0)
    reasons: List[str] = []
    metadata_visual_conflict: bool = False
    is_screenshot: bool = False
    is_ai_generated_indicators: bool = False
    compression_anomaly: bool = False
    details: Dict[str, Any] = {}

class HistoricalReport(BaseModel):
    is_historical: bool = False
    estimated_period: Optional[str] = None
    period_confidence: float = 0.0
    visual_cues: List[str] = []
    notes: Optional[str] = None

class InvestigationTimelineStep(BaseModel):
    step_number: int
    title: str
    status: Literal["COMPLETED", "IN_PROGRESS", "FAILED", "SKIPPED"]
    duration_ms: Optional[float] = None
    detail: str
    timestamp: str

class GeolocationResult(BaseModel):
    analysis_id: str
    image_id: str
    filename: str
    status: Literal["PENDING", "PROCESSING", "COMPLETED", "FAILED"]
    error: Optional[str] = None
    
    # Top Resolution
    top_prediction: Optional[CandidateLocation] = None
    precision: PrecisionLevel = "unknown"
    confidence_score: float = 0.0
    confidence_level: Literal["Very High", "High", "Moderate", "Low", "Insufficient"] = "Insufficient"
    uncertainty_radius_km: Optional[float] = None
    resolved_address: Optional[str] = None
    
    # Forensic Findings
    candidates: List[CandidateLocation] = []
    evidence_items: List[EvidenceItem] = []
    evidence_graph: EvidenceGraph = Field(default_factory=EvidenceGraph)
    timeline: List[InvestigationTimelineStep] = []
    
    # Metadata & Quality
    raw_metadata: Dict[str, Any] = {}
    reliability: ReliabilityReport
    historical: HistoricalReport
    
    # Forensic Explainability
    why_this_location: List[str] = []
    contradictions: List[str] = []
    
    # Level resolution
    resolution_level: str = "LEVEL 7 (Country-level prediction)"

class MultiImageStep(BaseModel):
    image_id: str
    filename: str
    sequence_index: int
    role: str  # e.g., "Origin / Departure", "Transit", "Commercial Area", "Landmark"
    candidate: CandidateLocation
    timestamp_estimate: Optional[str] = None
    confidence: float

class MultiImageRouteResult(BaseModel):
    investigation_id: str
    images_analyzed: int
    steps: List[MultiImageStep] = []
    total_distance_km: float = 0.0
    spatial_consistency: float = 0.0
    probable_trajectory: str = ""
    reconstructed_narrative: List[str] = []

class EvaluationMetricCase(BaseModel):
    test_id: str
    name: str
    ground_truth_lat: float
    ground_truth_lng: float
    ground_truth_city: str
    ground_truth_country: str
    predicted_lat: Optional[float] = None
    predicted_lng: Optional[float] = None
    predicted_city: Optional[str] = None
    predicted_country: Optional[str] = None
    predicted_precision: str
    error_distance_km: float
    confidence_score: float
    top1_match: bool
    top5_match: bool
    city_match: bool
    country_match: bool

class EvaluationReport(BaseModel):
    test_cases_evaluated: int
    top1_accuracy_percent: float
    top5_accuracy_percent: float
    country_accuracy_percent: float
    city_accuracy_percent: float
    exact_location_percent: float
    median_error_km: float
    mean_error_km: float
    calibration_bins: List[Dict[str, Any]] = []
    evaluated_cases: List[EvaluationMetricCase] = []
