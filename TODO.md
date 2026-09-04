# IncomeOS — REAL-WORLD OUTCOME ARCHITECTURE TODO

> This file is the engineering contract for converting IncomeOS from internal decision output into evidence-backed real-world outcome measurement.
>
> **Rule:** an `[AUTO]` item is checked only when its verification contract passes. `[MANUAL]` items require explicit engineering review.

## Core invariant

> IncomeOS must never claim a real-world state without verifiable evidence.

## Verification protocol

For every milestone:

```text
ARCHITECTURE
    ↓
IMPLEMENTATION
    ↓
UNIT TEST
    ↓
INTEGRATION TEST
    ↓
REAL EXECUTION
    ↓
INVARIANT AUDIT
    ↓
FULL TEST SUITE
    ↓
GIT DIFF REVIEW
    ↓
COMMIT
```

Only after the required checks pass may a milestone be marked `VERIFIED`.

---

# M0 — BASELINE / ARCHITECTURE INVENTORY

- [x] [AUTO] Full test suite passes (`172 passed` baseline) <!-- verify:full_tests -->
- [x] [AUTO] `incomeos` compiles successfully <!-- verify:compile_incomeos -->
- [x] [AUTO] `scripts` compiles successfully <!-- verify:compile_scripts -->
- [x] [AUTO] Repository security regression test passes <!-- verify:security_test -->
- [x] [AUTO] Real job pipeline execution test passes <!-- verify:real_pipeline_test -->
- [ ] [MANUAL] Map current decision, application, evidence, and outcome code
- [ ] [MANUAL] Identify reusable domain models and duplicate/legacy logic
- [ ] [MANUAL] Document current application state transitions
- [ ] [MANUAL] Document current persistence boundaries
- [ ] [MANUAL] Complete architecture inventory

### M0 Exit Criteria

- [ ] [MANUAL] Baseline is reproducible
- [ ] [MANUAL] Existing behavior is documented
- [ ] [MANUAL] No architecture changes are mixed into baseline

**M0 status: IN PROGRESS**

---

# M1 — EVIDENCE / TRUTH FOUNDATION

## Domain

- [ ] [MANUAL] Create `Evidence`
- [ ] [MANUAL] Create `EvidenceSource`
- [ ] [MANUAL] Create `Claim`
- [ ] [MANUAL] Add evidence reference / external reference
- [ ] [MANUAL] Add evidence timestamp
- [ ] [MANUAL] Define evidence integrity rules

## Invariants

- [ ] [MANUAL] Claim cannot be valid without evidence
- [ ] [MANUAL] Evidence source is mandatory
- [ ] [MANUAL] Evidence timestamp is mandatory
- [ ] [MANUAL] Evidence is immutable after creation
- [ ] [MANUAL] Evidence has deterministic identity
- [ ] [MANUAL] Duplicate evidence is handled deterministically
- [ ] [MANUAL] Invalid evidence is rejected

## Tests

- [ ] [MANUAL] Unit tests
- [ ] [MANUAL] Validation tests
- [ ] [MANUAL] Immutability tests
- [ ] [MANUAL] Serialization tests
- [ ] [MANUAL] Persistence tests
- [ ] [MANUAL] Integration tests

### M1 Exit Criteria

- [ ] [MANUAL] All M1 tests pass
- [ ] [MANUAL] Existing full test suite remains green
- [ ] [MANUAL] No existing behavior unintentionally changed
- [ ] [MANUAL] Evidence model can be consumed by Decision and Application domains

**M1 status: NOT STARTED**

---

# M2 — APPLICATION TRUTH STATE MACHINE

## States

- [ ] [MANUAL] `PREPARED`
- [ ] [MANUAL] `OPENED`
- [ ] [MANUAL] `USER_CONFIRMED`
- [ ] [MANUAL] `SUBMITTED`

## Rules

- [ ] [MANUAL] PREPARED → OPENED
- [ ] [MANUAL] OPENED → USER_CONFIRMED
- [ ] [MANUAL] USER_CONFIRMED → SUBMITTED
- [ ] [MANUAL] Invalid transitions are rejected
- [ ] [MANUAL] SUBMITTED requires submission evidence
- [ ] [MANUAL] No automatic fake SUBMITTED state
- [ ] [MANUAL] Every transition creates an auditable event
- [ ] [MANUAL] State can be reconstructed from event history

