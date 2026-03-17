export type StepKey =
  | "projects"
  | "new_run"
  | "evidence_review"
  | "stakeholder_map"
  | "scenario_lab"
  | "memo_workspace"
  | "assumption_review";

export type RunStatus =
  | "created"
  | "extracted"
  | "graph_built"
  | "simulated"
  | "memos_generated"
  | "memo_ready";

export type ScenarioVariant = "base_case" | "downside_case" | "severe_case";
export type HorizonKey = "30" | "90" | "180";

export interface ScenarioTemplate {
  id: string;
  label: string;
  summary: string;
  defaultRequirement: string;
}

export interface Project {
  id: string;
  name: string;
  organizationName?: string | null;
  createdAt: string;
  updatedAt?: string;
  scenarioType: string;
}

export interface DecisionRun {
  id: string;
  projectId: string;
  scenarioType: string;
  simulationRequirement: string;
  status: RunStatus;
  createdAt: string;
  updatedAt?: string;
  timeHorizons?: number[];
}

export interface EvidenceFile {
  id: string;
  projectId?: string;
  name: string;
  filename?: string;
  mimeType: string;
  extension?: string;
  size: number;
  sizeBytes?: number;
  extractedPreview?: string;
  tableSummary?: Record<string, unknown> | null;
}

export interface Assumption {
  id: string;
  key: string;
  value: string;
  statement: string;
  confidence: number;
  status: "confirmed" | "needs_review" | "missing_data";
  impactArea: "operations" | "finance" | "access" | "regulatory";
  category?: string;
  rationale?: string;
  sourceEvidenceIds?: string[];
  userModified?: boolean;
}

export interface ExtractedFact {
  id: string;
  evidenceFileId?: string | null;
  factType: string;
  title: string;
  detail: string;
  sourceExcerpt: string;
  confidence: number;
  normalizedValueJson?: Record<string, unknown>;
}

export interface Stakeholder {
  id: string;
  name: string;
  type: string;
  roleSummary?: string;
  incentive: string;
  pressurePoint: string;
  likelyReaction: string;
  influence: number;
}

export interface StakeholderEdge {
  id?: string;
  source: string;
  target: string;
  relation: string;
  rationale?: string;
}

export interface KpiScenarioCell {
  projected: number | null;
  delta: number | null;
}

export interface Kpi {
  id: string;
  label: string;
  unit: string;
  baseline: number;
  byHorizon: Record<HorizonKey, Record<ScenarioVariant, KpiScenarioCell>>;
}

export interface RiskCell {
  stakeholderId: string;
  stakeholder: string;
  operations: number;
  finance: number;
  access: number;
  regulatory: number;
}

export interface ExecutiveMetric {
  key: string;
  label: string;
  score: number;
  tone: "stable" | "elevated" | "critical";
  summary: string;
}

export interface ExecutiveDashboard {
  title: string;
  narrative: string;
  decisionFocus: string;
  metrics: ExecutiveMetric[];
}

export interface StakeholderConflict {
  stakeholderId: string;
  stakeholder: string;
  group: string;
  intensity: number;
  concern: string;
  likelyMove: string;
  pressure: string;
  response: string;
}

export interface ActionScenario {
  horizonDays: 30 | 90 | 180;
  title: string;
  summary: string;
  operatingFocus: string;
  capitalFocus: string;
  boardAsk: string;
}

export interface MitigationOption {
  id: string;
  name: string;
  positioning: string;
  composite: number;
  marginImpact: string;
  accessImpact: string;
  trustImpact: string;
  bestUse: string;
  tradeoff: string;
}

export interface TimelineEvent {
  id: string;
  day: 30 | 90 | 180;
  variant: ScenarioVariant;
  channel: "External Signals" | "Operational Network";
  stakeholder: string;
  event: string;
  implication: string;
  confidence: number;
  citations: string[];
}

export interface MemoSection {
  title: string;
  content: string;
  citations: string[];
}

export interface Memo {
  id?: string;
  type: "operator" | "capital";
  title?: string;
  contentMarkdown?: string;
  sections: MemoSection[];
  citations?: string[];
}

export interface InterrogationTurn {
  question: string;
  answer: string;
  citations: string[];
}

export interface RunArtifacts {
  facts: ExtractedFact[];
  assumptions: Assumption[];
  stakeholders: Stakeholder[];
  edges: StakeholderEdge[];
  kpis: Kpi[];
  riskHeatmap: RiskCell[];
  timeline: TimelineEvent[];
  executiveDashboard: ExecutiveDashboard | null;
  conflictMatrix: StakeholderConflict[];
  actionScenarios: ActionScenario[];
  mitigationOptions: MitigationOption[];
  memos: Record<"operator" | "capital", Memo>;
}

export interface NewRunInput {
  projectName: string;
  organizationName?: string;
  scenarioType: string;
  simulationRequirement: string;
}

export interface DataSourceState {
  mode: "api" | "demo";
  note: string;
}
