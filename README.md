# HealthTwin by H-Swarm

HealthTwin is a healthcare-native decision workspace for provider operators and capital stakeholders.
It is designed around one core use case: helping health systems understand what breaks first when
reimbursement pressure, denial intensity, labor strain, and covenant sensitivity begin to move at the
same time.

The product does not present itself as a generic AI simulator. It behaves like an evidence-controlled
workflow that turns uploaded financial, operational, and market materials into:

- a structured assumption set
- a stakeholder conflict view
- base, downside, and severe scenario outputs
- an `Operator Brief`
- a synchronized `Capital Memo`

## Repository Layout

- `apps/api`
  FastAPI backend for project creation, evidence ingestion, extraction, scenario runs, and memo generation.
- `apps/web`
  React frontend for the decision workflow.
- `packages/domain-healthcare`
  Shared scenario metadata, domain contract, and bundled demo pack.
- `packages/engine`
  Shared frontend types and helpers.
- `packages/evals`
  Evaluation and acceptance-test scaffolding.

## What This Repo Explains

This repository documents:

- how to run the product locally
- how the workflow is staged
- what external interfaces exist
- what artifacts are produced

It intentionally does not publish the full decision methodology, weighting logic, or proprietary framing
used to turn evidence into decision recommendations.

## Local Development

```bash
cd H-Swarm
npm run setup
npm run dev
```

Default ports:

- API: `http://localhost:8100`
- Web: `http://localhost:3200`

## Demo Run

HealthTwin includes a bundled MetroCare reimbursement-stress demo that can be imported directly from the UI
or from the API:

```bash
curl -X POST http://localhost:8100/api/demo/import
```

The demo path is deterministic by default so it remains reliable during live presentations even if an LLM
provider is slow or unavailable.

## Model Configuration

The backend supports OpenAI-compatible providers, including OpenRouter-compatible endpoints:

```bash
HT_LLM_API_KEY=...
HT_LLM_BASE_URL=https://openrouter.ai/api/v1
HT_LLM_MODEL=openai/gpt-oss-120b:free
```

Provider-backed enrichment is optional. If the provider returns invalid or incomplete output, the system
falls back to deterministic logic without breaking the user workflow.

## Documentation

- [Product Overview](./docs/product-overview.md)
- [Operator Workflow](./docs/operator-workflow.md)
- [Technical Setup](./docs/technical-setup.md)
- [Architecture Note](./docs/architecture-note.md)
- [Live Demo Script](./docs/live-demo-script.md)
- [Video Storyboard](./docs/video-storyboard.md)
- [Positioning Brief](./docs/positioning-brief.md)

## Buyer Positioning

The near-term buyer is:

- provider CFO / strategy / transformation teams
- turnaround offices
- healthcare lenders and investors that need an operating-intelligence layer

The likely strategic acquirer profile includes:

- provider revenue-cycle platforms
- healthcare operations platforms
- financial performance / analytics vendors
- healthcare diligence and risk platforms
