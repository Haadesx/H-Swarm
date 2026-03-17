import { useMemo, useState } from "react";
import { PRIMARY_SCENARIO, SCENARIO_TEMPLATES } from "../contracts";
import type { NewRunInput } from "../types";

interface NewDecisionRunViewProps {
  onCreate: (input: NewRunInput) => Promise<void> | void;
  onLoadDemo: () => Promise<void> | void;
}

export function NewDecisionRunView({ onCreate, onLoadDemo }: NewDecisionRunViewProps) {
  const [projectName, setProjectName] = useState("Regional Provider Reimbursement Stress Test");
  const [organizationName, setOrganizationName] = useState("MetroCare Health System");
  const [scenarioType, setScenarioType] = useState(PRIMARY_SCENARIO);
  const selectedTemplate = useMemo(
    () => SCENARIO_TEMPLATES.find((item) => item.id === scenarioType) ?? SCENARIO_TEMPLATES[0],
    [scenarioType]
  );
  const [simulationRequirement, setSimulationRequirement] = useState(selectedTemplate.defaultRequirement);

  function handleScenarioChange(next: string) {
    setScenarioType(next);
    const template = SCENARIO_TEMPLATES.find((item) => item.id === next);
    if (template) {
      setSimulationRequirement(template.defaultRequirement);
    }
  }

  return (
    <section className="view">
      <div className="view-header">
        <div>
          <p className="eyebrow">Case Intake</p>
          <h2>Define Scenario</h2>
          <p className="subtext">
            Frame the operating shock, then generate a decision run for healthcare operators and capital stakeholders.
          </p>
        </div>
        <button type="button" className="secondary-btn" onClick={onLoadDemo}>
          Load MetroCare Demo
        </button>
      </div>

      <div className="form-grid">
        <label>
          Project Name
          <input value={projectName} onChange={(event) => setProjectName(event.target.value)} />
        </label>

        <label>
          Organization
          <input value={organizationName} onChange={(event) => setOrganizationName(event.target.value)} />
        </label>

        <label>
          Scenario Template
          <select value={scenarioType} onChange={(event) => handleScenarioChange(event.target.value)}>
            {SCENARIO_TEMPLATES.map((template) => (
              <option key={template.id} value={template.id}>
                {template.label}
              </option>
            ))}
          </select>
        </label>

        <article className="scenario-summary">
          <p className="eyebrow">Current Template</p>
          <h3>{selectedTemplate.label}</h3>
          <p>{selectedTemplate.summary}</p>
        </article>

        <label className="full-width">
          Decision Question
          <textarea
            rows={6}
            value={simulationRequirement}
            onChange={(event) => setSimulationRequirement(event.target.value)}
          />
        </label>
      </div>

      <div className="action-row">
        <button
          type="button"
          className="primary-btn"
          onClick={() =>
            onCreate({
              projectName,
              organizationName,
              scenarioType,
              simulationRequirement
            })
          }
        >
          Create Decision Run
        </button>
      </div>
    </section>
  );
}
