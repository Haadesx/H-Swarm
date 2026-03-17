import { apiClient } from "./client";
import type {
  Assumption,
  DecisionRun,
  EvidenceFile,
  ExtractedFact,
  InterrogationTurn,
  Kpi,
  Memo,
  Project,
  RiskCell,
  RunArtifacts,
  Stakeholder,
  StakeholderEdge,
  TimelineEvent
} from "../types";

type AnyRecord = Record<string, unknown>;

function maybeData<T>(payload: unknown): T {
  if (payload && typeof payload === "object" && "data" in (payload as AnyRecord)) {
    return (payload as { data: T }).data;
  }
  return payload as T;
}

function mapProject(payload: AnyRecord): Project {
  return {
    id: String(payload.id || payload.project_id || payload.projectId),
    name: String(payload.name || "Untitled Project"),
    organizationName: (payload.organization_name || payload.organizationName || null) as string | null,
    createdAt: String(payload.created_at || payload.createdAt || new Date().toISOString()),
    updatedAt: String(payload.updated_at || payload.updatedAt || new Date().toISOString()),
    scenarioType: String(payload.scenario_type || payload.scenarioType || "reimbursement_cut")
  };
}

function mapDecisionRun(payload: AnyRecord): DecisionRun {
  return {
    id: String(payload.id || payload.run_id || payload.decision_run_id),
    projectId: String(payload.project_id || payload.projectId || ""),
    scenarioType: String(payload.scenario_type || payload.scenarioType || "reimbursement_cut"),
    simulationRequirement: String(payload.simulation_requirement || payload.simulationRequirement || ""),
    status: String(payload.status || "created") as DecisionRun["status"],
    createdAt: String(payload.created_at || payload.createdAt || new Date().toISOString()),
    updatedAt: String(payload.updated_at || payload.updatedAt || new Date().toISOString()),
    timeHorizons: (payload.time_horizons || payload.timeHorizons || [30, 90, 180]) as number[]
  };
}

function mapEvidence(payload: AnyRecord): EvidenceFile {
  return {
    id: String(payload.id || payload.file_id || crypto.randomUUID()),
    projectId: (payload.project_id || payload.projectId || "") as string,
    name: String(payload.filename || payload.name || "unknown"),
    filename: String(payload.filename || payload.name || "unknown"),
    mimeType: String(payload.content_type || payload.mime_type || payload.mimeType || "application/octet-stream"),
    extension: (payload.extension || "") as string,
    size: Number(payload.size_bytes || payload.size || 0),
    sizeBytes: Number(payload.size_bytes || payload.size || 0),
    extractedPreview: (payload.extracted_preview || payload.extractedPreview || "") as string,
    tableSummary: (payload.table_summary || null) as Record<string, unknown> | null
  };
}

