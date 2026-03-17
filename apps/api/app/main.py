"""FastAPI entrypoint for the healthcare-native decision twin API."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .config import get_settings, load_domain_contract
from .database import engine, get_db
from .models import Assumption, Base, DecisionRun, DecisionRunStatus, EvidenceFile, ExtractedFact, Memo, Project, ScenarioCase
from .pipeline import (
    ALLOWED_EXTENSIONS,
    build_stakeholder_graph,
    default_requirement_for_scenario,
    extract_text_and_table,
    generate_memos,
    interrogate_run,
    new_id,
    run_extraction,
    run_simulation,
)
from .schemas import ApiEnvelope, AssumptionUpdate, DecisionRunCreate, InterrogateRequest, ProjectCreate


settings = get_settings()
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


def _project_or_404(db: Session, project_id: str) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
    return project


def _run_or_404(db: Session, run_id: str) -> DecisionRun:
    run = db.get(DecisionRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Decision run not found: {run_id}")
    return run


NUMERIC_ASSUMPTION_KEYS = {
    "reimbursement_cut_pct",
    "denial_pressure_pct",
    "labor_cost_pressure_pct",
}


def _require_evidence(run: DecisionRun) -> None:
    if run.project and run.project.evidence_files:
        return
    raise HTTPException(
        status_code=400,
        detail="Evidence is required before running extraction, graph build, simulation, or memo generation.",
    )


def _require_stage(run: DecisionRun, allowed: set[DecisionRunStatus], action: str) -> None:
    if run.status in allowed:
        return
    allowed_text = ", ".join(sorted(item.value for item in allowed))
    raise HTTPException(
        status_code=409,
        detail=f"Run must be in one of [{allowed_text}] before {action}. Current status: {run.status.value}",
    )


def _memo_by_type(run: DecisionRun, memo_type: str | None) -> Memo | None:
    if not memo_type:
        return run.memos[0] if run.memos else None
    for memo in run.memos:
        if memo.memo_type.value == memo_type:
            return memo
    return None


def _serialize_project(project: Project) -> Dict[str, Any]:
    return {
        "id": project.id,
        "name": project.name,
        "organization_name": project.organization_name,
        "scenario_type": project.scenario_type,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
    }


def _serialize_evidence(evidence: EvidenceFile) -> Dict[str, Any]:
    return {
        "id": evidence.id,
        "project_id": evidence.project_id,
        "filename": evidence.filename,
        "extension": evidence.extension,
        "size_bytes": evidence.size_bytes,
        "content_type": evidence.content_type,
        "extracted_preview": evidence.extracted_text[:220],
        "table_summary": evidence.extracted_table,
    }


def _serialize_assumption(item: Assumption) -> Dict[str, Any]:
    return {
        "id": item.id,
        "key": item.key,
        "value": item.value,
        "category": item.category,
        "impact_area": item.impact_area,
        "rationale": item.rationale,
        "source_evidence_ids": item.source_evidence_ids,
        "confidence": item.confidence,
        "status": item.status,
        "user_modified": item.user_modified,
    }


def _serialize_fact(item: ExtractedFact) -> Dict[str, Any]:
    return {
        "id": item.id,
        "evidence_file_id": item.evidence_file_id,
        "fact_type": item.fact_type,
        "title": item.title,
        "detail": item.detail,
        "source_excerpt": item.source_excerpt,
        "normalized_value_json": item.normalized_value_json,
        "confidence": item.confidence,
    }


def _serialize_run(run: DecisionRun) -> Dict[str, Any]:
    return {
        "id": run.id,
        "project_id": run.project_id,
        "scenario_type": run.scenario_type,
        "simulation_requirement": run.simulation_requirement,
        "time_horizons": run.time_horizons,
        "status": run.status.value,
        "metadata_json": run.metadata_json,
        "created_at": run.created_at.isoformat(),
        "updated_at": run.updated_at.isoformat(),
    }


def _metric_tone(score: int) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "elevated"
    return "stable"


def _scenario_label(scenario_type: str) -> str:
    contract = load_domain_contract()
    for template in contract.get("scenarioTemplates", []):
        if template.get("id") == scenario_type:
            return template.get("label", scenario_type)
    return scenario_type.replace("_", " ").title()


def _build_executive_dashboard(
    run: DecisionRun,
    stakeholders: List[Dict[str, Any]],
    risk_heatmap: List[Dict[str, Any]],
    timeline: List[Dict[str, Any]],
) -> Dict[str, Any]:
    avg_finance = round(sum(item["finance"] for item in risk_heatmap) / max(len(risk_heatmap), 1))
    avg_access = round(sum(item["access"] for item in risk_heatmap) / max(len(risk_heatmap), 1))
    avg_regulatory = round(sum(item["regulatory"] for item in risk_heatmap) / max(len(risk_heatmap), 1))
    avg_operations = round(sum(item["operations"] for item in risk_heatmap) / max(len(risk_heatmap), 1))
    lender_pressure = any("Lender" in item["stakeholder"] or "Credit" in item["stakeholder"] for item in timeline)
    payer_pressure = any("Payer" in item["stakeholder"] for item in timeline)
    operator_name = run.project.organization_name or run.project.name
    scenario_label = _scenario_label(run.scenario_type)
    finance_score = min(96, avg_finance + (8 if payer_pressure else 0) + (6 if lender_pressure else 0))
    trust_score = min(96, round((avg_access * 0.55) + (avg_regulatory * 0.45)))

    lead_pressure = max(
        [
            ("margin pressure", finance_score),
            ("care access stress", avg_access),
            ("regulatory heat", avg_regulatory),
            ("operating strain", avg_operations),
        ],
        key=lambda item: item[1],
    )[0]

    return {
        "title": f"{operator_name} executive impact dashboard",
        "decisionFocus": run.simulation_requirement,
        "narrative": (
            f"{operator_name} is running a {scenario_label.lower()} decision rehearsal. "
            f"The current signal set points to {lead_pressure} as the lead board issue, with the strongest "
            "30-day requirement being coordinated payer, operating, and financing actions rather than isolated workstreams."
        ),
        "metrics": [
            {
                "key": "margin",
                "label": "Margin Pressure",
                "score": finance_score,
                "tone": _metric_tone(finance_score),
                "summary": "Reimbursement, denial, and liquidity signals are shaping the near-term downside."
            },
            {
                "key": "access",
                "label": "Care Access Stress",
                "score": avg_access,
                "tone": _metric_tone(avg_access),
                "summary": "Wait-time and throughput pressure determine how quickly the case becomes public and regulatory."
            },
            {
                "key": "operations",
                "label": "Operating Strain",
                "score": avg_operations,
                "tone": _metric_tone(avg_operations),
                "summary": "Clinical workforce and service-line execution determine whether the base case holds."
            },
            {
                "key": "trust",
                "label": "Stakeholder Trust",
                "score": trust_score,
                "tone": _metric_tone(trust_score),
                "summary": "Community, regulator, and capital narratives are highly sensitive to access deterioration."
            },
        ],
    }


def _build_conflict_matrix(
    stakeholders: List[Dict[str, Any]],
    risk_heatmap: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    heatmap_by_name = {item["stakeholder"]: item for item in risk_heatmap}
    matrix = []
    for stakeholder in stakeholders[:6]:
        heat = heatmap_by_name.get(stakeholder["name"], {})
        intensity = max(
            int(heat.get("operations", 0)),
            int(heat.get("finance", 0)),
            int(heat.get("access", 0)),
            int(heat.get("regulatory", 0)),
        )
        group = stakeholder["type"]
        if group == "Payer":
            concern = "Limit reimbursement exposure and resist provider repricing."
            response = "Negotiate with contract, denial, and access evidence in one lane."
        elif group == "Regulator":
            concern = "Avoid visible access deterioration and unmanaged compliance risk."
            response = "Pre-brief remediation and access protections before formal escalation."
        elif group == "Lender":
            concern = "Protect covenant headroom and confidence in downside control."
            response = "Share trigger-based cash planning and downside actions early."
        elif group in {"Hospital", "Provider"}:
            concern = "Protect operating margin without letting access fracture."
            response = "Coordinate service-line triage with payer and workforce actions."
        else:
            concern = "Preserve leverage while downside pressure is still manageable."
            response = "Bind this stakeholder into the decision cadence with explicit asks."

        matrix.append(
            {
                "stakeholderId": stakeholder["id"],
                "stakeholder": stakeholder["name"],
                "group": stakeholder["type"],
                "intensity": intensity,
                "concern": concern,
                "likelyMove": stakeholder["likelyReaction"],
                "pressure": stakeholder["pressurePoint"],
                "response": response,
            }
        )
    matrix.sort(key=lambda item: item["intensity"], reverse=True)
    return matrix


def _build_action_scenarios(run: DecisionRun) -> List[Dict[str, Any]]:
    scenario_label = _scenario_label(run.scenario_type)
    return [
        {
            "horizonDays": 30,
            "title": "Stabilize the case and stop drift",
            "summary": f"Use the first 30 days to lock the response model for the {scenario_label.lower()} scenario.",
            "operatingFocus": "Protect throughput, denial turnaround, and exposed service lines.",
            "capitalFocus": "Stand up weekly cash and covenant triggers.",
            "boardAsk": "Approve one rapid-response governance lane with named owners.",
        },
        {
            "horizonDays": 90,
            "title": "Reset contracts and operating posture",
            "summary": "Convert reaction into leverage by aligning payer, workforce, and regulator responses.",
            "operatingFocus": "Rebalance staffing and service-line mix based on realized pressure.",
            "capitalFocus": "Retire low-conviction spend and tie funding to KPI recovery.",
            "boardAsk": "Choose one strategy path instead of incremental mitigations.",
        },
        {
            "horizonDays": 180,
            "title": "Reposition for resilience",
            "summary": "Move from containment into a durable operating and financing thesis.",
            "operatingFocus": "Rebuild access resilience and footprint discipline.",
            "capitalFocus": "Align capital structure with sustained margin recovery.",
            "boardAsk": "Back the portfolio and financing posture for the next two quarters.",
        },
    ]


def _build_mitigation_options(
    dashboard: Dict[str, Any],
    conflict_matrix: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    margin_score = next((item["score"] for item in dashboard["metrics"] if item["key"] == "margin"), 60)
    access_score = next((item["score"] for item in dashboard["metrics"] if item["key"] == "access"), 60)
    trust_score = next((item["score"] for item in dashboard["metrics"] if item["key"] == "trust"), 60)
    dominant_group = conflict_matrix[0]["group"] if conflict_matrix else "Provider"

    options = [
        {
            "id": "payer-command-center",
            "name": "Payer and Denial Command Center",
            "positioning": "Best when reimbursement and claims friction are the main source of downside.",
            "composite": min(96, int(margin_score * 0.7 + 20)),
            "marginImpact": "High upside",
            "accessImpact": "Moderate risk",
            "trustImpact": "Neutral if framed around access protection",
            "bestUse": "Use when payer behavior is the fastest path to cash and margin deterioration.",
            "tradeoff": "Can look purely financial if not paired with an access protection plan.",
        },
        {
            "id": "access-protection-lane",
            "name": "Care Access Protection Plan",
            "positioning": "Best when regulator, patient, or workforce pressure is leading the case.",
            "composite": min(96, int(access_score * 0.6 + trust_score * 0.2 + 22)),
            "marginImpact": "Medium",
            "accessImpact": "Strong protection",
            "trustImpact": "Strong protection",
            "bestUse": "Use when the board needs visible proof that operations and access are being defended.",
            "tradeoff": "Financial recovery is slower without a reimbursement or liquidity lane.",
        },
        {
            "id": "capital-preservation",
            "name": "Liquidity and Covenant Preservation",
            "positioning": "Best when lenders or sponsors are beginning to shape the decision clock.",
            "composite": min(96, int(margin_score * 0.45 + trust_score * 0.15 + 28)),
            "marginImpact": "Protective",
            "accessImpact": "Moderate pressure",
            "trustImpact": "Requires careful communications",
            "bestUse": f"Use when {dominant_group.lower()} pressure could rapidly impair financing flexibility.",
            "tradeoff": "Can signal weakness unless paired with a credible operating improvement story.",
        },
    ]
    options.sort(key=lambda item: item["composite"], reverse=True)
    return options


def _serialize_artifacts(run: DecisionRun) -> Dict[str, Any]:
    assumptions = [
        {
            **_serialize_assumption(item),
            "statement": f"{item.key}: {item.value}",
            "impactArea": item.impact_area,
            "sourceEvidenceIds": item.source_evidence_ids,
        }
        for item in run.assumptions
    ]
    extracted_facts = [_serialize_fact(item) for item in run.extracted_facts]

    stakeholders = [
        {
            "id": node.id,
            "name": node.name,
            "type": node.entity_type,
            "incentive": node.role_summary,
            "pressurePoint": node.role_summary,
            "likelyReaction": node.role_summary,
            "influence": round(node.influence_score * 100),
        }
        for node in run.stakeholder_nodes
    ]
    edges = [
        {
            "source": edge.source_node_id,
            "target": edge.target_node_id,
            "relation": edge.relation_type,
            "rationale": edge.rationale,
        }
        for edge in run.stakeholder_edges
    ]

    kpi_index: Dict[str, Dict[str, Any]] = {}
    for kpi in run.kpis:
        if kpi.case_name is None:
            kpi_index.setdefault(
                kpi.name,
                {
                    "id": kpi.id,
                    "label": kpi.name,
                    "unit": kpi.unit,
                    "baseline": kpi.baseline_value,
                    "byHorizon": {str(day): {} for day in run.time_horizons},
                },
            )
            continue
        horizon_key = str(kpi.horizon_days)
        case_key = kpi.case_name.value
        kpi_index.setdefault(
            kpi.name,
            {
                "id": kpi.id,
                "label": kpi.name,
                "unit": kpi.unit,
                "baseline": kpi.baseline_value,
                "byHorizon": {str(day): {} for day in run.time_horizons},
            },
        )
        kpi_index[kpi.name]["byHorizon"].setdefault(horizon_key, {})
        kpi_index[kpi.name]["byHorizon"][horizon_key][case_key] = kpi.delta_value

    timeline = [
        {
            "id": event.id,
            "day": event.horizon_days,
            "variant": event.case_name.value,
            "channel": "Operational Network" if event.event_order % 2 else "External Signals",
            "stakeholder": event.stakeholder,
            "event": event.event_type,
            "implication": event.description,
            "confidence": event.confidence,
            "citations": event.citation_evidence_ids,
        }
        for event in sorted(run.simulation_events, key=lambda item: (item.case_name.value, item.horizon_days, item.event_order))
    ]

    risk_heatmap: List[Dict[str, Any]] = []
    for node in run.stakeholder_nodes:
        risk_heatmap.append(
            {
                "stakeholderId": node.id,
                "stakeholder": node.name,
                "operations": min(100, int(node.influence_score * 85)),
                "finance": min(100, int(node.influence_score * 92)),
                "access": min(100, int(node.influence_score * 70)),
                "regulatory": min(100, int(node.influence_score * 76)),
            }
        )

    executive_dashboard = _build_executive_dashboard(run, stakeholders, risk_heatmap, timeline)
    conflict_matrix = _build_conflict_matrix(stakeholders, risk_heatmap)
    action_scenarios = _build_action_scenarios(run)
    mitigation_options = _build_mitigation_options(executive_dashboard, conflict_matrix)

    memos = {
        memo.memo_type.value: {
            "id": memo.id,
            "type": memo.memo_type.value,
            "title": memo.title,
            "contentMarkdown": memo.content_markdown,
            "sections": [
                {
                    "title": section["name"],
                    "content": section.get("content", ""),
                    "citations": section.get("citations", []),
                }
                for section in memo.sections[:10]
            ],
        }
        for memo in run.memos
    }

    return {
        "facts": extracted_facts,
        "assumptions": assumptions,
        "stakeholders": stakeholders,
        "edges": edges,
        "kpis": list(kpi_index.values()),
        "riskHeatmap": risk_heatmap,
        "timeline": timeline,
        "executiveDashboard": executive_dashboard,
        "conflictMatrix": conflict_matrix,
        "actionScenarios": action_scenarios,
        "mitigationOptions": mitigation_options,
        "memos": memos,
    }


async def _store_evidence_files(project: Project, files: List[UploadFile], db: Session) -> List[Dict[str, Any]]:
    saved: List[Dict[str, Any]] = []
    project_dir = Path(settings.upload_dir) / project.id
    project_dir.mkdir(parents=True, exist_ok=True)

    for upload in files:
        content = await upload.read()
        evidence = _create_evidence_record(
            project=project,
            filename=upload.filename,
            content_type=upload.content_type,
            content=content,
        )
        db.add(evidence)
        saved.append(_serialize_evidence(evidence))
    db.commit()
    return saved


def _create_evidence_record(project: Project, filename: str, content_type: str | None, content: bytes) -> EvidenceFile:
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")
    text, table = extract_text_and_table(filename, content)
    project_dir = Path(settings.upload_dir) / project.id
    project_dir.mkdir(parents=True, exist_ok=True)
    storage_name = f"{uuid4().hex}_{filename}"
    storage_path = project_dir / storage_name
    storage_path.write_bytes(content)
    return EvidenceFile(
        id=new_id(),
        project_id=project.id,
        filename=filename,
        content_type=content_type,
        extension=ext,
        storage_path=storage_path.as_posix(),
        size_bytes=len(content),
        extracted_text=text,
        extracted_table=table,
    )


def _demo_evidence_dir() -> Path:
    return Path(settings.domain_contract_path).resolve().parent / "demo-evidence"


def _store_demo_evidence(project: Project, db: Session) -> List[Dict[str, Any]]:
    evidence_dir = _demo_evidence_dir()
    if not evidence_dir.exists():
        raise HTTPException(status_code=500, detail=f"Demo evidence directory not found: {evidence_dir}")

    saved: List[Dict[str, Any]] = []
    for path in sorted(evidence_dir.iterdir()):
        if not path.is_file():
            continue
        evidence = _create_evidence_record(
            project=project,
            filename=path.name,
            content_type="text/plain" if path.suffix.lower() in {".txt", ".md"} else "text/csv",
            content=path.read_bytes(),
        )
        db.add(evidence)
        saved.append(_serialize_evidence(evidence))
    db.commit()
    return saved


@app.get("/health", response_model=ApiEnvelope)
def health() -> ApiEnvelope:
    return ApiEnvelope(success=True, data={"status": "ok", "service": settings.app_name})


@app.get(f"{settings.api_prefix}/domain", response_model=ApiEnvelope)
def get_domain_contract() -> ApiEnvelope:
    return ApiEnvelope(success=True, data=load_domain_contract())


@app.get(f"{settings.api_prefix}/projects", response_model=ApiEnvelope)
def list_projects(db: Session = Depends(get_db)) -> ApiEnvelope:
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return ApiEnvelope(success=True, data=[_serialize_project(project) for project in projects])


@app.post(f"{settings.api_prefix}/projects", response_model=ApiEnvelope)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> ApiEnvelope:
    project = Project(
        id=new_id(),
        name=payload.name,
        organization_name=payload.organization_name,
        scenario_type=payload.scenario_type,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return ApiEnvelope(success=True, data=_serialize_project(project))


@app.get(f"{settings.api_prefix}/projects/{{project_id}}", response_model=ApiEnvelope)
def get_project(project_id: str, db: Session = Depends(get_db)) -> ApiEnvelope:
    project = _project_or_404(db, project_id)
    return ApiEnvelope(success=True, data=_serialize_project(project))


@app.post(f"{settings.api_prefix}/projects/{{project_id}}/evidence", response_model=ApiEnvelope)
async def upload_evidence(project_id: str, files: List[UploadFile] = File(...), db: Session = Depends(get_db)) -> ApiEnvelope:
    project = _project_or_404(db, project_id)
    saved = await _store_evidence_files(project, files, db)
    return ApiEnvelope(success=True, data=saved)


@app.get(f"{settings.api_prefix}/projects/{{project_id}}/evidence", response_model=ApiEnvelope)
def list_evidence(project_id: str, db: Session = Depends(get_db)) -> ApiEnvelope:
    project = _project_or_404(db, project_id)
    return ApiEnvelope(success=True, data=[_serialize_evidence(item) for item in project.evidence_files])


@app.post(f"{settings.api_prefix}/runs", response_model=ApiEnvelope)
def create_run(payload: DecisionRunCreate, db: Session = Depends(get_db)) -> ApiEnvelope:
    project = _project_or_404(db, payload.project_id)
    run = DecisionRun(
        id=new_id(),
        project_id=project.id,
        scenario_type=payload.scenario_type or project.scenario_type,
        simulation_requirement=payload.simulation_requirement or default_requirement_for_scenario(payload.scenario_type or project.scenario_type),
        time_horizons=payload.time_horizons,
        status=DecisionRunStatus.created,
        metadata_json={"project_name": project.name},
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return ApiEnvelope(success=True, data=_serialize_run(run))


@app.post(f"{settings.api_prefix}/evidence/upload", response_model=ApiEnvelope)
async def upload_evidence_compat(
    project_id: str | None = Form(default=None),
    run_id: str | None = Form(default=None),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
) -> ApiEnvelope:
    if not project_id:
        if not run_id:
            raise HTTPException(status_code=400, detail="Either project_id or run_id is required.")
        run = _run_or_404(db, run_id)
        project_id = run.project_id
    project = _project_or_404(db, project_id)
    saved = await _store_evidence_files(project, files, db)
    return ApiEnvelope(success=True, data={"project_id": project_id, "files": saved})


@app.post(f"{settings.api_prefix}/demo/import", response_model=ApiEnvelope)
def import_demo_workspace(db: Session = Depends(get_db)) -> ApiEnvelope:
    project = Project(
        id=new_id(),
        name="MetroCare Health System",
        organization_name="MetroCare",
        scenario_type="reimbursement_cut",
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    evidence = _store_demo_evidence(project, db)

    run = DecisionRun(
        id=new_id(),
        project_id=project.id,
        scenario_type=project.scenario_type,
        simulation_requirement=default_requirement_for_scenario(project.scenario_type),
        time_horizons=[30, 90, 180],
        status=DecisionRunStatus.created,
        metadata_json={
            "project_name": project.name,
            "demo_import": True,
            "force_deterministic_demo": True,
        },
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    run_extraction(db, run, project)
    build_stakeholder_graph(db, run)
    run_simulation(db, run)
    generate_memos(db, run)
    db.commit()
    db.refresh(run)

    return ApiEnvelope(
        success=True,
        data={
            "project": _serialize_project(project),
            "run": _serialize_run(run),
            "evidence": evidence,
            "artifacts": _serialize_artifacts(run),
        },
    )


@app.post(f"{settings.api_prefix}/decision-runs", response_model=ApiEnvelope)
def create_run_compat(payload: DecisionRunCreate, db: Session = Depends(get_db)) -> ApiEnvelope:
    return create_run(payload, db)


@app.get(f"{settings.api_prefix}/runs/{{run_id}}", response_model=ApiEnvelope)
def get_run(run_id: str, db: Session = Depends(get_db)) -> ApiEnvelope:
    run = _run_or_404(db, run_id)
    return ApiEnvelope(success=True, data=_serialize_run(run))


@app.post(f"{settings.api_prefix}/runs/{{run_id}}/extract", response_model=ApiEnvelope)
def extract_run(run_id: str, db: Session = Depends(get_db)) -> ApiEnvelope:
    run = _run_or_404(db, run_id)
    _require_evidence(run)
    _require_stage(run, {DecisionRunStatus.created, DecisionRunStatus.extracted}, "extraction")
    result = run_extraction(db, run, run.project)
    db.commit()
    db.refresh(run)
    return ApiEnvelope(success=True, data={"run": _serialize_run(run), "result": result})


@app.post(f"{settings.api_prefix}/decision-runs/{{run_id}}/extract", response_model=ApiEnvelope)
def extract_run_compat(run_id: str, db: Session = Depends(get_db)) -> ApiEnvelope:
    run = _run_or_404(db, run_id)
    _require_evidence(run)
    _require_stage(run, {DecisionRunStatus.created, DecisionRunStatus.extracted}, "extraction")
    result = run_extraction(db, run, run.project)
    db.commit()
    db.refresh(run)
    assumptions = [_serialize_assumption(item) for item in result["assumptions"]]
    facts = [_serialize_fact(item) for item in result["facts"]]
    return ApiEnvelope(
        success=True,
        data={
            "run": _serialize_run(run),
            "assumptions": assumptions,
            "facts": facts,
            "baseline_kpis": result["baseline_kpis"],
        },
    )


@app.post(f"{settings.api_prefix}/runs/{{run_id}}/graph", response_model=ApiEnvelope)
def graph_run(run_id: str, db: Session = Depends(get_db)) -> ApiEnvelope:
    run = _run_or_404(db, run_id)
    _require_evidence(run)
    _require_stage(
        run,
        {DecisionRunStatus.extracted, DecisionRunStatus.graph_built, DecisionRunStatus.simulated, DecisionRunStatus.memos_generated},
        "building the stakeholder graph",
    )
    result = build_stakeholder_graph(db, run)
    db.commit()
    db.refresh(run)
    return ApiEnvelope(success=True, data={"run": _serialize_run(run), "result": result})


@app.post(f"{settings.api_prefix}/decision-runs/{{run_id}}/build-graph", response_model=ApiEnvelope)
def graph_run_compat(run_id: str, db: Session = Depends(get_db)) -> ApiEnvelope:
    run = _run_or_404(db, run_id)
    _require_evidence(run)
    _require_stage(
        run,
        {DecisionRunStatus.extracted, DecisionRunStatus.graph_built, DecisionRunStatus.simulated, DecisionRunStatus.memos_generated},
        "building the stakeholder graph",
    )
    result = build_stakeholder_graph(db, run)
    db.commit()
    db.refresh(run)
    return ApiEnvelope(success=True, data={"run": _serialize_run(run), "graph_summary": result})


@app.get(f"{settings.api_prefix}/decision-runs/{{run_id}}/stakeholder-graph", response_model=ApiEnvelope)
def get_stakeholder_graph(run_id: str, db: Session = Depends(get_db)) -> ApiEnvelope:
    run = _run_or_404(db, run_id)
    return ApiEnvelope(
        success=True,
        data={
            "stakeholders": [
                {
                    "id": node.id,
                    "name": node.name,
                    "type": node.entity_type,
                    "incentive": node.role_summary,
                    "pressurePoint": node.role_summary,
                    "likelyReaction": node.role_summary,
                    "influence": round(node.influence_score * 100),
                }
                for node in run.stakeholder_nodes
            ],
            "edges": [
                {
                    "id": edge.id,
                    "source": edge.source_node_id,
                    "target": edge.target_node_id,
                    "relation": edge.relation_type,
                    "rationale": edge.rationale,
                }
                for edge in run.stakeholder_edges
            ],
        },
    )


@app.post(f"{settings.api_prefix}/runs/{{run_id}}/simulate", response_model=ApiEnvelope)
def simulate_run(run_id: str, db: Session = Depends(get_db)) -> ApiEnvelope:
    run = _run_or_404(db, run_id)
    _require_evidence(run)
    _require_stage(
        run,
        {DecisionRunStatus.graph_built, DecisionRunStatus.simulated, DecisionRunStatus.memos_generated},
        "simulation",
    )
    result = run_simulation(db, run)
    db.commit()
    db.refresh(run)
    return ApiEnvelope(success=True, data={"run": _serialize_run(run), "result": result})


@app.post(f"{settings.api_prefix}/decision-runs/{{run_id}}/simulate", response_model=ApiEnvelope)
def simulate_run_compat(run_id: str, db: Session = Depends(get_db)) -> ApiEnvelope:
    return simulate_run(run_id, db)


@app.post(f"{settings.api_prefix}/runs/{{run_id}}/memos", response_model=ApiEnvelope)
def memo_run(run_id: str, db: Session = Depends(get_db)) -> ApiEnvelope:
    run = _run_or_404(db, run_id)
    _require_evidence(run)
    _require_stage(
        run,
        {DecisionRunStatus.simulated, DecisionRunStatus.memos_generated},
        "memo generation",
    )
    result = generate_memos(db, run)
    db.commit()
    db.refresh(run)
    return ApiEnvelope(success=True, data={"run": _serialize_run(run), "result": result})


@app.post(f"{settings.api_prefix}/decision-runs/{{run_id}}/generate-memo", response_model=ApiEnvelope)
def memo_run_compat(run_id: str, db: Session = Depends(get_db)) -> ApiEnvelope:
    return memo_run(run_id, db)


@app.post(f"{settings.api_prefix}/runs/{{run_id}}/execute", response_model=ApiEnvelope)
def execute_run(run_id: str, db: Session = Depends(get_db)) -> ApiEnvelope:
    run = _run_or_404(db, run_id)
    _require_evidence(run)
    run_extraction(db, run, run.project)
    build_stakeholder_graph(db, run)
    run_simulation(db, run)
    generate_memos(db, run)
    db.commit()
    db.refresh(run)
    return ApiEnvelope(success=True, data={"run": _serialize_run(run), "artifacts": _serialize_artifacts(run)})


@app.get(f"{settings.api_prefix}/runs/{{run_id}}/artifacts", response_model=ApiEnvelope)
def get_run_artifacts(run_id: str, db: Session = Depends(get_db)) -> ApiEnvelope:
    run = _run_or_404(db, run_id)
    return ApiEnvelope(success=True, data=_serialize_artifacts(run))


@app.get(f"{settings.api_prefix}/decision-runs/{{run_id}}/timeline", response_model=ApiEnvelope)
def get_timeline(run_id: str, case: str = "base_case", db: Session = Depends(get_db)) -> ApiEnvelope:
    run = _run_or_404(db, run_id)
    events = [
        {
            "id": event.id,
            "day": event.horizon_days,
            "variant": event.case_name.value,
            "case": event.case_name.value,
            "channel": "Operational Network" if event.event_order % 2 else "External Signals",
            "event_type": event.event_type,
            "event": event.event_type,
            "stakeholder": event.stakeholder,
            "description": event.description,
            "implication": event.description,
            "confidence": event.confidence,
            "citations": event.citation_evidence_ids,
        }
        for event in run.simulation_events
        if event.case_name.value == case
    ]
    return ApiEnvelope(success=True, data={"events": events})


@app.get(f"{settings.api_prefix}/decision-runs/{{run_id}}/kpis", response_model=ApiEnvelope)
def get_kpis(run_id: str, case: str = "base_case", db: Session = Depends(get_db)) -> ApiEnvelope:
    run = _run_or_404(db, run_id)
    baseline_kpis = {kpi.name: kpi for kpi in run.kpis if kpi.case_name is None}
    case_kpis = [kpi for kpi in run.kpis if kpi.case_name and kpi.case_name.value == case]
    rows = []
    for kpi in case_kpis:
        base = baseline_kpis.get(kpi.name)
        rows.append(
            {
                "name": kpi.name,
                "label": kpi.name,
                "baseline_value": kpi.baseline_value,
                "baseline": kpi.baseline_value,
                "projected_value": kpi.projected_value,
                "delta_value": kpi.delta_value,
                "unit": kpi.unit,
                "horizon_days": kpi.horizon_days,
                "source_evidence_ids": kpi.source_evidence_ids,
                "baseline_source_evidence_ids": base.source_evidence_ids if base else kpi.source_evidence_ids,
            }
        )
    risk_heatmap = _serialize_artifacts(run)["riskHeatmap"]
    return ApiEnvelope(success=True, data={"kpis": rows, "risk_heatmap": risk_heatmap})


@app.get(f"{settings.api_prefix}/decision-runs/{{run_id}}/evidence-review", response_model=ApiEnvelope)
def get_evidence_review(run_id: str, db: Session = Depends(get_db)) -> ApiEnvelope:
    run = _run_or_404(db, run_id)
    return ApiEnvelope(
        success=True,
        data={
            "run": _serialize_run(run),
            "evidence_files": [_serialize_evidence(item) for item in run.project.evidence_files],
            "facts": [_serialize_fact(item) for item in run.extracted_facts],
            "assumptions": [_serialize_assumption(item) for item in run.assumptions],
            "baseline_kpis": [
                {
                    "id": item.id,
                    "name": item.name,
                    "baseline_value": item.baseline_value,
                    "unit": item.unit,
                    "source_evidence_ids": item.source_evidence_ids,
                }
                for item in run.kpis
                if item.case_name is None
            ],
        },
    )


@app.get(f"{settings.api_prefix}/decision-runs/{{run_id}}/assumptions", response_model=ApiEnvelope)
def get_assumptions(run_id: str, db: Session = Depends(get_db)) -> ApiEnvelope:
    run = _run_or_404(db, run_id)
    return ApiEnvelope(success=True, data={"assumptions": [_serialize_assumption(item) for item in run.assumptions]})


@app.patch(f"{settings.api_prefix}/decision-runs/{{run_id}}/assumptions/{{assumption_id}}", response_model=ApiEnvelope)
def update_assumption(run_id: str, assumption_id: str, payload: AssumptionUpdate, db: Session = Depends(get_db)) -> ApiEnvelope:
    run = _run_or_404(db, run_id)
    assumption = next((item for item in run.assumptions if item.id == assumption_id), None)
    if assumption is None:
        raise HTTPException(status_code=404, detail=f"Assumption not found: {assumption_id}")
    if assumption.key in NUMERIC_ASSUMPTION_KEYS:
        try:
            float(payload.value)
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Assumption '{assumption.key}' requires a numeric value.",
            ) from exc
    assumption.value = payload.value
    if payload.rationale is not None:
        assumption.rationale = payload.rationale
    if payload.status is not None:
        assumption.status = payload.status
    assumption.user_modified = True
    db.commit()
    db.refresh(assumption)
    return ApiEnvelope(success=True, data={"assumption": _serialize_assumption(assumption)})


@app.get(f"{settings.api_prefix}/decision-runs/{{run_id}}/scenario-cases", response_model=ApiEnvelope)
def get_scenario_cases(run_id: str, db: Session = Depends(get_db)) -> ApiEnvelope:
    run = _run_or_404(db, run_id)
    cases = []
    for case in ScenarioCase:
        case_events = [event for event in run.simulation_events if event.case_name == case]
        cases.append(
            {
                "case_name": case.value,
                "event_count": len(case_events),
                "horizons": sorted({event.horizon_days for event in case_events}),
                "headline": case_events[0].description if case_events else "",
            }
        )
    return ApiEnvelope(success=True, data={"cases": cases})


@app.get(f"{settings.api_prefix}/decision-runs/{{run_id}}/memos/{{memo_type}}", response_model=ApiEnvelope)
def get_memo(run_id: str, memo_type: str, db: Session = Depends(get_db)) -> ApiEnvelope:
    run = _run_or_404(db, run_id)
    memo = _memo_by_type(run, memo_type)
    if not memo:
        raise HTTPException(status_code=404, detail=f"Memo not found for type: {memo_type}")
    return ApiEnvelope(
        success=True,
        data={
            "id": memo.id,
            "memo_type": memo.memo_type.value,
            "title": memo.title,
            "content_markdown": memo.content_markdown,
            "sections": memo.sections,
            "citations": memo.citations,
        },
    )


@app.post(f"{settings.api_prefix}/decision-runs/{{run_id}}/interrogate", response_model=ApiEnvelope)
def interrogate_compat(run_id: str, payload: InterrogateRequest, db: Session = Depends(get_db)) -> ApiEnvelope:
    return interrogate(run_id, payload, db)


@app.post(f"{settings.api_prefix}/runs/{{run_id}}/interrogate", response_model=ApiEnvelope)
def interrogate(run_id: str, payload: InterrogateRequest, db: Session = Depends(get_db)) -> ApiEnvelope:
    run = _run_or_404(db, run_id)
    memo = _memo_by_type(run, payload.memo_type)
    answer, citations = interrogate_run(run, payload.question, memo)
    return ApiEnvelope(success=True, data={"question": payload.question, "answer": answer, "citations": citations})
