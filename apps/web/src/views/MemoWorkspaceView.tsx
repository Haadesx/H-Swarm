import { useState } from "react";
import { MemoView } from "../components/MemoView";
import type { Memo } from "../types";

interface MemoWorkspaceViewProps {
  memos: { operator: Memo; capital: Memo };
  onGenerateMemos: () => Promise<void> | void;
  onAdvance: () => void;
}

export function MemoWorkspaceView({ memos, onGenerateMemos, onAdvance }: MemoWorkspaceViewProps) {
  const [active, setActive] = useState<"operator" | "capital">("operator");

  return (
    <section className="view">
      <div className="view-header">
        <div>
          <p className="eyebrow">Memo Workspace</p>
          <h2>Read Memo</h2>
          <p className="subtext">
            Generate synchronized outputs for operators and capital providers from the same scenario artifacts.
          </p>
        </div>
        <div className="action-row">
          <button type="button" className="secondary-btn" onClick={onAdvance}>
            Compare Actions
          </button>
          <button type="button" className="primary-btn" onClick={onGenerateMemos}>
            Generate Operator + Capital Memos
          </button>
        </div>
      </div>

      <div className="memo-tab-row">
        <button type="button" className={active === "operator" ? "active" : ""} onClick={() => setActive("operator")}>
          Operator Brief
        </button>
        <button type="button" className={active === "capital" ? "active" : ""} onClick={() => setActive("capital")}>
          Capital Memo
        </button>
      </div>

      <MemoView memo={memos[active]} />
    </section>
  );
}