function mapArtifacts(data: AnyRecord): RunArtifacts {
  const assumptions = ((data.assumptions || []) as AnyRecord[]).map((item) => ({
    id: String(item.id || crypto.randomUUID()),
    key: String(item.key || ""),
    value: String(item.value || ""),
    statement: String(item.statement || `${item.key || "assumption"}: ${item.value || ""}`),
    confidence: Number(item.confidence || 0.5),
    status: String(item.status || "needs_review") as Assumption["status"],
    impactArea: String(item.impactArea || item.impact_area || "operations") as Assumption["impactArea"],
    category: (item.category || "") as string,
    rationale: (item.rationale || "") as string,
    sourceEvidenceIds: (item.sourceEvidenceIds || item.source_evidence_ids || []) as string[],
    userModified: Boolean(item.user_modified || item.userModified)
  }));

  const facts = ((data.facts || []) as AnyRecord[]).map((item) => ({
    id: String(item.id || crypto.randomUUID()),
    evidenceFileId: (item.evidence_file_id || item.evidenceFileId || null) as string | null,
    factType: String(item.fact_type || item.factType || "fact"),
    title: String(item.title || "Untitled fact"),
    detail: String(item.detail || ""),
    sourceExcerpt: String(item.source_excerpt || item.sourceExcerpt || ""),
    confidence: Number(item.confidence || 0.5),
    normalizedValueJson: (item.normalized_value_json || item.normalizedValueJson || {}) as Record<string, unknown>
  }));

  const stakeholders = ((data.stakeholders || []) as AnyRecord[]).map((item) => ({
    id: String(item.id || item.uuid || item.name),
    name: String(item.name || "Unknown"),
    type: String(item.type || item.entity_type || "Organization"),
    roleSummary: (item.roleSummary || item.role_summary || "") as string,
    incentive: String(item.incentive || item.roleSummary || item.role_summary || "Not specified"),
    pressurePoint: String(item.pressurePoint || item.pressure_point || item.roleSummary || item.role_summary || "Not specified"),
    likelyReaction: String(item.likelyReaction || item.likely_reaction || item.roleSummary || item.role_summary || "Not specified"),
    influence: Number(item.influence || item.influence_score || 50)
  }));

  const edges = ((data.edges || []) as AnyRecord[]).map((item) => ({
    id: (item.id || "") as string,
    source: String(item.source || item.source_node_id || item.from || ""),
    target: String(item.target || item.target_node_id || item.to || ""),
    relation: String(item.relation || item.relation_type || item.type || "RELATED_TO"),
    rationale: (item.rationale || "") as string
  }));

  const kpis = ((data.kpis || []) as AnyRecord[]).map((item) => ({
    id: String(item.id || item.name),
    label: String(item.label || item.name || "Unnamed KPI"),
    unit: String(item.unit || "%"),
    baseline: Number(item.baseline || item.baseline_value || 0),
    byHorizon: (["30", "90", "180"] as const).reduce((acc, horizon) => {
      const horizonPayload = ((item.byHorizon || item.by_horizon || {}) as AnyRecord)[horizon] as AnyRecord | undefined;
      const baseline = Number(item.baseline || item.baseline_value || 0);
      const readCell = (value: unknown) => {
        if (value && typeof value === "object") {
          const record = value as AnyRecord;
          const delta = record.delta == null ? 0 : Number(record.delta);
          const projected = record.projected == null ? baseline + delta : Number(record.projected);
          return { projected, delta };
        }
        const delta = value == null ? 0 : Number(value);
        return { projected: baseline + delta, delta };
      };
      acc[horizon] = {
        base_case: readCell(horizonPayload?.base_case),
        downside_case: readCell(horizonPayload?.downside_case),
        severe_case: readCell(horizonPayload?.severe_case)
      };
      return acc;
    }, {} as Kpi["byHorizon"])
  }));

  const riskHeatmap = ((data.riskHeatmap || []) as AnyRecord[]).map((item) => ({
    stakeholderId: String(item.stakeholderId || item.stakeholder_id || item.id),
    stakeholder: String(item.stakeholder || item.name || "Unknown"),
    operations: Number(item.operations || 0),
    finance: Number(item.finance || 0),
    access: Number(item.access || 0),
    regulatory: Number(item.regulatory || 0)
  }));

  const timeline = ((data.timeline || []) as AnyRecord[]).map((item, index) => ({
    id: String(item.id || `ev_${index}`),
    day: Number(item.day || item.horizon || 30) as TimelineEvent["day"],
    variant: String(item.variant || item.case || "base_case") as TimelineEvent["variant"],
    channel: String(item.channel || "External Signals") as TimelineEvent["channel"],
    stakeholder: String(item.stakeholder || "Unknown"),
    event: String(item.event || item.event_type || item.title || ""),
    implication: String(item.implication || item.description || ""),
    confidence: Number(item.confidence || 0.6),
    citations: (item.citations || item.citation_evidence_ids || []) as string[]
  }));

  const memosPayload = (data.memos || {}) as Record<string, AnyRecord>;
  const operator: Memo = {
    type: "operator",
    sections: ((memosPayload.operator?.sections || []) as AnyRecord[]).map((section) => ({
      title: String(section.title || "Untitled"),
      content: String(section.content || ""),
      citations: (section.citations || []) as string[]
    }))
  };
  const capital: Memo = {
    type: "capital",
    sections: ((memosPayload.capital?.sections || []) as AnyRecord[]).map((section) => ({
      title: String(section.title || "Untitled"),
      content: String(section.content || ""),
      citations: (section.citations || []) as string[]
    }))
  };

  return {
    facts,
    assumptions,
    stakeholders,
    edges,
    kpis,
    riskHeatmap,
    timeline,
    executiveDashboard: (data.executiveDashboard || null) as RunArtifacts["executiveDashboard"],
    conflictMatrix: ((data.conflictMatrix || []) as RunArtifacts["conflictMatrix"]),
    actionScenarios: ((data.actionScenarios || []) as RunArtifacts["actionScenarios"]),
    mitigationOptions: ((data.mitigationOptions || []) as RunArtifacts["mitigationOptions"]),
    memos: { operator, capital }
  };
}

