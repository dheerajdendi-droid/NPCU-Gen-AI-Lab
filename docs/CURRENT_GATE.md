# Gate 6 — Structured Management Analytics

Gate 6 entered its mandatory design checkpoint on **2026-09-13** from the clean, synchronized Gate
5 acceptance commit `1070ab59569aef446733c4e175aa801f2e179dee`. The accepted baseline was
reproduced with 202 deterministic tests passing, all three live tests skipped by default, and Ruff
passing.

This document is a proposal for owner review. No Gate 6 dependency has been installed, no workbook
or database has been created, and no analytics implementation has started. Gate 6 is not accepted,
and Gate 7 has not started.

## Objective

Build the smallest understandable structured-analytics capability that loads synthetic credit-union
management information from one Excel workbook into DuckDB and answers defined analytical
questions with validated rows and deterministic, parameterized SQL.

The central demonstration question is:

> Why did arrears deteriorate in August?

The analytics layer will calculate what happened. It may report measured differences, temporal
associations, and explicitly labelled possible contributing factors, but it will not use a language
model, infer missing values, or claim that an observed association proves causation.

## Proposed canonical workbook

The sole canonical structured-data input will be
`data/structured/npcu_management_analytics.xlsx`. It will contain values only: formulas, macros,
external links, hidden data sheets, merged data cells, and free-form notes outside the declared
tables will be rejected or absent. Sheet order and names will be exact:

1. `data_dictionary`
2. `loans`
3. `loan_snapshots`
4. `operational_incidents`
5. `payroll_events`
6. `payments`
7. `credit_control_actions`
8. `complaints`

Every business row, and every data-dictionary row, will contain
`synthetic_marker = "YES"`. Workbook content will be fictional and denominated in GBP. Dates will
be genuine Excel date cells, not display-formatted text. Decimal money values will have at most two
fractional digits.

### Data dictionary

The dictionary will have one row for every declared column in every sheet, including its own
columns. The application schema remains authoritative; the loader will compare dictionary rows
with it so the workbook cannot redefine the contract.

| Column | Logical type | Key | Nullable | Allowed values or rule |
| --- | --- | --- | --- | --- |
| `sheet_name` | TEXT | PK part 1 | No | One of the eight exact sheet names |
| `column_name` | TEXT | PK part 2 | No | Exact declared header in that sheet |
| `logical_type` | TEXT | — | No | `TEXT`, `DATE`, `INTEGER`, `DECIMAL(14,2)`, or `BOOLEAN` |
| `nullable` | BOOLEAN | — | No | `TRUE` or `FALSE` |
| `primary_key_position` | INTEGER | — | Yes | One-based key order, or null when not part of the PK |
| `foreign_key` | TEXT | — | Yes | Exact `sheet.column` target, or null when not an FK |
| `allowed_values` | TEXT | — | Yes | Pipe-separated enumeration or a documented validation rule |
| `description` | TEXT | — | No | Nonblank plain-language definition |
| `synthetic_marker` | TEXT | — | No | Literal `YES` |

### Loans

One row represents one synthetic loan and its stable analytical dimensions.

| Column | Logical type | Key | Nullable | Allowed values or rule |
| --- | --- | --- | --- | --- |
| `loan_id` | TEXT | PK | No | Unique, nonblank; pattern `LN-###` |
| `product` | TEXT | — | No | `PERSONAL_LOAN`, `JOIN_AND_BORROW` |
| `origination_date` | DATE | — | No | On or after membership start |
| `risk_band` | TEXT | — | No | `LOW`, `MEDIUM`, `HIGH` |
| `employer_group` | TEXT | — | No | `EMPLOYER_A`, `EMPLOYER_B`, `EMPLOYER_C` |
| `membership_start_date` | DATE | — | No | On or before origination |
| `synthetic_marker` | TEXT | — | No | Literal `YES` |

Origination cohort is the calendar month of `origination_date`. Membership-tenure buckets are
calculated at each snapshot date as `UNDER_90_DAYS`, `90_TO_364_DAYS`, or
`365_DAYS_AND_OVER`; the boundary values belong to the latter two buckets respectively.