## Tests

- [ ] [MANUAL] Valid transition tests
- [ ] [MANUAL] Invalid transition tests
- [ ] [MANUAL] Evidence requirement tests
- [ ] [MANUAL] Replay/state reconstruction tests
- [ ] [MANUAL] Persistence tests

### M2 Exit Criteria

- [ ] [MANUAL] Application state is evidence-backed
- [ ] [MANUAL] No unverified SUBMITTED state is possible
- [ ] [MANUAL] Existing application behavior remains truthful

**M2 status: NOT STARTED**

---

# M3 — OUTCOME ENGINE

## Outcome Events

- [ ] [MANUAL] `ACKNOWLEDGED`
- [ ] [MANUAL] `RESPONSE`
- [ ] [MANUAL] `SCREENING`
- [ ] [MANUAL] `INTERVIEW`
- [ ] [MANUAL] `REJECTED`
- [ ] [MANUAL] `OFFER`
- [ ] [MANUAL] `HIRED`
- [ ] [MANUAL] `WITHDRAWN`
- [ ] [MANUAL] `NO_RESPONSE`

## Domain

- [ ] [MANUAL] Create `OutcomeEvent`
- [ ] [MANUAL] Outcome evidence
- [ ] [MANUAL] Outcome source
- [ ] [MANUAL] External reference
- [ ] [MANUAL] Outcome timestamp

## Rules

- [ ] [MANUAL] Outcome references an application
- [ ] [MANUAL] Outcome requires evidence
- [ ] [MANUAL] Outcome chronology is validated
- [ ] [MANUAL] Impossible transitions are rejected
- [ ] [MANUAL] Duplicate events are deterministic
- [ ] [MANUAL] Outcome history is immutable/auditable

## Tests

- [ ] [MANUAL] Outcome creation tests
- [ ] [MANUAL] Evidence validation tests
- [ ] [MANUAL] State transition tests
- [ ] [MANUAL] Duplicate event tests
- [ ] [MANUAL] Historical replay tests

### M3 Exit Criteria

- [ ] [MANUAL] Real application outcomes can be recorded
- [ ] [MANUAL] Outcome history is auditable
- [ ] [MANUAL] No fabricated outcome is possible

**M3 status: NOT STARTED**

---

# M4 — REAL-WORLD MEASUREMENT

## Metrics

- [ ] [MANUAL] Applications submitted
- [ ] [MANUAL] Response rate
- [ ] [MANUAL] Interview rate
- [ ] [MANUAL] Offer rate
- [ ] [MANUAL] Hire rate
- [ ] [MANUAL] Rejection rate
- [ ] [MANUAL] No-response rate
- [ ] [MANUAL] Time-to-response
- [ ] [MANUAL] Time-to-interview
- [ ] [MANUAL] Time-to-offer

## Segmentation

- [ ] [MANUAL] Job source
- [ ] [MANUAL] Company
- [ ] [MANUAL] Job category
- [ ] [MANUAL] Required skills
- [ ] [MANUAL] Capability match
- [ ] [MANUAL] Decision type
- [ ] [MANUAL] Time period

## Rules

- [ ] [MANUAL] Metrics derive only from persisted events
- [ ] [MANUAL] No manually entered summary metrics
- [ ] [MANUAL] Unknown values remain unknown
- [ ] [MANUAL] Insufficient evidence is explicitly reported
- [ ] [MANUAL] Metric calculations are deterministic

### M4 Exit Criteria

- [ ] [MANUAL] IncomeOS reports actual observed outcomes
- [ ] [MANUAL] Every metric is traceable to underlying events
- [ ] [MANUAL] Metrics can be reproduced from database state

**M4 status: NOT STARTED**

---

# M5 — FEEDBACK & LEARNING

## Feedback

