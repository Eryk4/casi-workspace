# Full Client Billing Domain Plan

Last checked: 2026-07-06

This document defines the target direction for the future `Rozliczenia klientow, uczniow, rodzin i platnikow` domain in CASI Workspace. It is an implementation plan and audit, not a migration spec. No tables, endpoints, write actions, or UI changes are introduced by this document.

## 1. Goal

`Rozliczenia` should become a full operational settlement module for service businesses and education businesses. The target module must explain who should pay, for whom, for which service, for which period, what has been paid, what is overdue, what is overpaid, and what requires a human decision.

The module should support:

- business clients and private payers,
- parents as payers,
- children/students as service beneficiaries,
- families as settlement groups,
- siblings and sibling discounts,
- several children under one payer,
- future multi-payer cases for one student if required,
- contact person vs paying person,
- cyclic classes, semester courses, camps, workshops, subscriptions, and one-off services,
- charges, payments, allocations, overpayments, arrears, corrections, reminders, and owner reports.

The module must not become a small `kasa` table. It should be a domain model for operational money flow, family/customer context, and human-controlled settlement decisions.

## 2. Current State

### Current Product Surface

- Canonical route: `/rozliczenia`.
- Legacy route: `/kasa`, redirect only.
- Active screen: `Centrum rozliczen v1`, with read-only payer detail under `/rozliczenia/platnicy/{payerId}`.
- Current screen mode: financial state is read-only. Active billing write paths are narrow and additive: payer notes and payment operational review status.
- Current frontend sources:
  - `GET /api/billing/ledger/balances?organization_id=...`,
  - `GET /api/billing/payers?organization_id=...`,
  - `GET /api/billing/payers/{payerId}/notes?organization_id=...`,
  - `GET /api/billing/students?organization_id=...`,
  - `GET /api/billing/charges?organization_id=...`,
  - `GET /api/invoices?organization_id=...`,
  - `GET /api/contractors?organization_id=...`,
  - `GET /api/work-items?organization_id=...&only_open=1&limit=100`.

The current screen answers a narrow question: what is the visible money/payment/receivable situation for the selected organization, and who currently appears as family/payer/student in the existing billing data. It also allows a narrow additive payer note for human context. It does not yet manage enrollments, full charge lifecycle, payment imports, allocations, reminders, or accounting exports in the active Next UI.

### Current Frontend Model

Files reviewed:

- `frontend/src/modules/billing/BillingPage.tsx`,
- `frontend/src/modules/billing/BillingLedgerOverview.tsx`,
- `frontend/src/modules/billing/billingModel.ts`,
- `frontend/src/app/rozliczenia/page.tsx`,
- `frontend/src/app/kasa/page.tsx`,
- `frontend/scripts/test-billing.js`,
- `frontend/docs/BILLING_CENTER_PRODUCT_NOTE.md`,
- `frontend/docs/NEXT_MODULES_STATUS.md`,
- `frontend/docs/WRITE_ACTIONS_STATUS.md`.

The frontend already has:

- organization-scoped read model for balances,
- derived attention items,
- read-only family/payer/student foundation over existing `billing_payers` and `billing_students`,
- invoice rows,
- contractor rows,
- related Work Item rows,
- recent payment rows,
- read-only payer detail route,
- read-only guardrails,
- technical leakage checks,
- `/kasa` redirect regression.

The frontend does not yet have:

- family detail route as a separate concept, if product scope later requires it,
- payer detail route is now started in Next as read-only `/rozliczenia/platnicy/{payerId}`,
- student detail route,
- enrollment list/detail,
- charge center,
- payment center,
- import workflow,
- allocation workflow,
- arrears/reminders workflow,
- owner settlement reports,
- accounting export workflow.

### Current Backend Billing Tables

Current billing-related tables found in `app/db.py` and migration coverage:

