# HealthTwin by H-Swarm

![HealthTwin Demo Video](./docs/demo.webp)

HealthTwin is a healthcare-native decision workspace I built for provider operators and capital stakeholders.
I designed it around one core use case: helping health systems understand what breaks first when
reimbursement pressure, denial intensity, labor strain, and covenant sensitivity begin to move at the
same time.

The product does not present itself as a generic AI simulator. Instead, I built it to behave like an evidence-controlled
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

Through this repository, I document:

- how to run the product locally
- how the workflow is staged
- what external interfaces exist
- what artifacts are produced

I intentionally do not publish the full decision methodology, weighting logic, or the proprietary framing
I use to turn evidence into decision recommendations here.

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

I've included a bundled MetroCare reimbursement-stress demo that can be imported directly from the UI
or from the API:

```bash
curl -X POST http://localhost:8100/api/demo/import
```

I made the demo path deterministic by default so it remains reliable during live presentations, providing a consistent experience even if an LLM provider is slow or unavailable.

## Model Configuration

The backend supports OpenAI-compatible providers, including OpenRouter-compatible endpoints:

```bash
HT_LLM_API_KEY=...
HT_LLM_BASE_URL=https://openrouter.ai/api/v1
HT_LLM_MODEL=openai/gpt-oss-120b:free
```

Provider-backed enrichment is optional. If the provider returns invalid or incomplete output, the system
falls back to my deterministic logic without breaking the user workflow.

## Documentation

- [Product Overview](./docs/product-overview.md)
- [Operator Workflow](./docs/operator-workflow.md)
- [Technical Setup](./docs/technical-setup.md)
- [Architecture Note](./docs/architecture-note.md)
- [Live Demo Script](./docs/live-demo-script.md)
- [Video Storyboard](./docs/video-storyboard.md)
- [Positioning Brief](./docs/positioning-brief.md)

## Strategic Value & Positioning

I built this primarily for:

- provider CFO / strategy / transformation teams
- turnaround offices
- healthcare lenders and investors that need an operating-intelligence layer

As the platform matures, I see clear strategic value for:

- provider revenue-cycle platforms looking for an executive application layer
- healthcare operations platforms wanting to connect operational data to capital decisions
- financial performance / analytics vendors seeking to upgrade from reporting dashboards to decision-making workflows
- healthcare diligence and risk platforms aiming to automate scenario planning
