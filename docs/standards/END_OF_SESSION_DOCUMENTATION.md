# End-of-Session Documentation Standards

> **Document Created:** February 3, 2026
> **Last Updated:** February 3, 2026
> **Version:** 1.0
> **Status:** Active — Mandatory for All Development Sessions
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1–19)

---

## Purpose

This document defines the mandatory end-of-session documentation requirements for the IP2A Database v2 (UnionCore) project. Following these standards ensures:

1. **Historical Record-Keeping** — Every development session is documented for future reference
2. **Project Continuity** — Knowledge isn't lost when switching contexts or developers
3. **"Bus Factor" Protection** — The project can continue even if key contributors are unavailable
4. **Compliance** — NLRA 7-year audit requirements are met through comprehensive documentation

---

## The Rule

> **MANDATORY**: Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.

---

## Checklist

Before ending any development session, complete the following:

### 1. Code Documentation

- [ ] New functions/methods have docstrings
- [ ] Complex logic has inline comments
- [ ] Type hints are present on new code
- [ ] README files updated if new components added

### 2. Core Project Files

- [ ] `/CHANGELOG.md` — Add entries for significant changes
- [ ] `/CLAUDE.md` — Update current state if major progress made
- [ ] Version bump if milestone reached

### 3. Documentation Updates

- [ ] `/docs/IP2A_MILESTONE_CHECKLIST.md` — Update task status
- [ ] `/docs/IP2A_BACKEND_ROADMAP.md` — Update if phase progress
- [ ] Relevant architecture docs in `/docs/architecture/`
- [ ] Phase-specific docs (e.g., `/docs/phase7/` for Phase 7 work)

### 4. Architecture Decision Records

- [ ] Create new ADR if architectural decision was made
- [ ] Update existing ADR if implementation status changed
- [ ] Update `/docs/decisions/README.md` index if ADR added

### 5. Session Log

- [ ] Create session log in `/docs/reports/session-logs/YYYY-MM-DD-*.md`
- [ ] Include: date, focus area, tasks completed, blockers, next steps

### 6. Test Documentation

- [ ] New tests documented in CHANGELOG
- [ ] Test count updated in CLAUDE.md if significant change
- [ ] Test strategies documented if new patterns introduced

---

## Session Log Template

Create a new file at `/docs/reports/session-logs/YYYY-MM-DD-session-name.md`:

```markdown
# Session Log: [Session Name]

> **Date:** YYYY-MM-DD
> **Duration:** X hours
> **Phase/Week:** Phase X / Week Y
> **Version:** vX.Y.Z-alpha

---

## Objectives

- Primary goal
- Secondary goal (if any)

---

## Work Completed

1. **Task 1**: Description
   - Files created/modified
   - Tests added

2. **Task 2**: Description
   - Files created/modified
   - Tests added

---

## Decisions Made

- Decision 1: Rationale
- Decision 2: Rationale

---

## Blockers/Issues Encountered

- Issue 1: Resolution or status
- Issue 2: Resolution or status

---

## Next Steps

- [ ] Task for next session
- [ ] Task for next session

---

## Files Changed

```
path/to/file1.py
path/to/file2.html
...
```

---

## Test Results

```
Tests: X passed / Y total
New tests: Z
```
```

---

## When to Create an ADR

Create an Architecture Decision Record when:

1. Choosing a technology (database, framework, library)
2. Defining a significant pattern (authentication, caching)
3. Making schema design decisions
4. Establishing API conventions
5. Setting up infrastructure
6. Implementing security measures

See `/docs/decisions/README.md` for the ADR template and the current index of all 14 ADRs.

---

## Documentation Quality Standards

### Headers

Every documentation file should include a header block:

```markdown
> **Document Created:** YYYY-MM-DD
> **Last Updated:** YYYY-MM-DD
> **Version:** X.Y
> **Status:** Active | Draft | Deprecated
> **Project Version:** vX.Y.Z-alpha
```

### Cross-References

When referring to other documents, use relative paths:

- ✅ Correct: `See [ADR-012](../decisions/ADR-012-audit-logging.md)`
- ❌ Incorrect: `See ADR-012` (no link)

### Implementation Status Tables

Use consistent status indicators:

| Symbol | Meaning |
|--------|---------|
| ✅ Done | Implemented and tested |
| 🔜 In Progress | Currently being worked on |
| ❌ Not Started | Planned but not started |
| ⛔ Blocked | Waiting on dependency |
| N/A | Not applicable |

### Version Footers

Every document should end with version information:

```markdown
*Document Version: X.Y*
*Last Updated: YYYY-MM-DD*
```

---

## Enforcement

This documentation standard is:

1. **Referenced in CLAUDE.md** — The main project context document
2. **Embedded in all instruction documents** — Weekly session instructions and continuity docs
3. **Part of the session workflow** — Listed in session ending checklist
4. **Reviewed during documentation updates** — Checked in batch updates
5. **Included in all standards/guides** — Via the end-of-session rule footer

---

## Related Documents

| Document | Location | Purpose |
|----------|----------|---------|
| CLAUDE.md | `/CLAUDE.md` | Main project context document |
| ADR README | `/docs/decisions/README.md` | Architecture decision index (14 ADRs) |
| Milestone Checklist | `/docs/IP2A_MILESTONE_CHECKLIST.md` | Task tracking |
| Backend Roadmap v3.0 | `/docs/IP2A_BACKEND_ROADMAP.md` | Development plan |
| Session Logs | `/docs/reports/session-logs/` | Historical session records |
| Coding Standards | `/docs/standards/coding-standards.md` | Code conventions |
| Naming Conventions | `/docs/standards/naming-conventions.md` | Naming patterns |

---

*Document Version: 1.0*
*Last Updated: February 3, 2026*
