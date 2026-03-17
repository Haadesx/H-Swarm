import type { Stakeholder, StakeholderEdge } from "../types";

interface GraphProps {
  stakeholders: Stakeholder[];
  edges: StakeholderEdge[];
}

export function StakeholderGraphPreview({ stakeholders, edges }: GraphProps) {
  if (!stakeholders.length) {
    return <div className="empty">No stakeholder map yet. Build the graph to inspect network exposure.</div>;
  }

  const radius = 132;
  const centerX = 180;
  const centerY = 180;
  const nodes = stakeholders.slice(0, 10).map((stakeholder, index, arr) => {
    const angle = (index / arr.length) * Math.PI * 2;
    return {
      ...stakeholder,
      x: centerX + Math.cos(angle) * radius,
      y: centerY + Math.sin(angle) * radius
    };
  });

  return (
    <section className="panel graph-preview">
      <div className="panel-header-row">
        <div>
          <h3>Secondary Network View</h3>
          <p className="subtext">Keep the graph secondary to the matrix, but available for relationship context.</p>
        </div>
      </div>

      <svg viewBox="0 0 360 360" aria-label="stakeholder network">
        {edges.slice(0, 24).map((edge) => {
          const source = nodes.find((node) => node.id === edge.source);
          const target = nodes.find((node) => node.id === edge.target);
          if (!source || !target) {
            return null;
          }
          return (
            <line
              key={edge.id}
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              stroke="rgba(9, 57, 74, 0.25)"
              strokeWidth={1.6}
            />
          );
        })}
        {nodes.map((node) => (
          <g key={node.id}>
            <circle cx={node.x} cy={node.y} r={18} fill="#0b4d5d" />
            <text x={node.x} y={node.y + 4} textAnchor="middle" className="graph-node-label">
              {node.type.slice(0, 1)}
            </text>
          </g>
        ))}
      </svg>

      <div className="legend-inline">
        {nodes.map((node) => (
          <span key={node.id}>
            <strong>{node.type}</strong>: {node.name}
          </span>
        ))}
      </div>
    </section>
  );
}
