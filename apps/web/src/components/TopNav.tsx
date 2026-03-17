import { PRODUCT_NAME, PRODUCT_TAGLINE } from "../contracts";
import type { DataSourceState } from "../types";

interface TopNavProps {
  sourceState: DataSourceState;
}

export function TopNav({ sourceState }: TopNavProps) {
  return (
    <header className="top-nav">
      <div>
        <p className="eyebrow">Healthcare Decision Twin</p>
        <h1>{PRODUCT_NAME} Workspace</h1>
        <p className="top-subtitle">{PRODUCT_TAGLINE}</p>
      </div>
      <div className="source-pill">
        <span className={`dot dot-${sourceState.mode}`} />
        <div>
          <strong>{sourceState.mode === "api" ? "Live Local API" : "Deterministic Demo"}</strong>
          <p>{sourceState.note}</p>
        </div>
      </div>
    </header>
  );
}
