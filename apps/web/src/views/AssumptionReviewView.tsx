import { useState } from "react";
import type { Assumption, InterrogationTurn } from "../types";

interface AssumptionReviewViewProps {
  assumptions: Assumption[];
  interrogation: InterrogationTurn[];
  onUpdateAssumption: (assumptionId: string, value: string) => Promise<void> | void;
  onAsk: (question: string, memoType?: "operator" | "capital") => Promise<void> | void;
}

export function AssumptionReviewView({
  assumptions,
  interrogation,
  onUpdateAssumption,
  onAsk
}: AssumptionReviewViewProps) {
  const [question, setQuestion] = useState("What actions should we take in the next 30 days?");
  const [memoType, setMemoType] = useState<"operator" | "capital">("operator");
  const [drafts, setDrafts] = useState<Record<string, string>>({});

  return (
    <section className="view">
      <div className="view-header">
        <div>
          <p className="eyebrow">Decision Review</p>
          <h2>Compare Actions</h2>
          <p className="subtext">
            Adjust assumptions, test questions, and compare operator versus capital interpretations of the same run.
          </p>
        </div>
      </div>

      <section className="panel">
        <div className="panel-header-row">
          <div>
            <h3>Assumption Confidence</h3>
            <p className="subtext">Pin the assumptions that matter before you treat the memo as a board-level output.</p>
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
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {assumptions.map((assumption) => (
              <tr key={assumption.id}>
                <td>
                  <strong>{assumption.key}</strong>
                  <p className="cell-meta">{assumption.statement}</p>
                </td>
                <td>
                  <input
                    value={drafts[assumption.id] ?? assumption.value}
                    onChange={(event) =>
                      setDrafts((current) => ({
                        ...current,
                        [assumption.id]: event.target.value
                      }))
                    }
                  />
                </td>
                <td>{assumption.impactArea}</td>
                <td>{Math.round(assumption.confidence * 100)}%</td>
                <td>{assumption.status.replace(/_/g, " ")}</td>
                <td>
                  <button
                    type="button"
                    className="secondary-btn"
                    onClick={() => onUpdateAssumption(assumption.id, drafts[assumption.id] ?? assumption.value)}
                  >
                    Confirm
                  </button>
                </td>
              </tr>
            ))}
            {!assumptions.length ? (
              <tr>
                <td colSpan={6} className="empty">
                  No assumptions available yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </section>

      <section className="panel">
        <div className="panel-header-row">
          <div>
            <h3>Interrogate the Decision</h3>
            <p className="subtext">Ask the run for an operator or capital answer grounded in the generated artifacts.</p>
          </div>
          <div className="variant-tabs">
            <button
              type="button"
              className={memoType === "operator" ? "active" : ""}
              onClick={() => setMemoType("operator")}
            >
              Operator
            </button>
            <button
              type="button"
              className={memoType === "capital" ? "active" : ""}
              onClick={() => setMemoType("capital")}
            >
              Capital
            </button>
          </div>
        </div>

        <div className="action-row">
          <input
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask about covenant pressure, access risk, service-line actions, or mitigation priorities."
          />
          <button type="button" className="primary-btn" onClick={() => onAsk(question, memoType)}>
            Ask
          </button>
        </div>

        <div className="chat-list">
          {interrogation.map((turn, index) => (
            <article key={`${turn.question}-${index}`} className="chat-item">
              <p className="chat-q">Q: {turn.question}</p>
              <p className="chat-a">A: {turn.answer}</p>
              {turn.citations.length ? <p className="citations">Sources: {turn.citations.join(", ")}</p> : null}
            </article>
          ))}
          {!interrogation.length ? <p className="empty">No interrogation turns yet.</p> : null}
        </div>
      </section>
    </section>
  );
}
