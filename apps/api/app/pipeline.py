"""Deterministic local-dev pipeline for HealthTwin decision runs."""

from __future__ import annotations

from dataclasses import dataclass
import csv
import io
import json
import re
import uuid
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from openai import OpenAI
from sqlalchemy import delete
from sqlalchemy.orm import Session

from .config import get_settings, load_domain_contract
from .models import (
    Assumption,
    DecisionRun,
    DecisionRunStatus,
    EvidenceFile,
    ExtractedFact,
    KPI,
    Memo,
    MemoType,
    Project,
    ScenarioCase,
    SimulationEvent,
    StakeholderEdge,
    StakeholderNode,
)


ALLOWED_EXTENSIONS = {"txt", "md", "csv"}
CASE_FACTORS = {
    ScenarioCase.base: 1.0,
    ScenarioCase.downside: 1.6,
    ScenarioCase.severe: 2.3,
}
settings = get_settings()


@dataclass(frozen=True)
class AssumptionSpec:
    key: str
    value: str
    category: str
    impact_area: str
    rationale: str
    confidence: float
    status: str
    source_evidence_ids: List[str]

    def to_model(self, run_id: str) -> Assumption:
        return Assumption(
            id=new_id(),
            decision_run_id=run_id,
            key=self.key,
            value=self.value,
            category=self.category,
            impact_area=self.impact_area,
            rationale=self.rationale,
            source_evidence_ids=self.source_evidence_ids,
            confidence=self.confidence,
            status=self.status,
            user_modified=False,
        )


def new_id() -> str:
    return str(uuid.uuid4())


def default_requirement_for_scenario(scenario_type: str) -> str:
    contract = load_domain_contract()
    for template in contract.get("scenarioTemplates", []):
        if template["id"] == scenario_type:
            return template["defaultRequirement"]
    return (
        "Simulate reimbursement pressure and its impact on operations, care access, "
        "and financing outcomes over 30, 90, and 180 days."
    )


def extract_text_and_table(filename: str, content: bytes) -> Tuple[str, Dict | None]:
    ext = Path(filename).suffix.lower().lstrip(".")
    decoded = content.decode("utf-8", errors="ignore")

    if ext in {"txt", "md"}:
        return decoded.strip(), None

    if ext == "csv":
        rows = list(csv.DictReader(io.StringIO(decoded)))
        numeric_summaries: Dict[str, float] = {}
        if rows:
            for key in rows[0].keys():
                values = []
                for row in rows:
                    raw = (row.get(key) or "").replace(",", "").strip()
                    try:
                        values.append(float(raw))
                    except ValueError:
                        continue
                if values:
                    numeric_summaries[key] = sum(values) / len(values)
        table = {
            "row_count": len(rows),
            "columns": list(rows[0].keys()) if rows else [],
            "numeric_means": numeric_summaries,
        }
        return decoded.strip(), table

    raise ValueError(f"Unsupported file extension: {ext}")


def _find_percentage(text: str, pattern: str, default: float) -> float:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return default
    try:
        return float(match.group(1))
    except (TypeError, ValueError):
        return default


def _collect_text(evidence_files: Iterable[EvidenceFile]) -> str:
    return "\n\n".join(f.extracted_text for f in evidence_files if f.extracted_text)


def _evidence_catalog(evidence_files: Iterable[EvidenceFile]) -> List[dict]:
    return [
        {
            "id": item.id,
            "filename": item.filename,
            "extension": item.extension,
            "preview": item.extracted_text[:400],
        }
        for item in evidence_files
    ]


def _citation_filenames(evidence_files: List[EvidenceFile], ids: List[str]) -> List[str]:
    by_id = {item.id: item.filename for item in evidence_files}
    return [by_id[evidence_id] for evidence_id in ids if evidence_id in by_id][:4]


def _infer_baseline_kpis(evidence_files: Iterable[EvidenceFile]) -> Dict[str, float]:
    kpis = {
        "net_margin_pct": 3.2,
        "days_cash_on_hand": 145.0,
        "denied_claim_rate_pct": 11.0,
        "avg_wait_days": 14.0,
        "occupancy_pct": 78.0,
    }
    for ev in evidence_files:
        table = ev.extracted_table or {}
        means = table.get("numeric_means", {})
        for key, value in means.items():
            lowered = key.lower()
            if "margin" in lowered:
                kpis["net_margin_pct"] = float(value)
            elif "cash" in lowered and "day" in lowered:
                kpis["days_cash_on_hand"] = float(value)
            elif "denial" in lowered:
                kpis["denied_claim_rate_pct"] = float(value)
            elif "wait" in lowered or "delay" in lowered:
                kpis["avg_wait_days"] = float(value)
            elif "occupancy" in lowered:
                kpis["occupancy_pct"] = float(value)
    return kpis


def _llm_client() -> OpenAI | None:
    if not settings.llm_api_key or not settings.llm_model:
        return None
    return OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url or None)


