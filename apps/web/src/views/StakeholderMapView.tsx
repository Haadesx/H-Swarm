import { StakeholderGraphPreview } from "../components/StakeholderGraphPreview";
import type { Stakeholder, StakeholderEdge } from "../types";

interface StakeholderMapViewProps {
  stakeholders: Stakeholder[];
  edges: StakeholderEdge[];
  onBuildMap: () => Promise<void> | void;
}

export function StakeholderMapView({ stakeholders, edges, onBuildMap }: StakeholderMapViewProps) {
  return (
    <section className="view">
      <div className="view-header">
        <div>
          <p className="eyebrow">Stakeholder Map</p>
          <h2>Inspect Stakeholders</h2>
          <p className="subtext">
            Build the healthcare stakeholder network, then inspect incentive conflict, exposure, and likely reactions.
          </p>
        </div>
        <button type="button" className="primary-btn" onClick={onBuildMap}>
          Build Stakeholder Graph
        </button>
      </div>

      <div className="layout-two">
        <section className="panel">
          <div className="panel-header-row">
            <div>
              <h3>Stakeholder Matrix</h3>
              <p className="subtext">Use the matrix first. The graph remains available as supporting context.</p>
            </div>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Stakeholder</th>
                <th>Incentive</th>
                <th>Pressure Point</th>
                <th>Likely Reaction</th>
                <th>Influence</th>
              </tr>
            </thead>
            <tbody>
              {stakeholders.map((stakeholder) => (
                <tr key={stakeholder.id}>
                  <td>
                    <strong>{stakeholder.name}</strong>
                    <p className="cell-meta">{stakeholder.type}</p>
                  </td>
                  <td>{stakeholder.incentive}</td>
                  <td>{stakeholder.pressurePoint}</td>
                  <td>{stakeholder.likelyReaction}</td>
                  <td>{stakeholder.influence}</td>
                </tr>
              ))}
              {!stakeholders.length ? (
                <tr>
                  <td colSpan={5} className="empty">
                    No stakeholders yet. Build the graph to populate the matrix.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </section>

        <StakeholderGraphPreview stakeholders={stakeholders} edges={edges} />
      </div>
    </section>
  );
}
