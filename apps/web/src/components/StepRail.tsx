import type { StepKey } from "../types";

const STEPS: Array<{ id: StepKey; label: string; short: string; hint: string }> = [
  { id: "projects", label: "Projects", short: "01", hint: "Review active cases and choose a workspace." },
  { id: "new_run", label: "Define Scenario", short: "02", hint: "Frame the decision question and primary shock." },
  { id: "evidence_review", label: "Review Assumptions", short: "03", hint: "Upload evidence and extract KPI signals." },
  { id: "stakeholder_map", label: "Inspect Stakeholders", short: "04", hint: "See who drives downside and who reacts first." },
  { id: "scenario_lab", label: "Replay Impacts", short: "05", hint: "Compare base, downside, and severe paths." },
  { id: "memo_workspace", label: "Read Memo", short: "06", hint: "Generate operator and capital narratives." },
  { id: "assumption_review", label: "Compare Actions", short: "07", hint: "Interrogate tradeoffs and next moves." }
];

interface StepRailProps {
  activeStep: StepKey;
  onSelect: (step: StepKey) => void;
}

export function StepRail({ activeStep, onSelect }: StepRailProps) {
  return (
    <aside className="step-rail">
      <p className="eyebrow">Decision Workflow</p>
      {STEPS.map((step) => (
        <button
          key={step.id}
          className={`step-btn ${activeStep === step.id ? "active" : ""}`}
          onClick={() => onSelect(step.id)}
          type="button"
        >
          <span className="step-num">{step.short}</span>
          <span className="step-copy">
            <strong>{step.label}</strong>
            <small>{step.hint}</small>
          </span>
        </button>
      ))}
    </aside>
  );
}