def _safe_json_completion(system_prompt: str, user_prompt: str) -> dict | None:
    client = _llm_client()
    if client is None:
        return None
    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or ""
        return json.loads(content)
    except Exception:
        return None


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_default_assumption_specs(
    evidence_ids: List[str],
    reimbursement_cut_pct: float,
    denial_increase_pct: float,
    labor_increase_pct: float,
) -> List[AssumptionSpec]:
    return [
        AssumptionSpec(
            key="reimbursement_cut_pct",
            value=f"{reimbursement_cut_pct:.1f}",
            category="revenue",
            impact_area="finance",
            rationale="Detected reimbursement cut signal from evidence and scenario framing.",
            source_evidence_ids=evidence_ids,
            confidence=0.84,
            status="needs_review",
        ),
        AssumptionSpec(
            key="denial_pressure_pct",
            value=f"{denial_increase_pct:.1f}",
            category="payer",
            impact_area="finance",
            rationale="Denial pressure is modeled as a secondary effect during reimbursement stress.",
            source_evidence_ids=evidence_ids,
            confidence=0.77,
            status="needs_review",
        ),
        AssumptionSpec(
            key="labor_cost_pressure_pct",
            value=f"{labor_increase_pct:.1f}",
            category="labor",
            impact_area="operations",
            rationale="Labor pressure from staffing retention is applied as a cost-side amplifier.",
            source_evidence_ids=evidence_ids,
            confidence=0.72,
            status="needs_review",
        ),
    ]


def _build_provider_assumption_specs(llm_result: dict, evidence_ids: List[str]) -> List[AssumptionSpec]:
    specs: List[AssumptionSpec] = []
    for item in llm_result.get("assumptions", []):
        specs.append(
            AssumptionSpec(
                key=str(item.get("key", "assumption_key")),
                value=str(item.get("value", "")),
                category=str(item.get("category", "operations")),
                impact_area=str(item.get("impact_area", "operations")),
                rationale=str(item.get("rationale", "Provider-backed extraction output.")),
                source_evidence_ids=evidence_ids,
                confidence=_float_or_none(item.get("confidence")) or 0.7,
                status=str(item.get("status", "needs_review")),
            )
        )
    return specs


def _provider_simulation_has_kpi_deltas(cases: Iterable[dict]) -> bool:
    for case in cases:
        for horizon in case.get("horizons", []) or []:
            for delta in horizon.get("kpi_deltas", []) or []:
                name = delta.get("name")
                delta_value = _float_or_none(delta.get("delta_value"))
                if name and delta_value is not None:
                    return True
    return False


def _build_provider_simulation_rows(
    run: DecisionRun,
    provider_simulation: dict,
    baseline_kpis: Dict[str, KPI],
) -> tuple[list[SimulationEvent], list[KPI], int, int]:
    events: list[SimulationEvent] = []
    kpis: list[KPI] = []
    total_events = 0
    provider_kpi_rows = 0
    citation_ids = [item.id for item in run.project.evidence_files[:2]]
    for case in provider_simulation.get("cases", []):
        case_name = case.get("case_name")
        if case_name not in {member.value for member in ScenarioCase}:
            continue
        case_enum = next(member for member in ScenarioCase if member.value == case_name)
        for horizon_entry in case.get("horizons", []) or []:
            horizon_days = int(horizon_entry.get("horizon_days", run.time_horizons[0] if run.time_horizons else 30))
            impacts_by_name: Dict[str, float] = {}
            for item in horizon_entry.get("kpi_deltas", []) or []:
                name = item.get("name")
                delta = _float_or_none(item.get("delta_value"))
                if name and delta is not None:
                    impacts_by_name[name] = delta

            for idx, event in enumerate(horizon_entry.get("events", []) or [], start=1):
                events.append(
                    SimulationEvent(
                        id=new_id(),
                        decision_run_id=run.id,
                        case_name=case_enum,
                        horizon_days=horizon_days,
                        event_order=idx,
                        event_type=str(event.get("event_type", "Scenario Event")),
                        stakeholder=str(event.get("stakeholder", "Unknown Stakeholder")),
                        description=str(event.get("description", "")),
                        kpi_impacts=impacts_by_name,
                        confidence=_float_or_none(event.get("confidence")) or 0.7,
                        citation_evidence_ids=citation_ids,
                    )
                )
                total_events += 1

            for metric_name, delta in impacts_by_name.items():
                baseline = baseline_kpis.get(metric_name)
                if baseline is None:
                    continue
                kpis.append(
                    KPI(
                        id=new_id(),
                        decision_run_id=run.id,
                        case_name=case_enum,
                        horizon_days=horizon_days,
                        name=metric_name,
                        unit=baseline.unit,
                        baseline_value=baseline.baseline_value,
                        projected_value=round(baseline.baseline_value + delta, 2),
                        delta_value=delta,
                        source_evidence_ids=baseline.source_evidence_ids,
                    )
                )
                provider_kpi_rows += 1
    return events, kpis, total_events, provider_kpi_rows


