# ADR 0001: Foundation architecture

## Context

The project needs a structure that supports incremental learning and future capability growth
without coupling application concepts to vendors.

## Decision

Use a modular Python 3.12 `src`-layout architecture with provider-independent domain boundaries.

## Alternatives considered

- A flat script-based repository, which is initially simpler but obscures boundaries as it grows.
- Early adoption of a GenAI framework, which would hide mechanics the project intends to teach.
- Provider-shaped domain objects, which would make future replacements costly.

## Consequences

The repository has more structure at the outset, but imports, ownership, and future integration
points are explicit. Provider adapters can be added behind stable boundaries in later gates.

