---
name: npcu-gate-review
description: Review an NPCU repository Gate for documented readiness, regression evidence, and scope compliance. Use for Gate audits or readiness reports; do not use to implement work, accept a Gate, or begin the next Gate.
---

# NPCU Gate Review

Review the current Gate without changing repository or external state. The user's explicit request
takes precedence over this workflow, subject to repository instructions and execution permissions.

## Establish the contract

Read `AGENTS.md`, `docs/PROJECT_STATE.md`, `docs/CURRENT_GATE.md`, `docs/DECISIONS.md`,
`docs/GATE_LOG.md`, `docs/LEARNING_LOG.md`, `docs/ARCHITECTURE.md`, and ADRs relevant to the current
and previously accepted Gates. Inspect Git status before drawing conclusions.

Treat the current Gate document as the review contract. Extract its entry conditions, in-scope work,
exclusions, expected behavior, errors, verification, and exit criteria. Do not infer acceptance from
an implementation commit or passing tests.

## Review

- Map each Gate requirement to repository evidence, a deterministic check, an explicit assumption,
  or an identified gap.
- Confirm previously accepted Gate contracts and their tests remain intact.
- Run only the deterministic checks appropriate to the documented Gate. Do not run live-provider
  tests or incur cost unless the current user directly authorizes those exact external operations.
- Inspect dependencies and changed files for technology or behavior outside the current Gate.
- Identify undocumented decisions, incomplete requirements, contradictory documentation, and
  evidence that cannot be reproduced.
- Distinguish a verified pass, a failure, an unverified claim, and a recommendation.

Do not implement missing work unless the user separately and explicitly asks for implementation.
Never formally accept a Gate, modify Gate status, commit, push, or start the next Gate under this
review workflow.

## Report

Lead with the readiness result. Explain blockers and material risks in plain language for a
non-technical owner, then provide the supporting checks, assumptions, limitations, and important
technical and educational learnings. Recommend acceptance only when every documented criterion is
demonstrated; leave the acceptance decision to the owner.
