from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient


def _build_client(tmp_path: Path) -> TestClient:
    db_path = tmp_path / "healthtwin_stage.db"
    upload_dir = tmp_path / "uploads-stage"
    contract_path = Path(__file__).resolve().parents[3] / "packages" / "domain-healthcare" / "domain.json"

    os.environ["HT_DB_URL"] = f"sqlite:///{db_path.as_posix()}"
    os.environ["HT_UPLOAD_DIR"] = upload_dir.as_posix()
    os.environ["HT_DOMAIN_CONTRACT_PATH"] = contract_path.as_posix()

    for mod in ("app.main", "app.database", "app.config", "app.models", "app.pipeline"):
        if mod in sys.modules:
            del sys.modules[mod]

    api_root = Path(__file__).resolve().parents[1]
    if api_root.as_posix() not in sys.path:
        sys.path.insert(0, api_root.as_posix())

    app_module = importlib.import_module("app.main")
    from app.database import engine
    from app.models import Base

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    return TestClient(app_module.app)


def _create_run(client: TestClient) -> str:
    project_res = client.post(
        "/api/projects",
        json={
            "name": "MetroCare Stage Gate",
            "organization_name": "MetroCare",
            "scenario_type": "reimbursement_cut",
        },
    )
    project_id = project_res.json()["data"]["id"]
    client.post(
        "/api/evidence/upload",
        data={"project_id": project_id},
        files=[
            ("files", ("scenario.md", b"Scenario update: 7% reimbursement cut expected this quarter.", "text/markdown")),
            (
                "files",
                (
                    "kpis.csv",
                    b"net_margin_pct,days_cash_on_hand,denied_claim_rate_pct,avg_wait_days,occupancy_pct\n3.4,152,10.4,13,80",
                    "text/csv",
                ),
            ),
        ],
    )
    run_res = client.post(
        "/api/decision-runs",
        json={"project_id": project_id, "scenario_type": "reimbursement_cut", "time_horizons": [30, 90, 180]},
    )
    return run_res.json()["data"]["id"]


def test_stage_gate_blocks_graph_before_extraction(tmp_path: Path):
    client = _build_client(tmp_path)
    run_id = _create_run(client)
    response = client.post(f"/api/decision-runs/{run_id}/build-graph")
    assert response.status_code == 409
    assert "building the stakeholder graph" in response.json()["detail"]


def test_stage_gate_blocks_simulation_before_graph(tmp_path: Path):
    client = _build_client(tmp_path)
    run_id = _create_run(client)
    extract_res = client.post(f"/api/decision-runs/{run_id}/extract")
    assert extract_res.status_code == 200
    simulate_res = client.post(f"/api/decision-runs/{run_id}/simulate")
    assert simulate_res.status_code == 409
    assert "simulation" in simulate_res.json()["detail"]


def test_stage_gate_blocks_memo_before_simulation(tmp_path: Path):
    client = _build_client(tmp_path)
    run_id = _create_run(client)
    client.post(f"/api/decision-runs/{run_id}/extract")
    client.post(f"/api/decision-runs/{run_id}/build-graph")
    memo_res = client.post(f"/api/decision-runs/{run_id}/generate-memo")
    assert memo_res.status_code == 409
    assert "memo generation" in memo_res.json()["detail"]


def test_numeric_assumption_validation(tmp_path: Path):
    client = _build_client(tmp_path)
    run_id = _create_run(client)
    extract_res = client.post(f"/api/decision-runs/{run_id}/extract")
    assumptions = extract_res.json()["data"]["assumptions"]
    target = next((item for item in assumptions if item.get("key") == "reimbursement_cut_pct"), None)
    assert target is not None
    bad_patch = client.patch(
        f"/api/decision-runs/{run_id}/assumptions/{target['id']}",
        json={"value": "invalid-number"},
    )
    assert bad_patch.status_code == 422
    assert "numeric" in bad_patch.json()["detail"].lower()


def test_simulation_fallback_without_provider_kpi_deltas(tmp_path: Path, monkeypatch):
    client = _build_client(tmp_path)
    run_id = _create_run(client)

    def fake_provider_simulation(run, assumptions, stakeholders, baseline_kpis):
        return {
            "cases": [
                {
                    "case_name": "base_case",
                    "horizons": [
                        {
                            "horizon_days": 30,
                            "events": [
                                {
                                    "event_type": "Provider test event",
                                    "stakeholder": "Provider Operations Office",
                                    "description": "Simulated impulse without KPI deltas.",
                                    "confidence": 0.6,
                                }
                            ],
                            "kpi_deltas": [],
                        }
                    ],
                }
            ]
        }

    monkeypatch.setattr("app.pipeline._provider_backed_simulation", fake_provider_simulation)
    client.post(f"/api/decision-runs/{run_id}/extract")
    client.post(f"/api/decision-runs/{run_id}/build-graph")
    simulate_res = client.post(f"/api/decision-runs/{run_id}/simulate")
    assert simulate_res.status_code == 200
    metadata = simulate_res.json()["data"]["run"]["metadata_json"]
    assert metadata["simulation_mode"] == "deterministic"
    assert metadata["simulation_mode_reason"] == "provider_response_lacked_kpi_deltas"
