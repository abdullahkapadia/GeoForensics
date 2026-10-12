import { useState } from 'react';
import { X, Eye, EyeOff } from 'lucide-react';
import type { EvidenceItem } from '../api';

interface AnnotatedImageModalProps {
  imageUrl: string;
  evidenceItems: EvidenceItem[];
  highlightedEvidenceId?: string | null;
  onClose: () => void;
}

export default function AnnotatedImageModal({
  imageUrl,
  evidenceItems,
  highlightedEvidenceId,
  onClose,
}: AnnotatedImageModalProps) {
  const [showBboxes, setShowBboxes] = useState(true);

  // Filter items that actually have bounding boxes
  const bboxItems = evidenceItems.filter((e) => e.bbox != null);

  return (
    <div
      className="image-modal-backdrop"
      onClick={onClose}
    >
      <div
        style={{
          position: 'relative',
          maxWidth: '92vw',
          maxHeight: '92vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Controls Bar */}
        <div
          style={{
            position: 'absolute',
            top: '-44px',
            right: 0,
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          {bboxItems.length > 0 && (
            <button
              type="button"
              onClick={() => setShowBboxes(!showBboxes)}
              style={{
                background: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid var(--border-secondary)',
                borderRadius: 'var(--radius-full)',
                color: '#fff',
                padding: '6px 12px',
                fontSize: '12px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                cursor: 'pointer',
              }}
            >
              {showBboxes ? <EyeOff size={14} /> : <Eye size={14} />}
              {showBboxes ? 'Hide Detections' : 'Show Detections'}
            </button>
          )}

          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid var(--border-secondary)',
              borderRadius: '50%',
              color: '#fff',
              width: '32px',
              height: '32px',
              display: 'grid',
              placeItems: 'center',
              cursor: 'pointer',
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Image Container with Absolute Bounding Box Overlays */}
        <div style={{ position: 'relative', display: 'inline-block' }}>
          <img
            src={imageUrl}
            alt="Forensic target preview"
            style={{
              display: 'block',
              maxWidth: '85vw',
              maxHeight: '82vh',
              objectFit: 'contain',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-secondary)',
            }}
          />

          {showBboxes &&
            bboxItems.map((item) => {
              if (!item.bbox) return null;
              const { ymin, xmin, ymax, xmax } = item.bbox;
              const top = `${ymin * 100}%`;
              const left = `${xmin * 100}%`;
              const width = `${(xmax - xmin) * 100}%`;
              const height = `${(ymax - ymin) * 100}%`;

              const isHighlighted = highlightedEvidenceId === item.id;

              return (
                <div
                  key={item.id}
                  className="bbox-overlay"
                  style={{
                    top,
                    left,
                    width,
                    height,
                    borderColor: isHighlighted ? '#c85a32' : undefined,
                    borderWidth: isHighlighted ? '3px' : '2px',
                    boxShadow: isHighlighted ? '0 0 12px rgba(200, 90, 50, 0.6)' : undefined,
                  }}
                >
                  <span
                    className="bbox-overlay__label"
                    style={{
                      background: isHighlighted ? '#c85a32' : undefined,
                    }}
                  >
                    {item.label}
                  </span>
                </div>
              );
            })}
        </div>
      </div>
    </div>
  );
}
