import { useState } from "react";
import type { Assumption, DecisionRun, EvidenceFile, ExtractedFact, Project } from "../types";

interface EvidenceReviewViewProps {
  project: Project | null;
  run: DecisionRun | null;
  evidence: EvidenceFile[];
  facts: ExtractedFact[];
  assumptions: Assumption[];
  onLoadDemo: () => Promise<void> | void;
  onUpload: (files: File[]) => Promise<void> | void;
  onExtract: () => Promise<void> | void;
}

export function EvidenceReviewView({
  project,
  run,
  evidence,
  facts,
  assumptions,
  onLoadDemo,
  onUpload,
  onExtract
}: EvidenceReviewViewProps) {
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const canExtract = evidence.length > 0;

  return (
    <section className="view">
      <div className="view-header">
        <div>
          <p className="eyebrow">Evidence Review</p>
          <h2>Review Assumptions</h2>
          <p className="subtext">
            Upload healthcare evidence, then extract assumptions, KPI candidates, and grounded facts for the run.
          </p>
        </div>
      </div>

      <div className="layout-two">
        <section className="panel">
          <div className="panel-header-row">
            <div>
              <h3>Active Case</h3>
              <p className="subtext">Project, scenario, and run metadata for the current decision workspace.</p>
            </div>
          </div>
          <div className="summary-grid">
            <article className="summary-card">
              <span className="summary-label">Project</span>
              <strong>{project?.name ?? "No project selected"}</strong>
            </article>
            <article className="summary-card">
              <span className="summary-label">Scenario</span>
              <strong>{run?.scenarioType.replace(/_/g, " ") ?? "Not started"}</strong>
            </article>
            <article className="summary-card">
              <span className="summary-label">Run ID</span>
              <strong>{run?.id ?? "Create a run first"}</strong>
            </article>
            <article className="summary-card">
              <span className="summary-label">Requirement</span>
              <strong>{run?.simulationRequirement ?? "No decision question yet"}</strong>
            </article>
          </div>
        </section>

        <section className="panel">
          <div className="panel-header-row">
            <div>
              <h3>Upload Evidence Pack</h3>
              <p className="subtext">Supports `.txt`, `.md`, and `.csv` in the current local-dev pipeline.</p>
            </div>
          </div>

          <input
            type="file"
            accept=".txt,.md,.csv"
            multiple
            onChange={(event) => setPendingFiles(event.target.files ? Array.from(event.target.files) : [])}
          />

          <div className="action-row">
            <button type="button" className="secondary-btn" onClick={onLoadDemo}>
              Load MetroCare Demo
            </button>
            <button
              type="button"
              className="secondary-btn"
              disabled={!pendingFiles.length}
              onClick={() => onUpload(pendingFiles)}
            >
              Upload Evidence
            </button>
            <button type="button" className="primary-btn" disabled={!canExtract} onClick={onExtract}>
              Extract Assumptions and KPI Signals
            </button>
          </div>

          {!canExtract ? (
            <p className="subtext">
              Upload at least one evidence file before extracting assumptions and KPI signals, or import the MetroCare demo
              from the Projects screen.
            </p>
          ) : null}

          <ul className="evidence-list">
            {evidence.map((file) => (
              <li key={file.id}>
                <strong>{file.filename ?? file.name}</strong>
                <span>
                  {Math.round((file.sizeBytes ?? file.size) / 1024)} KB · {file.extension?.toUpperCase() ?? "FILE"}
                </span>
                {file.extractedPreview ? <p className="cell-meta">{file.extractedPreview}</p> : null}
              </li>
            ))}
            {!evidence.length ? <li className="empty">No evidence uploaded yet.</li> : null}
          </ul>
        </section>
      </div>

      <section className="panel">
        <div className="panel-header-row">
          <div>
            <h3>Extracted Facts</h3>
            <p className="subtext">Facts are source-linked observations that ground the rest of the decision twin.</p>
          </div>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Fact</th>
              <th>Type</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {facts.map((fact) => (
              <tr key={fact.id}>
                <td>
                  <strong>{fact.title}</strong>
                  <p className="cell-meta">{fact.detail || fact.sourceExcerpt}</p>
                </td>
                <td>{fact.factType}</td>
                <td>{Math.round(fact.confidence * 100)}%</td>
              </tr>
            ))}
            {!facts.length ? (
              <tr>
                <td colSpan={3} className="empty">
                  No facts extracted yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </section>

      <section className="panel">
        <div className="panel-header-row">
          <div>
            <h3>Decision Assumptions</h3>
            <p className="subtext">These assumptions feed the stakeholder graph, scenario replay, and memo outputs.</p>
          </div>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Assumption</th>
              <th>Value</th>
              <th>Impact Area</th>
              <th>Confidence</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {assumptions.map((assumption) => (
              <tr key={assumption.id}>
                <td>
                  <strong>{assumption.key}</strong>
                  <p className="cell-meta">{assumption.statement}</p>
                </td>
                <td>{assumption.value}</td>
                <td>{assumption.impactArea}</td>
                <td>{Math.round(assumption.confidence * 100)}%</td>
                <td>{assumption.status.replace(/_/g, " ")}</td>
              </tr>
            ))}
            {!assumptions.length ? (
              <tr>
                <td colSpan={5} className="empty">
                  No assumptions extracted yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </section>
    </section>
  );
}
