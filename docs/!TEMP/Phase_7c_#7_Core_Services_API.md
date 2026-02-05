# SUB-PHASE 7c: CORE SERVICES + API

**Status:** Stub — Waiting on 7b
**Estimated Effort:** 25-35 hours
**Prerequisites:** 7b complete — Schema locked, migrations applied
**Spoke:** Spoke 2 (Operations)
**Parent:** [Phase 7 Framework](Phase_7_Subphase_Instruction_Framework.md)

---

## Objective

Implement all 7 services and 5 API routers for the dispatch/referral system. Encode all 14 business rules as service-layer logic.

## Note: Existing Implementation

Weeks 22-25 already built 7 services and 5 routers (~51 endpoints). This sub-phase VALIDATES and REFINES those implementations against the locked schema from 7b.

### Services to Validate/Refine

| Service | File | Endpoints | Key Business Rules |
|---------|------|-----------|-------------------|
| ReferralBookService | `src/services/referral_book_service.py` | Book CRUD, catalog queries | Rule 2 (processing order) |
| BookRegistrationService | `src/services/book_registration_service.py` | Register, re-sign, queue | Rules 5, 6, 7 |
| LaborRequestService | `src/services/labor_request_service.py` | Create, fill, cancel | Rules 3, 4 |
| JobBidService | `src/services/job_bid_service.py` | Time-gated bidding | Rule 8 |
| DispatchService | `src/services/dispatch_service.py` | Dispatch, accept, reject | Rules 9, 10, 11, 12 |
| QueueService | `src/services/queue_service.py` | Processing order, morning sort | Rule 2 |
| EnforcementService | `src/services/enforcement_service.py` | Check marks, exemptions, blackouts | Rules 10, 11, 12, 13, 14 |

### API Routers to Validate/Refine

| Router | File | Endpoints |
|--------|------|-----------|
| referral_books_api | `src/routers/referral_books_api.py` | ~10 |
| registration_api | `src/routers/registration_api.py` | ~10 |
| labor_request_api | `src/routers/labor_request_api.py` | ~9 |
| job_bid_api | `src/routers/job_bid_api.py` | ~8 |
| dispatch_api | `src/routers/dispatch_api.py` | ~14 |

## Input

- Locked schema from 7b
- Priority 1 data analysis from 7a
- 14 business rules (documented in Spoke 2 project instructions)
- Existing service and router code from Weeks 22-25

## Expected Output

- Validated/refined services with full business rule coverage
- Updated API routers with correct request/response schemas
- Comprehensive test suite for each service
- API documentation (docstrings on every endpoint)

## Acceptance Criteria

- [ ] All 14 business rules have corresponding service methods
- [ ] All services have comprehensive test coverage
- [ ] All API endpoints return correct response schemas
- [ ] Audit logging active on all state-changing endpoints
- [ ] Error handling for all business rule violations
- [ ] CLAUDE.md, CHANGELOG.md updated

## ⚠️ NOT YET READY — Waiting on 7b (schema finalization)

---

*Created: February 5, 2026 — Spoke 2*
