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

- [ ] Formalize evidence types
- [ ] Formalize evidence dimensions
- [ ] Make evidence traceable to source
- [ ] Separate file presence from actual implementation evidence
- [ ] Prevent unsupported skill claims
- [ ] Add evidence contract tests


# PHASE 2 — SKILL CONFIDENCE

- [ ] Define exact meaning of confidence
- [ ] Document aggregation formula
- [ ] Test repetition bonus
- [ ] Test saturation behavior
- [ ] Test multi-repository evidence
- [ ] Remove dead aggregation implementation
- [ ] Ensure confidence is not professional level


# PHASE 3 — CAPABILITY CONTRACT

- [ ] Define capability semantics
- [ ] Separate capability from raw skill
- [ ] Remove duplicate capability semantics
- [ ] Add capability evidence explanations
- [ ] Test capability construction
- [ ] Test insufficient evidence cases


# PHASE 4 — A / B CAPABILITY LEVEL

- [ ] Define A-level evidence requirements
- [ ] Define B-level evidence requirements
- [ ] Define UNKNOWN / UNVERIFIED state
- [ ] Create explicit CapabilityLevel model
- [ ] Do not derive A/B from confidence alone
- [ ] Add evidence-based classification
- [ ] Add human verification path
- [ ] Add classification tests


# PHASE 5 — OPPORTUNITY MATCHING

- [ ] Connect capability level to readiness
- [ ] Handle missing capabilities
- [ ] Explain why opportunity matches
- [ ] Explain missing evidence
- [ ] Prevent confidence-only matching
- [ ] Add matching tests


# PHASE 6 — JOB FIT

- [ ] Normalize job requirements
- [ ] Match requirements against verified capabilities
- [ ] Separate job fit from capability level
- [ ] Generate explainable fit reasons
- [ ] Detect unsupported requirements
- [ ] Add false-positive tests


# PHASE 7 — DECISION PERSISTENCE

- [ ] Create stable Decision ID
- [ ] Persist opportunity/job decision
- [ ] Store evidence used for decision
- [ ] Store decision score
- [ ] Store decision reason
- [ ] Make decisions reproducible
- [ ] Add audit trail
- [ ] Add persistence tests


# PHASE 8 — APPLICATION INTELLIGENCE

- [ ] Keep application preparation truthful
- [ ] Remove hard-coded skills
- [ ] Generate application content from verified evidence
- [ ] Separate preparation from submission
- [ ] Correct application states
- [ ] Add application preparation tests


# PHASE 9 — EXECUTION BOUNDARY

- [ ] Preserve OPENED_IN_BROWSER state
- [ ] Preserve PREPARED state
- [ ] Human submission remains explicit
- [ ] Never claim SUBMITTED without external evidence
- [ ] Require external evidence for CONFIRMED
- [ ] Test execution contract


# PHASE 10 — OUTCOME TRACKING

- [ ] Create outcome model
- [ ] Track application outcome
- [ ] Track response
- [ ] Track interview
- [ ] Track rejection
- [ ] Track offer
- [ ] Store external evidence
- [ ] Add outcome persistence tests


# PHASE 11 — FEEDBACK LOOP

- [ ] Analyze successful applications
- [ ] Analyze rejected applications
- [ ] Analyze false-positive matches
- [ ] Analyze missing capabilities
- [ ] Update opportunity matching using evidence
- [ ] Update profile using verified outcomes
- [ ] Preserve auditability


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
