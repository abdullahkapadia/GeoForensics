import { useState } from 'react';
import { ChevronDown, ChevronUp, MapPin, CheckCircle } from 'lucide-react';
import type { CandidateLocation } from '../api';

interface CandidateCardProps {
  candidate: CandidateLocation;
  rank: number;
  isSelected: boolean;
  onSelect: () => void;
}

export default function CandidateCard({
  candidate,
  rank,
  isSelected,
  onSelect,
}: CandidateCardProps) {
  const [expanded, setExpanded] = useState(rank === 1);
  const scorePercent = candidate.score > 1
    ? Math.min(100, Math.max(0, Math.round(candidate.score)))
    : Math.min(100, Math.max(0, Math.round(candidate.score * 100)));

  return (
    <div
      className={`candidate-card ${rank === 1 ? 'candidate-card--top' : ''} ${
        isSelected ? 'candidate-card--selected' : ''
      }`}
      onClick={onSelect}
      style={{
        outline: isSelected ? '2px solid var(--accent-terracotta)' : 'none',
      }}
    >
      <div className="candidate-card__header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="candidate-card__rank">
            {rank === 1 ? '★ Top Prediction' : `Candidate #${rank}`}
          </div>
          <div className="candidate-card__name">{candidate.name}</div>
          <div className="candidate-card__location">
            <MapPin size={12} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
            {candidate.city ? `${candidate.city}, ` : ''}
            {candidate.state_province ? `${candidate.state_province}, ` : ''}
            {candidate.country}
            {candidate.country_code ? ` (${candidate.country_code})` : ''}
          </div>
        </div>

        <span className={`precision-badge precision-badge--${candidate.precision_level || 'unknown'}`}>
          {candidate.precision_level || 'approximate'}
        </span>
      </div>

      <div className="candidate-card__score-row">
        <div className="candidate-card__score-bar">
          <div
            className="candidate-card__score-fill"
            style={{ width: `${scorePercent}%` }}
          />
        </div>
        <div className="candidate-card__score-num">{scorePercent}%</div>
      </div>

      {candidate.resolved_address && (
        <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '8px', fontFamily: 'var(--font-mono)' }}>
          {candidate.resolved_address}
        </div>
      )}

      {candidate.uncertainty_radius_km && (
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
          Radius: ±{candidate.uncertainty_radius_km} km
        </div>
      )}

      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          setExpanded(!expanded);
        }}
        style={{
          background: 'none',
          border: 'none',
          color: 'var(--text-tertiary)',
          fontSize: '11.5px',
          cursor: 'pointer',
          padding: '6px 0 0 0',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          fontFamily: 'var(--font-sans)',
        }}
      >
        {expanded ? (
          <>
            <ChevronUp size={14} /> Hide Breakdown & Rationale
          </>
        ) : (
          <>
            <ChevronDown size={14} /> View Breakdown & Rationale
          </>
        )}
      </button>

      {expanded && (
        <div style={{ marginTop: '12px', borderTop: '1px solid var(--border-primary)', paddingTop: '10px' }}>
          {candidate.score_breakdown && (
            <>
              <div style={{ fontSize: '10.5px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '6px' }}>
                Score Attribution
              </div>
              <div className="score-breakdown">
                {candidate.score_breakdown.ocr > 0 && (
                  <div className="score-breakdown__item">
                    <span className="score-breakdown__item-label">OCR / Script</span>
                    <span className="score-breakdown__item-value">{(candidate.score_breakdown.ocr * 100).toFixed(0)}%</span>
                  </div>
                )}
                {candidate.score_breakdown.landmark > 0 && (
                  <div className="score-breakdown__item">
                    <span className="score-breakdown__item-label">Landmark</span>
                    <span className="score-breakdown__item-value">{(candidate.score_breakdown.landmark * 100).toFixed(0)}%</span>
                  </div>
                )}
                {candidate.score_breakdown.visual_similarity > 0 && (
                  <div className="score-breakdown__item">
                    <span className="score-breakdown__item-label">Visual Sim</span>
                    <span className="score-breakdown__item-value">{(candidate.score_breakdown.visual_similarity * 100).toFixed(0)}%</span>
                  </div>
                )}
                {candidate.score_breakdown.geospatial > 0 && (
                  <div className="score-breakdown__item">
                    <span className="score-breakdown__item-label">Geospatial</span>
                    <span className="score-breakdown__item-value">{(candidate.score_breakdown.geospatial * 100).toFixed(0)}%</span>
                  </div>
                )}
                {candidate.score_breakdown.architecture > 0 && (
                  <div className="score-breakdown__item">
                    <span className="score-breakdown__item-label">Architecture</span>
                    <span className="score-breakdown__item-value">{(candidate.score_breakdown.architecture * 100).toFixed(0)}%</span>
                  </div>
                )}
                {candidate.score_breakdown.environment > 0 && (
                  <div className="score-breakdown__item">
                    <span className="score-breakdown__item-label">Environment</span>
                    <span className="score-breakdown__item-value">{(candidate.score_breakdown.environment * 100).toFixed(0)}%</span>
                  </div>
                )}
                {candidate.score_breakdown.exif > 0 && (
                  <div className="score-breakdown__item">
                    <span className="score-breakdown__item-label">EXIF GPS</span>
                    <span className="score-breakdown__item-value">{(candidate.score_breakdown.exif * 100).toFixed(0)}%</span>
                  </div>
                )}
                {candidate.score_breakdown.contradiction_penalty > 0 && (
                  <div className="score-breakdown__item" style={{ borderColor: 'rgba(239, 68, 68, 0.4)' }}>
                    <span className="score-breakdown__item-label" style={{ color: 'var(--accent-red)' }}>Contradiction</span>
                    <span className="score-breakdown__item-value" style={{ color: 'var(--accent-red)' }}>
                      -{(candidate.score_breakdown.contradiction_penalty * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
              </div>
            </>
          )}

          {candidate.rationale && candidate.rationale.length > 0 && (
            <div style={{ marginTop: '12px' }}>
              <div style={{ fontSize: '10.5px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '6px' }}>
                Forensic Rationale
              </div>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {candidate.rationale.map((r, i) => (
                  <li key={i} style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'flex-start', gap: '6px', lineHeight: '1.4' }}>
                    <CheckCircle size={12} style={{ color: 'var(--accent-terracotta)', marginTop: '2px', flexShrink: 0 }} />
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
