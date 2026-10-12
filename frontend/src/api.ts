const API_BASE = 'http://localhost:8000/api/v1';

export interface BoundingBox {
  ymin: number;
  xmin: number;
  ymax: number;
  xmax: number;
  label?: string;
}

export interface EvidenceItem {
  id: string;
  type: string;
  label: string;
  description: string;
  confidence: number;
  bbox?: BoundingBox | null;
  supporting_candidates: string[];
  contradicts_candidates: string[];
  polarity: 'supports' | 'contradicts' | 'neutral';
  metadata_details?: Record<string, unknown> | null;
}

export interface ScoreBreakdown {
  ocr: number;
  landmark: number;
  visual_similarity: number;
  geospatial: number;
  architecture: number;
  environment: number;
  exif: number;
  contradiction_penalty: number;
}

export interface CandidateLocation {
  id: string;
  name: string;
  city: string;
  state_province: string;
  country: string;
  country_code: string;
  lat: number;
  lng: number;
  score: number;
  precision_level: 'exact' | 'probable' | 'approximate' | 'regional' | 'unknown';
  uncertainty_radius_km?: number | null;
  supporting_evidence_ids: string[];
  contradicting_evidence_ids: string[];
  score_breakdown: ScoreBreakdown;
  rationale: string[];
  resolved_address?: string | null;
  place_type?: string | null;
}

export interface EvidenceGraphNode {
  id: string;
  label: string;
  type: string;
  confidence?: number | null;
}

export interface EvidenceGraphEdge {
  source: string;
  target: string;
  relation: string;
  weight: number;
  notes?: string | null;
}

export interface EvidenceGraph {
  nodes: EvidenceGraphNode[];
  edges: EvidenceGraphEdge[];
}

export interface TimelineStep {
  step_number: number;
  title: string;
  status: 'COMPLETED' | 'IN_PROGRESS' | 'FAILED' | 'SKIPPED';
  duration_ms?: number | null;
  detail: string;
  timestamp: string;
}

export interface ReliabilityReport {
  status: 'HIGH' | 'QUESTIONABLE' | 'MANIPULATED';
  score: number;
  reasons: string[];
  metadata_visual_conflict: boolean;
  is_screenshot: boolean;
  is_ai_generated_indicators: boolean;
  compression_anomaly: boolean;
  details: Record<string, unknown>;
}

export interface GeolocationResult {
  analysis_id: string;
  image_id: string;
  filename: string;
  status: string;
  top_prediction?: CandidateLocation | null;
  precision: string;
  confidence_score: number;
  confidence_level: string;
  uncertainty_radius_km?: number | null;
  resolved_address?: string | null;
  candidates: CandidateLocation[];
  evidence_items: EvidenceItem[];
  evidence_graph: EvidenceGraph;
  timeline: TimelineStep[];
  raw_metadata: Record<string, unknown>;
  reliability: ReliabilityReport;
  why_this_location: string[];
  contradictions: string[];
  resolution_level: string;
}

export interface UploadResponse {
  analysis_id: string;
  image_id: string;
  status: string;
  message: string;
}

export async function uploadImage(file: File, cues?: string): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (cues && cues.trim()) {
    formData.append('cues', cues.trim());
  }

  const res = await fetch(`${API_BASE}/images/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || `Upload failed (${res.status})`);
  }

  return res.json();
}

export async function getAnalysis(analysisId: string): Promise<GeolocationResult> {
  const res = await fetch(`${API_BASE}/geolocation/${analysisId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch analysis (${res.status})`);
  }
  return res.json();
}
