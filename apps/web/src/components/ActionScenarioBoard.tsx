import type { ActionScenario } from "../types";

interface ActionScenarioBoardProps {
  scenarios: ActionScenario[];
}

export function ActionScenarioBoard({ scenarios }: ActionScenarioBoardProps) {
  if (!scenarios.length) {
    return null;
  }

  return (
    <section className="panel">
      <div className="panel-header-row">
        <div>
          <h3>30 / 90 / 180 Day Action Scenarios</h3>
          <p className="subtext">Translate the replay into concrete operating, capital, and board actions over each horizon.</p>
        </div>
      </div>

      <div className="scenario-board-grid">
        {scenarios.map((scenario) => (
          <article key={scenario.horizonDays} className="scenario-board-card">
            <div className="scenario-window">Day {scenario.horizonDays}</div>
            <h4>{scenario.title}</h4>
            <p>{scenario.summary}</p>
            <div className="scenario-board-section">
              <span className="eyebrow">Operating Focus</span>
              <p>{scenario.operatingFocus}</p>
            </div>
            <div className="scenario-board-section">
              <span className="eyebrow">Capital Focus</span>
              <p>{scenario.capitalFocus}</p>
            </div>
            <div className="scenario-board-section">
              <span className="eyebrow">Board Ask</span>
              <p>{scenario.boardAsk}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