def _provider_backed_extraction(
    run: DecisionRun,
    project: Project,
    evidence_files: List[EvidenceFile],
    combined_text: str,
    baseline: Dict[str, float],
) -> dict | None:
    if run.metadata_json.get("force_deterministic_demo"):
        return None
    payload = {
        "project_name": project.name,
        "scenario_type": run.scenario_type,
        "simulation_requirement": run.simulation_requirement,
        "baseline_kpis": baseline,
        "evidence": [
            {
                "id": item.id,
                "filename": item.filename,
                "preview": item.extracted_text[:1200],
                "table_summary": item.extracted_table,
            }
            for item in evidence_files[:5]
        ],
        "combined_text_preview": combined_text[:6000],
    }
    system_prompt = (
        "You are a healthcare finance extraction engine. Return strict JSON with keys "
        "'assumptions' and 'facts'. Assumptions must be an array of objects with keys "
        "key, value, category, impact_area, rationale, confidence, status. Facts must be an array of objects "
        "with keys fact_type, title, detail, source_excerpt, confidence, normalized_value_json. "
        "Use only evidence provided. Keep categories aligned to healthcare operator and capital workflows."
    )
    parsed = _safe_json_completion(system_prompt, json.dumps(payload, ensure_ascii=False))
    if not parsed:
        return None
    assumptions = parsed.get("assumptions")
    facts = parsed.get("facts")
    if not isinstance(assumptions, list) or not isinstance(facts, list):
        return None
    return {"assumptions": assumptions[:8], "facts": facts[:12]}


def _provider_backed_graph(
    run: DecisionRun,
    assumptions: List[Assumption],
    facts: List[ExtractedFact],
) -> dict | None:
    if run.metadata_json.get("force_deterministic_demo"):
        return None
    payload = {
        "scenario_type": run.scenario_type,
        "simulation_requirement": run.simulation_requirement,
        "assumptions": [
            {
                "key": item.key,
                "value": item.value,
                "impact_area": item.impact_area,
                "rationale": item.rationale,
            }
            for item in assumptions[:8]
        ],
        "facts": [
            {
                "fact_type": item.fact_type,
                "title": item.title,
                "detail": item.detail,
            }
            for item in facts[:10]
        ],
    }
    system_prompt = (
        "You are a healthcare stakeholder graph synthesis engine. Return strict JSON with keys 'nodes' and 'edges'. "
        "Nodes require name, entity_type, role_summary, influence_score. "
        "Edges require source_name, target_name, relation_type, rationale. "
        "Prefer operators, payers, regulators, patient groups, lenders, investors, and workforce entities."
    )
    parsed = _safe_json_completion(system_prompt, json.dumps(payload, ensure_ascii=False))
    if not parsed:
        return None
    nodes = parsed.get("nodes")
    edges = parsed.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return None
    return {"nodes": nodes[:12], "edges": edges[:18]}


def _provider_backed_simulation(
    run: DecisionRun,
    assumptions: List[Assumption],
    stakeholders: List[StakeholderNode],
    baseline_kpis: Dict[str, KPI],
) -> dict | None:
    if run.metadata_json.get("force_deterministic_demo"):
        return None
    payload = {
        "scenario_type": run.scenario_type,
        "simulation_requirement": run.simulation_requirement,
        "time_horizons": run.time_horizons,
        "assumptions": [
            {"key": item.key, "value": item.value, "impact_area": item.impact_area}
            for item in assumptions[:8]
        ],
        "stakeholders": [
            {
                "name": item.name,
                "entity_type": item.entity_type,
                "role_summary": item.role_summary,
                "influence_score": item.influence_score,
            }
            for item in stakeholders[:10]
        ],
        "baseline_kpis": {
            key: {"baseline_value": item.baseline_value, "unit": item.unit}
            for key, item in baseline_kpis.items()
        },
    }
    system_prompt = (
        "You are a healthcare decision simulation engine. Return strict JSON with key 'cases'. "
        "Cases must be an array of objects, one per case_name in ['base_case','downside_case','severe_case']. "
        "Each case object must include case_name and horizons. Horizons is an array with horizon_days, events, and kpi_deltas. "
        "Each event needs event_type, stakeholder, description, confidence. "
        "Each kpi_delta item needs name, delta_value. Keep outputs grounded and concise."
    )
    parsed = _safe_json_completion(system_prompt, json.dumps(payload, ensure_ascii=False))
    if not parsed:
        return None
    cases = parsed.get("cases")
    if not isinstance(cases, list):
        return None
    return {"cases": cases}