async function getRunArtifacts(runId: string): Promise<RunArtifacts> {
  const payload = await apiClient.get<unknown>(`/api/runs/${runId}/artifacts`);
  return mapArtifacts(maybeData<AnyRecord>(payload));
}

export async function checkHealth(): Promise<{ status: string; service: string }> {
  const payload = await apiClient.get<unknown>("/health");
  return maybeData<{ status: string; service: string }>(payload);
}

export async function listProjects(): Promise<Project[]> {
  const payload = await apiClient.get<unknown>("/api/projects");
  const data = maybeData<AnyRecord[]>(payload);
  return data.map(mapProject);
}

export async function createProject(name: string, scenarioType: string, organizationName?: string): Promise<Project> {
  const payload = await apiClient.post<unknown>("/api/projects", {
    name,
    scenario_type: scenarioType,
    organization_name: organizationName || null
  });
  return mapProject(maybeData<AnyRecord>(payload));
}

export async function uploadEvidence(projectId: string, files: File[]): Promise<EvidenceFile[]> {
  const formData = new FormData();
  formData.append("project_id", projectId);
  for (const file of files) {
    formData.append("files", file, file.name);
  }
  const payload = await apiClient.post<unknown>("/api/evidence/upload", formData);
  const data = maybeData<AnyRecord>(payload);
  return ((data.files || []) as AnyRecord[]).map(mapEvidence);
}

export async function createDecisionRun(input: {
  projectId: string;
  scenarioType: string;
  simulationRequirement: string;
}): Promise<DecisionRun> {
  const payload = await apiClient.post<unknown>("/api/decision-runs", {
    project_id: input.projectId,
    scenario_type: input.scenarioType,
    simulation_requirement: input.simulationRequirement
  });
  return mapDecisionRun(maybeData<AnyRecord>(payload));
}

export async function getDecisionRun(runId: string): Promise<DecisionRun> {
  const payload = await apiClient.get<unknown>(`/api/runs/${runId}`);
  return mapDecisionRun(maybeData<AnyRecord>(payload));
}

export async function extractDecisionRun(runId: string): Promise<{ assumptions: Assumption[]; facts: ExtractedFact[] }> {
  const payload = await apiClient.post<unknown>(`/api/decision-runs/${runId}/extract`);
  const data = maybeData<AnyRecord>(payload);
  return {
    assumptions: ((data.assumptions || []) as AnyRecord[]).map((item) => ({
      id: String(item.id || crypto.randomUUID()),
      key: String(item.key || ""),
      value: String(item.value || ""),
      statement: String(item.statement || `${item.key || "assumption"}: ${item.value || ""}`),
      confidence: Number(item.confidence || 0.5),
      status: String(item.status || "needs_review") as Assumption["status"],
      impactArea: String(item.impactArea || item.impact_area || "operations") as Assumption["impactArea"],
      category: (item.category || "") as string,
      rationale: (item.rationale || "") as string,
      sourceEvidenceIds: (item.sourceEvidenceIds || item.source_evidence_ids || []) as string[],
      userModified: Boolean(item.user_modified || item.userModified)
    })),
    facts: ((data.facts || []) as AnyRecord[]).map((item) => ({
      id: String(item.id || crypto.randomUUID()),
      evidenceFileId: (item.evidence_file_id || null) as string | null,
      factType: String(item.fact_type || "fact"),
      title: String(item.title || "Untitled fact"),
      detail: String(item.detail || ""),
      sourceExcerpt: String(item.source_excerpt || ""),
      confidence: Number(item.confidence || 0.5),
      normalizedValueJson: (item.normalized_value_json || {}) as Record<string, unknown>
    }))
  };
}

