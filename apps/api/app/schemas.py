"""Pydantic schemas for API contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    organization_name: Optional[str] = Field(default=None, max_length=200)
    scenario_type: str = Field(default="reimbursement_cut", max_length=80)


class ProjectRead(BaseModel):
    id: str
    name: str
    organization_name: Optional[str]
    scenario_type: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EvidenceRead(BaseModel):
    id: str
    project_id: str
    filename: str
    extension: str
    size_bytes: int
    extracted_preview: str


class DecisionRunCreate(BaseModel):
    project_id: str
    scenario_type: Optional[str] = "reimbursement_cut"
    simulation_requirement: Optional[str] = None
    time_horizons: List[int] = Field(default_factory=lambda: [30, 90, 180])


class DecisionRunRead(BaseModel):
    id: str
    project_id: str
    scenario_type: str
    simulation_requirement: str
    time_horizons: List[int]
    status: str
    metadata_json: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssumptionRead(BaseModel):
    id: str
    key: str
    value: str
    category: str
    impact_area: str
    rationale: str
    source_evidence_ids: List[str]
    confidence: float
    status: str
    user_modified: bool

    model_config = {"from_attributes": True}


class AssumptionUpdate(BaseModel):
    value: str = Field(min_length=1, max_length=300)
    rationale: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[str] = Field(default=None, max_length=40)


class KPIRead(BaseModel):
    id: str
    case_name: Optional[str]
    horizon_days: Optional[int]
    name: str
    unit: str
    baseline_value: float
    projected_value: Optional[float]
    delta_value: Optional[float]
    source_evidence_ids: List[str]

    model_config = {"from_attributes": True}


class ExtractedFactRead(BaseModel):
    id: str
    evidence_file_id: Optional[str]
    fact_type: str
    title: str
    detail: str
    source_excerpt: str
    normalized_value_json: Dict[str, Any]
    confidence: float

    model_config = {"from_attributes": True}


class StakeholderNodeRead(BaseModel):
    id: str
    name: str
    entity_type: str
    role_summary: str
    influence_score: float

    model_config = {"from_attributes": True}


class StakeholderEdgeRead(BaseModel):
    id: str
    source_node_id: str
    target_node_id: str
    relation_type: str
    rationale: str

    model_config = {"from_attributes": True}


class SimulationEventRead(BaseModel):
    id: str
    case_name: str
    horizon_days: int
    event_order: int
    event_type: str
    stakeholder: str
    description: str
    kpi_impacts: Dict[str, float]
    confidence: float
    citation_evidence_ids: List[str]

    model_config = {"from_attributes": True}


class MemoRead(BaseModel):
    id: str
    memo_type: str
    title: str
    content_markdown: str
    sections: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}


class InterrogateRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    memo_type: Optional[str] = None


class InterrogateResponse(BaseModel):
    question: str
    answer: str
    citations: List[Dict[str, Any]]


class ApiEnvelope(BaseModel):
    success: bool = True
    data: Any
