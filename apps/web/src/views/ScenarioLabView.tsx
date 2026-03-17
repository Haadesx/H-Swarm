import { useState } from "react";
import { KpiTable } from "../components/KpiTable";
import { RiskHeatmap } from "../components/RiskHeatmap";
import { TimelineView } from "../components/TimelineView";
import type { Kpi, RiskCell, Stakeholder, TimelineEvent } from "../types";

interface ScenarioLabViewProps {
  kpis: Kpi[];
  riskHeatmap: RiskCell[];
  timeline: TimelineEvent[];
  stakeholders: Stakeholder[];
  onSimulate: () => Promise<void> | void;
  onAdvance: () => void;
}

export function ScenarioLabView({
  kpis,
  riskHeatmap,
  timeline,
  stakeholders,
  onSimulate,
  onAdvance
}: ScenarioLabViewProps) {
  const [variant, setVariant] = useState<TimelineEvent["variant"]>("base_case");
  const [horizon, setHorizon] = useState<"30" | "90" | "180">("90");
  const stakeholderCount = stakeholders.length;

  return (
    <section className="view">
      <div className="view-header">
        <div>
          <p className="eyebrow">Scenario Lab</p>
          <h2>Replay Impacts</h2>
          <p className="subtext">
            Run base, downside, and severe cases to compare KPI drift, event timing, and stakeholder pressure.
          </p>
        </div>
        <div className="action-row">
          <button type="button" className="secondary-btn" onClick={onAdvance}>
            Go to Memo Workspace
          </button>
          <button type="button" className="primary-btn" onClick={onSimulate}>
            Run Scenario Lab
          </button>
        </div>
      </div>

      <section className="scenario-banner">
        <article className="scenario-banner-card">
          <span className="summary-label">Stakeholders in Play</span>
          <strong>{stakeholderCount}</strong>
        </article>
        <article className="scenario-banner-card">
          <span className="summary-label">Timeline Events</span>
          <strong>{timeline.length}</strong>
        </article>
        <article className="scenario-banner-card">
          <span className="summary-label">KPI Lines</span>
          <strong>{kpis.length}</strong>
        </article>
      </section>

      <KpiTable kpis={kpis} selectedHorizon={horizon} onHorizonChange={setHorizon} />
      <RiskHeatmap rows={riskHeatmap} />
      <TimelineView events={timeline} selectedVariant={variant} onVariantChange={setVariant} />
    </section>
  );
}
