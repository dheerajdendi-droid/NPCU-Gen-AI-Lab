---
name: npcu-safe-checkpoint
description: Inspect and prepare an NPCU Gate implementation for a safe Git checkpoint. Use only when invoked as $npcu-safe-checkpoint; do not use for ordinary code review, deployment, or implicit Git mutations.
---

# NPCU Safe Checkpoint

Prepare a reviewable Git checkpoint without altering implementation content. The user's explicit
request takes precedence, but selecting this skill does not itself authorize staging, committing,
pushing, merging, rebasing, opening a pull request, or deployment.

## Inspect

Read `AGENTS.md`, the project state, current Gate, and its required verification. Then:

- inspect the current branch, status, remote, intended diff, and staged versus unstaged files;
- preserve unrelated and pre-existing changes, and identify any overlap before proceeding;
- run the Gate's documented deterministic tests, lint, dependency, import, and whitespace checks;
- scan intended tracked content for credentials, accidental `.env` tracking, generated artifacts,
  and out-of-scope additions;
- confirm Git author name and email are configured without inventing or modifying either value; and
- propose a concise commit message and list exactly which files belong in the checkpoint.

Do not open or reveal `.env`. Do not discard, overwrite, reset, clean, or otherwise remove user
changes. Never modify Git identity.

## Mutation boundary

Without a direct user request for the specific action, stop after the readiness report. Stage only
explicitly identified relevant files when staging is authorized. Commit only when a commit is
authorized. Push only when the target remote and branch are explicitly authorized and verified.
Treat each broader action as separate authority; permission to commit does not imply permission to
push.

Never merge, rebase, create a pull request, deploy, or interact with Vercel or another hosting
provider unless the user separately requests that exact action.

## Report

State whether the checkpoint is ready, the checks and results, assumptions or blockers, the exact
included files, excluded unrelated changes, proposed or created commit message and hash, and final
branch/ahead-behind status. Clearly distinguish planned actions from actions actually performed.