| Table | Current role | Main gap for full domain |
| --- | --- | --- |
| `billing_schools` | School/location reference for education billing. | Too education-specific; not a general service location/provider model. |
| `billing_models` | Pricing/settlement model for school year, lesson day, monthly/semester rates, sibling/large-family discounts. | Mixes service, price plan, period assumptions, and discount policy in one table. |
| `billing_payers` | Current payer/family-like record with phone/payment identifier/contact. | No explicit family entity, payer person role, relationship graph, corporate/private distinction, consent/contact preferences. |
| `billing_students` | Student/beneficiary linked to payer, school, model, group. | No enrollment contract, start/end dates, status lifecycle, multi-payer support, service history. |
| `billing_charge_batches` | Generated charge batch for model/period. | Batch belongs to model, not a richer billing period/rule execution. |
| `billing_charges` | Charge for student/payer/model/period with discounts and status. | No adjustment chain, allocation state, reasoned corrections, invoice linkage as first-class relation. |
| `billing_student_charge_state` | Carries intro/sibling discount state per student/year. | Narrow for current education rules only. |
| `billing_payer_charge_state` | Carries large family discount state per payer/year. | Narrow for current discount rule only. |
| `billing_bank_accounts` | Organization bank accounts. | Good foundation; needs stronger operational permissions before UI writes. |
| `billing_statement_imports` | Imported bank statement batch metadata. | No full review/approval workflow in Next. |
| `billing_transactions` | Imported bank transactions with raw data and match status. | No safe product workflow for unknown payments, partial matches, split allocations, refunds. |
| `billing_payment_matches` | Match transaction to payer and optionally charge. | Needs allocation model that can split one payment across multiple charges/invoices/services. |
| `billing_payer_ledger_entries` | Ledger entries for charges and payment matches. | Needs richer audit/event model, snapshots, explanations, and corrections. |
| `billing_notes` | Additive operator notes attached to a payer. | Good first low-risk write path; later needs edit/delete policy, retention policy, richer audit UI, and possible links to charges/periods. |
| `billing_payment_review_events` | Additive operational status history for visible payment transactions. | Good second low-risk billing write path; intentionally not an allocation, match, balance mutation, reminder, or accounting status. |

These tables are already included in the SQLite to configured DB migration tests. The existing backend is more advanced than the current Next read-only surface, but it is still not the full target domain.

### Current Backend Billing Endpoints

Current billing endpoints found in `app/api/http_server.py`:

Read endpoints:

- `GET /api/billing/ledger/balances`,
- `GET /api/billing/ledger/entries`,
- `GET /api/billing/ledger/matches`,
- `GET /api/billing/bank-accounts`,
- `GET /api/billing/transactions`,
- `GET /api/billing/schools`,
- `GET /api/billing/models`,
- `GET /api/billing/payers`,
- `GET /api/billing/payers/{payerId}/notes`,
- `GET /api/billing/students`,
- `GET /api/billing/charges`,
- `GET /api/billing/payments/{paymentId}/review-status`.

Write endpoints exist in the backend but are not exposed as active Next write actions:

- `POST /api/billing/bank-accounts`,
- `POST /api/billing/schools`,
- `POST /api/billing/models`,
- `POST /api/billing/payers`,
- `POST /api/billing/payers/{payerId}/notes`,
- `POST /api/billing/students`,
- `POST /api/billing/charges/generate`,
- `POST /api/billing/statements/import-csv`,
- `POST /api/billing/ledger/matches`,
- `POST /api/billing/payments/{paymentId}/review-status`.

`POST /api/billing/payers/{payerId}/notes` is the first promoted billing write path. It is intentionally additive, accepts only `{ note_text }`, requires `organization_id`, and must not change balances, charges, payments, matches, reminders, or accounting state. Other write endpoints should not be promoted into the active frontend until separate endpoint-specific UX, permissions, payload allowlist, tenant-isolation, audit, and live verification work is complete.

`POST /api/billing/payments/{paymentId}/review-status` is the second promoted billing write path. It accepts only `{ status, note_text? }`, requires `organization_id`, writes an append-only record to `billing_payment_review_events`, and must not change `billing_transactions`, `billing_charges`, `billing_payment_matches`, `billing_payer_ledger_entries`, balances, imports, reminders, or accounting state. It is an operational marker, not a payment allocation workflow.

### Current Services And Repositories

Current backend services/repositories:

- `app/services/billing_service.py`,
- `app/services/billing_ledger_service.py`,
- `app/repositories/billing_repository.py`,
- `app/repositories/billing_ledger_repository.py`.

Current capabilities include:

- creating schools,
- creating billing models,
- creating payers,
- creating students,
- generating charges from a model,
- carrying intro/sibling/large-family discounts through current state tables,
- importing CSV statements,
- auto-matching transactions by phone/payment identifier,
- manual match service logic,
- recording payer ledger entries,
- listing balances, ledger entries, and matches.

### Current Sandbox Data

`app/demo_seed.py` currently seeds billing data for the local sandbox, especially for `Misja Robotyka`:

- schools,
- billing models,
- payers/families,
- students,
- charge batches,
- bank accounts,
- statement rows/transactions.

This is useful for product verification, but it is not a production data model guarantee. It should remain safe sandbox data.

### Current Test Coverage

Relevant tests found:

- `tests/test_billing_schools.py`,
- `tests/test_billing_models.py`,
- `tests/test_billing_customers.py`,
- `tests/test_billing_charges.py`,
- `tests/test_billing_import.py`,
- `tests/test_demo_seed.py`,
- `tests/test_sqlite_to_configured_db_migrator.py`,
- `frontend/scripts/test-billing.js`.

Coverage already validates important concepts such as school/model creation, payer/student creation, family payment visibility for siblings, charge generation, discounts, import behavior, latest family payment, and migration inclusion.

## 3. Gap Against The Target Module

The current state is a useful foundation, but it lacks several domain boundaries required for a durable settlement module.

Key gaps:

- `billing_payers` currently acts partly like family, payer, and contact in one table.
- `billing_students` links directly to payer/model, but there is no explicit family membership or service enrollment contract.
- `billing_models` mixes service definition, pricing plan, discount configuration, and school-year assumptions.
- There is no general `service_contract` or `service_enrollment` lifecycle with start/end/status.
- There is no first-class `family` entity.
- There is no first-class `payer` role independent from family or contractor.
- There is no explicit support for several payers per student.
- Payment allocation is narrower than the target model; it can match transaction to payer/charge, but not model complex splits, refunds, unapplied cash, or multi-child allocations as a first-class workflow.
- Adjustments are not first-class; current charge values store discounts, but manual corrections and owner decisions need their own auditable model.
- Reminders and communication history are not modeled as human-approved settlement workflow.
- Reports for owner-level revenue, arrears, overpayments, risk, and cash forecast are not formalized.
- Accounting export is not modeled as a controlled export artifact.
- Active Next UI intentionally exposes none of the billing writes.

## 4. Target Domain Model

The following model should be treated as the target direction, not an immediate migration list.

### Core Parties

#### `billing_party`

A normalized party record for any person or organization participating in settlements.

Suggested fields:

- `billing_party_id`,
- `organization_id`,
- `party_type`: `private_person`, `company`, `family_group`, `school`, `other`,
- `display_name`,
- `legal_name`,
- `tax_id`,
- `email`,
- `phone`,
- `address_json`,
- `contractor_id` nullable for CRM linkage,
- `is_active`,
- `created_at`, `updated_at`.

Purpose: avoid forcing parent, family, student, and company into one payer table.

#### `family`

A settlement household/group.

Suggested fields:

- `family_id`,
- `organization_id`,
- `family_name`,
- `primary_payer_party_id`,
- `default_contact_party_id`,
- `notes`,
- `is_active`,
- `created_at`, `updated_at`.

Purpose: support siblings, shared balances, and family-level view.

#### `family_member`

Links parties and students to a family.

Suggested fields:

- `family_member_id`,
- `organization_id`,
- `family_id`,
- `party_id` nullable,
- `student_id` nullable,
- `relationship_type`: `parent`, `guardian`, `student`, `payer`, `contact`,
- `is_primary_contact`,
- `is_primary_payer`,
- `valid_from`, `valid_to`,
- `created_at`, `updated_at`.

Purpose: support parent vs payer vs contact without duplicating people.

#### `student`

Beneficiary of classes/services.

Suggested fields:

- `student_id`,
- `organization_id`,
- `family_id` nullable,
- `display_name`,
- `birth_date` nullable,
- `school_id` nullable,
- `notes`,
- `is_active`,
- `created_at`, `updated_at`.

Purpose: keep student as a beneficiary, not a payer.

#### `payer_account`

Settlement account for who is responsible for payment.

Suggested fields:

- `payer_account_id`,
- `organization_id`,
- `party_id` nullable,
- `family_id` nullable,
- `contractor_id` nullable,
- `account_kind`: `family`, `private_payer`, `company`, `internal`,
- `payment_identifier`,
- `default_currency`,
- `is_active`,
- `created_at`, `updated_at`.

Purpose: separate payer account from family and CRM contractor.

### Services, Enrollments, Pricing

#### `service_catalog_item`

Defines what can be sold or billed.

Suggested fields:

- `service_catalog_item_id`,
- `organization_id`,
- `name`,
- `service_type`: `cyclic_class`, `semester_course`, `camp`, `workshop`, `subscription`, `one_off`, `consulting`,
- `default_duration`,
- `default_tax_profile` nullable,
- `is_active`,
- `created_at`, `updated_at`.

#### `service_contract`

Agreement with a payer/family/company.

Suggested fields:

- `service_contract_id`,
- `organization_id`,
- `payer_account_id`,
- `family_id` nullable,
- `contractor_id` nullable,
- `contract_number`,
- `status`: `draft`, `active`, `ended`, `terminated`, `suspended`,
- `start_date`, `end_date`,
- `notice_period_days`,
- `notes`,
- `created_at`, `updated_at`.

#### `service_enrollment`

Assigns a student/client to a service under a contract.

Suggested fields:

- `service_enrollment_id`,
- `organization_id`,
- `service_contract_id`,
- `service_catalog_item_id`,
- `student_id` nullable,
- `contractor_id` nullable,
- `payer_account_id`,
- `pricing_plan_id`,
- `status`: `active`, `ended`, `terminated`, `suspended`,
- `start_date`, `end_date`,
- `group_name`,
- `notes`,
- `created_at`, `updated_at`.

#### `pricing_plan`

Separates price rules from service identity.

Suggested fields:

- `pricing_plan_id`,
- `organization_id`,
- `service_catalog_item_id`,
- `name`,
- `billing_frequency`: `monthly`, `semester`, `annual`, `per_turnus`, `one_off`, `custom`,
- `base_amount`,
- `currency`,
- `period_unit`,
- `valid_from`, `valid_to`,
- `is_active`,
- `created_at`, `updated_at`.

#### `discount_rule`

Rules that can apply to an enrollment or payer account.

Suggested fields:

- `discount_rule_id`,
- `organization_id`,
- `pricing_plan_id` nullable,
- `discount_type`: `sibling`, `next_year`, `large_family`, `intro`, `manual`, `loyalty`,
- `amount_type`: `fixed`, `percent`,
- `amount_value`,
- `max_uses`,
- `priority`,
- `conditions_json`,
- `is_active`,
- `created_at`, `updated_at`.

### Charges, Payments, Balances

#### `billing_period`

A stable period object for monthly/semester/year/custom billing.

Suggested fields:

- `billing_period_id`,
- `organization_id`,
- `period_type`,
- `label`,
- `date_from`, `date_to`,
- `due_date`,
- `is_closed`,
- `created_at`, `updated_at`.

#### `billing_charge`

What should be paid.

Suggested fields:

- `billing_charge_id`,
- `organization_id`,
- `billing_period_id`,
- `payer_account_id`,
- `family_id` nullable,
- `student_id` nullable,
- `service_enrollment_id` nullable,
- `invoice_id` nullable,
- `source_kind`: `enrollment`, `manual`, `invoice`, `adjustment`,
- `base_amount`,
- `discount_amount`,
- `adjustment_amount`,
- `total_amount`,
- `currency`,
- `status`: `draft`, `open`, `partially_paid`, `paid`, `cancelled`, `corrected`,
- `due_date`,
- `reason`,
- `created_at`, `updated_at`.