def run_extraction(db: Session, run: DecisionRun, project: Project) -> dict:
    evidence_files = list(project.evidence_files)
    combined_text = _collect_text(evidence_files)
    reimbursement_cut_pct = _find_percentage(
        combined_text,
        r"(\d+(?:\.\d+)?)\s*%\s*(?:cms\s*)?(?:reimbursement|rate)\s*(?:cut|reduction)",
        7.0,
    )
    denial_increase_pct = _find_percentage(
        combined_text,
        r"(\d+(?:\.\d+)?)\s*%\s*(?:increase|rise).{0,30}(?:denial|denied)",
        2.0,
    )
    labor_increase_pct = _find_percentage(
        combined_text,
        r"(\d+(?:\.\d+)?)\s*%\s*(?:increase|rise).{0,30}(?:labor|staff|wage)",
        5.0,
    )
    baseline = _infer_baseline_kpis(evidence_files)

    db.execute(delete(Assumption).where(Assumption.decision_run_id == run.id))
    db.execute(delete(ExtractedFact).where(ExtractedFact.decision_run_id == run.id))
    db.execute(delete(KPI).where(KPI.decision_run_id == run.id, KPI.case_name.is_(None)))

    llm_extraction = _provider_backed_extraction(run, project, evidence_files, combined_text, baseline)
    evidence_ids = [e.id for e in evidence_files[:2]]
    default_assumption_specs = _build_default_assumption_specs(
        evidence_ids,
        reimbursement_cut_pct,
        denial_increase_pct,
        labor_increase_pct,
    )
    assumption_specs = default_assumption_specs
    if llm_extraction:
        provider_assumptions = _build_provider_assumption_specs(llm_extraction, evidence_ids)
        if provider_assumptions:
            assumption_specs = provider_assumptions

    assumptions = [spec.to_model(run.id) for spec in assumption_specs]
    db.add_all(assumptions)

    extracted_facts = [
        ExtractedFact(
            id=new_id(),
            decision_run_id=run.id,
            evidence_file_id=evidence_files[0].id if evidence_files else None,
            fact_type="scenario_signal",
            title="Reimbursement pressure detected",
            detail=f"Scenario framing indicates a {reimbursement_cut_pct:.1f}% reimbursement reduction affecting provider economics.",
            source_excerpt=combined_text[:280],
            normalized_value_json={"metric": "reimbursement_cut_pct", "value": reimbursement_cut_pct, "unit": "%"},
            confidence=0.84,
        ),
        ExtractedFact(
            id=new_id(),
            decision_run_id=run.id,
            evidence_file_id=evidence_files[1].id if len(evidence_files) > 1 else (evidence_files[0].id if evidence_files else None),
            fact_type="financial_baseline",
            title="Baseline operating performance captured",
            detail=(
                f"Baseline net margin is {baseline['net_margin_pct']:.1f}%, denied-claim rate is "
                f"{baseline['denied_claim_rate_pct']:.1f}%, and days cash on hand is {baseline['days_cash_on_hand']:.1f}."
            ),
            source_excerpt="Structured KPI baseline extracted from uploaded evidence.",
            normalized_value_json=baseline,
            confidence=0.88,
        ),
        ExtractedFact(
            id=new_id(),
            decision_run_id=run.id,
            evidence_file_id=evidence_files[0].id if evidence_files else None,
            fact_type="operational_constraint",
            title="Operational access pressure likely",
            detail=(
                f"Labor-cost pressure of {labor_increase_pct:.1f}% and denial pressure of {denial_increase_pct:.1f}% "
                "indicate likely access and throughput deterioration."
            ),
            source_excerpt=combined_text[:280],
            normalized_value_json={
                "labor_cost_pressure_pct": labor_increase_pct,
                "denial_pressure_pct": denial_increase_pct,
            },
            confidence=0.76,
        ),
    ]
    if llm_extraction:
        extracted_facts = []
        for item in llm_extraction["facts"]:
            extracted_facts.append(
                ExtractedFact(
                    id=new_id(),
                    decision_run_id=run.id,
                    evidence_file_id=evidence_files[0].id if evidence_files else None,
                    fact_type=str(item.get("fact_type", "fact")),
                    title=str(item.get("title", "Extracted fact")),
                    detail=str(item.get("detail", "")),
                    source_excerpt=str(item.get("source_excerpt", combined_text[:280])),
                    normalized_value_json=item.get("normalized_value_json", {}) if isinstance(item.get("normalized_value_json", {}), dict) else {},
                    confidence=float(item.get("confidence", 0.7)),
                )
            )
    db.add_all(extracted_facts)

    for name, value in baseline.items():
        unit = "%"
        if "days" in name:
            unit = "days"
        db.add(
            KPI(
                id=new_id(),
                decision_run_id=run.id,
                case_name=None,
                horizon_days=None,
                name=name,
                unit=unit,
                baseline_value=float(value),
                projected_value=None,
                delta_value=None,
                source_evidence_ids=[e.id for e in evidence_files[:2]],
            )
        )

    run.status = DecisionRunStatus.extracted
    run.metadata_json = {
        **run.metadata_json,
        "extracted": True,
        "baseline_kpis": baseline,
        "assumption_keys": [a.key for a in assumptions],
        "extracted_fact_count": len(extracted_facts),
        "extraction_mode": "provider" if llm_extraction else "deterministic",
    }
    return {"assumptions": assumptions, "baseline_kpis": baseline, "facts": extracted_facts}