### Loan snapshots

One row represents one loan at one calendar month end. The composite primary key is
`(loan_id, snapshot_month)`.

| Column | Logical type | Key | Nullable | Allowed values or rule |
| --- | --- | --- | --- | --- |
| `loan_id` | TEXT | PK part 1, FK | No | References `loans.loan_id` |
| `snapshot_month` | DATE | PK part 2 | No | Calendar month-end date |
| `outstanding_balance` | DECIMAL(14,2) | — | No | At least 0.00 |
| `arrears_balance` | DECIMAL(14,2) | — | No | From 0.00 through outstanding balance |
| `days_past_due` | INTEGER | — | No | Zero or positive; booleans are not integers |
| `synthetic_marker` | TEXT | — | No | Literal `YES` |

`arrears_balance = 0` requires `days_past_due = 0`; a positive arrears balance requires positive
days past due. The canonical scenario requires exactly one 2026-07-31 and one 2026-08-31 snapshot
for every loan.

### Operational incidents

One row represents one operational incident.

| Column | Logical type | Key | Nullable | Allowed values or rule |
| --- | --- | --- | --- | --- |
| `incident_id` | TEXT | PK | No | Unique and nonblank |
| `started_date` | DATE | — | No | — |
| `resolved_date` | DATE | — | Yes | Not earlier than `started_date` |
| `incident_type` | TEXT | — | No | `PAYROLL_PROCESSING`, `CORE_BANKING`, `SUPPLIER_SERVICE` |
| `severity` | TEXT | — | No | `LOW`, `MEDIUM`, `HIGH` |
| `affected_employer_group` | TEXT | — | Yes | One declared employer group |
| `status` | TEXT | — | No | `OPEN`, `RESOLVED` |
| `summary` | TEXT | — | No | Nonblank synthetic description |
| `synthetic_marker` | TEXT | — | No | Literal `YES` |

`RESOLVED` requires a resolution date; `OPEN` requires it to be null.

### Payroll events

One row represents one employer payroll-processing event.

| Column | Logical type | Key | Nullable | Allowed values or rule |
| --- | --- | --- | --- | --- |
| `payroll_event_id` | TEXT | PK | No | Unique and nonblank |
| `incident_id` | TEXT | FK | No | References `operational_incidents.incident_id` |
| `event_date` | DATE | — | No | Within the linked incident interval |
| `employer_group` | TEXT | — | No | One declared employer group |
| `event_type` | TEXT | — | No | `FILE_LATE`, `FILE_REJECTED`, `DEDUCTION_SHORTFALL` |
| `status` | TEXT | — | No | `OPEN`, `RESOLVED` |
| `resolved_date` | DATE | — | Yes | Not earlier than `event_date` |
| `synthetic_marker` | TEXT | — | No | Literal `YES` |

The linked incident must be `PAYROLL_PROCESSING`, and its affected employer group must equal the
payroll event's group. Resolution status and date follow the incident rules.

### Payments

One row represents one scheduled loan payment.

| Column | Logical type | Key | Nullable | Allowed values or rule |
| --- | --- | --- | --- | --- |
| `payment_id` | TEXT | PK | No | Unique and nonblank |
| `loan_id` | TEXT | FK | No | References `loans.loan_id` |
| `due_date` | DATE | — | No | On or after loan origination |
| `expected_amount` | DECIMAL(14,2) | — | No | Greater than 0.00 |
| `received_amount` | DECIMAL(14,2) | — | No | From 0.00 through expected amount |
| `payment_status` | TEXT | — | No | `SUCCESS`, `PARTIAL`, `FAILED` |
| `payment_method` | TEXT | — | No | `PAYROLL_DEDUCTION`, `DIRECT_DEBIT` |
| `payroll_event_id` | TEXT | FK | Yes | References `payroll_events.payroll_event_id` |
| `synthetic_marker` | TEXT | — | No | Literal `YES` |

