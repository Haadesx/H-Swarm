"""SQLAlchemy ORM models for HealthTwin domain."""

from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def utcnow() -> datetime:
    return datetime.now(UTC)


class ScenarioCase(str, enum.Enum):
    base = "base_case"
    downside = "downside_case"
    severe = "severe_case"


class MemoType(str, enum.Enum):
    operator = "operator"
    capital = "capital"


class DecisionRunStatus(str, enum.Enum):
    created = "created"
    extracted = "extracted"
    graph_built = "graph_built"
    simulated = "simulated"
    memos_generated = "memos_generated"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    organization_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    scenario_type: Mapped[str] = mapped_column(String(80), default="reimbursement_cut", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    evidence_files: Mapped[list["EvidenceFile"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    decision_runs: Mapped[list["DecisionRun"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class EvidenceFile(Base):
    __tablename__ = "evidence_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    extension: Mapped[str] = mapped_column(String(20), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    extracted_table: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="evidence_files")


class DecisionRun(Base):
    __tablename__ = "decision_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    scenario_type: Mapped[str] = mapped_column(String(80), nullable=False)
    simulation_requirement: Mapped[str] = mapped_column(Text, nullable=False)
    time_horizons: Mapped[list[int]] = mapped_column(JSON, default=[30, 90, 180], nullable=False)
    status: Mapped[DecisionRunStatus] = mapped_column(Enum(DecisionRunStatus), default=DecisionRunStatus.created, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="decision_runs")
    assumptions: Mapped[list["Assumption"]] = relationship(back_populates="decision_run", cascade="all, delete-orphan")
    extracted_facts: Mapped[list["ExtractedFact"]] = relationship(back_populates="decision_run", cascade="all, delete-orphan")
    kpis: Mapped[list["KPI"]] = relationship(back_populates="decision_run", cascade="all, delete-orphan")
    stakeholder_nodes: Mapped[list["StakeholderNode"]] = relationship(back_populates="decision_run", cascade="all, delete-orphan")
    stakeholder_edges: Mapped[list["StakeholderEdge"]] = relationship(back_populates="decision_run", cascade="all, delete-orphan")
    simulation_events: Mapped[list["SimulationEvent"]] = relationship(back_populates="decision_run", cascade="all, delete-orphan")
    memos: Mapped[list["Memo"]] = relationship(back_populates="decision_run", cascade="all, delete-orphan")


class Assumption(Base):
    __tablename__ = "assumptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    decision_run_id: Mapped[str] = mapped_column(ForeignKey("decision_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(120), nullable=False)
    value: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[str] = mapped_column(String(80), default="operations", nullable=False)
    impact_area: Mapped[str] = mapped_column(String(80), default="operations", nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    source_evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="needs_review", nullable=False)
    user_modified: Mapped[bool] = mapped_column(default=False, nullable=False)

    decision_run: Mapped["DecisionRun"] = relationship(back_populates="assumptions")


class ExtractedFact(Base):
    __tablename__ = "extracted_facts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    decision_run_id: Mapped[str] = mapped_column(ForeignKey("decision_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_file_id: Mapped[Optional[str]] = mapped_column(ForeignKey("evidence_files.id", ondelete="SET NULL"), nullable=True, index=True)
    fact_type: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    source_excerpt: Mapped[str] = mapped_column(Text, default="", nullable=False)
    normalized_value_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    decision_run: Mapped["DecisionRun"] = relationship(back_populates="extracted_facts")


class KPI(Base):
    __tablename__ = "kpis"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    decision_run_id: Mapped[str] = mapped_column(ForeignKey("decision_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    case_name: Mapped[Optional[ScenarioCase]] = mapped_column(Enum(ScenarioCase), nullable=True)
    horizon_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    baseline_value: Mapped[float] = mapped_column(Float, nullable=False)
    projected_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    delta_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source_evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    decision_run: Mapped["DecisionRun"] = relationship(back_populates="kpis")


class StakeholderNode(Base):
    __tablename__ = "stakeholder_nodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    decision_run_id: Mapped[str] = mapped_column(ForeignKey("decision_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    role_summary: Mapped[str] = mapped_column(Text, nullable=False)
    influence_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)

    decision_run: Mapped["DecisionRun"] = relationship(back_populates="stakeholder_nodes")


class StakeholderEdge(Base):
    __tablename__ = "stakeholder_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    decision_run_id: Mapped[str] = mapped_column(ForeignKey("decision_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    source_node_id: Mapped[str] = mapped_column(ForeignKey("stakeholder_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id: Mapped[str] = mapped_column(ForeignKey("stakeholder_nodes.id", ondelete="CASCADE"), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(80), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)

    decision_run: Mapped["DecisionRun"] = relationship(back_populates="stakeholder_edges")


class SimulationEvent(Base):
    __tablename__ = "simulation_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    decision_run_id: Mapped[str] = mapped_column(ForeignKey("decision_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    case_name: Mapped[ScenarioCase] = mapped_column(Enum(ScenarioCase), nullable=False)
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    event_order: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    stakeholder: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    kpi_impacts: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    citation_evidence_ids: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    decision_run: Mapped["DecisionRun"] = relationship(back_populates="simulation_events")


class Memo(Base):
    __tablename__ = "memos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    decision_run_id: Mapped[str] = mapped_column(ForeignKey("decision_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    memo_type: Mapped[MemoType] = mapped_column(Enum(MemoType), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    sections: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    citations: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    decision_run: Mapped["DecisionRun"] = relationship(back_populates="memos")
