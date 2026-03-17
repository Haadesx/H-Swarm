# Architecture Note

## Intent

This note explains the product architecture at the level needed for operators, collaborators, and technical
buyers. It deliberately omits the detailed internal scoring and decision logic that differentiate the product.

## System Shape

HealthTwin is split into:

- `apps/web` for the decision workspace
- `apps/api` for workflow orchestration and artifact generation
- `packages/domain-healthcare` for domain contract and scenario metadata

## Workflow Stages

The backend follows a staged model:

1. project and run creation
2. evidence ingestion
3. assumption and fact extraction
4. stakeholder synthesis
5. scenario simulation
6. memo generation
7. follow-up interrogation

Each stage is independently addressable through API routes and subject to stage gating.

## Reliability Model

The product supports provider-backed enrichment through OpenAI-compatible APIs, but it does not depend on
them to stay usable. Local deterministic paths exist to keep the workflow intact when provider responses are:

- slow
- malformed
- incomplete
- unavailable

This design is especially important for live demos and buyer-facing reliability.

## Public Artifact Types

The current system exposes:

- evidence files
- extracted facts
- typed assumptions
- stakeholder nodes and edges
- KPI trajectories
- event timelines
- operator and capital memos

## Why This Matters

Most healthcare software can show dashboards or summarize documents. Fewer systems can move a team from
evidence to stakeholder-aware scenario comparison and then into boardroom-ready outputs within one workflow.

That is the layer this product is designed to occupy.
