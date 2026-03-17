import type { ScenarioTemplate } from "./types";

export const PRODUCT_NAME = "HealthTwin";
export const PRODUCT_TAGLINE = "Healthcare decision twin for operators and capital stakeholders";
export const BUYER_WEDGE = "operator_capital";
export const PRIMARY_SCENARIO = "reimbursement_cut";

export const SCENARIO_TEMPLATES: ScenarioTemplate[] = [
  {
    id: "reimbursement_cut",
    label: "Reimbursement Cut",
    summary: "Stress-test reimbursement pressure across margin, operations, access, and financing.",
    defaultRequirement:
      "Simulate how a 7% reimbursement reduction affects provider operations, patient access, lender confidence, and investor sentiment over 30, 90, and 180 days."
  },
  {
    id: "staffing_shortage",
    label: "Staffing Shortage",
    summary: "Model labor pressure, throughput decline, and care-access impact.",
    defaultRequirement:
      "Simulate how nurse and physician shortages affect labor cost, throughput, patient access, and financing risk over 30, 90, and 180 days."
  },
  {
    id: "payer_conflict",
    label: "Payer Conflict",
    summary: "Model denials, contract dispute, and public friction effects.",
    defaultRequirement:
      "Simulate how a payer-provider dispute and rising denials affect revenue realization, care delays, reputation, and lender concern."
  },
  {
    id: "adverse_event",
    label: "Adverse Event",
    summary: "Model regulatory attention, patient trust loss, and financial fallout.",
    defaultRequirement:
      "Simulate how a public adverse event affects regulator response, patient confidence, service-line utilization, and financing options."
  },
  {
    id: "expansion_acquisition",
    label: "Expansion / Acquisition",
    summary: "Model execution risk and market reaction around expansion or acquisition.",
    defaultRequirement:
      "Simulate how a clinic expansion or acquisition changes referral flow, payer posture, investor confidence, and execution risk."
  },
  {
    id: "turnaround_liquidity",
    label: "Turnaround / Liquidity",
    summary: "Model covenant pressure, turnaround actions, and capital availability.",
    defaultRequirement:
      "Simulate how a liquidity-constrained provider responds to margin pressure, covenant risk, and operational deterioration."
  }
];

export const CASE_HORIZONS = [30, 90, 180] as const;
export const CASE_VARIANTS = [
  { id: "base_case", label: "Base Case" },
  { id: "downside_case", label: "Downside Case" },
  { id: "severe_case", label: "Severe Case" }
] as const;

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  const num = Number(value);
  const sign = num > 0 ? "+" : "";
  return `${sign}${num.toFixed(1)}%`;
}

export function formatDelta(value: number | null | undefined, suffix = ""): string {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  const num = Number(value);
  const sign = num > 0 ? "+" : "";
  return `${sign}${num.toFixed(1)}${suffix}`;
}
