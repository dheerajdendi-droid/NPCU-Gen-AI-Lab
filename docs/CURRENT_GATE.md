# Gate 6 — Structured Management Analytics — Design Approval Pending

Gate 5.5 was formally accepted on **2026-09-19**. Gate 6 now returns to the documentation-only
design checkpoint originally preserved on 2026-09-13. No Gate 6 dependency, workbook, database,
application module, or test has been added, and Gate 7 has not started.

The complete proposed contract is recorded in
[`gate_designs/GATE_6_STRUCTURED_ANALYTICS_CHECKPOINT.md`](gate_designs/GATE_6_STRUCTURED_ANALYTICS_CHECKPOINT.md),
with the proposed architecture decision in
[`adr/0007-structured-management-analytics.md`](adr/0007-structured-management-analytics.md).
Those documents remain proposals until the owner explicitly approves or amends them.

## Proposed objective

Build the smallest understandable structured-analytics capability that loads synthetic
credit-union management information from one Excel workbook into DuckDB and answers defined
analytical questions with validated rows and deterministic, parameterized SQL.

The central demonstration question is:

> Why did arrears deteriorate in August?

The system will calculate measured changes and may report clearly qualified associations or
possible contributing factors. It will not claim causal proof, use an LLM for calculation or
explanation, or combine analytics with the accepted policy RAG path.

## Proposed dependencies

- `openpyxl>=3.1.3,<4` for strict, read-only `.xlsx` workbook inspection.
- `duckdb>=1.5.5,<2` for embedded analytical SQL over validated application records.
- Existing Pydantic models for application-owned validation.
- No pandas, DuckDB Excel extension, analytics framework, OpenAI call, or Pinecone operation.

These dependencies must not be installed until the owner approves the design checkpoint.

## Assumptions requiring explicit owner approval

1. Use the July and August 2026 closed periods and GBP amounts in the preserved checkpoint.
2. Define PAR30 as the outstanding balance of loans at least 30 days past due divided by total
   outstanding balance.
3. Measure contact completion per scheduled action, not per distinct loan.
4. Treat `PARTIAL` and `FAILED` payments as non-success while reporting hard failures separately.
5. Define the affected cohort from explicit August payment-to-payroll-event links and compare the
   same loans with their July records.
6. Permit only product, origination month, risk band, employer group, membership tenure, and
   affected payroll cohort as segmentation dimensions.
7. Use `openpyxl` for workbook inspection and DuckDB only after complete application validation.
8. Treat the designed equality between the £6,000 August payment shortfall and £6,000 arrears
   increase as an association, not a causal or complete accounting roll-forward.
9. Generate readable analysis from deterministic templates and defer narrative generation or
   combined policy answers to a separately approved later gate.

## Approval state

- [x] Gates 0–5.5 are formally accepted.
- [x] The Gate 6 design, scenario, metrics, validation rules, tests, and exclusions are documented.
- [x] ADR 0007 is preserved as proposed rather than accepted.
- [ ] The owner approves or amends the two proposed dependencies.
- [ ] The owner approves or amends all nine design assumptions.
- [ ] The owner authorizes Gate 6 implementation to begin.

## Explicitly not started

- Dependency installation
- Synthetic workbook creation
- DuckDB creation or schema work
- Analytics models, adapters, SQL, services, reports, or tests
- Changes to RAG, retrieval, generation, evaluation, or the Streamlit UI
- Gate 7 work

The next valid action is an explicit owner design-approval decision. Implementation must remain
paused until that decision is recorded in the architecture documents.
