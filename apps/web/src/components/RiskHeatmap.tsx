import type { RiskCell } from "../types";

function scoreClass(score: number): string {
  if (score >= 80) return "risk-high";
  if (score >= 60) return "risk-medium";
  return "risk-low";
}

interface RiskHeatmapProps {
  rows: RiskCell[];
}

export function RiskHeatmap({ rows }: RiskHeatmapProps) {
  return (
    <section className="panel">
      <div className="panel-header-row">
        <div>
          <h3>Risk Heatmap</h3>
          <p className="subtext">Executive readout across operations, finance, access, and regulatory stress.</p>
        </div>
      </div>
      <table className="data-table heatmap">
        <thead>
          <tr>
            <th>Stakeholder</th>
            <th>Operations</th>
            <th>Finance</th>
            <th>Access</th>
            <th>Regulatory</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.stakeholderId}>
              <td>{row.stakeholder}</td>
              <td className={scoreClass(row.operations)}>{row.operations}</td>
              <td className={scoreClass(row.finance)}>{row.finance}</td>
              <td className={scoreClass(row.access)}>{row.access}</td>
              <td className={scoreClass(row.regulatory)}>{row.regulatory}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
