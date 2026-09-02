# IncomeOS — Architecture TODO

## Goal

Build IncomeOS as an evidence-driven Opportunity Intelligence Platform.

Core pipeline:

GitHub / Project Evidence
        |
        v
Repository Evidence
        |
        v
Skill Evidence
        |
        v
Evidence Confidence
        |
        v
Master Skill Profile
        |
        v
Capability
        |
        v
Capability Level
   +----+----+
   |         |
   A         B
        |
        v
Opportunity Match
        |
        v
Job Fit
        |
        v
Decision
        |
        v
Application Preparation
        |
        v
OPENED_IN_BROWSER / PREPARED
        |
        v
Human Action
        |
        v
External Outcome Evidence
        |
        v
Outcome Tracking
        |
        v
Feedback / Profile Update


# PHASE 0 — BASELINE FREEZE

- [ ] Confirm Python version
- [ ] Confirm pytest version
- [ ] Run complete test suite
- [ ] Inspect git status
- [ ] Inspect current diff
- [ ] Identify intentional vs unrelated changes
- [ ] Do not reset or delete existing work


# PHASE 1 — EVIDENCE CONTRACT

- [x] Formalize evidence types
- [x] Formalize evidence dimensions
- [ ] Make evidence traceable to source
- [ ] Separate file presence from actual implementation evidence
- [ ] Prevent unsupported skill claims
- [ ] Add evidence contract tests


# PHASE 2 — SKILL CONFIDENCE

- [x] Define exact meaning of confidence
- [ ] Document aggregation formula
- [x] Test repetition bonus
- [x] Test saturation behavior
- [x] Test multi-repository evidence
- [x] Remove dead aggregation implementation
- [x] Ensure confidence is not professional level


# PHASE 3 — CAPABILITY CONTRACT

- [x] Define capability semantics
- [x] Separate capability from raw skill
- [ ] Remove duplicate capability semantics
- [x] Add capability evidence explanations
- [x] Test capability construction
- [ ] Test insufficient evidence cases


# PHASE 4 — A / B CAPABILITY LEVEL

- [x] Define A-level evidence requirements
- [x] Define B-level evidence requirements
- [x] Define UNKNOWN / UNVERIFIED state
- [x] Create explicit CapabilityLevel model
- [x] Do not derive A/B from confidence alone
- [x] Add evidence-based classification
- [ ] Add human verification path
- [x] Add classification tests


# PHASE 5 — OPPORTUNITY MATCHING

- [x] Connect capability level to readiness
- [ ] Handle missing capabilities
- [ ] Explain why opportunity matches
- [ ] Explain missing evidence
- [x] Prevent confidence-only matching
- [x] Add matching tests


# PHASE 6 — JOB FIT

- [x] Normalize job requirements
- [x] Match requirements against verified capabilities
- [x] Separate job fit from capability level
- [x] Generate explainable fit reasons
- [x] Detect unsupported requirements
- [x] Add false-positive tests


# PHASE 7 — DECISION PERSISTENCE

- [x] Create stable Decision ID
- [x] Persist opportunity/job decision
- [x] Store evidence used for decision
- [x] Store decision score
- [x] Store decision reason
- [x] Make decisions reproducible
- [x] Add audit trail
- [x] Add persistence tests


# PHASE 8 — APPLICATION INTELLIGENCE

- [x] Keep application preparation truthful
- [x] Remove hard-coded skills
- [ ] Generate application content from verified evidence
- [x] Separate preparation from submission
- [x] Correct application states
- [x] Add application preparation tests


# PHASE 9 — EXECUTION BOUNDARY

- [ ] Preserve OPENED_IN_BROWSER state
- [ ] Preserve PREPARED state
- [ ] Human submission remains explicit
- [ ] Never claim SUBMITTED without external evidence
- [ ] Require external evidence for CONFIRMED
- [ ] Test execution contract


# PHASE 10 — OUTCOME TRACKING

- [x] Create outcome model
- [x] Track application outcome
- [x] Track response
- [x] Track interview
- [x] Track rejection
- [x] Track offer
- [x] Store external evidence
- [x] Add outcome persistence tests


# PHASE 11 — FEEDBACK LOOP

- [x] Analyze successful applications
- [x] Analyze rejected applications
- [ ] Analyze false-positive matches
- [ ] Analyze missing capabilities
- [ ] Update opportunity matching using evidence
- [ ] Update profile using verified outcomes
- [x] Preserve auditability


# PHASE 12 — FINAL AUDIT

- [ ] Full pytest passes
- [ ] No unexplained failures
- [ ] No dead critical code
- [ ] No unsupported capability claims
- [ ] No fake submission states
- [ ] Evidence is traceable
- [ ] Confidence != capability level
- [ ] Capability level != job fit
- [ ] Job fit != application outcome
- [ ] Decisions are persistent
- [ ] Outcomes are externally evidenced
- [ ] Feedback loop is functional
- [ ] Documentation matches implementation
- [ ] Git diff reviewed
- [ ] Security-sensitive files reviewed
- [ ] End-to-end dry run completed


# DEFINITION OF DONE

IncomeOS is considered architecturally complete only when:

1. Every important claim has traceable evidence.
2. Evidence confidence is separate from capability level.
3. Capability level is separate from job fit.
4. Job fit is separate from application outcome.
5. Decisions have stable persistent identities.
6. Application preparation is truthful.
7. Submission is never fabricated.
8. External outcomes have evidence.
9. Outcomes feed back into the system.
10. Existing tests remain green.
11. Documentation and implementation are synchronized.
12. The complete pipeline is auditable end-to-end.
