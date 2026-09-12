---
name: npcu-live-provider-smoke
description: Run explicitly approved NPCU OpenAI and Pinecone smoke tests with bounded effects and safe reporting. Use only when invoked as $npcu-live-provider-smoke; do not use for routine offline tests or implicit provider checks.
---

# NPCU Live Provider Smoke

Run only the repository's already approved live-provider verification. The user's explicit request
takes precedence over this workflow, but selecting this skill does not itself authorize external
data disclosure, cost, or remote mutation.

## Authorization boundary

Before any network call, confirm the current user message directly authorizes the named live test,
the synthetic data that will leave the machine, the providers involved, expected cost, and every
possible remote mutation. If authorization is missing or only implied, stop and request it.

Never create, recreate, clear, or delete a Pinecone index; delete vectors or namespaces; or
re-embed and upsert the corpus unless the user explicitly authorizes that exact action. Stop before
any destructive or broader remote operation, even after a partial success.

## Preflight

1. Read `AGENTS.md`, the project state, current Gate, decisions, relevant ADRs, and the exact live
   test before execution.
2. Confirm Git status and the accepted baseline required by the test.
3. Load configuration only through the application's normal settings path. Never open, print, copy,
   edit, or commit `.env`.
4. Report only boolean presence for credential settings. Never place credential values in commands,
   logs, test output, generated files, or Git.
5. Confirm `.env` is ignored and that the live test remains separate from normal offline tests.
6. State the exact command, provider calls, data disclosure, cost class, and remote effects before
   requesting execution approval.

## Execute and diagnose

Run only the repository's approved, explicitly marked live tests. Do not improvise additional live
queries or rerun a corpus-indexing test when a focused test exists.

On failure, preserve successful evidence and classify the issue as configuration, authentication,
billing, permissions, model availability, index contract, vector dimensions, metadata mapping,
retrieval, generation, citation validation, propagation timing, or application behavior. A retry
must be bounded, relevant to the diagnosed transient issue, and within the user's authorization.

## Report

Report the model and API path, index contract, namespace vector count, scenarios exercised,
grounding and citations, duration, provider operations, approximate usage or high-level cost, and
any skipped or blocked step. Never include secrets, complete prompts, full retrieved context, or raw
provider objects. Do not commit, push, accept a Gate, or start the next Gate unless separately asked.
