import sys
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_healthtwin_execute_flow(tmp_path, monkeypatch):
    from app.config import get_settings, load_domain_contract

    monkeypatch.setenv("HT_DB_URL", f"sqlite:///{(tmp_path / 'healthtwin.db').as_posix()}")
    monkeypatch.setenv("HT_UPLOAD_DIR", (tmp_path / "uploads").as_posix())
    monkeypatch.setenv(
        "HT_DOMAIN_CONTRACT_PATH",
        str(Path(__file__).resolve().parents[3] / "packages" / "domain-healthcare" / "domain.json"),
    )
    get_settings.cache_clear()
    load_domain_contract.cache_clear()

    from app.database import engine
    from app.main import app
    from app.models import Base

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    client = TestClient(app)

    project_response = client.post(
        "/api/projects",
        json={"name": "MetroCare Native", "organization_name": "MetroCare", "scenario_type": "reimbursement_cut"},
    )
    assert project_response.status_code == 200
    project_id = project_response.json()["data"]["id"]

    upload_response = client.post(
        f"/api/projects/{project_id}/evidence",
        files=[
            ("files", ("financials.csv", b"operating_margin,days_cash_on_hand,denial_rate\n3.4,121,8.1\n", "text/csv")),
            ("files", ("brief.txt", b"CMS reimbursement reduction raises lender concern and patient access pressure.", "text/plain")),
        ],
    )
    assert upload_response.status_code == 200
    assert len(upload_response.json()["data"]) == 2

    run_response = client.post(
        "/api/runs",
        json={"project_id": project_id, "scenario_type": "reimbursement_cut", "time_horizons": [30, 90, 180]},
    )
    assert run_response.status_code == 200
    run_id = run_response.json()["data"]["id"]

    execute_response = client.post(f"/api/runs/{run_id}/execute")
    assert execute_response.status_code == 200
    payload = execute_response.json()["data"]
    assert payload["run"]["status"] == "memos_generated"
    assert len(payload["artifacts"]["assumptions"]) >= 1
    assert len(payload["artifacts"]["stakeholders"]) >= 5
    assert "operator" in payload["artifacts"]["memos"]


def test_demo_import_executes_bundled_healthcare_pack(tmp_path, monkeypatch):
    from app.config import get_settings, load_domain_contract

    monkeypatch.setenv("HT_DB_URL", f"sqlite:///{(tmp_path / 'healthtwin-demo.db').as_posix()}")
    monkeypatch.setenv("HT_UPLOAD_DIR", (tmp_path / "uploads-demo").as_posix())
    monkeypatch.setenv(
        "HT_DOMAIN_CONTRACT_PATH",
        str(Path(__file__).resolve().parents[3] / "packages" / "domain-healthcare" / "domain.json"),
    )
    get_settings.cache_clear()
    load_domain_contract.cache_clear()

    from app.database import engine
    from app.main import app
    from app.models import Base

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    client = TestClient(app)
    response = client.post("/api/demo/import")
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["project"]["name"] == "MetroCare Health System"
    assert payload["run"]["status"] == "memos_generated"
    assert len(payload["evidence"]) >= 4
    assert len(payload["artifacts"]["timeline"]) >= 5
    assert "capital" in payload["artifacts"]["memos"]
