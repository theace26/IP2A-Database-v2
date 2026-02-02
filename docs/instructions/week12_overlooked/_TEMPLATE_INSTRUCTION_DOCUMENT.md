# Week [XX]: [Feature Name]

**Version:** 1.0.0  
**Created:** [Date]  
**Branch:** `develop`  
**Estimated Effort:** [X-X hours] ([X sessions])  
**Dependencies:** [List any prerequisite weeks or features]

---

## Overview

[2-3 sentence description of what this week implements and why it matters]

### Objectives

- [ ] Objective 1
- [ ] Objective 2
- [ ] Objective 3

### Out of Scope

- Item not being addressed this week
- Deferred to future week

---

## Pre-Flight Checklist

- [ ] On `develop` branch (`git checkout develop && git pull`)
- [ ] All tests passing (`pytest -v`)
- [ ] Docker services running (`docker-compose up -d`)
- [ ] Reviewed relevant existing code
- [ ] Scanned `/docs/*` for context
- [ ] Previous week(s) complete (if applicable)

---

## Phase 1: [Phase Name]

### 1.1 [Task Name]

[Description of what to do]

```python
# Example code if applicable
```

### 1.2 [Task Name]

[Description]

---

## Phase 2: [Phase Name]

### 2.1 [Task Name]

[Description]

### 2.2 [Task Name]

[Description]

---

## Phase 3: [Phase Name]

[Continue pattern...]

---

## Testing Requirements

### Unit Tests

Create/update these test files:
- `src/tests/test_[feature].py`
- `src/tests/test_[feature]_service.py`
- `src/tests/test_[feature]_ui.py`

### Test Scenarios

1. **[Scenario Name]**
   - Given: [precondition]
   - When: [action]
   - Then: [expected result]

2. **[Scenario Name]**
   - Given: [precondition]
   - When: [action]
   - Then: [expected result]

### Minimum Coverage

- [ ] All CRUD operations tested
- [ ] Edge cases handled
- [ ] Error conditions tested
- [ ] UI routes tested (if applicable)

---

## Migration Notes

If database changes required:

```bash
# Generate migration
alembic revision --autogenerate -m "[description]"

# Review migration file for:
# - Foreign key dependencies
# - Destructive operations
# - Index creation

# Apply migration
alembic upgrade head
```

---

## Acceptance Criteria

### Required

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
- [ ] All new code has test coverage
- [ ] No regressions in existing tests

### Optional (Nice to Have)

- [ ] Optional enhancement 1
- [ ] Optional enhancement 2

---

## Rollback Plan

If issues arise:

```bash
# Revert migration (if applicable)
alembic downgrade -1

# Revert code changes
git checkout develop -- src/[affected_files]
```

---

## 📝 MANDATORY: End-of-Session Documentation

> **REQUIRED:** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. **Do not forget about ADRs—update as necessary.**

### Quick Checklist

- [ ] `/CHANGELOG.md` — Version bump, changes summary
- [ ] `/CLAUDE.md` — If architecture/patterns changed  
- [ ] `/docs/IP2A_MILESTONE_CHECKLIST.md` — Progress updates
- [ ] `/docs/decisions/ADR-XXX.md` — If architectural decisions made
- [ ] `/docs/reports/session-logs/YYYY-MM-DD-*.md` — **Create new session log**

### Session Log Template

Create: `/docs/reports/session-logs/YYYY-MM-DD-[brief-description].md`

```markdown
# Session Log: YYYY-MM-DD

**Branch:** develop
**Version:** v0.X.X-alpha
**Duration:** ~X hours
**Instruction Doc:** Week [XX]

## Objectives
- [ ] Goal 1
- [ ] Goal 2

## Completed
- Item 1
- Item 2

## Changes Made
- `path/to/file.py` - Description of change

## Tests
- Added/Modified: X tests
- All passing: Yes/No

## Blockers/Issues
- Issue encountered (if any)

## Next Session
- Priority item 1
- Priority item 2

## Notes
Any relevant observations or decisions made.
```

### ADR Triggers

Create an ADR (`/docs/decisions/ADR-XXX-[topic].md`) if:
- Choosing between competing technical approaches
- Adopting a new library, tool, or pattern
- Changing an existing architectural decision
- Making trade-offs with long-term implications
- Deciding how to handle edge cases that affect design

---

## References

- Related ADR: [ADR-XXX](../decisions/ADR-XXX.md)
- Related documentation: [link]
- External reference: [link]

---

*Last Updated: [Date]*