def build_stakeholder_graph(db: Session, run: DecisionRun) -> dict:
    db.execute(delete(StakeholderEdge).where(StakeholderEdge.decision_run_id == run.id))
    db.execute(delete(StakeholderNode).where(StakeholderNode.decision_run_id == run.id))

    provider_graph = _provider_backed_graph(run, list(run.assumptions), list(run.extracted_facts))

    node_specs = [
        ("Provider Operations Office", "Provider", "Operating owner of service-line execution.", 0.92),
        ("Regional Hospital Network", "Hospital", "Core care delivery and margin center.", 0.86),
        ("Commercial Payer Coalition", "Payer", "Reimbursement and denial policy counterpart.", 0.83),
        ("State Health Regulator", "Regulator", "Oversight on access, safety, and reporting.", 0.74),
        ("Patient Advocacy Council", "PatientAdvocate", "Public pressure on delays and access.", 0.66),
        ("Credit Facility Lender", "Lender", "Monitors covenant and liquidity risk.", 0.88),
        ("Growth Equity Sponsor", "Investor", "Tracks downside, recovery, and strategic options.", 0.79),
        ("Nursing Workforce Pool", "Organization", "Labor availability and wage pressure vector.", 0.69),
    ]
    nodes: Dict[str, StakeholderNode] = {}
    selected_node_specs = node_specs
    selected_edge_specs = edge_specs = [
        ("Provider Operations Office", "Regional Hospital Network", "OPERATES", "Provider office directs hospital execution."),
        ("Commercial Payer Coalition", "Regional Hospital Network", "CONTRACTS_WITH", "Payer reimbursement terms drive realized revenue."),
        ("State Health Regulator", "Regional Hospital Network", "REGULATES", "Regulator monitors access and compliance."),
        ("Patient Advocacy Council", "State Health Regulator", "INFLUENCES", "Public complaints affect regulator scrutiny."),
        ("Credit Facility Lender", "Regional Hospital Network", "EXPOSED_TO", "Lender risk tracks operating deterioration."),
        ("Growth Equity Sponsor", "Provider Operations Office", "FUNDS", "Sponsor influences restructuring decisions."),
        ("Nursing Workforce Pool", "Regional Hospital Network", "DEPENDS_ON", "Staffing availability shapes throughput."),
        ("Commercial Payer Coalition", "Patient Advocacy Council", "RESPONDS_TO", "Payer posture reacts to public pressure."),
    ]
    if provider_graph:
        selected_node_specs = [
            (
                str(item.get("name", "Stakeholder")),
                str(item.get("entity_type", "Organization")),
                str(item.get("role_summary", "Healthcare stakeholder.")),
                float(item.get("influence_score", 0.6)),
            )
            for item in provider_graph["nodes"]
        ]
        selected_edge_specs = [
            (
                str(item.get("source_name", "")),
                str(item.get("target_name", "")),
                str(item.get("relation_type", "RELATED_TO")),
                str(item.get("rationale", "Provider-backed graph relation.")),
            )
            for item in provider_graph["edges"]
        ]

    for name, entity_type, summary, influence in selected_node_specs:
        node = StakeholderNode(
            id=new_id(),
            decision_run_id=run.id,
            name=name,
            entity_type=entity_type,
            role_summary=summary,
            influence_score=influence,
        )
        nodes[name] = node
        db.add(node)

    for source, target, relation, rationale in selected_edge_specs:
        if source not in nodes or target not in nodes:
            continue
        db.add(
            StakeholderEdge(
                id=new_id(),
                decision_run_id=run.id,
                source_node_id=nodes[source].id,
                target_node_id=nodes[target].id,
                relation_type=relation,
                rationale=rationale,
            )
        )

    run.status = DecisionRunStatus.graph_built
    run.metadata_json = {**run.metadata_json, "graph_built": True, "graph_mode": "provider" if provider_graph else "deterministic"}
    return {"node_count": len(selected_node_specs), "edge_count": len(selected_edge_specs)}


def _baseline_kpi_map(db: Session, run_id: str) -> Dict[str, KPI]:
    baseline_kpis = (
        db.query(KPI)
        .filter(KPI.decision_run_id == run_id, KPI.case_name.is_(None))
        .all()
    )
    return {k.name: k for k in baseline_kpis}


