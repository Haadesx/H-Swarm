import type { DecisionRun, Project } from "../types";

interface ProjectsViewProps {
  projects: Project[];
  selectedProjectId: string | null;
  selectedProject: Project | null;
  activeRun: DecisionRun | null;
  onSelect: (projectId: string) => void;
  onCreateNew: () => void;
  onLoadDemo: () => Promise<void> | void;
}

export function ProjectsView({
  projects,
  selectedProjectId,
  selectedProject,
  activeRun,
  onSelect,
  onCreateNew,
  onLoadDemo
}: ProjectsViewProps) {
  return (
    <section className="view">
      <div className="view-header">
        <div>
          <p className="eyebrow">Workspace</p>
          <h2>Projects</h2>
          <p className="subtext">
            Start with a reimbursement-cut case, or reopen an existing provider decision workspace.
          </p>
        </div>
        <div className="action-row">
          <button type="button" className="secondary-btn" onClick={onLoadDemo}>
            Import MetroCare Demo
          </button>
          <button type="button" className="primary-btn" onClick={onCreateNew}>
            New Decision Run
          </button>
        </div>
      </div>

      <div className="layout-two layout-two-balanced">
        <section className="panel">
          <div className="panel-header-row">
            <div>
              <h3>Decision Workspaces</h3>
              <p className="subtext">{projects.length} project{projects.length === 1 ? "" : "s"} in the local workspace.</p>
            </div>
          </div>

          <div className="project-grid">
            {projects.map((project) => (
              <button
                key={project.id}
                type="button"
                className={`project-card ${selectedProjectId === project.id ? "selected" : ""}`}
                onClick={() => onSelect(project.id)}
              >
                <p className="eyebrow">Scenario</p>
                <h3>{project.name}</h3>
                <p>{project.organizationName ?? "Unnamed organization"}</p>
                <div className="project-meta-list">
                  <span>{project.scenarioType.replace(/_/g, " ")}</span>
                  <span>Created {new Date(project.createdAt).toLocaleDateString()}</span>
                </div>
              </button>
            ))}
          </div>
        </section>

        <section className="panel workspace-summary">
          <p className="eyebrow">Selected Workspace</p>
          <h3>{selectedProject?.name ?? "No project selected"}</h3>
          <p className="subtext">
            {selectedProject
              ? "Use this case to move through evidence extraction, stakeholder inspection, scenario replay, and memo generation."
              : "Select or create a project to begin."}
          </p>

          <div className="summary-grid">
            <article className="summary-card">
              <span className="summary-label">Organization</span>
              <strong>{selectedProject?.organizationName ?? "Not set"}</strong>
            </article>
            <article className="summary-card">
              <span className="summary-label">Scenario</span>
              <strong>{selectedProject?.scenarioType.replace(/_/g, " ") ?? "Not set"}</strong>
            </article>
            <article className="summary-card">
              <span className="summary-label">Run Status</span>
              <strong>{activeRun?.status.replace(/_/g, " ") ?? "No active run"}</strong>
            </article>
            <article className="summary-card">
              <span className="summary-label">Run ID</span>
              <strong>{activeRun?.id ?? "Create or import a run"}</strong>
            </article>
          </div>
        </section>
      </div>
    </section>
  );
}
