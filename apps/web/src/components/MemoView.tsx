import type { Memo } from "../types";

interface MemoViewProps {
  memo: Memo;
}

export function MemoView({ memo }: MemoViewProps) {
  return (
    <div className="memo-container">
      <header className="memo-header">
        <div>
          <p className="eyebrow">{memo.type === "operator" ? "Operator View" : "Capital View"}</p>
          <h3>{memo.title}</h3>
        </div>
        {(memo.citations?.length ?? 0) > 0 && <p className="memo-citations">Sources: {memo.citations?.join(", ")}</p>}
      </header>

      {memo.sections.map((section) => (
        <section key={section.title} className="memo-section">
          <h4>{section.title}</h4>
          <div className="memo-body">
            {section.content.split("\n").filter(Boolean).map((line, index) => (
              <p key={`${section.title}-${index}`}>{line.replace(/^- /, "")}</p>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
