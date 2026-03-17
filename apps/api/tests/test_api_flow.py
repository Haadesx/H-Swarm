from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient


def _build_client(tmp_path: Path) -> TestClient:
    db_path = tmp_path / "healthtwin_test.db"
    upload_dir = tmp_path / "uploads"
    contract_path = Path(__file__).resolve().parents[3] / "packages" / "domain-healthcare" / "domain.json"

    os.environ["HT_DB_URL"] = f"sqlite:///{db_path.as_posix()}"
    os.environ["HT_UPLOAD_DIR"] = upload_dir.as_posix()
    os.environ["HT_DOMAIN_CONTRACT_PATH"] = contract_path.as_posix()

    for mod in ["app.main", "app.database", "app.config", "app.models", "app.pipeline"]:
        if mod in sys.modules:
            del sys.modules[mod]

    api_root = Path(__file__).resolve().parents[1]
    if api_root.as_posix() not in sys.path:
        sys.path.insert(0, api_root.as_posix())

    app_module = importlib.import_module("app.main")
    return TestClient(app_module.app)


def test_decision_run_end_to_end(tmp_path: Path):
    client = _build_client(tmp_path)
    with client:
        project_res = client.post(
            "/api/projects",
            json={"name": "MetroCare Reimbursement Test", "organization_name": "MetroCare", "scenario_type": "reimbursement_cut"},
        )
        assert project_res.status_code == 200
        project_id = project_res.json()["data"]["id"]

        evidence_res = client.post(
            "/api/evidence/upload",
            data={"project_id": project_id},
            files=[
                (
                    "files",
                    ("scenario.md", b"Scenario update: 7% reimbursement cut expected this quarter.", "text/markdown"),
                ),
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
        assert evidence_res.status_code == 200
        assert len(evidence_res.json()["data"]["files"]) == 2

        run_res = client.post(
            "/api/decision-runs",
            json={"project_id": project_id, "scenario_type": "reimbursement_cut", "time_horizons": [30, 90, 180]},
        )
        assert run_res.status_code == 200
        run_id = run_res.json()["data"]["id"]

        extract_res = client.post(f"/api/decision-runs/{run_id}/extract")
        assert extract_res.status_code == 200
        assert len(extract_res.json()["data"]["assumptions"]) >= 3

        graph_res = client.post(f"/api/decision-runs/{run_id}/build-graph")
        assert graph_res.status_code == 200
        assert graph_res.json()["data"]["graph_summary"]["node_count"] >= 6

        sim_res = client.post(f"/api/decision-runs/{run_id}/simulate")
        assert sim_res.status_code == 200
        assert sim_res.json()["data"]["run"]["status"] == "simulated"

        memo_res = client.post(f"/api/decision-runs/{run_id}/generate-memo")
        assert memo_res.status_code == 200
        assert memo_res.json()["data"]["run"]["status"] == "memos_generated"

        timeline_res = client.get(f"/api/decision-runs/{run_id}/timeline", params={"case": "base_case"})
        assert timeline_res.status_code == 200
        assert len(timeline_res.json()["data"]["events"]) >= 5

        kpi_res = client.get(f"/api/decision-runs/{run_id}/kpis", params={"case": "downside_case"})
        assert kpi_res.status_code == 200
        assert len(kpi_res.json()["data"]["kpis"]) > 0

        operator_memo = client.get(f"/api/decision-runs/{run_id}/memos/operator")
        assert operator_memo.status_code == 200
        assert "Operator Brief" in operator_memo.json()["data"]["content_markdown"]

        qa_res = client.post(
            f"/api/decision-runs/{run_id}/interrogate",
            json={"question": "What is the covenant risk outlook?", "memo_type": "capital"},
        )
        assert qa_res.status_code == 200
        assert "covenant" in qa_res.json()["data"]["answer"].lower()
