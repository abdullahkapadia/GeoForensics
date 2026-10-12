import { CheckCircle2, Clock, XCircle, AlertCircle } from 'lucide-react';
import type { TimelineStep } from '../api';

interface TimelineViewProps {
  timeline: TimelineStep[];
}

export default function TimelineView({ timeline }: TimelineViewProps) {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state__icon">⏱</div>
        <div className="empty-state__text">No timeline events recorded for this analysis.</div>
      </div>
    );
  }

  const getStatusIcon = (status: TimelineStep['status']) => {
    switch (status) {
      case 'COMPLETED':
        return <CheckCircle2 size={13} style={{ color: 'var(--accent-emerald)' }} />;
      case 'FAILED':
        return <XCircle size={13} style={{ color: 'var(--accent-red)' }} />;
      case 'IN_PROGRESS':
        return <Clock size={13} style={{ color: 'var(--accent-terracotta)' }} />;
      case 'SKIPPED':
      default:
        return <AlertCircle size={13} style={{ color: 'var(--accent-amber)' }} />;
    }
  };

  return (
    <div className="timeline-list">
      {timeline.map((step) => {
        const isFailed = step.status === 'FAILED';
        return (
          <div key={step.step_number} className="timeline-step">
            <div className={`timeline-step__dot ${isFailed ? 'timeline-step__dot--failed' : ''}`}>
              {step.step_number}
            </div>

            <div className="timeline-step__body">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
                <span className="timeline-step__title">{step.title}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {getStatusIcon(step.status)}
                  {typeof step.duration_ms === 'number' && (
                    <span className="timeline-step__duration">{step.duration_ms} ms</span>
                  )}
                </div>
              </div>

              <div className="timeline-step__detail">{step.detail}</div>

              {step.timestamp && (
                <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
                  {new Date(step.timestamp).toLocaleTimeString()}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
