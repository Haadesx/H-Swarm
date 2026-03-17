import type { TimelineEvent } from "../types";

interface TimelineViewProps {
  events: TimelineEvent[];
  selectedVariant: TimelineEvent["variant"];
  onVariantChange: (variant: TimelineEvent["variant"]) => void;
}

export function TimelineView({ events, selectedVariant, onVariantChange }: TimelineViewProps) {
  const filtered = events
    .filter((event) => event.variant === selectedVariant)
    .sort((a, b) => a.day - b.day || a.event.localeCompare(b.event));

  return (
    <section className="panel">
      <div className="panel-header-row">
        <div>
          <h3>30 / 90 / 180 Day Timeline</h3>
          <p className="subtext">Scenario replay is expressed as operating, regulatory, and capital events rather than social actions.</p>
        </div>
        <div className="variant-tabs">
          <button
            className={selectedVariant === "base_case" ? "active" : ""}
            type="button"
            onClick={() => onVariantChange("base_case")}
          >
            Base
          </button>
          <button
            className={selectedVariant === "downside_case" ? "active" : ""}
            type="button"
            onClick={() => onVariantChange("downside_case")}
          >
            Downside
          </button>
          <button
            className={selectedVariant === "severe_case" ? "active" : ""}
            type="button"
            onClick={() => onVariantChange("severe_case")}
          >
            Severe
          </button>
        </div>
      </div>
      <div className="timeline">
        {filtered.map((event) => (
          <article key={event.id} className="timeline-card">
            <div className="timeline-day">Day {event.day}</div>
            <div>
              <h4>{event.event}</h4>
              <p className="timeline-meta">
                {event.channel} · {event.stakeholder} · {Math.round(event.confidence * 100)}% confidence
              </p>
              <p>{event.implication}</p>
              {event.citations.length > 0 && <p className="citations">Sources: {event.citations.join(", ")}</p>}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
