import { useState, useEffect } from 'react';
import {
  Compass,
  ArrowLeft,
  AlertTriangle,
  Layers,
  MapPin,
  CheckCircle,
  Share2,
  Clock,
  RotateCcw,
} from 'lucide-react';
import { uploadImage, getAnalysis } from './api';
import type { GeolocationResult } from './api';
import 'leaflet/dist/leaflet.css';
import './App.css';

import UploadZone from './components/UploadZone';
import MapViewer from './components/MapViewer';
import CandidateCard from './components/CandidateCard';
import EvidenceCard from './components/EvidenceCard';
import TimelineView from './components/TimelineView';
import ReliabilityView from './components/ReliabilityView';
import EvidenceGraphView from './components/EvidenceGraphView';
import AnnotatedImageModal from './components/AnnotatedImageModal';

type TabKey = 'candidates' | 'evidence' | 'report' | 'graph' | 'timeline';

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [cues, setCues] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GeolocationResult | null>(null);
  const [activeTab, setActiveTab] = useState<TabKey>('candidates');
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const [imageModalOpen, setImageModalOpen] = useState<boolean>(false);
  const [highlightedEvidenceId, setHighlightedEvidenceId] = useState<string | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  // Check backend health on mount
  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then((res) => (res.ok ? setBackendOnline(true) : setBackendOnline(false)))
      .catch(() => setBackendOnline(false));
  }, []);

  const handleFileSelected = (selectedFile: File | null) => {
    if (!selectedFile) {
      setFile(null);
      setPreviewUrl(null);
      setError(null);
      return;
    }
    setFile(selectedFile);
    try {
      const objectUrl = URL.createObjectURL(selectedFile);
      setPreviewUrl(objectUrl);
    } catch {
      setPreviewUrl(null);
    }
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      const uploadRes = await uploadImage(file, cues);
      // Backend performs synchronous analysis in the endpoint and returns analysis_id
      const analysisData = await getAnalysis(uploadRes.analysis_id);
      setResult(analysisData);
      if (analysisData.candidates && analysisData.candidates.length > 0) {
        setSelectedCandidateId(analysisData.candidates[0].id);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Analysis failed. Please verify the backend is running.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setFile(null);
    setPreviewUrl(null);
    setCues('');
    setError(null);
    setSelectedCandidateId(null);
    setActiveTab('candidates');
  };

  const topCandidate = result?.top_prediction || (result?.candidates && result.candidates[0]) || null;
  const confidencePercent = result
    ? result.confidence_score > 1
      ? Math.min(100, Math.round(result.confidence_score))
      : Math.min(100, Math.round(result.confidence_score * 100))
    : 0;

  return (
    <div className="app-shell">
      {/* Top Command Bar */}
      <header className="top-bar">
        <div className="top-bar__left">
          <div className="top-bar__brand">
            <div className="top-bar__emblem">
              <Compass size={14} strokeWidth={2.4} />
            </div>
            <div className="top-bar__title-block">
              <div className="top-bar__app-name">
                GEOFORENSICS <span className="top-bar__dot">•</span> <span className="top-bar__sub-brand">LAB</span>
              </div>
              <div className="top-bar__tagline">
                OPEN-SOURCE INTELLIGENCE & FORENSIC GEOLOCATION
              </div>
            </div>
          </div>
        </div>

        {/* Center: Live Engine Pipeline Matrix */}
        <div className="top-bar__center">
          <div className="engine-matrix">
            <div className="engine-node">
              <span className="engine-node__dot" />
              <span className="engine-node__key">VISION:</span>
              <span className="engine-node__val">GEMINI 3.1</span>
            </div>
            <div className="engine-divider" />
            <div className="engine-node">
              <span className="engine-node__dot" />
              <span className="engine-node__key">SPATIAL:</span>
              <span className="engine-node__val">OSM NOMINATIM</span>
            </div>
            <div className="engine-divider" />
            <div className="engine-node">
              <span className="engine-node__dot" />
              <span className="engine-node__key">METADATA:</span>
              <span className="engine-node__val">EXIF FORENSICS</span>
            </div>
            <div className="engine-divider" />
            <div className="engine-node">
              <span className="engine-node__dot" />
              <span className="engine-node__key">OCR:</span>
              <span className="engine-node__val">MULTILINGUAL</span>
            </div>
          </div>
        </div>

        {/* Right: Telemetry & Actions */}
        <div className="top-bar__right">
          <div className="telemetry-chip">
            <div
              className="telemetry-chip__dot"
              style={{
                background:
                  backendOnline === true
                    ? 'var(--status-verified)'
                    : backendOnline === false
                    ? 'var(--status-critical)'
                    : 'var(--accent-sand)',
              }}
            />
            <span className="telemetry-chip__label">PIPELINE:</span>
            <span className="telemetry-chip__status">
              {backendOnline === true
                ? 'OPERATIONAL'
                : backendOnline === false
                ? 'OFFLINE'
                : 'CONNECTING'}
            </span>
          </div>

          <div className="dossier-pill">
            <span className="dossier-pill__prefix">DOSSIER</span>
            <span className="dossier-pill__id">#GF-2026-X</span>
          </div>

          {result && (
            <button type="button" className="top-bar__action-btn" onClick={handleReset}>
              <RotateCcw size={12} />
              Reset Workspace
            </button>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="main-content">
        {error && (
          <div
            style={{
              padding: '12px 24px',
              background: 'var(--status-critical-dim)',
              borderBottom: '1px solid rgba(181, 39, 39, 0.25)',
              color: 'var(--status-critical)',
              fontSize: '13px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* View 1: Upload View */}
        {!result && !loading && (
          <UploadZone
            onFileSelected={handleFileSelected}
            selectedFile={file}
            previewUrl={previewUrl}
            cues={cues}
            onCuesChange={setCues}
            onUpload={handleUpload}
            uploading={loading}
          />
        )}

        {/* View 2: Processing Overlay */}
        {loading && (
          <div className="processing-overlay">
            <div className="processing-spinner" />
            <div className="processing-text">
              Executing Multi-Modal Forensic Pipeline…
            </div>
            <div className="processing-sub">
              Extracting EXIF metadata, identifying utility pole patterns & road markings,
              performing multilingual OCR, resolving terrain elevation, and querying OpenStreetMap road nodes.
            </div>
          </div>
        )}

        {/* View 3: Results Dashboard */}
        {result && !loading && (
          <div className="results-layout">
            {/* Top Intelligence Ribbon */}
            <div className="summary-bar">
              <div className="summary-bar__primary">
                <button type="button" className="summary-bar__return-btn" onClick={handleReset}>
                  <ArrowLeft size={13} />
                  Return to Intake
                </button>

                <div className="summary-bar__headline">
                  <span className="summary-bar__tag">TOP GEO-LOCATION PREDICTION</span>
                  <span className="summary-bar__location-name">
                    {topCandidate ? topCandidate.name : 'Location Discovered'}
                    {topCandidate?.country ? `, ${topCandidate.country}` : ''}
                  </span>
                  <div className="summary-bar__address-row">
                    <span className="summary-bar__address">
                      {result.resolved_address || (topCandidate?.resolved_address ?? 'Coordinates resolved on map')}
                    </span>
                  </div>
                </div>
              </div>

              <div className="summary-bar__metrics">
                <div className="metric-gauge">
                  <span className="metric-gauge__label">Confidence</span>
                  <span className="metric-gauge__value">{confidencePercent}%</span>
                </div>

                <div className="metric-gauge">
                  <span className="metric-gauge__label">Precision</span>
                  <span className="metric-gauge__value" style={{ textTransform: 'capitalize' }}>
                    {result.precision || 'Probable'}
                  </span>
                </div>

                <div className="metric-gauge">
                  <span className="metric-gauge__label">Uncertainty</span>
                  <span className="metric-gauge__value">
                    {result.uncertainty_radius_km ? `±${result.uncertainty_radius_km} km` : '±10 km'}
                  </span>
                </div>

                <div className="metric-gauge">
                  <span className="metric-gauge__label">Resolution</span>
                  <span className="metric-gauge__value" style={{ textTransform: 'uppercase' }}>
                    {result.resolution_level || 'City'}
                  </span>
                </div>
              </div>
            </div>

            {/* Left Panel: Map & Image */}
            <section className="left-panel">
              <MapViewer
                candidates={result.candidates}
                selectedCandidateId={selectedCandidateId}
                onSelectCandidate={(id) => setSelectedCandidateId(id)}
                previewUrl={previewUrl}
                onOpenImageModal={() => setImageModalOpen(true)}
              />
            </section>

            {/* Right Panel: Forensic Workbench Tabs */}
            <section className="right-panel">
              <nav className="tab-bar">
                <button
                  type="button"
                  className={`tab-bar__item ${activeTab === 'candidates' ? 'tab-bar__item--active' : ''}`}
                  onClick={() => setActiveTab('candidates')}
                >
                  <MapPin size={12} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
                  Candidates ({result.candidates.length})
                </button>

                <button
                  type="button"
                  className={`tab-bar__item ${activeTab === 'evidence' ? 'tab-bar__item--active' : ''}`}
                  onClick={() => setActiveTab('evidence')}
                >
                  <Layers size={12} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
                  Evidence ({result.evidence_items.length})
                </button>

                <button
                  type="button"
                  className={`tab-bar__item ${activeTab === 'report' ? 'tab-bar__item--active' : ''}`}
                  onClick={() => setActiveTab('report')}
                >
                  <CheckCircle size={12} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
                  Forensic Report
                </button>

                <button
                  type="button"
                  className={`tab-bar__item ${activeTab === 'graph' ? 'tab-bar__item--active' : ''}`}
                  onClick={() => setActiveTab('graph')}
                >
                  <Share2 size={12} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
                  Graph
                </button>

                <button
                  type="button"
                  className={`tab-bar__item ${activeTab === 'timeline' ? 'tab-bar__item--active' : ''}`}
                  onClick={() => setActiveTab('timeline')}
                >
                  <Clock size={12} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
                  Timeline ({result.timeline.length})
                </button>
              </nav>

              <div className="tab-content">
                {/* Tab 1: Candidates */}
                {activeTab === 'candidates' && (
                  <div>
                    <div className="section-header">Ranked Geographic Hypotheses</div>
                    {result.candidates.map((cand, index) => (
                      <CandidateCard
                        key={cand.id}
                        candidate={cand}
                        rank={index + 1}
                        isSelected={cand.id === selectedCandidateId}
                        onSelect={() => setSelectedCandidateId(cand.id)}
                      />
                    ))}
                  </div>
                )}

                {/* Tab 2: Evidence Items */}
                {activeTab === 'evidence' && (
                  <div>
                    <div className="section-header">Extracted Forensic Cues</div>
                    {result.evidence_items.map((item) => (
                      <EvidenceCard
                        key={item.id}
                        evidence={item}
                        onHighlightBbox={(id) => {
                          setHighlightedEvidenceId(id);
                          setImageModalOpen(true);
                        }}
                      />
                    ))}
                  </div>
                )}

                {/* Tab 3: Forensic Report & Explainability */}
                {activeTab === 'report' && (
                  <div>
                    <div className="section-header">Image Authenticity & Tampering Audit</div>
                    {result.reliability && (
                      <ReliabilityView
                        reliability={result.reliability}
                        rawMetadata={result.raw_metadata}
                      />
                    )}

                    <div className="section-header" style={{ marginTop: '20px' }}>
                      Why This Location?
                    </div>
                    {result.why_this_location && result.why_this_location.length > 0 ? (
                      <div className="explanation-list">
                        {result.why_this_location.map((item, idx) => (
                          <div key={idx} className="explanation-item">
                            {item}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="empty-state">
                        <div className="empty-state__text">No specific explanations generated.</div>
                      </div>
                    )}

                    {result.contradictions && result.contradictions.length > 0 && (
                      <>
                        <div className="section-header" style={{ marginTop: '20px', color: 'var(--accent-red)' }}>
                          Identified Contradictions & Discarded Hypotheses
                        </div>
                        <div className="explanation-list">
                          {result.contradictions.map((item, idx) => (
                            <div key={idx} className="explanation-item explanation-item--contradiction">
                              {item}
                            </div>
                          ))}
                        </div>
                      </>
                    )}
                  </div>
                )}

                {/* Tab 4: Evidence Graph */}
                {activeTab === 'graph' && (
                  <div>
                    <div className="section-header">Knowledge & Evidence Relationship Network</div>
                    <EvidenceGraphView graph={result.evidence_graph} />
                  </div>
                )}

                {/* Tab 5: Pipeline Timeline */}
                {activeTab === 'timeline' && (
                  <div>
                    <div className="section-header">Pipeline Execution Audit Log</div>
                    <TimelineView timeline={result.timeline} />
                  </div>
                )}
              </div>
            </section>
          </div>
        )}
      </main>

      {/* Image inspection modal */}
      {imageModalOpen && previewUrl && (
        <AnnotatedImageModal
          imageUrl={previewUrl}
          evidenceItems={result?.evidence_items || []}
          highlightedEvidenceId={highlightedEvidenceId}
          onClose={() => {
            setImageModalOpen(false);
            setHighlightedEvidenceId(null);
          }}
        />
      )}
    </div>
  );
}
