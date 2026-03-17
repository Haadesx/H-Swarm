import { useEffect, useMemo, useState } from "react";
import {
  buildGraph,
  checkHealth,
  createDecisionRun,
  createProject,
  extractDecisionRun,
  generateMemos,
  getDecisionRun,
  importBundledDemo,
  interrogate,
  listProjects,
  simulate,
  updateAssumption,
  uploadEvidence
} from "./api/healthtwin";
import { PRIMARY_SCENARIO, PRODUCT_TAGLINE } from "./contracts";
import { StepRail } from "./components/StepRail";
import { TopNav } from "./components/TopNav";
import { demoArtifacts, demoEvidence, demoInterrogation, demoProject, demoRun } from "./data/demo";
import type {
  DataSourceState,
  DecisionRun,
  EvidenceFile,
  InterrogationTurn,
  Memo,
  NewRunInput,
  Project,
  RunArtifacts,
  StepKey
} from "./types";
import { AssumptionReviewView } from "./views/AssumptionReviewView";
import { EvidenceReviewView } from "./views/EvidenceReviewView";
import { MemoWorkspaceView } from "./views/MemoWorkspaceView";
import { NewDecisionRunView } from "./views/NewDecisionRunView";
import { ProjectsView } from "./views/ProjectsView";
import { ScenarioLabView } from "./views/ScenarioLabView";
import { StakeholderMapView } from "./views/StakeholderMapView";

const STORAGE_KEY = "healthtwin-local-projects";

const EMPTY_ARTIFACTS: RunArtifacts = {
  facts: [],
  assumptions: [],
  stakeholders: [],
  edges: [],
  kpis: [],
  riskHeatmap: [],
  timeline: [],
  executiveDashboard: null,
  conflictMatrix: [],
  actionScenarios: [],
  mitigationOptions: [],
  memos: demoArtifacts.memos
};

