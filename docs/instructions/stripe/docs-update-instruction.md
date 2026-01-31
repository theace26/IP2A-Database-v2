# Documentation Update Instruction Block

**Add this section to any/all instruction documents in your project.**

---

## 📝 Session Documentation Requirements (MANDATORY)

> **IMPORTANT:** Before concluding ANY development session, you MUST complete the following documentation tasks.

### Documentation Update Checklist

At the end of every development session, perform these actions:

1. **Scan `/docs/*` directory** for all existing documentation
2. **Update relevant documents** to capture progress made this session
3. **Create new documents** if the session introduced new concepts, decisions, or components not yet documented
4. **Review ADRs (Architecture Decision Records)** - update existing or create new ADRs for any architectural decisions made
5. **Update session logs** with date, work completed, and any blockers encountered
6. **Update changelogs** if applicable (CHANGELOG.md, version bumps, etc.)
7. **Update milestone checklists** to reflect completed tasks

### Documents to Consider Updating

| Document Type | When to Update |
|---------------|----------------|
| `SESSION_LOG.md` | Every session - always |
| `CHANGELOG.md` | When features added, bugs fixed, or breaking changes made |
| `README.md` | When setup steps, features, or usage changes |
| `ADR-xxx.md` | When architectural decisions are made or modified |
| `CONTINUITY_*.md` | When context for handoffs changes |
| `MILESTONE_*.md` | When milestone tasks are completed |
| `*_INSTRUCTIONS.md` | When procedures or workflows change |
| `API_DOCS.md` | When endpoints are added/modified |
| `TESTING_GUIDE.md` | When test patterns or coverage changes |

### ADR Update Guidelines

Check if any of these warrant a new or updated ADR:
- [ ] New technology or library introduced
- [ ] Database schema changes
- [ ] API design decisions
- [ ] Authentication/authorization changes
- [ ] Integration patterns (Stripe, QuickBooks, etc.)
- [ ] Deployment or infrastructure decisions
- [ ] Breaking changes to existing patterns

### Documentation Quality Standards

- Use consistent formatting (headers, lists, code blocks)
- Include dates and version numbers where applicable
- Cross-reference related documents
- Mark deprecated information clearly
- Include "Last Updated" timestamps

---

**Copy everything below the `---` line into your instruction documents:**

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