#### `payment`

A received or manually entered payment.

Suggested fields:

- `payment_id`,
- `organization_id`,
- `payer_account_id` nullable,
- `billing_transaction_id` nullable,
- `amount`,
- `currency`,
- `payment_date`,
- `source_type`: `manual`, `bank_import`, `cash`, `card`, `other`,
- `counterparty_name`,
- `title`,
- `reference`,
- `status`: `unmatched`, `partially_allocated`, `allocated`, `refunded`, `ignored`,
- `created_by_user_id`,
- `created_at`, `updated_at`.

#### `payment_allocation`

How a payment is applied.

Suggested fields:

- `payment_allocation_id`,
- `organization_id`,
- `payment_id`,
- `billing_charge_id` nullable,
- `invoice_id` nullable,
- `service_enrollment_id` nullable,
- `payer_account_id`,
- `allocated_amount`,
- `allocation_reason`,
- `allocated_by_user_id`,
- `allocated_at`,
- `created_at`.

#### `account_balance_snapshot`

Materialized snapshot for fast read models.

Suggested fields:

- `account_balance_snapshot_id`,
- `organization_id`,
- `payer_account_id`,
- `family_id` nullable,
- `student_id` nullable,
- `billing_period_id` nullable,
- `total_charges`,
- `total_allocations`,
- `balance_due`,
- `overpayment_amount`,
- `as_of`,
- `created_at`.

#### `billing_adjustment`

Auditable correction or owner decision.

Suggested fields:

- `billing_adjustment_id`,
- `organization_id`,
- `billing_charge_id` nullable,
- `payer_account_id`,
- `adjustment_type`: `discount`, `correction`, `waiver`, `refund`, `manual_decision`,
- `amount_delta`,
- `reason`,
- `approved_by_user_id`,
- `created_by_user_id`,
- `created_at`.

### Communication, Reporting, Audit

#### `payment_reminder`

Human-controlled reminder record.

Suggested fields:

- `payment_reminder_id`,
- `organization_id`,
- `payer_account_id`,
- `family_id` nullable,
- `billing_charge_id` nullable,
- `channel`: `sms`, `email`, `phone`, `manual`,
- `status`: `draft`, `approved`, `sent`, `cancelled`, `failed`,
- `message_text`,
- `approved_by_user_id`,
- `sent_at`,
- `created_at`, `updated_at`.

#### `billing_note`

Internal note for a payer/family/student/charge/payment.

Suggested fields:

- `billing_note_id`,
- `organization_id`,
- `payer_account_id` nullable,
- `family_id` nullable,
- `student_id` nullable,
- `billing_charge_id` nullable,
- `payment_id` nullable,
- `note_text`,
- `author_user_id`,
- `created_at`.

#### `billing_audit_event`

Domain-specific audit trail.

Suggested fields:

- `billing_audit_event_id`,
- `organization_id`,
- `entity_type`,
- `entity_id`,
- `event_type`,
- `summary`,
- `details_json`,
- `actor_user_id`,
- `created_at`.

## 5. Target Relationships

- Parent/payer party -> family through `family_member` and/or `payer_account`.
- Family -> students through `family_member` or direct `student.family_id`.
- Student -> enrollments through `service_enrollment`.
- Service -> pricing through `pricing_plan`.
- Pricing/discount rules -> charges through charge generation details and adjustment records.
- Payment -> allocations through `payment_allocation`.
- Allocation -> charge/invoice/service through nullable references with strict validation.
- Invoice -> contractor/payer through existing `contractor_id` plus future `payer_account_id` relation.
- Balance -> payer/family/student through snapshots and ledger events.
- Work Item -> arrears/payment/invoice/family through typed metadata or future relation table.

Important invariant: every relation must carry `organization_id` or be resolved through an organization-scoped parent. Cross-organization allocations, charges, family links, and payment matches must be impossible at repository/service level, not only hidden in UI.

## 6. Business Rules To Support

### Pricing And Enrollment

