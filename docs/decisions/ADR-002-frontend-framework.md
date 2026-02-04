# ADR-002: Frontend Framework Choice

> **Document Created:** 2026-01-27
> **Last Updated:** February 3, 2026
> **Version:** 2.0
> **Status:** Implemented — Jinja2 + HTMX + Alpine.js stack used across all 19 weeks

## Status
Implemented

## Date
2026-01-27

## Context

We need to choose a frontend technology for the IP2A staff interface. Constraints:

1. **Developer Experience:** Primary developer has no React/Vue/Svelte experience
2. **Time:** 5-10 hours/week available for development
3. **Maintainability:** Must be maintainable by volunteer union tech folks
4. **Longevity:** 10+ year horizon — must survive framework churn
5. **Features Required:**
   - Forms and CRUD operations
   - Data tables with search/filter
   - Data visualization (charts)
   - Keyboard shortcuts (like Google Docs)
   - Integration with backend services (QuickBooks, Stripe)

## Options Considered

### Option A: React
- Industry standard (~40% market share)
- Large ecosystem
- Steep learning curve
- Requires separate build process and deployment
- Subject to ecosystem churn

### Option B: Vue.js
- Gentler learning curve than React
- Still requires JavaScript expertise
- Still requires separate deployment

### Option C: Server-Side Rendering (Jinja2 + HTMX + Alpine.js)
- Minimal JavaScript required
- Single deployment (FastAPI serves everything)
- HTML/CSS are the most stable web technologies
- HTMX provides dynamic updates via HTML attributes
- Alpine.js handles keyboard shortcuts and micro-interactions
- Can add React later for member portal if needed

## Decision

We will use **Server-Side Rendering with HTMX and Alpine.js** for the staff interface.

Tech stack:
- **Jinja2:** HTML templating (built into FastAPI)
- **HTMX:** Dynamic updates without JavaScript
- **Alpine.js:** Keyboard shortcuts, modals, and small interactions
- **Chart.js:** Data visualization (analytics dashboard)
- **DaisyUI + Tailwind CSS:** Component library and utility styling (see ADR-005)

## Implementation Status

| Component | Status | Week | Notes |
|-----------|--------|------|-------|
| Jinja2 templating | ✅ | 1 | Base layout, template inheritance |
| HTMX integration | ✅ | 1 | Search, filters, partial updates |
| Alpine.js integration | ✅ | 1 | Modals, dropdowns, form validation |
| DaisyUI component library | ✅ | 1 | Buttons, cards, tables, badges, steps |
| Auth pages (login, setup) | ✅ | 1 | Cookie-based JWT flow |
| Dashboard | ✅ | 2 | Stats cards, quick actions |
| Staff management UI | ✅ | 3 | CRUD with search/filter |
| Training module UI | ✅ | 4 | Cohorts, students, credentials |
| Members module UI | ✅ | 5 | Profiles, employment, notes |
| Operations module UI | ✅ | 7 | SALTing, benevolence, grievances (ADR-010) |
| Reports module UI | ✅ | 8 | WeasyPrint PDF + openpyxl Excel |
| Document management UI | ✅ | 9 | Upload, download, categories |
| Dues module UI | ✅ | 10 | Rates, periods, payments, adjustments (ADR-011) |
| Stripe payment flow | ✅ | 11 | Checkout Sessions redirect (ADR-013) |
| Profile & settings UI | ✅ | 12 | User preferences, password change |
| Grant compliance UI | ✅ | 14 | Dashboard, enrollments, reports (ADR-014) |
| Mobile PWA | ✅ | 18 | Service worker, offline support, bottom nav |
| Analytics dashboard | ✅ | 19 | Chart.js, trends, report builder |

### Frontend Test Coverage
- **~200+ frontend tests** covering all modules
- Tests use FastAPI TestClient with template rendering assertions
- HTMX partial response testing for search/filter endpoints

### Key Patterns Established
- **Combined frontend service pattern** — One service per module domain (ADR-010, ADR-011)
- **HTMX `hx-include` for filter state** — All list pages maintain filter context
- **Alpine.js modals for in-page actions** — Record payment, approve adjustment, etc.
- **DaisyUI `steps` component** — Status workflow visualization
- **Badge helper methods** — Consistent color-coded status indicators
- **Template partials** — `partials/_table.html` for HTMX-swappable table content

## Consequences

### Positive
- Single codebase, single deployment
- No build step required
- HTML attributes are stable (won't break in 10 years)
- Lower learning curve for primary developer
- Easier onboarding for future contributors
- Backend integrations (QuickBooks, Stripe) unaffected
- PWA support proved straightforward to add (Week 18)
- Chart.js integrated cleanly for analytics (Week 19)

### Negative
- Less "modern" feel than SPA
- Complex real-time features (if needed) require more work
- Fewer pre-built component libraries (mitigated by DaisyUI)
- May need React for member portal in Phase 4+

### Risks
- HTMX is newer (less proven than React)
  - **Mitigation:** HTMX degrades gracefully to standard HTML forms
  - **Mitigation:** Core functionality works without JavaScript
  - **Update:** 19 weeks of production use confirms HTMX reliability

## References
- [HTMX Documentation](https://htmx.org/)
- [Alpine.js Documentation](https://alpinejs.dev/)
- [DaisyUI Documentation](https://daisyui.com/)
- [Chart.js Documentation](https://www.chartjs.org/)
- ADR-005: CSS Framework (Tailwind + DaisyUI)
- ADR-010: Operations Frontend Patterns
- ADR-011: Dues Frontend Patterns
- `src/templates/` — All Jinja2 templates
- `src/services/*_frontend_service.py` — Frontend service pattern files

---

## 🔄 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs, update as necessary.

---

Document Version: 2.0
Last Updated: February 3, 2026
Previous Version: 1.0 (2026-01-27 — original decision record)