- [ ] [MANUAL] Decision → Outcome linkage
- [ ] [MANUAL] Prediction vs actual comparison
- [ ] [MANUAL] Correct decision classification
- [ ] [MANUAL] False positive classification
- [ ] [MANUAL] False negative classification
- [ ] [MANUAL] Unknown / insufficient evidence classification

## Learning metrics

- [ ] [MANUAL] Decision conversion rate
- [ ] [MANUAL] Fit-score calibration
- [ ] [MANUAL] Source conversion performance
- [ ] [MANUAL] Skill/profile conversion performance
- [ ] [MANUAL] Job-category conversion performance
- [ ] [MANUAL] Application strategy performance

## Rules

- [ ] [MANUAL] Learning uses observed outcomes
- [ ] [MANUAL] No unsupported AI-generated conclusions
- [ ] [MANUAL] Small sample sizes are flagged
- [ ] [MANUAL] Historical evidence is retained
- [ ] [MANUAL] Learning calculations are reproducible

### M5 Exit Criteria

- [ ] [MANUAL] IncomeOS compares decisions against real outcomes
- [ ] [MANUAL] IncomeOS identifies what worked and what did not
- [ ] [MANUAL] Future ranking can use empirical evidence

**M5 status: NOT STARTED**

---

# M6 — END-TO-END REAL-WORLD PIPELINE

```text
JOB
 ↓
EVIDENCE
 ↓
CAPABILITY
 ↓
FIT
 ↓
DECISION
 ↓
APPLICATION
 ↓
SUBMISSION EVIDENCE
 ↓
OUTCOME
 ↓
MEASUREMENT
 ↓
FEEDBACK
 ↓
LEARNING
 ↓
NEXT DECISION
```

- [ ] [MANUAL] Real job ingestion
- [ ] [MANUAL] Real capability profile
- [ ] [MANUAL] Decision persistence
- [ ] [MANUAL] Application preparation
- [ ] [MANUAL] Human-confirmed submission
- [ ] [MANUAL] Outcome recording
- [ ] [MANUAL] Metric generation
- [ ] [MANUAL] Feedback generation
- [ ] [MANUAL] Learning calculation

### M6 Exit Criteria

- [ ] [MANUAL] Full pipeline is reproducible
- [ ] [MANUAL] Every real-world claim is evidence-backed
- [ ] [MANUAL] No fake submission/outcome state exists
- [ ] [MANUAL] Actual conversion metrics are measurable
- [ ] [MANUAL] Historical outcome data can improve future decisions

**M6 status: NOT STARTED**

---

# SECURITY / INTEGRITY

- [x] [AUTO] No embedded Telegram credential in tracked source-like files <!-- verify:security_test -->
- [ ] [MANUAL] No fake external submission
- [ ] [MANUAL] No fake outcome generation
- [ ] [MANUAL] No fabricated metrics
- [ ] [MANUAL] No silent state transitions
- [ ] [MANUAL] No destructive history mutation
- [ ] [MANUAL] Audit trail preserved
- [ ] [MANUAL] Sensitive credentials excluded from repository

---

# ENGINEERING RULES

1. One milestone at a time.
2. Code only after architecture is mapped.
3. Every milestone requires tests.
4. Every milestone requires integration verification.
5. Existing tests remain green unless behavior is intentionally changed.
6. No large unverified refactor.
7. No fake real-world state.
8. Unknown must remain unknown.
9. Evidence must precede claims.
10. Commit after every verified milestone.

---

# CURRENT STATUS

- [x] Existing IncomeOS engineering hardening
- [x] 172 automated tests passing
- [x] Security regression test passing
- [x] Real pipeline execution test passing
- [ ] M0 architecture inventory
- [ ] M1 Evidence / Truth Foundation
- [ ] M2 Application Truth State Machine
- [ ] M3 Outcome Engine
- [ ] M4 Real-World Measurement
- [ ] M5 Feedback & Learning
- [ ] M6 End-to-End Real-World Pipeline

## Definition of Done

IncomeOS is `REAL-OUTCOME READY` only when:

```text
Decision ≠ Result

Decision
    ↓
Action
    ↓
Evidence
    ↓
Observed Outcome
    ↓
Measurement
    ↓
Feedback
    ↓
Learning
```

Every real-world result must be traceable to evidence.