`SUCCESS` means received equals expected, `PARTIAL` means received is strictly between zero and
expected, and `FAILED` means zero was received. A payroll-event link is allowed only for
`PAYROLL_DEDUCTION`, and the event's employer group must match the loan's employer group.

### Credit-control actions

One row represents one scheduled contact action. Completion is measured per scheduled action, not
per loan.

| Column | Logical type | Key | Nullable | Allowed values or rule |
| --- | --- | --- | --- | --- |
| `action_id` | TEXT | PK | No | Unique and nonblank |
| `loan_id` | TEXT | FK | No | References `loans.loan_id` |
| `scheduled_date` | DATE | — | No | On or after loan origination |
| `completion_status` | TEXT | — | No | `COMPLETED`, `NOT_COMPLETED` |
| `completed_date` | DATE | — | Yes | Not earlier than scheduled date |
| `channel` | TEXT | — | No | `PHONE`, `SMS`, `EMAIL`, `LETTER` |
| `outcome` | TEXT | — | Yes | `MEMBER_CONTACTED`, `NO_RESPONSE`, `PROMISE_TO_PAY`, `REFERRED` |
| `synthetic_marker` | TEXT | — | No | Literal `YES` |

`COMPLETED` requires both completion date and outcome; `NOT_COMPLETED` requires both to be null.

### Complaints

One row represents one complaint linked to a loan.

| Column | Logical type | Key | Nullable | Allowed values or rule |
| --- | --- | --- | --- | --- |
| `complaint_id` | TEXT | PK | No | Unique and nonblank |
| `loan_id` | TEXT | FK | No | References `loans.loan_id` |
| `received_date` | DATE | — | No | On or after loan origination |
| `category` | TEXT | — | No | `ARREARS_HANDLING`, `PAYMENT_PROCESSING`, `AFFORDABILITY`, `OTHER` |
| `status` | TEXT | — | No | `OPEN`, `CLOSED` |
| `related_incident_id` | TEXT | FK | Yes | References `operational_incidents.incident_id` |
| `synthetic_marker` | TEXT | — | No | Literal `YES` |

## Proposed metric definitions

All periods are closed calendar months represented by their month-end date. Money uses DuckDB
`DECIMAL(14,2)`; ratios are calculated from exact numerators and denominators and rounded to six
decimal places only at the application result boundary.

| Metric identity | Exact definition |
| --- | --- |
| `outstanding_balance.v1` | Sum of `loan_snapshots.outstanding_balance` for the period |
| `arrears_balance.v1` | Sum of `loan_snapshots.arrears_balance` for the period |
| `accounts_in_arrears.v1` | Count of distinct period loans where arrears balance is greater than zero |
| `accounts_in_arrears_rate.v1` | Accounts in arrears divided by all loan snapshots in the period |
| `par30.v1` | Outstanding balance of loans with `days_past_due >= 30` divided by total outstanding balance |
| `early_arrears_accounts.v1` | Count of distinct loans with positive arrears and 1–29 days past due |
| `early_arrears_balance.v1` | Arrears balance of loans with positive arrears and 1–29 days past due |
| `payment_success_rate.v1` | Count of due payments with `SUCCESS` divided by all due payments |
| `payment_failure_rate.v1` | Count of due payments with `FAILED` divided by all due payments |
| `payment_non_success_rate.v1` | Count of due `PARTIAL` or `FAILED` payments divided by all due payments |
| `payment_shortfall.v1` | Sum of expected amount minus received amount for due payments |
| `contact_completion_rate.v1` | Count of scheduled actions marked `COMPLETED` divided by all actions scheduled |
| `complaint_count.v1` | Count of distinct complaints received in the period |
| `incident_count.v1` | Count of distinct operational incidents started in the period |
| `payroll_event_count.v1` | Count of distinct payroll events dated in the period |

For additive metrics, `numerator` and `value` contain the calculated amount or count and
`denominator` is null. For ratios, all three fields are populated; a zero denominator is retained
as zero and produces `value = null`, never zero or one.