export async function getEvidenceReview(runId: string): Promise<{
  evidence: EvidenceFile[];
  facts: ExtractedFact[];
  assumptions: Assumption[];
}> {
  const payload = await apiClient.get<unknown>(`/api/decision-runs/${runId}/evidence-review`);
  const data = maybeData<AnyRecord>(payload);
  return {
    evidence: ((data.evidence_files || []) as AnyRecord[]).map(mapEvidence),
    facts: ((data.facts || []) as AnyRecord[]).map((item) => ({
      id: String(item.id || crypto.randomUUID()),
      evidenceFileId: (item.evidence_file_id || null) as string | null,
      factType: String(item.fact_type || "fact"),
      title: String(item.title || "Untitled fact"),
      detail: String(item.detail || ""),
      sourceExcerpt: String(item.source_excerpt || ""),
      confidence: Number(item.confidence || 0.5),
      normalizedValueJson: (item.normalized_value_json || {}) as Record<string, unknown>
    })),
    assumptions: ((data.assumptions || []) as AnyRecord[]).map((item) => ({
      id: String(item.id || crypto.randomUUID()),
      key: String(item.key || ""),
      value: String(item.value || ""),
      statement: String(item.statement || `${item.key || "assumption"}: ${item.value || ""}`),
      confidence: Number(item.confidence || 0.5),
      status: String(item.status || "needs_review") as Assumption["status"],
      impactArea: String(item.impactArea || item.impact_area || "operations") as Assumption["impactArea"],
      category: (item.category || "") as string,
      rationale: (item.rationale || "") as string,
      sourceEvidenceIds: (item.sourceEvidenceIds || item.source_evidence_ids || []) as string[],
      userModified: Boolean(item.user_modified || item.userModified)
    }))
  };
}

export async function updateAssumption(
  runId: string,
  assumptionId: string,
  updates: { value: string; rationale?: string; status?: Assumption["status"] }
): Promise<Assumption> {
  const payload = await apiClient.patch<unknown>(`/api/decision-runs/${runId}/assumptions/${assumptionId}`, updates);
  const data = maybeData<AnyRecord>(payload);
  const item = (data.assumption || {}) as AnyRecord;
  return {
    id: String(item.id || crypto.randomUUID()),
    key: String(item.key || ""),
    value: String(item.value || ""),
    statement: String(item.statement || `${item.key || "assumption"}: ${item.value || ""}`),
    confidence: Number(item.confidence || 0.5),
    status: String(item.status || "needs_review") as Assumption["status"],
    impactArea: String(item.impactArea || item.impact_area || "operations") as Assumption["impactArea"],
    category: (item.category || "") as string,
    rationale: (item.rationale || "") as string,
    sourceEvidenceIds: (item.sourceEvidenceIds || item.source_evidence_ids || []) as string[],
    userModified: Boolean(item.user_modified || item.userModified)
  };
}

export async function buildGraph(runId: string): Promise<{ stakeholders: Stakeholder[]; edges: StakeholderEdge[] }> {
  await apiClient.post(`/api/decision-runs/${runId}/build-graph`);
  const artifacts = await getRunArtifacts(runId);
  return { stakeholders: artifacts.stakeholders, edges: artifacts.edges };
}

export async function simulate(runId: string): Promise<{
  kpis: Kpi[];
  riskHeatmap: RiskCell[];
  timeline: TimelineEvent[];
}> {
  await apiClient.post(`/api/decision-runs/${runId}/simulate`);
  const artifacts = await getRunArtifacts(runId);
  return {
    kpis: artifacts.kpis,
    riskHeatmap: artifacts.riskHeatmap,
    timeline: artifacts.timeline
  };
}

export async function generateMemos(runId: string): Promise<{ operator: Memo; capital: Memo }> {
  await apiClient.post(`/api/decision-runs/${runId}/generate-memo`);
  const artifacts = await getRunArtifacts(runId);
  return artifacts.memos;
}

export async function importBundledDemo(): Promise<{
  project: Project;
  run: DecisionRun;
  evidence: EvidenceFile[];
  artifacts: RunArtifacts;
}> {
  const payload = await apiClient.post<unknown>("/api/demo/import");
  const data = maybeData<AnyRecord>(payload);
  return {
    project: mapProject((data.project || {}) as AnyRecord),
    run: mapDecisionRun((data.run || {}) as AnyRecord),
    evidence: ((data.evidence || []) as AnyRecord[]).map(mapEvidence),
    artifacts: mapArtifacts((data.artifacts || {}) as AnyRecord)
  };
}

export async function interrogate(runId: string, question: string, memoType?: "operator" | "capital"): Promise<InterrogationTurn> {
  const payload = await apiClient.post<unknown>(`/api/decision-runs/${runId}/interrogate`, { question, memo_type: memoType });
  const data = maybeData<AnyRecord>(payload);
  return {
    question,
    answer: String(data.answer || data.response || "No answer returned."),
    citations: (data.citations || []) as string[]
  };
}
