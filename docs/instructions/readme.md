# Phase 6 Week 1 - Frontend Foundation

**Total Estimated Time:** 4-6 hours
**Session Strategy:** Can be done in 2-3 sessions of 2-3 hours each

---

## Document Execution Order

| # | Document | Time | Focus | Status |
|---|----------|------|-------|--------|
| 1 | [1-preflight-and-setup.md](1-preflight-and-setup.md) | 30-45 min | Pre-checks, tag v0.7.0, directories | ✅ Complete |
| 2 | [2-base-templates.md](2-base-templates.md) | 20-30 min | base.html, base_auth.html | ✅ Complete |
| 3 | [3-components.md](3-components.md) | 30-40 min | Navbar, sidebar, flash, modal | ✅ Complete |
| 4 | [4-pages-and-static.md](4-pages-and-static.md) | 45-60 min | Login, dashboard, errors, CSS, JS | Pending |
| 5 | [5-router-and-integration.md](5-router-and-integration.md) | 30-40 min | Frontend router, main.py | Pending |
| 6 | [6-testing-and-commit.md](6-testing-and-commit.md) | 30-45 min | Tests, verify, commit | Pending |

---

## Suggested Sessions

**Session A (2-3 hours):**
- Document 1: Setup
- Document 2: Base templates
- Document 3: Components

**Session B (2-3 hours):**
- Document 4: Pages & Static
- Document 5: Router & Integration
- Document 6: Testing & Commit

---

## Quick Reference

**Start of any session:**
```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short
```

**End of any session:**
```bash
pytest -v
git status
git add -A
git commit -m "wip: Phase 6 Week 1 progress"
git push origin main
```

---

## Deliverables Checklist

After all 6 documents:

- [x] v0.7.0 tagged ✅ (Session A)
- [ ] `/login` renders styled login form
- [ ] `/dashboard` renders with sidebar and stats
- [x] Static files serve correctly (CSS/JS created) ✅ (Session A)
- [ ] 404/500 error pages work
- [x] 165 tests pass ✅ (Session A)
- [ ] All changes committed

### Session A Progress (Jan 28, 2026)
- ✅ Pre-flight checks passed
- ✅ v0.7.0 tag created
- ✅ CLAUDE.md updated for frontend phase
- ✅ Directory structure created (templates, static)
- ✅ Base templates created (base.html, base_auth.html)
- ✅ Components created (_navbar, _sidebar, _flash, _modal)
- ✅ Custom CSS and JS created
- ✅ All 165 tests passing

---

*Created: January 28, 2026*
*For: Claude Code execution*
