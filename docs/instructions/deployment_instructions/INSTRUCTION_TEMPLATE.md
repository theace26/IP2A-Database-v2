# Instruction Document Template

**Use this template when creating new instruction documents for Claude Code sessions.**

---

## Standard Header

```markdown
# [Week/Phase] [Topic]: Session [Letter]

**Duration:** X-X hours
**Version:** vX.X.X → vX.X.X
**Goal:** [One sentence description]

---
```

## Standard Sections

1. **Prerequisites** - What must be complete before starting
2. **Tasks** - Numbered implementation steps
3. **Verification** - How to confirm it works
4. **Git Workflow** - Commit, tag, push instructions
5. **Documentation Update** ← REQUIRED (see below)

---

## REQUIRED: Documentation Update Section

**Include this section at the END of EVERY instruction document:**

```markdown
---

## Documentation Update (End of Session)

**CRITICAL:** Before committing, update *ANY* and *ALL* relevant documents to capture progress made this session.

### Scan and Update

1. **Scan `/docs/*`** for any documents that need updates:
   - `/docs/guides/` - Update if workflow changed
   - `/docs/reference/` - Update if API/CLI changed
   - `/docs/architecture/` - Update if design changed
   - `/docs/decisions/` - Create or update ADRs if architectural decisions were made

2. **Required Updates:**
   - [ ] `CHANGELOG.md` - Add entry for this session
   - [ ] `CLAUDE.md` - Update version, test count, current state
   - [ ] `docs/IP2A_MILESTONE_CHECKLIST.md` - Mark tasks complete
   - [ ] Session log in `docs/reports/session-logs/`

3. **ADR Check:**
   - Did you make an architectural decision? → Create/update ADR
   - Did you change an existing pattern? → Update related ADR
   - Did you reject an alternative approach? → Document in ADR

### Documentation Checklist

Before committing:
- [ ] CHANGELOG.md updated
- [ ] CLAUDE.md version and stats current
- [ ] Milestone checklist reflects completed tasks
- [ ] Any new ADRs created (if needed)
- [ ] Session log created
- [ ] Relevant guide/reference docs updated
```

---

## Example: Complete Instruction Document

```markdown
# Phase 6 Week 11: Audit Trail UI - Session A

**Duration:** 2-3 hours
**Version:** v0.7.9 → v0.7.10
**Goal:** Implement audit log viewer with role-based access

---

## Prerequisites

- [ ] v0.7.9 tagged and pushed
- [ ] All 330 tests passing
- [ ] Week 10 complete

---

## Tasks

### 1. Create AuditFrontendService

[implementation details...]

### 2. Create Audit Log Templates

[implementation details...]

### 3. Add Routes

[implementation details...]

---

## Verification

```bash
pytest src/tests/test_audit_ui.py -v
# All new tests should pass

# Manual test
# 1. Login as admin
# 2. Navigate to /admin/audit-logs
# 3. Verify filtering works
```

---

## Git Workflow

```bash
git add -A
git commit -m "feat(audit): add audit log viewer with role filtering

- Add AuditFrontendService with role-based queries
- Add audit log list page with HTMX search
- Add field-level redaction for sensitive data
- Add X new tests"

git push origin develop

# If ready for demo:
git checkout main
git merge develop
git push origin main
git checkout develop
```

---

## Documentation Update (End of Session)

**CRITICAL:** Before committing, update *ANY* and *ALL* relevant documents.

### Scan and Update

1. **Scan `/docs/*`** for documents needing updates
2. **Required Updates:**
   - [ ] `CHANGELOG.md` - Add Week 11 Session A entry
   - [ ] `CLAUDE.md` - Update to v0.7.10, ~345 tests
   - [ ] `docs/IP2A_MILESTONE_CHECKLIST.md` - Mark Session A tasks done
   - [ ] `docs/reports/session-logs/2026-XX-XX-week11-session-a.md` - Create log

3. **ADR Check:**
   - Audit patterns documented in ADR-008? → Verify still accurate
   - New pattern introduced? → Update ADR-008 or create new ADR

### Documentation Checklist

Before committing:
- [ ] CHANGELOG.md updated
- [ ] CLAUDE.md version and stats current
- [ ] Milestone checklist reflects completed tasks
- [ ] Session log created
```

---

## Why This Matters

1. **Continuity** - Next session (or next developer) knows exactly where things stand
2. **Compliance** - Audit trail of development decisions (meta!)
3. **Demo-ready** - Documentation reflects actual state for leadership
4. **Professionalism** - Shows this is a serious, well-managed project

---

*Template Version: 1.0 - January 2026*
