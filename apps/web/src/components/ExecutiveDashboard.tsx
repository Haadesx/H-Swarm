import type { ExecutiveDashboard as ExecutiveDashboardType } from "../types";

interface ExecutiveDashboardProps {
  dashboard: ExecutiveDashboardType | null;
}

export function ExecutiveDashboard({ dashboard }: ExecutiveDashboardProps) {
  if (!dashboard) {
    return null;
  }

  return (
    <section className="panel executive-panel">
      <div className="executive-summary">
        <div>
          <p className="eyebrow">Executive Impact Dashboard</p>
          <h2>{dashboard.title}</h2>
          <p className="subtext executive-text">{dashboard.narrative}</p>
        </div>
        <div className="executive-focus-card">
          <span className="eyebrow">Decision Focus</span>
          <strong>{dashboard.decisionFocus}</strong>
        </div>
      </div>
      <div className="executive-metric-grid">
        {dashboard.metrics.map((metric) => (
          <article key={metric.key} className={`executive-metric executive-metric-${metric.tone}`}>
            <div className="executive-metric-top">
              <span className="eyebrow">{metric.label}</span>
              <strong>{metric.score}/100</strong>
            </div>
            <div className="executive-meter">
              <span style={{ width: `${metric.score}%` }} />
            </div>
            <p>{metric.summary}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