function loadStoredProjects(): Project[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw) as Project[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export default function App() {
  const [activeStep, setActiveStep] = useState<StepKey>("projects");
  const [sourceState, setSourceState] = useState<DataSourceState>({
    mode: "demo",
    note: "Checking local API. Deterministic reimbursement-cut demo is ready as fallback."
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [run, setRun] = useState<DecisionRun | null>(null);
  const [evidence, setEvidence] = useState<EvidenceFile[]>([]);
  const [artifacts, setArtifacts] = useState<RunArtifacts>(EMPTY_ARTIFACTS);
  const [memos, setMemos] = useState<{ operator: Memo; capital: Memo }>(demoArtifacts.memos);
  const [interrogation, setInterrogation] = useState<InterrogationTurn[]>([]);

  const selectedProject = useMemo(
    () => projects.find((project) => project.id === selectedProjectId) ?? null,
    [projects, selectedProjectId]
  );
  const isLocalDemoRun = run?.id === demoRun.id || sourceState.mode === "demo";

  useEffect(() => {
    void bootstrapWorkspace();
  }, []);

  useEffect(() => {
    if (projects.length) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(projects));
    }
  }, [projects]);

  async function bootstrapWorkspace() {
    setLoading(true);
    setError(null);
    try {
      await checkHealth();
      const apiProjects = await listProjects();
      if (apiProjects.length) {
        setProjects(apiProjects);
        setSelectedProjectId(apiProjects[0].id);
        setSourceState({ mode: "api", note: "Connected to local HealthTwin API." });
      } else {
        const stored = loadStoredProjects();
        setProjects(stored);
        setSelectedProjectId(stored[0]?.id ?? null);
        setSourceState({
          mode: "api",
          note: "API is live. No runs yet, so the workspace is starting clean."
        });
      }
    } catch (err) {
      const fallbackProjects = loadStoredProjects();
      if (fallbackProjects.length) {
        setProjects(fallbackProjects);
        setSelectedProjectId(fallbackProjects[0].id);
      } else {
        setProjects([demoProject]);
        setSelectedProjectId(demoProject.id);
        setRun(demoRun);
        setEvidence(demoEvidence);
        setArtifacts(demoArtifacts);
        setMemos(demoArtifacts.memos);
        setInterrogation(demoInterrogation);
      }
      setSourceState({
        mode: "demo",
        note: "Local API unavailable. Using deterministic MetroCare evidence, stakeholders, and memos."
      });
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateRun(input: NewRunInput) {
    setLoading(true);
    setError(null);
    setInterrogation([]);
    try {
      const project = await createProject(input.projectName, input.scenarioType, input.organizationName);
      const nextRun = await createDecisionRun({
        projectId: project.id,
        scenarioType: input.scenarioType,
        simulationRequirement: input.simulationRequirement
      });
      setProjects((current) => [project, ...current.filter((item) => item.id !== project.id)]);
      setSelectedProjectId(project.id);
      setRun(nextRun);
      setEvidence([]);
      setArtifacts(EMPTY_ARTIFACTS);
      setMemos(demoArtifacts.memos);
      setSourceState({ mode: "api", note: "New decision run created from the local API." });
      setActiveStep("evidence_review");
    } catch (err) {
      setProjects([demoProject]);
      setSelectedProjectId(demoProject.id);
      setRun({
        ...demoRun,
        scenarioType: input.scenarioType || PRIMARY_SCENARIO,
        simulationRequirement: input.simulationRequirement
      });
      setEvidence(demoEvidence);
      setArtifacts(demoArtifacts);
      setMemos(demoArtifacts.memos);
      setInterrogation(demoInterrogation);
      setSourceState({
        mode: "demo",
        note: "Run creation failed. Loaded deterministic MetroCare reimbursement scenario."
      });
      setError((err as Error).message);
      setActiveStep("evidence_review");
    } finally {
      setLoading(false);
    }
  }

  async function handleLoadDemo() {
    setLoading(true);
    setError(null);
    setInterrogation([]);
    try {
      const imported = await importBundledDemo();
      setProjects((current) => [imported.project, ...current.filter((item) => item.id !== imported.project.id)]);
      setSelectedProjectId(imported.project.id);
      setRun(imported.run);
      setEvidence(imported.evidence);
      setArtifacts(imported.artifacts);
      setMemos(imported.artifacts.memos);
      setSourceState({ mode: "api", note: "Bundled MetroCare demo imported from the local API." });
      setActiveStep("evidence_review");
    } catch (err) {
      setProjects([demoProject]);
      setSelectedProjectId(demoProject.id);
      setRun(demoRun);
      setEvidence(demoEvidence);
      setArtifacts(demoArtifacts);
      setMemos(demoArtifacts.memos);
      setInterrogation(demoInterrogation);
      setSourceState({ mode: "demo", note: "Loaded bundled deterministic MetroCare demo locally." });
      setError((err as Error).message);
      setActiveStep("evidence_review");
    } finally {
      setLoading(false);
    }
  }

  async function handleUploadEvidence(files: File[]) {
    if (!run || !files.length) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const uploaded = await uploadEvidence(run.projectId, files);
      setEvidence((current) => [...uploaded, ...current]);
      setSourceState({ mode: "api", note: "Evidence pack uploaded and attached to the selected project." });
    } catch (err) {
      const fallback = files.map((file) => ({
        id: `${file.name}_${file.size}`,
        projectId: run.projectId,
        name: file.name,
        filename: file.name,
        mimeType: file.type || "application/octet-stream",
        extension: file.name.split(".").pop() || "",
        size: file.size,
        sizeBytes: file.size,
        extractedPreview: "Uploaded locally while API is unavailable."
      }));
      setEvidence((current) => [...fallback, ...current]);
      setSourceState({
        mode: "demo",
        note: "Upload API unavailable. Files are represented locally for workspace continuity."
      });
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function handleExtract() {
    if (!run) {
      return;
    }
    if (!evidence.length) {
      setError("Upload evidence first, or import the MetroCare demo workspace from Projects.");
      setSourceState({
        mode: sourceState.mode,
        note: "Evidence is required before extraction. Upload files or import the bundled demo case."
      });
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const extracted = await extractDecisionRun(run.id);
      const refreshedRun = await getDecisionRun(run.id);
      setRun(refreshedRun);
      setArtifacts((current) => ({ ...current, assumptions: extracted.assumptions, facts: extracted.facts }));
      setSourceState({ mode: "api", note: "Assumptions and KPI evidence extracted from uploaded materials." });
      setActiveStep("stakeholder_map");
    } catch (err) {
      setArtifacts((current) => ({
        ...current,
        assumptions: demoArtifacts.assumptions,
        facts: demoArtifacts.facts
      }));
      setSourceState({
        mode: "demo",
        note: "Extraction failed. Using deterministic healthcare assumptions and facts."
      });
      setError((err as Error).message);
      setActiveStep("stakeholder_map");
    } finally {
      setLoading(false);
    }
  }

  async function handleBuildMap() {
    if (!run) {
      return;
    }
    if (isLocalDemoRun) {
      setArtifacts((current) => ({
        ...current,
        stakeholders: demoArtifacts.stakeholders,
        edges: demoArtifacts.edges
      }));
      setSourceState({ mode: "demo", note: "Loaded deterministic stakeholder map for the bundled MetroCare demo." });
      setError(null);
      setActiveStep("scenario_lab");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const graph = await buildGraph(run.id);
      const refreshedRun = await getDecisionRun(run.id);
      setRun(refreshedRun);
      setArtifacts((current) => ({ ...current, stakeholders: graph.stakeholders, edges: graph.edges }));
      setSourceState({ mode: "api", note: "Stakeholder graph built from the local healthcare graph service." });
      setActiveStep("scenario_lab");
    } catch (err) {
      setArtifacts((current) => ({
        ...current,
        stakeholders: demoArtifacts.stakeholders,
        edges: demoArtifacts.edges
      }));
      setSourceState({ mode: "demo", note: "Graph build failed. Loaded deterministic stakeholder map." });
      setError((err as Error).message);
      setActiveStep("scenario_lab");
    } finally {
      setLoading(false);
    }
  }

  async function handleSimulate() {
    if (!run) {
      return;
    }
    if (isLocalDemoRun) {
      setArtifacts((current) => ({
        ...current,
        kpis: demoArtifacts.kpis,
        riskHeatmap: demoArtifacts.riskHeatmap,
        timeline: demoArtifacts.timeline
      }));
      setSourceState({ mode: "demo", note: "Loaded deterministic 30/90/180 scenario outputs for the MetroCare demo." });
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const simulation = await simulate(run.id);
      const refreshedRun = await getDecisionRun(run.id);
      setRun(refreshedRun);
      setArtifacts((current) => ({
        ...current,
        kpis: simulation.kpis,
        riskHeatmap: simulation.riskHeatmap,
        timeline: simulation.timeline
      }));
      setSourceState({ mode: "api", note: "Base, downside, and severe scenarios simulated successfully." });
    } catch (err) {
      setArtifacts((current) => ({
        ...current,
        kpis: demoArtifacts.kpis,
        riskHeatmap: demoArtifacts.riskHeatmap,
        timeline: demoArtifacts.timeline
      }));
      setSourceState({ mode: "demo", note: "Simulation failed. Loaded deterministic 30/90/180 outputs." });
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateMemos() {
    if (!run) {
      return;
    }
    if (isLocalDemoRun) {
      setMemos(demoArtifacts.memos);
      setSourceState({ mode: "demo", note: "Loaded deterministic operator and capital memos for the MetroCare demo." });
      setError(null);
      setActiveStep("memo_workspace");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const nextMemos = await generateMemos(run.id);
      const refreshedRun = await getDecisionRun(run.id);
      setRun(refreshedRun);
      setMemos(nextMemos);
      setSourceState({ mode: "api", note: "Operator brief and capital memo generated from typed artifacts." });
      setActiveStep("memo_workspace");
    } catch (err) {
      setMemos(demoArtifacts.memos);
      setSourceState({ mode: "demo", note: "Memo generation failed. Showing deterministic operator and capital memos." });
      setError((err as Error).message);
      setActiveStep("memo_workspace");
    } finally {
      setLoading(false);
    }
  }

  async function handleAsk(question: string, memoType?: "operator" | "capital") {
    if (!run || !question.trim()) {
      return;
    }
    if (isLocalDemoRun) {
      const fallback = demoInterrogation.find((item) => item.question.toLowerCase() === question.toLowerCase()) ?? {
        question,
        answer:
          "Prioritize denial reduction, cash preservation, and lender communication in the next 30 days while protecting high-throughput service lines.",
        citations: ["metrocare_financials_q4.csv"]
      };
      setInterrogation((current) => [{ ...fallback, question }, ...current]);
      setSourceState({ mode: "demo", note: "Answered from the deterministic MetroCare demo artifact set." });
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const turn = await interrogate(run.id, question, memoType);
      setInterrogation((current) => [turn, ...current]);
      setSourceState({ mode: "api", note: "Interrogation grounded against run facts, assumptions, and memos." });
    } catch (err) {
      const fallback = demoInterrogation[0] ?? {
        question,
        answer:
          "Prioritize denial reduction, cash preservation, and lender communication in the next 30 days while protecting high-throughput service lines.",
        citations: ["metrocare_financials_q4.csv"]
      };
      setInterrogation((current) => [{ ...fallback, question }, ...current]);
      setSourceState({ mode: "demo", note: "Interrogation API unavailable. Returned deterministic healthcare answer." });
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function handleAssumptionUpdate(assumptionId: string, value: string) {
    if (!run) {
      return;
    }
    setArtifacts((current) => ({
      ...current,
      assumptions: current.assumptions.map((assumption) =>
        assumption.id === assumptionId
          ? {
              ...assumption,
              value,
              statement: `${assumption.key}: ${value}`,
              status: "confirmed",
              userModified: true
            }
          : assumption
      )
    }));

    try {
      const updated = await updateAssumption(run.id, assumptionId, { value, status: "confirmed" });
      setArtifacts((current) => ({
        ...current,
        assumptions: current.assumptions.map((assumption) => (assumption.id === assumptionId ? updated : assumption))
      }));
      setSourceState({ mode: "api", note: "Assumption updated and pinned to the decision run." });
    } catch (err) {
      setSourceState({ mode: "demo", note: "Assumption edit kept locally because the API update failed." });
      setError((err as Error).message);
    }
  }

  const currentMemoSections = memos.operator.sections.length + memos.capital.sections.length;

  const view = (() => {
    switch (activeStep) {
      case "projects":
        return (
          <ProjectsView
            projects={projects}
            selectedProjectId={selectedProjectId}
            selectedProject={selectedProject}
            activeRun={run}
            onSelect={setSelectedProjectId}
            onCreateNew={() => setActiveStep("new_run")}
            onLoadDemo={handleLoadDemo}
          />
        );
      case "new_run":
        return <NewDecisionRunView onCreate={handleCreateRun} onLoadDemo={handleLoadDemo} />;
      case "evidence_review":
        return (
          <EvidenceReviewView
            project={selectedProject}
            run={run}
            evidence={evidence}
            assumptions={artifacts.assumptions}
            facts={artifacts.facts}
            onLoadDemo={handleLoadDemo}
            onUpload={handleUploadEvidence}
            onExtract={handleExtract}
          />
        );
      case "stakeholder_map":
        return (
          <StakeholderMapView stakeholders={artifacts.stakeholders} edges={artifacts.edges} onBuildMap={handleBuildMap} />
        );
      case "scenario_lab":
        return (
          <ScenarioLabView
            kpis={artifacts.kpis}
            riskHeatmap={artifacts.riskHeatmap}
            timeline={artifacts.timeline}
            stakeholders={artifacts.stakeholders}
            onSimulate={handleSimulate}
            onAdvance={() => setActiveStep("memo_workspace")}
          />
        );
      case "memo_workspace":
        return (
          <MemoWorkspaceView
            memos={memos}
            onGenerateMemos={handleGenerateMemos}
            onAdvance={() => setActiveStep("assumption_review")}
          />
        );
      case "assumption_review":
        return (
          <AssumptionReviewView
            assumptions={artifacts.assumptions}
            interrogation={interrogation}
            onUpdateAssumption={handleAssumptionUpdate}
            onAsk={handleAsk}
          />
        );
      default:
        return null;
    }
  })();

  return (
    <div className="app-shell">
      <TopNav sourceState={sourceState} />

      <div className="content-shell">
        <StepRail activeStep={activeStep} onSelect={setActiveStep} />

        <main className="main-content">
          <section className="hero-band">
            <article className="hero-card hero-card-primary">
              <p className="eyebrow">Decision Focus</p>
              <h3>{selectedProject?.name ?? "Healthcare decision workspace"}</h3>
              <p>{PRODUCT_TAGLINE}</p>
            </article>

            <article className="hero-card">
              <p className="eyebrow">Active Scenario</p>
              <h3>{run?.scenarioType ?? PRIMARY_SCENARIO}</h3>
              <p>{run?.simulationRequirement ?? "Start a new run or import the MetroCare reimbursement-cut demo."}</p>
            </article>

            <article className="hero-card hero-card-metric">
              <p className="eyebrow">Workspace Pulse</p>
              <h3>
                {artifacts.assumptions.length} assumptions · {artifacts.stakeholders.length} stakeholders
              </h3>
              <p>{currentMemoSections} memo sections ready for operator and capital review.</p>
            </article>
          </section>

          {loading ? <div className="status-banner info">Running healthcare decision workflow...</div> : null}
          {!loading && error ? <div className="status-banner warn">Last issue: {error}</div> : null}
          {!loading && !error ? <div className="status-banner ok">Workspace ready.</div> : null}

          {view}

          {!run && activeStep !== "projects" && activeStep !== "new_run" ? (
            <section className="panel empty-state-panel">
              <h3>No decision run selected</h3>
              <p>
                Create a new decision run or import the bundled MetroCare demo to unlock evidence review, stakeholder
                mapping, simulation, memo generation, and interrogation.
              </p>
            </section>
          ) : null}
        </main>
      </div>
    </div>
  );
}