def run_simulation(db: Session, run: DecisionRun) -> dict:
    db.execute(delete(SimulationEvent).where(SimulationEvent.decision_run_id == run.id))
    db.execute(delete(KPI).where(KPI.decision_run_id == run.id, KPI.case_name.is_not(None)))

    assumptions = {a.key: float(a.value) for a in run.assumptions}
    reimbursement_cut = assumptions.get("reimbursement_cut_pct", 7.0)
    denial_pressure = assumptions.get("denial_pressure_pct", 2.0)
    labor_pressure = assumptions.get("labor_cost_pressure_pct", 5.0)
    baseline_kpis = _baseline_kpi_map(db, run.id)

    provider_simulation = _provider_backed_simulation(
        run,
        list(run.assumptions),
        list(run.stakeholder_nodes),
        baseline_kpis,
    )
    total_events = 0
    provider_kpi_rows = 0
    provider_simulation_reason: str | None = None
    if provider_simulation:
        if _provider_simulation_has_kpi_deltas(provider_simulation.get("cases", [])):
            events, kpis, total_events, provider_kpi_rows = _build_provider_simulation_rows(
                run,
                provider_simulation,
                baseline_kpis,
            )
            if provider_kpi_rows:
                db.add_all(events)
                db.add_all(kpis)
                run.status = DecisionRunStatus.simulated
                run.metadata_json = {
                    **run.metadata_json,
                    "simulated": True,
                    "event_count": total_events,
                    "simulation_mode": "provider",
                    "simulation_mode_reason": "provider_response_valid",
                    "provider_kpi_rows": provider_kpi_rows,
                }
                return {"event_count": total_events}
        provider_simulation_reason = "provider_response_lacked_kpi_deltas"

    for case_name, factor in CASE_FACTORS.items():
        for horizon in run.time_horizons:
            horizon_ratio = horizon / 90.0
            margin_delta = -(0.6 + reimbursement_cut * 0.08) * factor * horizon_ratio
            denial_delta = (0.5 + denial_pressure * 0.35) * factor * horizon_ratio
            wait_delta = (0.8 + labor_pressure * 0.30) * factor * horizon_ratio
            cash_delta = -(4.0 + reimbursement_cut * 0.7) * factor * horizon_ratio
            occupancy_delta = -(0.7 + reimbursement_cut * 0.20) * factor * horizon_ratio

            impacts = {
                "net_margin_pct": round(margin_delta, 2),
                "denied_claim_rate_pct": round(denial_delta, 2),
                "avg_wait_days": round(wait_delta, 2),
                "days_cash_on_hand": round(cash_delta, 2),
                "occupancy_pct": round(occupancy_delta, 2),
            }
            events = [
                ("Revenue Pressure", "Commercial Payer Coalition", f"Reimbursement compression reduces realized revenue by horizon {horizon} days."),
                ("Operational Strain", "Regional Hospital Network", "Service-line throughput slows as labor and denial pressure accumulate."),
                ("Regulatory Escalation", "State Health Regulator", "Access deterioration raises oversight intensity and reporting burden."),
                ("Capital Concern", "Credit Facility Lender", "Liquidity stress increases covenant watch probability."),
                ("Public Trust Drift", "Patient Advocacy Council", "Wait-time growth raises reputational downside and complaint volume."),
            ]
            for idx, (event_type, stakeholder, description) in enumerate(events, start=1):
                db.add(
                    SimulationEvent(
                        id=new_id(),
                        decision_run_id=run.id,
                        case_name=case_name,
                        horizon_days=horizon,
                        event_order=idx,
                        event_type=event_type,
                        stakeholder=stakeholder,
                        description=description,
                        kpi_impacts=impacts,
                        confidence=max(0.55, 0.87 - idx * 0.04),
                        citation_evidence_ids=[e.id for e in run.project.evidence_files[:2]],
                    )
                )
                total_events += 1

            for metric_name, delta in impacts.items():
                baseline = baseline_kpis.get(metric_name)
                if baseline is None:
                    continue
                db.add(
                    KPI(
                        id=new_id(),
                        decision_run_id=run.id,
                        case_name=case_name,
                        horizon_days=horizon,
                        name=metric_name,
                        unit=baseline.unit,
                        baseline_value=baseline.baseline_value,
                        projected_value=round(baseline.baseline_value + delta, 2),
                        delta_value=delta,
                        source_evidence_ids=baseline.source_evidence_ids,
                    )
                )

    run.status = DecisionRunStatus.simulated
    run.metadata_json = {
        **run.metadata_json,
        "simulated": True,
        "event_count": total_events,
        "simulation_mode": "deterministic",
        "simulation_mode_reason": provider_simulation_reason or "deterministic",
    }
    return {"event_count": total_events}


def generate_memos(db: Session, run: DecisionRun) -> dict:
    db.execute(delete(Memo).where(Memo.decision_run_id == run.id))
    contract = load_domain_contract()
    sections = contract.get("memoSections", [])
    assumptions = list(run.assumptions)
    base_events = [
        e
        for e in run.simulation_events
        if e.case_name == ScenarioCase.base and e.horizon_days in (30, 90, 180)
    ]
    kpis = [k for k in run.kpis if k.case_name == ScenarioCase.base]

    evidence_files = list(run.project.evidence_files)
    memo_payload = _build_memo_payload(run, assumptions, base_events, kpis, evidence_files)
    operator_content, operator_sections = _draft_memo(
        memo_type=MemoType.operator,
        title=f"Operator Brief - {run.project.name}",
        payload=memo_payload,
    )
    capital_content, capital_sections = _draft_memo(
        memo_type=MemoType.capital,
        title=f"Capital Memo - {run.project.name}",
        payload=memo_payload,
    )

    citations = [{"type": "evidence_file", "id": e.id, "filename": e.filename} for e in evidence_files]

    operator_memo = Memo(
        id=new_id(),
        decision_run_id=run.id,
        memo_type=MemoType.operator,
        title=f"Operator Brief - {run.project.name}",
        content_markdown=operator_content,
        sections=operator_sections or [{"name": s} for s in sections],
        citations=citations,
    )
    capital_memo = Memo(
        id=new_id(),
        decision_run_id=run.id,
        memo_type=MemoType.capital,
        title=f"Capital Memo - {run.project.name}",
        content_markdown=capital_content,
        sections=capital_sections or [{"name": s} for s in sections],
        citations=citations,
    )
    db.add(operator_memo)
    db.add(capital_memo)

    run.status = DecisionRunStatus.memos_generated
    run.metadata_json = {**run.metadata_json, "memos_generated": True}
    return {"memo_ids": [operator_memo.id, capital_memo.id]}