Segment contribution is the segment's August arrears balance minus its July arrears balance.
Contribution share is that movement divided by total portfolio movement when the total is nonzero;
negative movements remain negative. Approved dimensions are product, origination month, risk band,
employer group, membership-tenure bucket, and August payroll-event cohort. No other breakdown will
be added without a new decision.

## Proposed July-to-August scenario

The workbook will contain 12 loans, 24 month-end snapshots, 24 scheduled payments, one operational
incident, one linked payroll event, nine credit-control actions, and five complaints. Each payment
has an expected amount of £1,500.

The four `EMPLOYER_A` loans form the August payroll-affected cohort because their August payroll
payments link to the single payroll event. No loan is classified by employer name alone, and the
cohort label is not applied to July facts until the fixed August cohort is deliberately used for a
same-loan comparison.

| Measure | July 2026 | August 2026 | Change |
| --- | ---: | ---: | ---: |
| Outstanding balance | £120,000 | £116,000 | -£4,000 (-3.33%) |
| Arrears balance | £6,000 | £12,000 | +£6,000 (+100%) |
| Accounts in arrears | 3/12 | 6/12 | +3 accounts; +25 percentage points |
| PAR30 numerator | £20,000 | £38,500 | +£18,500 |
| PAR30 | 20,000/120,000 = 16.6667% | 38,500/116,000 = 33.1897% | +16.5230 percentage points |
| Early-arrears accounts | 1 | 2 | +1 |
| Early-arrears balance | £1,000 | £2,500 | +£1,500 |
| Payment success | 11/12 = 91.6667% | 6/12 = 50.0000% | -41.6667 percentage points |
| Partial payments | 1/12 | 4/12 | +3 |
| Failed payments | 0/12 | 2/12 | +2 |
| Payment shortfall | £500 | £6,000 | +£5,500 |
| Contact completion | 3/3 = 100% | 3/6 = 50% | -50 percentage points |
| Complaints received | 1 | 4 | +3 |
| Operational incidents started | 0 | 1 | +1 |
| Payroll events | 0 | 1 | +1 |

The August arrears movement is deliberately arithmetically consistent with August payment
shortfalls at loan level: the four affected loans contribute £5,000 of the £6,000 increase, and the
eight unaffected loans contribute £1,000. This equality is a fixture property, not proof that the
payment event caused the arrears movement.

| August cohort | Loans | July arrears | August arrears | Movement | July payment success | August payment success | July PAR30 | August PAR30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Payroll affected | 4 | £1,000 | £6,000 | +£5,000 | 4/4 | 0/4 | £0/£40,000 | £19,000/£38,000 |
| Unaffected | 8 | £5,000 | £6,000 | +£1,000 | 7/8 | 6/8 | £20,000/£80,000 | £19,500/£78,000 |

The operational incident starts on 2026-08-24 and the linked `EMPLOYER_A` payroll event occurs on
2026-08-25. Four August payments link to it. Three of the four August complaints link to that
incident; the July complaint and remaining August complaint do not. August credit-control
completion is 1/4 for affected loans and 2/2 for unaffected loans; all three July actions complete.

## Join and double-counting rules

- Snapshot balances and account measures query `loan_snapshots` directly. A one-to-one join to
  `loans` supplies dimensions without changing the snapshot grain.
- Payments, credit-control actions, complaints, incidents, and payroll events are each aggregated at
  their own declared grain before comparison. Counts use their primary IDs.
- The payroll cohort is built as one distinct `(loan_id, period)` relation from payment-event
  links before it joins snapshots. Raw payments are never joined directly to raw snapshots for
  balance aggregation.
- Cross-fact analysis joins pre-aggregated loan-period results or uses `EXISTS`; it never creates a
  payments × actions × complaints multiplication.
- Segment totals must reconcile to the unsegmented portfolio total for each period. A loan belongs
  to exactly one value of each loan dimension and exactly one payroll cohort for a comparison.
- Complaints and incidents are contextual counts. They are not added to loan or payment counts.

