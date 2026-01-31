# UnionCore Development: Master Instruction Document

**Project:** UnionCore (IP2A Database v2)
**Purpose:** Ensure consistent execution of all development sessions
**Last Updated:** January 30, 2026
**Applies To:** ALL instruction documents and development sessions

---

## ⚠️ MANDATORY INSTRUCTIONS - READ BEFORE EVERY SESSION

This document establishes **non-negotiable requirements** for every development session. These instructions take precedence over individual session documents.

---

## 🔴 CRITICAL: Documentation Requirements

### At Session END (MANDATORY - NO EXCEPTIONS)

> **You MUST complete the following before ending ANY session.**

```
┌─────────────────────────────────────────────────────────────────────┐
│  📝 END-OF-SESSION DOCUMENTATION CHECKLIST                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  SCAN all documentation in /app/*                                   │
│                                                                     │
│  UPDATE *ANY* & *ALL* relevant documentation as necessary           │
│  with current progress for the historical record.                   │
│                                                                     │
│  DO NOT FORGET to update:                                           │
│    □ ADRs (Architecture Decision Records) - if decisions made      │
│    □ Roadmap (IP2A_BACKEND_ROADMAP.md) - if milestones changed     │
│    □ Checklist (IP2A_MILESTONE_CHECKLIST.md) - mark tasks done     │
│    □ CLAUDE.md - update current status and version                  │
│    □ CHANGELOG.md - add entry for all changes                       │
│    □ CONTINUITY.md - update handoff context                         │
│    □ Session Log - create in docs/reports/session-logs/             │
│                                                                     │
│  AGAIN: Only update if necessary, but ALWAYS check.                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Documentation Scan Procedure

1. **List all docs**: `find /app/docs -name "*.md" -type f`
2. **Check each category**:
   - `/app/docs/decisions/` - ADRs
   - `/app/docs/reports/session-logs/` - Session logs
   - `/app/docs/guides/` - User guides
   - `/app/docs/instructions/` - Instruction documents
   - `/app/*.md` - Root-level docs (CLAUDE.md, CHANGELOG.md, etc.)

3. **For each document, ask**:
   - Does this session's work affect this document?
   - Is the information still accurate?
   - Should new sections be added?

---

## 🟡 Session Workflow (ALWAYS FOLLOW)

### Pre-Session Checklist

```bash
# 1. ALWAYS work on develop branch (main is frozen for demo)
git checkout develop
git pull origin develop

# 2. Start environment
docker-compose up -d

# 3. Verify tests pass BEFORE making changes
pytest -v --tb=short

# 4. Read the specific instruction document for this session
# 5. Review CLAUDE.md for current project state
```

### During Session

- **Commit incrementally** (small, focused commits)
- **Run tests after significant changes**: `pytest -v`
- **Follow the instruction document tasks in order**
- **Note any blockers or decisions in session log**

### End-Session Checklist

```bash
# 1. Verify ALL tests pass
pytest -v

# 2. Check for uncommitted changes
git status

# 3. Commit with conventional commit message
git add .
git commit -m "feat(module): description of changes"

# 4. Push to develop (NOT main)
git push origin develop

# 5. COMPLETE DOCUMENTATION REQUIREMENTS (see above)
```

---

## 🟢 Code Quality Standards

### Before Committing

```bash
# Format and lint
ruff check . --fix && ruff format .

# Run full test suite
pytest -v

# Check for any TODO/FIXME left in code
grep -r "TODO\|FIXME" src/ --include="*.py"
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Files | snake_case | `member_note_service.py` |
| Classes | PascalCase | `MemberNoteService` |
| Functions | snake_case | `get_by_member()` |
| Constants | UPPER_SNAKE | `AUDITED_TABLES` |
| Routes | kebab-case | `/api/v1/member-notes/` |

### Import Order

```python
# 1. Standard library
from datetime import datetime
from typing import Optional, List

# 2. Third-party
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# 3. Local imports
from src.models.member_note import MemberNote
from src.services.audit_service import audit_service
```

---

## 🔵 Testing Requirements

### Minimum Coverage

- **Every new model**: At least 3 tests (create, read, update/delete)
- **Every new service**: At least 5 tests (CRUD + edge cases)
- **Every new router**: At least 3 tests (auth, happy path, error)
- **Every new feature**: Integration test for full flow

### Test File Naming

```
src/tests/
├── test_member_notes.py          # Model + Service tests
├── test_member_notes_api.py      # Router tests (if large)
├── test_audit_immutability.py    # Specific feature tests
└── test_stripe_integration.py    # Integration tests
```

### Running Specific Tests

```bash
# Run single file
pytest src/tests/test_member_notes.py -v

# Run specific test
pytest src/tests/test_member_notes.py::TestMemberNoteService::test_create -v

# Run with coverage
pytest --cov=src --cov-report=html
```

---

## 📋 Instruction Document Template

All instruction documents MUST follow this structure:

```markdown
# [Phase/Week] [Session]: [Title]

**Project:** UnionCore (IP2A Database v2)
**Phase:** [Phase Number] - [Phase Name]
**Week:** [Week Number] - [Week Focus]
**Session:** [A/B/C/D] (of [total])
**Estimated Duration:** [X-Y hours]
**Branch:** `develop` (ALWAYS work on develop, main is frozen for Railway demo)
**Prerequisite:** [Previous session or requirement]

---

## Session Overview

[Brief description of what this session accomplishes]

---

## Pre-Session Checklist

[bash commands to verify environment]

---

## Tasks

### Task 1: [Title] ([estimated time])

[Detailed instructions with code examples]

### Task 2: [Title] ([estimated time])

[Detailed instructions with code examples]

[... more tasks ...]

---

## Acceptance Criteria

- [ ] [Criterion 1]
- [ ] [Criterion 2]
[... more criteria ...]

---

## Files Created/Modified

### Created
```
[file paths]
```

### Modified
```
[file paths]
```

---

## Next Session Preview

[Brief description of what comes next]

---

## 📝 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** 

### Before Ending This Session:

Scan all documentation in `/app/*`. Update *ANY* & *ALL* relevant documentation as necessary with current progress for the historical record. Do not forget to update ADRs, Roadmap, Checklist, again only if necessary.

**Documentation Checklist:**

| Document | Updated? | Notes |
|----------|----------|-------|
| CLAUDE.md | [ ] | |
| CHANGELOG.md | [ ] | |
| CONTINUITY.md | [ ] | |
| IP2A_MILESTONE_CHECKLIST.md | [ ] | |
| IP2A_BACKEND_ROADMAP.md | [ ] | |
| Relevant ADRs | [ ] | |
| Session log created | [ ] | |

This ensures historical record-keeping and project continuity ("bus factor" protection).

---

*End of instruction document*
```

---

## 📁 Project File Locations

### Key Documents

| Document | Location | Purpose |
|----------|----------|---------|
| CLAUDE.md | `/app/CLAUDE.md` | Project context for Claude |
| CHANGELOG.md | `/app/CHANGELOG.md` | Version history |
| CONTINUITY.md | `/app/CONTINUITY.md` | Handoff context |
| Milestone Checklist | `/app/docs/IP2A_MILESTONE_CHECKLIST.md` | Task tracking |
| Backend Roadmap | `/app/docs/IP2A_BACKEND_ROADMAP.md` | Phase planning |
| ADRs | `/app/docs/decisions/ADR-*.md` | Architecture decisions |
| Session Logs | `/app/docs/reports/session-logs/` | Historical record |
| Instructions | `/app/docs/instructions/` | Development guides |

### Instruction Document Locations

```
/app/docs/instructions/
├── stripe/
│   ├── STRIPE_PHASE1_BACKEND.md
│   ├── STRIPE_PHASE2_DATABASE_TESTING.md
│   └── STRIPE_PHASE3_FRONTEND_INTEGRATION.md
├── week11_instructions/
│   ├── WEEK11_SESSION_A_AUDIT_INFRASTRUCTURE.md
│   ├── WEEK11_SESSION_B_AUDIT_UI.md
│   └── WEEK11_SESSION_C_INLINE_HISTORY.md
├── week12_instructions/
│   └── WEEK12_SESSION_A_SETTINGS_PROFILE.md
└── MASTER_INSTRUCTIONS.md  ← THIS FILE
```

---

## 🚨 Common Mistakes to Avoid

1. **Forgetting to update documentation** - The #1 issue. ALWAYS scan /app/* at session end.

2. **Working on main branch** - ALWAYS use develop. Main is frozen for demo.

3. **Skipping tests** - Run `pytest -v` before AND after changes.

4. **Large commits** - Commit incrementally, not one giant commit.

5. **Missing session logs** - ALWAYS create a session log in `docs/reports/session-logs/`.

6. **Not updating CHANGELOG** - Every session should add an entry.

7. **Forgetting ADRs** - If you made an architectural decision, document it.

8. **Not reading prerequisites** - Always verify previous session is complete.

---

## 🔄 Version Tagging

When completing a significant milestone:

```bash
# Create version tag
git tag -a v0.8.2-alpha -m "Week 11 Session B - Audit UI complete"
git push origin v0.8.2-alpha

# Update CLAUDE.md version line
```

**Version Format:** `v{major}.{minor}.{patch}-{stage}`
- **major**: Breaking changes
- **minor**: New features
- **patch**: Bug fixes
- **stage**: alpha, beta, rc, (empty for release)

---

## ✅ Session Completion Verification

Before marking a session complete, verify:

```
□ All tasks from instruction document completed
□ All acceptance criteria met
□ All tests passing (pytest -v)
□ Code committed and pushed to develop
□ CLAUDE.md updated with current status
□ CHANGELOG.md entry added
□ Session log created in docs/reports/session-logs/
□ Milestone checklist updated
□ Any ADRs created/updated as needed
□ Roadmap updated if milestones changed
```

---

*This master document governs all development sessions. Compliance is mandatory.*

*Last Updated: January 30, 2026*
