import { CASE_VARIANTS } from "../contracts";
import type { HorizonKey, Kpi } from "../types";

function formatMetric(value: number | null, unit: string): string {
  if (value === null) {
    return "-";
  }
  return `${value.toFixed(1)}${unit}`;
}

function formatDelta(value: number | null, unit: string): string {
  if (value === null) {
    return "-";
  }
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}${unit}`;
}

interface KpiTableProps {
  kpis: Kpi[];
  selectedHorizon: HorizonKey;
  onHorizonChange: (horizon: HorizonKey) => void;
}

export function KpiTable({ kpis, selectedHorizon, onHorizonChange }: KpiTableProps) {
  return (
    <section className="panel">
      <div className="panel-header-row">
        <div>
          <h3>KPI Delta Grid</h3>
          <p className="subtext">Track baseline, projected state, and directional change across scenario variants.</p>
        </div>
        <div className="horizon-tabs">
          {(["30", "90", "180"] as const).map((horizon) => (
            <button
              key={horizon}
              className={selectedHorizon === horizon ? "active" : ""}
              type="button"
              onClick={() => onHorizonChange(horizon)}
            >
              Day {horizon}
            </button>
          ))}
        </div>
      </div>

      <table className="data-table">
        <thead>
          <tr>
            <th>KPI</th>
            <th>Baseline</th>
            {CASE_VARIANTS.map((variant) => (
              <th key={variant.id}>{variant.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {kpis.map((kpi) => (
            <tr key={kpi.id}>
              <td>
                <strong>{kpi.label}</strong>
              </td>
              <td>{formatMetric(kpi.baseline, kpi.unit)}</td>
              {CASE_VARIANTS.map((variant) => {
                const cell = kpi.byHorizon[selectedHorizon][variant.id];
                return (
                  <td key={variant.id}>
                    <div className="metric-stack">
                      <span>{formatMetric(cell?.projected ?? null, kpi.unit)}</span>
                      <small>{formatDelta(cell?.delta ?? null, kpi.unit)}</small>
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