## Evidence language

- **Measured fact:** a direct deterministic result, such as “August arrears were £12,000.”
- **Observed association:** a measured difference involving contemporaneous groups or events, such
  as “the payroll-affected cohort contributed £5,000 of the £6,000 movement.”
- **Possible contributing factor:** an explicitly qualified interpretation supported by timing and
  association, such as “the payroll disruption may have contributed.”
- **Unsupported causal claim:** language such as “the incident caused the deterioration.” The
  report must reject this because the fixture has no counterfactual, causal design, or complete
  arrears roll-forward.

The readable report will use deterministic templates and calculated result objects. It will not ask
an LLM to calculate, summarize, or explain the figures.

## Proposed dependencies

- `duckdb>=1.5.5,<2` for embedded analytical SQL.
- `openpyxl>=3.1.3,<4` for explicit, read-only `.xlsx` workbook inspection.
- Existing Pydantic models for application validation.
- No pandas or analytics framework.

DuckDB has an official Excel extension, but it transparently autoloads from an extension repository
and may infer spreadsheet types. Gate 6 instead proposes `openpyxl.load_workbook(...,
read_only=True, data_only=False, keep_links=False)`, rejects formula cells, closes the workbook
explicitly, maps cells to application-owned records, and inserts only validated values into typed
DuckDB tables. This adds one small Excel dependency while avoiding a runtime DuckDB extension
download and preserving visible validation mechanics.

No dependency will be installed until the owner approves this checkpoint.

## Proposed application boundaries and outputs

- `analytics.workbook`: the sole `openpyxl` adapter; it returns an application-owned
  `AnalyticsWorkbook` containing immutable validated record collections.
- `analytics.models`: strict records for each business sheet plus `MetricResult`,
  `SegmentResult`, `PeriodComparison`, and `ManagementAnalysis`. Provider and DuckDB types do
  not cross this boundary.
- `analytics.store`: one concrete DuckDB adapter behind a small application-owned
  `AnalyticsStore` contract. It creates typed tables and loads a complete validated workbook in
  one transaction.
- `analytics.metrics`: centralized SQL identities and parameterized calculations.
- `analytics.service`: orchestrates rebuild, reconciliation, July/August comparisons, segment
  contributions, and deterministic report construction.

Each `MetricResult` will contain metric name, calculation period, comparison period where
applicable, numerator, denominator, nullable value, sorted dimension values, supporting source-row
count, stable query identity, and limitations. Results will use `Decimal`, `date`, integers,
strings, and tuples only.

The DuckDB file is derived, rebuildable, ignored state. Tests will use temporary or in-memory
databases. Rebuilding replaces the known Gate 6 schema only after workbook validation; the workbook
remains the system of record.

## Validation and failure behavior

- A missing workbook raises `FileNotFoundError`.
- Invalid XLSX containers, unreadable workbooks, formulas, external links, or unsupported workbook
  features raise a safe `WorkbookValidationError`.
- Missing, duplicated, reordered, or unexpected sheets; missing, duplicated, reordered, or
  unexpected columns; blank headers; internal blank rows; and trailing undeclared cell values fail
  before loading.
- Wrong physical cell types, non-finite numbers, excess decimal scale, invalid dates,
  enumerations, nullability, or synthetic markers fail with sheet, row, column, and a stable error
  code. Errors never echo the full row.
- Duplicate primary keys, broken foreign keys, invalid date order, status/date inconsistencies,
  payment/status mismatches, snapshot inconsistencies, or payroll/incident/loan mismatches fail
  before DuckDB is changed.
- Database creation and insertion are transactional. A failed load leaves no partially populated
  analytical schema.
- Unsupported metric names, dimensions, or invalid periods fail before SQL execution.
- SQL values are bound parameters; metric and dimension identifiers come only from a fixed
  application-owned allowlist.
- Empty result sets return zero supporting rows and the metric's mathematically correct empty
  representation. Ratio denominators of zero produce `value = null`.
