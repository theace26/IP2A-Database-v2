# UnionCore — UI Enhancement Bundle: Execution Summary
**Spoke:** Spoke 3: Infrastructure
**Source:** Hub Handoff Document (February 10, 2026)
**Total Estimated Effort:** 8–12 hours across 2–3 sessions
**Version Baseline:** v0.9.16-alpha

---

## Instruction Documents

| # | File | Item | Est. Hours |
|---|------|------|-----------|
| 1 | `week43-item1-flatten-sidebar.md` | Flatten Operations sidebar menu | 1–2 |
| 2 | `week43-item3a-developer-role-backend.md` | Developer Super Admin role (backend) | 2–3 |
| 3 | `week44-item3b-view-as-frontend.md` | View As toggle (frontend) | 2–3 |
| 4 | `week44-item4-dashboard-cards.md` | Replace dashboard cards | 2–3 |
| 5 | `week44-item2-sortable-sticky-headers.md` | Sortable + sticky table headers | 3–4 |

---

## Execution Order & Dependencies

```
Item 1: Flatten Sidebar ──────────────────────┐
                                               │
Item 3A: Developer Role Backend ──┐            │
                                  ├─→ Item 4: Dashboard Cards
Item 3B: View As Frontend ────────┘            │
                                               │
Item 2: Sortable Headers ─────────────── (independent, can run in parallel)
```

**Hard dependencies:**
- Item 3B requires Item 3A (backend must exist before frontend)
- Item 4 benefits from Items 1 + 3 (for testing RBAC card visibility with View As)

**Soft dependencies:**
- Item 2 is fully independent — can be started at any time

---

## Suggested Session Plan

### Session 1 (~4–5 hours)
**Focus:** Foundation work

1. ✅ Item 1: Flatten Sidebar (1–2 hrs)
2. ✅ Item 3A: Developer Role Backend (2–3 hrs)

**Commit after each item.** If time remains, start Item 3B.

### Session 2 (~4–5 hours)
**Focus:** Frontend + Dashboard

1. ✅ Item 3B: View As Toggle Frontend (2–3 hrs)
2. ✅ Item 4: Dashboard Cards (2–3 hrs)

### Session 3 (~3–4 hours)
**Focus:** Table improvements

1. ✅ Item 2: Sortable Headers — macro + first table (1–1.5 hrs)
2. ✅ Item 2: Rollout to remaining tables (incrementally)

---

## Pre-Flight (Before Any Session)

Before handing any instruction document to Claude Code:

1. **Provide the current `CLAUDE.md`** so Claude Code knows project state
2. **Run the test suite** and record the baseline count
3. **Confirm the app starts** and you can login
4. **Check git status** is clean and you're on the correct branch

---

## Scope Boundaries (From Hub Handoff)

These are non-negotiable constraints from the Hub:

- ❌ DO NOT change URL routing structure
- ❌ DO NOT create new database models
- ❌ DO NOT implement client-side JavaScript sorting
- ❌ DO NOT add Developer role to production seed data
- ❌ DO NOT refactor the permission system beyond minimal additions
- ❌ DO NOT redesign the dashboard layout beyond the specified card changes

---

## Cross-Spoke Handoff Notes Required

After completing the bundle, generate handoff notes for:

| Recipient | Topic | Why |
|-----------|-------|-----|
| **Hub** | ADR-019 creation (if it doesn't exist) | Developer role needs ADR documentation |
| **Spoke 1** | Developer role + effective_role pattern | New permission checks must include developer |
| **Spoke 2** | Developer role + effective_role pattern | Same as Spoke 1 |
| **All Spokes** | Sortable header pattern | New tables should use the macro |
| **All Spokes** | Dashboard card dependencies | Service changes to LaborRequest/BookRegistration/Certification status fields will break dashboard |

---

## Known Risks & Blockers

| Risk | Mitigation |
|------|-----------|
| Certification model might not exist yet | Stub the Upcoming Expirations card with 0 and TODO comment |
| Session middleware might not be configured | Item 3A instructions include adding SessionMiddleware |
| Navbar height may differ from assumed 64px | Discovery steps require measuring actual height |
| HTMX partial rendering may not be an existing pattern | Item 2 instructions cover creating the pattern from scratch |
| Test accounts for specific roles may not exist | Note gaps, verify with available accounts |

---

*UI Enhancement Bundle — Execution Summary*
*Spoke 3: Infrastructure*
*Created: February 10, 2026*