- Monthly payment should generate charges per period and due date.
- Semester payment should either generate one semester charge or a documented installment plan.
- Annual payment should support one annual charge, installments, or prepayment depending on product decision.
- One-off services should generate one charge tied to a service occurrence or contract.
- Enrollment status must affect charge generation: active generates, suspended may pause, terminated respects notice period, ended stops.
- Mid-period start/end must support prorated charges when configured.

### Discounts

- Sibling discount should be calculated from family context and ordering/eligibility, not only manual student order.
- Next-year discount should be explicit and auditable.
- Large-family or owner-approved discounts should have rule source and remaining usage if limited.
- Individual price should be modeled as pricing override or adjustment, not hidden in notes.
- Manual correction should create an adjustment record with reason and actor.

### Payments And Allocations

- One transfer may pay for several children.
- One transfer may pay multiple periods.
- One payment may be partially allocated.
- One charge may be paid by several payments.
- Unknown transfer should stay unmatched until reviewed.
- Overpayment should remain available as unapplied balance or be refunded/transferred by explicit decision.
- Underpayment should leave residual arrears.
- Payment with wrong amount should produce a clear explanation, not silently mark paid.
- Refunds should be explicit negative payment/allocation or adjustment flow with audit.

### Arrears And Communication

- Arrears need amount, due date, age, service/student/family context, and last reminder status.
- Reminder drafts may be generated, but sending should require human approval unless a future plan explicitly allows automation.
- Reminder history must record channel, content, approver, sender, and result.
- No automatic debt collection should run without explicit product and legal review.

### Owner Decisions

- Owner decisions should be first-class events for waivers, exceptions, price corrections, payment reinterpretation, and reminder suppression.
- The system should explain every balance in business terms: charges minus allocations plus adjustments.

## 7. Implementation Stages

Do not implement this as one large rewrite. Recommended stages:

### Stage 1: Read-only family/payer/student foundation

Status: implemented as a compatibility read model in `/rozliczenia`.

The implemented stage reuses current `billing_payers` as family/payer/settlement account records and current `billing_students` as student beneficiaries linked to a payer. It adds the read-only section `Rodziny, uczniowie i płatnicy` in the active Next screen. It also separates company clients from family/student settlement accounts so a company contractor is not presented as a family.

No tables, migrations, write actions, payment imports, charge generation, reminders, or detail routes were added for this stage.

Goal: introduce or expose a minimal relationship model for families, payers, students, and current payer/student data.

Scope:

- no payments,
- no new charge generation,
- no imports,
- no write actions in Next,
- read-only foundation in `/rozliczenia` or linked detail views,
- sandbox data for at least two organizations.

Why first: current `billing_payers` and `billing_students` already exist, but the product needs a clearer family/payer/student language before adding money workflows.

### Stage 2: Read-only charges and balances

Status: implemented as a read-only balance explanation in `/rozliczenia`.

The implemented stage adds the section `Skąd wynika saldo`. It explains current balance from existing ledger summaries and current `billing_charges`: charged amount, paid amount, difference, overpayment or amount still due, last visible payment, and the most important charge rows. It does not generate charges, edit charges, import bank statements, match payments, send reminders, or perform accounting operations.

Goal: expose charges, periods, current balance explanation, and charge-to-student/payer context.

Scope:

- read-only charge list,
- read-only payer/family balance explanation,
- links from `/rozliczenia` to payer/student/family contexts,
- no generation button yet.

### Stage 2b: Services and enrollments read-only foundation

Status: implemented as a compatibility read model in `/rozliczenia` and `/rozliczenia/platnicy/{payerId}`.

The implemented stage adds `Usługi i zapisy` in the billing center and makes `Usługi do opłacenia` more explicit in payer detail. It reuses current `billing_models`, `billing_students`, `billing_charges`, invoices, and contractors. It shows service name, service type, payer, beneficiary, period, inferred enrollment status, charge count, and whether the row is inferred from charges or invoices.

No tables, migrations, routes, write actions, payment imports, charge generation, reminders, service creation, enrollment editing, or pricing changes were added for this stage.

Important limitation: this is not the target service/enrollment contract. Current data can explain what the payer appears to pay for, but it does not yet store full service catalog items, contracts, enrollment lifecycle, start/end dates, status history, or price rules.