- Database row counts, primary-ID sets, and additive totals must reconcile with the validated
  workbook before analysis is returned.

## Deterministic test strategy

- Valid workbook ingestion using a small hand-checkable XLSX fixture.
- Missing, duplicated, reordered, and unexpected sheets or columns.
- Invalid strings, Excel dates, integers, decimals, enumerations, formula cells, nullability, and
  synthetic markers.
- Duplicate simple and composite primary keys and broken foreign keys.
- Every cross-field rule for snapshots, payments, incident resolution, payroll linkage,
  credit-control completion, and complaint linkage.
- Exact workbook-to-DuckDB row, ID, and money reconciliation.
- Hand-calculated metric tests for balances, account counts, PAR30, early arrears, payments,
  contacts, complaints, and incidents.
- Exact July-to-August totals and changes defined in this document.
- Segment reconciliation and payroll-cohort analysis without fact multiplication.
- Zero denominators, empty result sets, invalid periods, and unsupported dimensions.
- Parameter binding verified with adversarial parameter values.
- Byte-for-byte deterministic serialized results and reports across repeated runs.
- Rebuilding the derived DuckDB state twice produces identical tables and results.
- All accepted Gate 0–5 tests remain passing and all live tests remain skipped by default.

## Exit criteria

- [ ] Owner approves this design checkpoint and every listed assumption
- [ ] DuckDB and openpyxl are recorded as accepted dependencies before installation
- [ ] One version-controlled synthetic-only workbook matches the approved schema and scenario
- [ ] Workbook validation covers exact structure, types, keys, relationships, dates, enums,
  formulas, nullability, and record-level synthetic markers
- [ ] A validated workbook loads transactionally into derived, rebuildable DuckDB state
- [ ] Workbook and DuckDB rows, IDs, and totals reconcile
- [ ] Centralized parameterized SQL returns provider-independent result models
- [ ] Every required July/August metric and approved segment is exactly reproducible
- [ ] Results distinguish fact, association, possible contribution, and unsupported causation
- [ ] Zero denominators and empty results retain explicit semantics
- [ ] Deterministic repeated analysis and database rebuilds are identical
- [ ] The complete deterministic suite and all final repository checks pass
- [ ] One local Gate 6 implementation commit contains only approved Gate 6 work
- [ ] Gate 6 remains pending owner review and is not pushed without explicit authorization
- [ ] Gate 7 has not started

## Explicit exclusions

- OpenAI calls, Pinecone queries, or vector-index changes
- RAG or policy-retrieval integration and combined analytics-plus-policy answers
- LLM-written explanations, LLM calculations, and natural-language-to-SQL
- Dashboards, APIs, Streamlit, or another user interface
- Graph databases, GraphRAG, web retrieval, agents, orchestration, or memory
- Real member, employee, organisational, or financial data
- Forecasting, machine learning, anomaly detection, or causal inference
- Pandas, LangChain, LlamaIndex, or a general analytics framework
- Gate 7 work

## Assumptions requiring owner approval

1. Use the July and August 2026 closed periods and GBP amounts shown above.
2. Define PAR30 using the full outstanding balance of loans at least 30 days past due, divided by
   total outstanding balance.
3. Measure contact completion per scheduled action, not per distinct loan.
4. Treat `PARTIAL` and `FAILED` as non-success while reporting hard failures separately.
5. Define the affected cohort from explicit August payment-to-payroll-event links and compare those
   same loans with their July records.
6. Use only product, origination month, risk band, employer group, membership tenure, and affected
   payroll cohort as segmentation dimensions.
7. Use `openpyxl` for strict workbook inspection rather than DuckDB's autoloaded Excel extension;
   use DuckDB only after application validation.
8. Treat equality between the £6,000 August payment shortfall and £6,000 arrears increase as a
   designed association, not a causal or complete accounting roll-forward.
9. Generate deterministic prose from fixed templates and leave any narrative generation or
   combined policy answer to a later, separately approved gate.

Implementation is paused at this checkpoint pending explicit owner approval.
