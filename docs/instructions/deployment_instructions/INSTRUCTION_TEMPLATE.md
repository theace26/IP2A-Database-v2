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

## 📝 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session.

### Before Ending This Session:

1. **Scan `/docs/*`** - Review all documentation files
2. **Update existing docs** - Reflect changes, progress, and decisions
3. **Create new docs** - If needed for new components or concepts
4. **ADR Review** - Update or create Architecture Decision Records as necessary
5. **Session log entry** - Record what was accomplished

This ensures historical record-keeping and project continuity ("bus factor" protection).
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

## 📝 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session.

### Before Ending This Session:

1. **Scan `/docs/*`** - Review all documentation files
2. **Update existing docs** - Reflect changes, progress, and decisions
3. **Create new docs** - If needed for new components or concepts
4. **ADR Review** - Update or create Architecture Decision Records as necessary
5. **Session log entry** - Record what was accomplished

This ensures historical record-keeping and project continuity ("bus factor" protection).
```

---

## Why This Matters

1. **Continuity** - Next session (or next developer) knows exactly where things stand
2. **Compliance** - Audit trail of development decisions (meta!)
3. **Demo-ready** - Documentation reflects actual state for leadership
4. **Professionalism** - Shows this is a serious, well-managed project

---

*Template Version: 1.0 - January 2026*
