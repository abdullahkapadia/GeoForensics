import { ShieldCheck, AlertTriangle, AlertOctagon, Check, X, FileSearch } from 'lucide-react';
import type { ReliabilityReport } from '../api';

interface ReliabilityViewProps {
  reliability: ReliabilityReport;
  rawMetadata?: Record<string, unknown>;
}

export default function ReliabilityView({ reliability, rawMetadata }: ReliabilityViewProps) {
  const statusLower = reliability.status.toLowerCase();
  const StatusIcon =
    statusLower === 'high'
      ? ShieldCheck
      : statusLower === 'manipulated'
      ? AlertOctagon
      : AlertTriangle;

  const scorePercent = Math.round(reliability.score * 100);

  return (
    <div>
      <div className="reliability-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <div className={`reliability-panel__status reliability-panel__status--${statusLower}`}>
            <StatusIcon size={14} />
            <span>Forensic Integrity: {reliability.status}</span>
          </div>

          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', fontWeight: 700, color: 'var(--accent-terracotta)' }}>
            Score: {scorePercent}%
          </div>
        </div>

        {/* 4 diagnostic checks */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '14px' }}>
          <div style={{ background: 'var(--bg-primary)', padding: '8px 10px', borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Screenshot Check</span>
            {reliability.is_screenshot ? (
              <span style={{ color: 'var(--accent-amber)', fontSize: '10.5px', display: 'flex', alignItems: 'center', gap: '3px' }}>
                <AlertTriangle size={11} /> Detected
              </span>
            ) : (
              <span style={{ color: 'var(--accent-emerald)', fontSize: '10.5px', display: 'flex', alignItems: 'center', gap: '3px' }}>
                <Check size={11} /> Clean
              </span>
            )}
          </div>

          <div style={{ background: 'var(--bg-primary)', padding: '8px 10px', borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>AI Generation</span>
            {reliability.is_ai_generated_indicators ? (
              <span style={{ color: 'var(--accent-red)', fontSize: '10.5px', display: 'flex', alignItems: 'center', gap: '3px' }}>
                <AlertOctagon size={11} /> Flagged
              </span>
            ) : (
              <span style={{ color: 'var(--accent-emerald)', fontSize: '10.5px', display: 'flex', alignItems: 'center', gap: '3px' }}>
                <Check size={11} /> Authentic
              </span>
            )}
          </div>

          <div style={{ background: 'var(--bg-primary)', padding: '8px 10px', borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Compression</span>
            {reliability.compression_anomaly ? (
              <span style={{ color: 'var(--accent-amber)', fontSize: '10.5px', display: 'flex', alignItems: 'center', gap: '3px' }}>
                <AlertTriangle size={11} /> Resaved
              </span>
            ) : (
              <span style={{ color: 'var(--accent-emerald)', fontSize: '10.5px', display: 'flex', alignItems: 'center', gap: '3px' }}>
                <Check size={11} /> Normal
              </span>
            )}
          </div>

          <div style={{ background: 'var(--bg-primary)', padding: '8px 10px', borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Metadata Conflict</span>
            {reliability.metadata_visual_conflict ? (
              <span style={{ color: 'var(--accent-red)', fontSize: '10.5px', display: 'flex', alignItems: 'center', gap: '3px' }}>
                <X size={11} /> Conflict
              </span>
            ) : (
              <span style={{ color: 'var(--accent-emerald)', fontSize: '10.5px', display: 'flex', alignItems: 'center', gap: '3px' }}>
                <Check size={11} /> None
              </span>
            )}
          </div>
        </div>

        {/* Reasons */}
        {reliability.reasons && reliability.reasons.length > 0 && (
          <div>
            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '6px' }}>
              Forensic Integrity Observations
            </div>
            <ul className="reliability-panel__reasons">
              {reliability.reasons.map((reason, index) => (
                <li key={index}>{reason}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Raw metadata viewer */}
      {rawMetadata && Object.keys(rawMetadata).length > 0 && (
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-primary)', borderRadius: 'var(--radius-md)', padding: '14px', marginTop: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '8px' }}>
            <FileSearch size={13} />
            Extracted Metadata Fields
          </div>
          <div style={{ maxHeight: '180px', overflowY: 'auto' }}>
            <table style={{ width: '100%', fontSize: '11.5px', borderCollapse: 'collapse' }}>
              <tbody>
                {Object.entries(rawMetadata).map(([key, val]) => (
                  <tr key={key} style={{ borderBottom: '1px solid var(--border-primary)' }}>
                    <td style={{ padding: '4px 6px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', width: '35%' }}>{key}</td>
                    <td style={{ padding: '4px 6px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
                      {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
