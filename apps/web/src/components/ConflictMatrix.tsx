import type { StakeholderConflict } from "../types";

interface ConflictMatrixProps {
  rows: StakeholderConflict[];
}

function intensityClass(score: number): string {
  if (score >= 75) return "critical";
  if (score >= 50) return "elevated";
  return "stable";
}

export function ConflictMatrix({ rows }: ConflictMatrixProps) {
  if (!rows.length) {
    return null;
  }

  return (
    <section className="panel">
      <div className="panel-header-row">
        <div>
          <h3>Stakeholder Conflict Matrix</h3>
          <p className="subtext">The highest-friction stakeholders, their likely moves, and the response each one demands.</p>
        </div>
      </div>

      <div className="conflict-grid">
        {rows.map((row) => (
          <article key={row.stakeholderId} className="conflict-card">
            <div className="conflict-card-top">
              <div>
                <p className="eyebrow">{row.group}</p>
                <h4>{row.stakeholder}</h4>
              </div>
              <span className={`conflict-badge ${intensityClass(row.intensity)}`}>{row.intensity}/100</span>
            </div>
            <div className="conflict-content">
              <div>
                <span className="eyebrow">Concern</span>
                <p>{row.concern}</p>
              </div>
              <div>
                <span className="eyebrow">Likely Move</span>
                <p>{row.likelyMove}</p>
              </div>
              <div>
                <span className="eyebrow">Pressure</span>
                <p>{row.pressure}</p>
              </div>
              <div>
                <span className="eyebrow">Response</span>
                <p>{row.response}</p>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
