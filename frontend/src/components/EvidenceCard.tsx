import { ShieldCheck, AlertTriangle, HelpCircle, Box } from 'lucide-react';
import type { EvidenceItem } from '../api';

interface EvidenceCardProps {
  evidence: EvidenceItem;
  onHighlightBbox?: (evidenceId: string) => void;
}

export default function EvidenceCard({ evidence, onHighlightBbox }: EvidenceCardProps) {
  const polarityClass =
    evidence.polarity === 'supports'
      ? 'evidence-card__type--supports'
      : evidence.polarity === 'contradicts'
      ? 'evidence-card__type--contradicts'
      : 'evidence-card__type--neutral';

  const PolarityIcon =
    evidence.polarity === 'supports'
      ? ShieldCheck
      : evidence.polarity === 'contradicts'
      ? AlertTriangle
      : HelpCircle;

  const confPercent = Math.round(evidence.confidence * 100);

  return (
    <div className="evidence-card">
      <div className="evidence-card__header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span className={`evidence-card__type ${polarityClass}`}>
            <PolarityIcon size={11} style={{ display: 'inline', marginRight: 4, verticalAlign: 'middle' }} />
            {evidence.type}
          </span>

          {evidence.bbox && (
            <span
              onClick={() => onHighlightBbox?.(evidence.id)}
              style={{
                fontSize: '10px',
                fontFamily: 'var(--font-mono)',
                color: 'var(--accent-terracotta)',
                background: 'var(--accent-terracotta-dim)',
                padding: '2px 6px',
                borderRadius: '4px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '3px',
                cursor: onHighlightBbox ? 'pointer' : 'default',
              }}
              title="Has localized bounding box on original image"
            >
              <Box size={10} /> bbox
            </span>
          )}
        </div>

        <div className="evidence-card__confidence">
          {confPercent}%
        </div>
      </div>

      <div className="evidence-card__label">{evidence.label}</div>
      <div className="evidence-card__desc">{evidence.description}</div>

      {(evidence.supporting_candidates.length > 0 || evidence.contradicts_candidates.length > 0) && (
        <div style={{ marginTop: '8px', display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
          {evidence.supporting_candidates.map((candId) => (
            <span
              key={candId}
              style={{
                fontSize: '10px',
                color: 'var(--accent-emerald)',
                background: 'var(--accent-emerald-dim)',
                padding: '2px 6px',
                borderRadius: '3px',
                fontFamily: 'var(--font-mono)',
              }}
            >
              ✓ Supports {candId}
            </span>
          ))}

          {evidence.contradicts_candidates.map((candId) => (
            <span
              key={candId}
              style={{
                fontSize: '10px',
                color: 'var(--accent-red)',
                background: 'var(--accent-red-dim)',
                padding: '2px 6px',
                borderRadius: '3px',
                fontFamily: 'var(--font-mono)',
              }}
            >
              ✗ Contradicts {candId}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
