# Repository guidance for coding agents

Before making changes:

1. Read `docs/PROJECT_STATE.md`.
2. Read `docs/CURRENT_GATE.md`.
3. Read relevant entries in `docs/DECISIONS.md` and `docs/adr/`.

While working:

4. Stay within the scope of the current gate.
5. Do not introduce future technologies early.
6. Keep provider-specific implementation behind appropriate boundaries.
7. Run relevant tests after code changes.
8. Report assumptions instead of silently making major architectural decisions.
9. Preserve the educational nature of the project.
10. Prefer simple implementations until a later gate justifies complexity.
11. Treat documented delivery estimates as planning assumptions, not guarantees.
12. Prioritise the core MVP before optional extensions unless the current gate explicitly
    requires otherwise.

