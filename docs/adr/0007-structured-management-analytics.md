# ADR 0007: Deterministic structured management analytics

## Status

Proposed on 2026-09-13 for the mandatory Gate 6 design checkpoint. Owner approval is required
before dependency installation, workbook generation, database creation, or implementation.

## Context

The accepted document-retrieval path is not suitable for exact management information. Questions
about balances, counts, rates, segment contributions, and month-to-month changes require typed
records, explicit joins, and deterministic calculations. DEC-005 already separates structured
analytics from document retrieval.

Gate 6 must demonstrate the question “Why did arrears deteriorate in August?” without asking a
language model to calculate figures or converting a temporal association into a causal claim. The
source must be synthetic, reviewable, version controlled, and small enough to reconcile by hand.

Excel is selected as the management-information source format and DuckDB as derived analytical
state. Excel does not enforce relational types or keys, so the application must validate workbook
content before it reaches DuckDB.

## Proposed decision

Use one canonical `.xlsx` workbook with eight exact sheets: `data_dictionary`, `loans`,
`loan_snapshots`, `operational_incidents`, `payroll_events`, `payments`,
`credit_control_actions`, and `complaints`. Require exact headers, explicit physical and logical
types, declared keys and relationships, strict enumerations, cross-field consistency, and
`synthetic_marker = "YES"` on every row.

Use `openpyxl>=3.1.3,<4` as the sole workbook reader. Open the workbook read-only with formulas
visible, disable external-link preservation, reject formula cells, and close it explicitly. Map
cells into strict application-owned Pydantic records before opening or modifying the analytical
database. Do not add pandas.

Use `duckdb>=1.5.5,<2` through an explicit connection owned by one adapter. Create typed tables
and insert the fully validated workbook in one transaction. Treat the DuckDB file as ignored,
derived, and rebuildable state; the workbook remains canonical. Provider or DuckDB result types do
not cross the application boundary.

Do not use DuckDB's Excel extension in Gate 6. Although DuckDB officially supports `.xlsx` through
the `excel` extension, the extension transparently autoloads from an extension repository and
spreadsheet imports may infer types. Explicit Python-side validation better exposes the mechanics
this educational gate is intended to teach and avoids a runtime extension download.

Centralize metric SQL under stable identities and bind period and filter values as parameters.
Allow only fixed application-owned metric and dimension identifiers. Aggregate each fact table at
its own grain before cross-fact joins, and reconcile segment totals with portfolio totals.

Return application-owned results with metric name, calculation and comparison periods, numerator,
denominator, nullable value, dimensions, supporting row count, query identity, and limitations.
For ratios, preserve a zero denominator and return a null value. Generate the local management
report from deterministic templates only.

Use the definitions and exact July/August scenario in `docs/CURRENT_GATE.md`. In particular,
PAR30 is the outstanding balance of loans at least 30 days past due divided by total outstanding
balance. Payroll-event cohorts come only from explicit payment-event links. Report measured facts,
observed associations, and possible contributing factors distinctly; never claim causal proof.

## Alternatives considered

- DuckDB's `excel` extension would remove one Python dependency, but it adds extension autoload
  behavior and makes strict cell-level validation and workbook-structure inspection less visible.
- pandas would make tabular loading convenient, but adds a larger abstraction and dependency
  surface that is unnecessary for the small workbook.
- CSV files would simplify parsing, but would not demonstrate the explicitly required Excel
  management-information boundary or multi-sheet contract.
- Direct Excel-to-SQL ingestion was rejected because invalid types, formulas, keys, and
  relationships must fail before derived state changes.
- In-memory Python aggregation was rejected because Gate 6 is intended to teach explicit,
  parameterized analytical SQL and database reconciliation.
- Natural-language-to-SQL and LLM-written explanations were rejected because they weaken numerical
  traceability and are explicitly outside Gate 6.

## Consequences

The design has two focused new dependencies and clear ownership: openpyxl reads cells, application
models validate meaning, and DuckDB calculates metrics. Exact grains, keys, and pre-aggregation
rules make double-counting testable. Rebuildable database state keeps the workbook authoritative.

The workbook is deliberately small and synthetic. Its constructed equality between August payment
shortfall and arrears movement demonstrates reconciliation and association, not a complete
accounting roll-forward or causation. No counterfactual, exposure adjustment, forecasting,
statistical inference, or production governance is provided. Workbook parsing also remains limited
to the approved `.xlsx` contract.

This ADR remains proposed until the owner explicitly approves the design checkpoint and listed
assumptions.

## References

- [DuckDB Excel extension](https://duckdb.org/docs/lts/core_extensions/excel)
- [DuckDB Python API](https://duckdb.org/docs/stable/clients/python/overview)
- [openpyxl read-only mode](https://openpyxl.readthedocs.io/en/stable/optimized.html)
- [openpyxl workbook reader](https://openpyxl.readthedocs.io/en/stable/api/openpyxl.reader.excel.html)
