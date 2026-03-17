export const CASE_HORIZONS = [30, 90, 180];

export const CASE_VARIANTS = [
  { id: "base_case", label: "Base Case" },
  { id: "downside_case", label: "Downside Case" },
  { id: "severe_case", label: "Severe Case" }
];

export function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  const num = Number(value);
  const sign = num > 0 ? "+" : "";
  return `${sign}${num.toFixed(1)}%`;
}

export function formatDelta(value, suffix = "") {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  const num = Number(value);
  const sign = num > 0 ? "+" : "";
  return `${sign}${num.toFixed(1)}${suffix}`;
}