Goal: answer "what is this payer paying for?" before adding payment and allocation workflows.

Scope:

- read-only service/enrollment rows inferred from existing charges and invoices,
- payer detail service rows with people, periods, status, amount, and charge count,
- company client service context without students,
- no new service or enrollment routes.

### Stage 2c: Billing period read-only view

Status: implemented as a read-only period view under `/rozliczenia/okresy`.

The implemented stage reuses current `billing_charges.period_label` and `billing_payment_matches` linked to charges. It shows available periods, selected period summary, payer rows, people covered by each payer, services in the period, visible matched payments, amount due, overpayment, settled rows, and attention items.

No tables, migrations, backend endpoints, write actions, payment imports, payment matching workflow, charge generation, reminders, exports, or period closing were added for this stage.

Important limitation: this is not the target `billing_period` domain object. Current data can explain visible settlements for a period, but it does not yet store formal period lifecycle, opening/closing state, carry-forward rules, accounting locks, or full allocation history.

Payment limitation: the read-only period view only counts payments when the payment match points to a concrete charge. Matches visible at payer level but not linked to a charge are intentionally not assigned to a period. A missing overpayment or settled row in the period view does not prove that the payer has no payments globally. Full period settlement needs a later `payment_allocation` model or an equivalent charge/payment allocation contract.

Goal: answer "what happened in this billing period?" before adding payment and allocation workflows.

Scope:

- read-only period list inferred from existing charges,
- read-only selected period summary,
- payer rows with charge/payment/balance explanation,
- service rows for the selected period,
- attention items for due and overpaid payers,
- no inferred period payment from payer-level matches without charge relation,
- no period write actions or closing workflow.

### Stage 2d: Payments and allocations read-only foundation

Status: implemented as a read-only payments/allocation view under `/rozliczenia/wplaty`.

The implemented stage reuses current `billing_transactions`, `billing_payment_matches`, `billing_charges`, `billing_payers`, and `billing_students`. It shows visible incoming payments and separates them into payments linked to a concrete charge, payments visible only at payer level, and payments that need later clarification.

No tables, migrations, backend endpoints, write actions, payment imports, allocation writes, charge generation, reminders, exports, or accounting operations were added for this stage.

Important limitation: this is not the target `payment_allocation` workflow. Current data can explain whether an existing payment match points to a charge or only to a payer, but it cannot yet model full splits, refunds, unapplied cash decisions, review state, or user-confirmed allocations as a first-class process.

Goal: answer "where do visible payments currently sit?" before adding payment imports, manual allocation, or automated matching.

Scope:

- read-only visible payment list,
- read-only distinction between charge-linked, payer-only, and unclear payments,
- links from known payers to `/rozliczenia/platnicy/{payerId}`,
- no import,
- no matching,
- no assignment edits,
- no accounting or period closing.

### Stage 3: Manual payments and allocations

Goal: safely add payment write paths without confusing operational review with financial allocation.

Scope:

- current first step: payment operational review status on `/rozliczenia/wplaty/{paymentId}`,
- status is append-only and does not change balances, matches, charges, transactions, ledger entries, imports, reminders, or accounting state,
- add manual payment only after endpoint audit,
- allocation must be explicit,
- success only after backend confirmation,
- tenant isolation and payload allowlist mandatory,
- no bank import yet.

### Stage 4: Bank statement import

Goal: controlled import of bank transactions.

Scope:

- upload/import review state,
- no automatic final posting without review,
- duplicate import protection,
- raw bank data redaction in UI.

### Stage 5: Payment matching

Goal: split and match payments to charges/invoices/services.

Scope:

- suggested matches can exist,
- user confirms allocations,
- support partial allocations,
- explain unmatched/overpaid/underpaid states.

### Stage 6: Reminders and human-controlled communication

Goal: help contact payers about arrears.

Scope:

- reminder drafts,
- approval before send,
- communication history,
- no fully automated debt collection by default.

### Stage 7: Owner reports

Goal: decision-grade reporting.

Scope:

- monthly revenue,
- arrears,
- overpayments,
- active families/students/clients,
- service revenue,
- risk list,
- cash forecast.

### Stage 8: Accounting export

Goal: controlled export, not replacing accounting software.

Scope:

- export packages,
- audit trail,
- accountant comments,
- separation from KSeF/OCR workflows unless explicitly designed.

## 8. Future Screens

Potential target routes:

- `/rozliczenia` - executive settlement center and triage.
- `/rozliczenia/rodziny` - family list with balance, children, payer, arrears status.
- `/rozliczenia/rodziny/{familyId}` - family settlement center.
- `/rozliczenia/platnicy/{payerId}` - payer account center.
- `/rozliczenia/uczniowie/{studentId}` - student settlement/enrollment context.
- `/rozliczenia/naliczenia` - charges by period/service/status.
- `/rozliczenia/platnosci` - payments and allocation status.
- `/rozliczenia/importy` - bank import batches and review queue.
- `/rozliczenia/zaleglosci` - arrears queue with reminder state.
- `/rozliczenia/nadplaty` - overpayment queue.
- `/rozliczenia/raporty` - owner reports.

These routes should not be added until their data contracts and product scope are agreed.

## 9. Risks

High-risk areas:

- promoting existing backend billing write endpoints into Next without product UX and payload hardening,
- treating `billing_payers` as both family and payer forever,
- adding payment import before allocation/review rules are clear,
- silently auto-matching wrong payments by phone/title,
- exposing raw bank data or storage-like technical fields,
- generating charges without reversible audit/adjustment model,
- sending reminders without human approval,
- building accounting export before source data is explainable,
- trying to retrofit multi-payer/family/sibling logic after money workflows are already public.

## 10. Do Not Do Too Early

Do not implement yet:

- bank import UI,
- automatic payment matching UI,
- charge generation button,
- reminder sending,
- accounting export,
- broad payment edit/delete,
- automatic debt collection,
- hidden AI decisions,
- cross-module writes from `/rozliczenia`,
- full migration to the target schema in one step.

## 11. Recommended First Implementation Step

Recommended next implementation step:

`Read-only charge list / payer context detail`

A safe next step should:

- keep financial state in `/rozliczenia` read-only; payer notes are the only narrow additive billing write,
- expose a clearer charge list or payer-context view only if current endpoints are sufficient,
- keep explaining balance in business language: payer, student, service/model, period, charge, payment match,
- avoid payment writes, allocation writes, imports, reminders, and exports,
- add model tests for charge-to-family/student mapping,
- keep the compatibility family/payer/student model stable until a dedicated schema migration is explicitly planned.

Before any schema change, decide whether current `billing_payers` and `billing_students` can continue as a compatibility layer for another read-only stage, or whether introducing target tables (`family`, `billing_party`, `payer_account`, `student`) is worth the migration cost.

### Stage 2e: Payment detail read-only view

Status: implemented as a read-only payment detail view under `/rozliczenia/wplaty/{paymentId}`.

The implemented stage treats `paymentId` as the current `billing_transactions.billing_transaction_id` and composes the detail from existing read-only sources: transactions, payment matches, charges, payers, and students. The UI does not expose this technical ID as a business payment number.

The view explains whether a visible payment is linked to a concrete charge, only visible at payer level, or still requires clarification. It does not import bank statements, create payments, allocate payments, edit matches, post accounting entries, change balances, send reminders, or add notes.

This remains a foundation before a future first-class `payment_allocation` model and before any manual or automatic payment matching workflow.

### Stage 2f: Debts and overpayments read-only decision center

Status: implemented in Next under `/rozliczenia/zaleglosci`.

This stage aggregates existing payer balances, charges, payment matches, transactions, students, and payer notes into a read-only decision screen. It separates payers with amount due, payers with overpayment, and cases requiring clarification.

No backend endpoints, migrations, payment writes, allocation writes, reminder workflow, overpayment settlement, accounting export, or automation were added.

Important limitation: this is not a debt collection workflow and not an overpayment settlement workflow. The view only shows current data and links to payer, payment, and period views. Payer-level payments without charge relation remain clarification signals rather than inferred period allocations.
