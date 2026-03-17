import type { MitigationOption } from "../types";

interface MitigationComparisonProps {
  options: MitigationOption[];
}

export function MitigationComparison({ options }: MitigationComparisonProps) {
  if (!options.length) {
    return null;
  }

  return (
    <section className="panel">
      <div className="panel-header-row">
        <div>
          <h3>Mitigation Comparison</h3>
          <p className="subtext">Side-by-side strategic lanes for margin defense, access protection, and capital confidence.</p>
        </div>
      </div>

      <div className="mitigation-grid">
        {options.map((option) => (
          <article key={option.id} className="mitigation-card">
            <div className="mitigation-card-top">
              <div>
                <h4>{option.name}</h4>
                <p>{option.positioning}</p>
              </div>
              <strong>{option.composite}/100</strong>
            </div>
            <div className="mitigation-pill-row">
              <span>{option.marginImpact}</span>
              <span>{option.accessImpact}</span>
              <span>{option.trustImpact}</span>
            </div>
            <div className="mitigation-section">
              <span className="eyebrow">Best Use</span>
              <p>{option.bestUse}</p>
            </div>
            <div className="mitigation-section">
              <span className="eyebrow">Tradeoff</span>
              <p>{option.tradeoff}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
