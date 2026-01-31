# Documentation Update Instruction - Integration Guide

**Project:** UnionCore (IP2A Database v2)
**Purpose:** Ensure consistent documentation updates across all development sessions

---

## Quick Reference

**The instruction to add to all instruction documents:**

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

## Integration Examples

### 1. For Continuity Documents (like `CONTINUITY_STRIPE.md`)

Add before the final `*End of continuity document*` line:

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

---

*End of continuity document*
```

### 2. For Session Templates

Add as the final section before sign-off:

```markdown
## Session Wrap-Up

### Code Changes
- [ ] All changes committed to appropriate branch
- [ ] Tests passing
- [ ] Linting clean (Ruff)

### Documentation Updates (REQUIRED)
- [ ] Scanned `/docs/*` for relevant documents
- [ ] Updated all applicable documentation
- [ ] Created new ADRs if architectural decisions were made
- [ ] Session log updated with today's progress
- [ ] CHANGELOG.md updated if applicable

> ⚠️ **MANDATORY:** Do not end session without completing documentation review.
```

### 3. For Development Instruction Documents

Add prominently near the top (after overview) AND at the bottom:

**Near top:**
```markdown
## Important Reminders

⚠️ **Documentation Requirement:** Every development session MUST end with a documentation review. See "End-of-Session Documentation" section at the bottom of this document.
```

**At bottom:**
```markdown
---

## 📝 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session.

### Documentation Checklist:

- [ ] Scanned `/docs/*` directory
- [ ] Updated relevant existing documents
- [ ] Created new documents if needed
- [ ] Reviewed/updated ADRs for any architectural decisions
- [ ] Added session log entry

### Documents to Check:

| Document | Updated? | Notes |
|----------|----------|-------|
| SESSION_LOG.md | [ ] | |
| CHANGELOG.md | [ ] | |
| Relevant ADR | [ ] | |
| MILESTONE_*.md | [ ] | |
| README.md | [ ] | |
```

### 4. For Milestone/Phase Documents

Add as a required completion step:

```markdown
## Phase Completion Criteria

### Functional Requirements
- [ ] All features implemented
- [ ] Tests passing
- [ ] Code reviewed

### Documentation Requirements (MANDATORY)
- [ ] Phase documentation updated
- [ ] ADRs created/updated for decisions made
- [ ] Session logs capture all work
- [ ] CHANGELOG reflects all changes
- [ ] Any new instruction documents created as needed
- [ ] `/docs/*` scanned and all relevant docs updated
```

---

## Documents That Should Include This Instruction

Based on your project structure, add the instruction to:

1. **CONTINUITY_*.md** - All continuity/handoff documents
2. **DEVELOPMENT_INSTRUCTIONS.md** - Main development guide
3. **PHASE_*_INSTRUCTIONS.md** - Phase-specific instructions
4. **SESSION_TEMPLATE.md** - If you have a session template
5. **CLAUDE_CODE_INSTRUCTIONS.md** - Instructions for Claude Code sessions
6. **MILESTONE_CHECKLIST.md** - Milestone tracking documents
7. **DEPLOYMENT_INSTRUCTIONS.md** - Deployment guides
8. **Any *_GUIDE.md or *_INSTRUCTIONS.md files**

---

## Suggested `/docs` Directory Structure

```
/docs
├── ADRs/
│   ├── ADR-001-architecture.md
│   ├── ADR-002-database.md
│   ├── ...
│   └── ADR-template.md
├── continuity/
│   ├── CONTINUITY_STRIPE.md
│   └── CONTINUITY_*.md
├── instructions/
│   ├── DEVELOPMENT_INSTRUCTIONS.md
│   ├── DEPLOYMENT_INSTRUCTIONS.md
│   └── CLAUDE_CODE_INSTRUCTIONS.md
├── logs/
│   ├── SESSION_LOG.md
│   └── session-archives/
├── milestones/
│   ├── MILESTONE_FRONTEND.md
│   └── MILESTONE_CHECKLIST.md
├── CHANGELOG.md
└── README.md
```

---

## Automation Idea (Future Enhancement)

Consider adding a pre-commit hook or session end script:

```bash
#!/bin/bash
# docs-reminder.sh

echo "=========================================="
echo "📝 DOCUMENTATION REMINDER"
echo "=========================================="
echo ""
echo "Before ending this session, have you:"
echo "  [ ] Scanned /docs/* for updates needed"
echo "  [ ] Updated all relevant documentation"
echo "  [ ] Created/updated ADRs as necessary"
echo "  [ ] Added session log entry"
echo ""
echo "Type 'done' to confirm: "
read confirmation

if [ "$confirmation" != "done" ]; then
    echo "⚠️  Please complete documentation updates before ending session."
    exit 1
fi
```

---

*Last Updated: January 30, 2026*
