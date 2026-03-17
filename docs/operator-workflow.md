# Operator Workflow

## Workflow Summary

HealthTwin is organized as a staged decision workflow:

1. Define case
2. Upload evidence
3. Review assumptions
4. Inspect stakeholders
5. Replay impacts
6. Read memo
7. Compare actions

## Step 1: Define Case

The user frames the operating question, scenario type, and decision requirement. In the current product,
the first optimized scenario is `reimbursement_cut`.

## Step 2: Upload Evidence

Users upload a case pack that may include:

- board materials
- KPI exports
- service-line financials
- financing snapshots
- market and payer notes

The current local workflow supports `txt`, `md`, and `csv`, with room to extend further.

## Step 3: Review Assumptions

The system generates a typed assumption set and initial KPI baseline. This step is designed to expose the
run’s operating frame before scenario outputs are consumed.

## Step 4: Inspect Stakeholders

Stakeholder output is presented first as a conflict and exposure view, with the graph positioned as a
secondary layer for context.

## Step 5: Replay Impacts

The user compares `base`, `downside`, and `severe` paths across key operating and financing signals.

## Step 6: Read Memo

The workflow produces two synchronized memo outputs:

- `Operator Brief`
- `Capital Memo`

These are generated from the same underlying run artifacts but framed for different decision audiences.

## Step 7: Compare Actions

The final stage supports follow-up interrogation and action comparison so the user can pressure-test next moves.
