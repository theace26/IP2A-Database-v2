# ADR-002: Frontend Framework Choice

## Status
Accepted

## Date
2026-01-27

## Context

We need to choose a frontend technology for the IP2A staff interface. Constraints:

1. **Developer Experience:** Primary developer has no React/Vue/Svelte experience
2. **Time:** 5-10 hours/week available for development
3. **Maintainability:** Must be maintainable by volunteer union tech folks
4. **Longevity:** 10+ year horizon - must survive framework churn
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
- **Alpine.js:** Keyboard shortcuts and small interactions
- **Chart.js:** Data visualization
- **Tailwind CSS:** Styling (optional, can use plain CSS)

## Consequences

### Positive
- Single codebase, single deployment
- No build step required
- HTML attributes are stable (won't break in 10 years)
- Lower learning curve for primary developer
- Easier onboarding for future contributors
- Backend integrations (QuickBooks, Stripe) unaffected

### Negative
- Less "modern" feel than SPA
- Complex real-time features (if needed) require more work
- Fewer pre-built component libraries
- May need React for member portal in Phase 4+

### Risks
- HTMX is newer (less proven than React)
- Mitigation: HTMX degrades gracefully to standard HTML forms
- Mitigation: Core functionality works without JavaScript

## References
- [HTMX Documentation](https://htmx.org/)
- [Alpine.js Documentation](https://alpinejs.dev/)
- [Why I Use HTMX](https://htmx.org/essays/)