def _build_memo_payload(
    run: DecisionRun,
    assumptions: List[Assumption],
    base_events: List[SimulationEvent],
    kpis: List[KPI],
    evidence_files: List[EvidenceFile],
) -> Dict[str, object]:
    return {
        "project": {
            "name": run.project.name,
            "organization_name": run.project.organization_name,
            "scenario_type": run.scenario_type,
            "simulation_requirement": run.simulation_requirement,
            "time_horizons": run.time_horizons,
        },
        "assumptions": [
            {
                "key": item.key,
                "value": item.value,
                "rationale": item.rationale,
                "confidence": item.confidence,
                "impact_area": item.impact_area,
                "status": item.status,
                "citations": _citation_filenames(evidence_files, item.source_evidence_ids),
            }
            for item in assumptions
        ],
        "facts": [
            {
                "title": item.title,
                "detail": item.detail,
                "confidence": item.confidence,
                "citations": _citation_filenames(evidence_files, [item.evidence_file_id] if item.evidence_file_id else []),
            }
            for item in run.extracted_facts[:10]
        ],
        "timeline": [
            {
                "day": item.horizon_days,
                "event_type": item.event_type,
                "stakeholder": item.stakeholder,
                "description": item.description,
                "confidence": item.confidence,
                "citations": _citation_filenames(evidence_files, item.citation_evidence_ids),
            }
            for item in sorted(base_events, key=lambda x: (x.horizon_days, x.event_order))
        ],
        "kpis": [
            {
                "name": item.name,
                "baseline_value": item.baseline_value,
                "projected_value": item.projected_value,
                "delta_value": item.delta_value,
                "unit": item.unit,
                "horizon_days": item.horizon_days,
                "citations": _citation_filenames(evidence_files, item.source_evidence_ids),
            }
            for item in sorted(kpis, key=lambda x: (x.horizon_days or 0, x.name))
        ],
        "stakeholders": [
            {
                "name": node.name,
                "entity_type": node.entity_type,
                "role_summary": node.role_summary,
                "influence_score": node.influence_score,
            }
            for node in run.stakeholder_nodes
        ],
        "evidence": _evidence_catalog(evidence_files),
        "force_deterministic_demo": bool(run.metadata_json.get("force_deterministic_demo")),
    }


def _draft_memo(memo_type: MemoType, title: str, payload: Dict[str, object]) -> Tuple[str, List[dict]]:
    if settings.llm_api_key and settings.llm_model and not bool(payload.get("force_deterministic_demo")):
        drafted = _draft_memo_with_llm(memo_type, title, payload)
        if drafted is not None:
            return drafted
    return _draft_memo_deterministic(memo_type, title, payload)


def _draft_memo_with_llm(
    memo_type: MemoType,
    title: str,
    payload: Dict[str, object],
) -> Tuple[str, List[dict]] | None:
    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url or None)
    system_prompt = (
        "You are drafting an evidence-backed healthcare decision memo. Use only the supplied JSON payload. "
        "Do not invent evidence, metrics, stakeholders, or timelines. Return strict JSON with keys "
        "'content_markdown' and 'sections'. Each item in 'sections' must include 'name', 'content', and 'citations'. "
        "Citations must be filenames present in the payload evidence catalog. State uncertainty explicitly."
    )
    user_prompt = (
        f"Memo type: {memo_type.value}\n"
        f"Title: {title}\n"
        "Draft for decision-makers in healthcare finance and operations.\n"
        "Required section coverage: Executive Summary, Scenario Assumptions, Stakeholder Map, "
        "30/90/180 Day Event Timeline, Recommended Actions, Confidence and Blind Spots.\n"
        f"Payload:\n{json.dumps(payload, ensure_ascii=False)}"
    )
    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or ""
        parsed = json.loads(content)
        markdown = str(parsed.get("content_markdown", "")).strip()
        sections = parsed.get("sections", [])
        if not markdown or not isinstance(sections, list):
            return None
        normalized_sections = []
        for item in sections:
            if not isinstance(item, dict):
                continue
            normalized_sections.append(
                {
                    "name": str(item.get("name") or "Untitled Section"),
                    "content": str(item.get("content") or ""),
                    "citations": [str(value) for value in item.get("citations", []) if value],
                }
            )
        if not normalized_sections:
            return None
        return markdown, normalized_sections
    except Exception:
        return None


