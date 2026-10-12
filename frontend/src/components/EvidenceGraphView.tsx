import { useState } from 'react';
import { Share2 } from 'lucide-react';
import type { EvidenceGraph } from '../api';

interface EvidenceGraphViewProps {
  graph: EvidenceGraph;
}

export default function EvidenceGraphView({ graph }: EvidenceGraphViewProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  if (!graph || !graph.nodes || graph.nodes.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state__icon">🕸</div>
        <div className="empty-state__text">No evidence graph generated for this image.</div>
      </div>
    );
  }

  const getNodeClass = (type: string) => {
    const t = type.toLowerCase();
    if (t.includes('image')) return 'graph-node--image';
    if (t.includes('meta') || t.includes('exif')) return 'graph-node--metadata';
    if (t.includes('ocr') || t.includes('text')) return 'graph-node--ocr';
    if (t.includes('landmark')) return 'graph-node--landmark';
    if (t.includes('road')) return 'graph-node--road';
    if (t.includes('geo')) return 'graph-node--geo';
    if (t.includes('candidate') || t.includes('location')) return 'graph-node--candidate';
    if (t.includes('arch')) return 'graph-node--architecture';
    return 'graph-node--object';
  };

  const getRelationClass = (relation: string) => {
    const r = relation.toLowerCase();
    if (r.includes('support')) return 'graph-edge__relation--supports';
    if (r.includes('contradict')) return 'graph-edge__relation--contradicts';
    return 'graph-edge__relation--derived';
  };

  const filteredEdges = selectedNodeId
    ? graph.edges.filter((e) => e.source === selectedNodeId || e.target === selectedNodeId)
    : graph.edges;

  return (
    <div className="graph-container">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.6px' }}>
          <Share2 size={13} />
          Evidence & Hypothesis Graph ({graph.nodes.length} Nodes, {graph.edges.length} Edges)
        </div>
        {selectedNodeId && (
          <button
            onClick={() => setSelectedNodeId(null)}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--accent-terracotta)',
              fontSize: '11px',
              cursor: 'pointer',
              textDecoration: 'underline',
            }}
          >
            Clear Filter
          </button>
        )}
      </div>

      <div style={{ marginBottom: '14px' }}>
        <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginBottom: '8px' }}>
          Click a node to filter incident edges:
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
          {graph.nodes.map((node) => {
            const isSelected = node.id === selectedNodeId;
            return (
              <button
                key={node.id}
                type="button"
                className={`graph-node ${getNodeClass(node.type)}`}
                onClick={() => setSelectedNodeId(isSelected ? null : node.id)}
                style={{
                  cursor: 'pointer',
                  transform: isSelected ? 'scale(1.05)' : 'none',
                  boxShadow: isSelected ? '0 0 10px rgba(200, 90, 50, 0.4)' : 'none',
                }}
              >
                <span>{node.label}</span>
                <span style={{ fontSize: '9px', opacity: 0.7, textTransform: 'uppercase' }}>
                  [{node.type}]
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <div className="graph-edges">
        <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '4px' }}>
          {selectedNodeId ? `Edges connected to "${selectedNodeId}"` : 'Forensic Relations'}
        </div>
        <div style={{ maxHeight: '240px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {filteredEdges.map((edge, index) => {
            const sourceNode = graph.nodes.find((n) => n.id === edge.source);
            const targetNode = graph.nodes.find((n) => n.id === edge.target);

            return (
              <div key={index} className="graph-edge" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                    {sourceNode ? sourceNode.label : edge.source}
                  </span>
                  <span className={`graph-edge__relation ${getRelationClass(edge.relation)}`}>
                    —[{edge.relation}]→
                  </span>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                    {targetNode ? targetNode.label : edge.target}
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0 }}>
                  <span style={{ color: 'var(--accent-terracotta)', fontSize: '10.5px' }}>
                    w: {edge.weight.toFixed(2)}
                  </span>
                  {edge.notes && (
                    <span style={{ color: 'var(--text-muted)', fontSize: '10px' }} title={edge.notes}>
                      ({edge.notes})
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
