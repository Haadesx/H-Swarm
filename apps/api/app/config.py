"""Runtime settings and shared domain contract loader."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


@dataclass(frozen=True)
class Settings:
    """Application runtime settings."""

    app_name: str = "HealthTwin API"
    api_prefix: str = "/api"
    db_url: str = os.getenv("HT_DB_URL", "")
    upload_dir: str = os.getenv("HT_UPLOAD_DIR", "")
    domain_contract_path: str = os.getenv("HT_DOMAIN_CONTRACT_PATH", "")
    llm_api_key: str = os.getenv("HT_LLM_API_KEY", "")
    llm_base_url: str = os.getenv("HT_LLM_BASE_URL", "")
    llm_model: str = os.getenv("HT_LLM_MODEL", "")


def _default_db_url() -> str:
    base = Path(__file__).resolve().parent.parent
    data_dir = base / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{(data_dir / 'healthtwin.db').as_posix()}"


def _default_upload_dir() -> str:
    base = Path(__file__).resolve().parent.parent
    uploads = base / "data" / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    return uploads.as_posix()


def _default_domain_contract_path() -> str:
    # apps/api/app/config.py -> healthtwin/packages/domain-healthcare/domain.json
    root = Path(__file__).resolve().parents[3]
    return (root / "packages" / "domain-healthcare" / "domain.json").as_posix()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    db_url = settings.db_url or _default_db_url()
    upload_dir = settings.upload_dir or _default_upload_dir()
    contract_path = settings.domain_contract_path or _default_domain_contract_path()
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    return Settings(
        app_name=settings.app_name,
        api_prefix=settings.api_prefix,
        db_url=db_url,
        upload_dir=upload_dir,
        domain_contract_path=contract_path,
        llm_api_key=settings.llm_api_key,
        llm_base_url=settings.llm_base_url,
        llm_model=settings.llm_model,
    )


@lru_cache(maxsize=1)
def load_domain_contract() -> Dict[str, Any]:
    settings = get_settings()
    contract_path = Path(settings.domain_contract_path)
    if not contract_path.exists():
        raise FileNotFoundError(f"Domain contract not found at: {contract_path}")
    with contract_path.open("r", encoding="utf-8") as f:
        return json.load(f)