def _draft_memo_deterministic(
    memo_type: MemoType,
    title: str,
    payload: Dict[str, object],
) -> Tuple[str, List[dict]]:
    assumptions = payload["assumptions"]
    facts = payload["facts"]
    timeline = payload["timeline"]
    kpis = payload["kpis"]
    stakeholders = payload["stakeholders"]
    evidence = payload["evidence"]
    if memo_type == MemoType.operator:
        executive = (
            "The evidence pack indicates reimbursement compression will first hit realized revenue and denial workload, "
            "then spill into throughput and patient access. The operator priority is to stabilize revenue-cycle execution "
            "and protect access-critical service lines before pressure compounds at 90 and 180 days."
        )
        recommendations = [
            "Stand up a payer escalation and denial-management command center within 30 days.",
            "Protect access-critical service lines before nonessential capital deployment.",
            "Review liquidity, wait-time, and throughput exceptions weekly with named owners.",
        ]
    else:
        executive = (
            "The uploaded evidence supports a base case that is manageable with early intervention, but downside paths "
            "rapidly convert into covenant sensitivity, reporting pressure, and tighter lender posture."
        )
        recommendations = [
            "Tie lender reporting cadence to denial-rate and cash-headroom triggers.",
            "Gate new capital deployment on measurable access and revenue-cycle stabilization.",
            "Prepare downside financing options before severe-case indicators compound.",
        ]

    section_rows = [
        {
            "name": "Executive Summary",
            "content": executive,
            "citations": [item["filename"] for item in evidence[:3]],
        },
        {
            "name": "Scenario Assumptions",
            "content": "\n".join(
                f"- {item['key']}: {item['value']} ({item['rationale']}, confidence {item['confidence']:.2f})"
                for item in assumptions[:6]
            ),
            "citations": sorted({citation for item in assumptions[:6] for citation in item.get("citations", [])}),
        },
        {
            "name": "Stakeholder Map",
            "content": "\n".join(
                f"- {item['name']} ({item['entity_type']}): {item['role_summary']}"
                for item in stakeholders[:8]
            ),
            "citations": [],
        },
        {
            "name": "Key Evidence Signals",
            "content": "\n".join(f"- {item['title']}: {item['detail']}" for item in facts[:5]),
            "citations": sorted({citation for item in facts[:5] for citation in item.get("citations", [])}),
        },
        {
            "name": "30/90/180 Day Event Timeline",
            "content": "\n".join(
                f"- Day {item['day']}: {item['event_type']} / {item['stakeholder']} - {item['description']}"
                for item in timeline[:9]
            ),
            "citations": sorted({citation for item in timeline[:9] for citation in item.get("citations", [])}),
        },
        {
            "name": "Revenue and Margin Exposure" if memo_type == MemoType.operator else "Liquidity and Covenant Implications",
            "content": "\n".join(
                f"- {item['name']}: {item['baseline_value']}{item['unit']} -> {item['projected_value']}{item['unit']} "
                f"(delta {item['delta_value']}{item['unit']}) at day {item['horizon_days']}"
                for item in kpis[:12]
            ),
            "citations": sorted({citation for item in kpis[:12] for citation in item.get("citations", [])}),
        },
        {
            "name": "Recommended Actions",
            "content": "\n".join(f"- {row}" for row in recommendations),
            "citations": [item["filename"] for item in evidence[:2]],
        },
        {
            "name": "Confidence and Blind Spots",
            "content": (
                "Confidence is moderate because the run is grounded in uploaded financial, financing, and market evidence. "
                "Blind spots remain around contract-level payer terms, service-line staffing elasticity, and the exact covenant "
                "interpretation lenders would apply under a sustained downside path."
            ),
            "citations": [item["filename"] for item in evidence[:2]],
        },
    ]

    content = f"# {title}\n\n" + "\n\n".join(
        f"## {section['name']}\n{section['content']}" for section in section_rows
    )
    return content, section_rows


def interrogate_run(run: DecisionRun, question: str, memo: Memo | None) -> tuple[str, list[dict]]:
    q = question.lower()
    citations = [{"type": "assumption", "id": a.id, "key": a.key} for a in run.assumptions[:2]]

    if "margin" in q or "revenue" in q:
        answer = (
            "Margin risk is front-loaded by reimbursement compression and compounds through denial pressure. "
            "The severe case shows the steepest 90-day and 180-day deterioration, so intervention should start within 30 days."
        )
    elif "covenant" in q or "liquidity" in q or "lender" in q:
        answer = (
            "Liquidity and covenant pressure increase materially in downside and severe paths. "
            "The lender-facing control is a weekly 13-week cash forecast with trigger thresholds linked to denial and wait-time KPIs."
        )
    elif "access" in q or "patient" in q or "wait" in q:
        answer = (
            "Care access deteriorates through rising wait times and reduced throughput. "
            "The most direct mitigations are staffing reallocation and denial-cycle acceleration in high-delay service lines."
        )
    elif memo:
        answer = (
            f"The {memo.memo_type.value} memo indicates the main risks are reimbursement pressure, "
            "operational strain, and financing sensitivity; use the 30/90/180 timeline to prioritize interventions."
        )
    else:
        answer = (
            "This run indicates reimbursement-cut stress propagates from payer economics into operations, "
            "care access, and capital confidence. Ask about margin, covenant risk, or access for specific guidance."
        )
    return answer, citations
