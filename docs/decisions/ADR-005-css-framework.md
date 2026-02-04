# ADR-005: CSS Framework

> **Document Created:** 2026-01
> **Last Updated:** February 3, 2026
> **Version:** 2.0
> **Status:** Implemented — Tailwind CSS + DaisyUI used across all frontend modules

## Status
Implemented

## Date
2026-01

## Context

IP2A Database needs consistent styling for the web interface. Constraints:

1. **Rapid development** — Limited time for custom CSS
2. **Consistency** — Professional appearance without a designer
3. **Responsiveness** — Must work on various screen sizes (including mobile PWA)
4. **Maintainability** — Easy to update and modify
5. **Bundle size** — Should not slow down page loads

## Decision

Use **Tailwind CSS** with **DaisyUI** component library:
- **CDN** for development (instant setup, no build step)
- **Tailwind CLI** for production (tree-shaking, smaller bundle)
- **Utility-first approach** — Classes in HTML, minimal custom CSS
- **DaisyUI** — Pre-built component classes (buttons, cards, tables, modals, badges, steps, etc.)

## Implementation Status

| Component | Status | Week | Notes |
|-----------|--------|------|-------|
| Tailwind CSS via CDN | ✅ | 1 | Development setup, no build step |
| DaisyUI component library | ✅ | 1 | Semantic component classes |
| Responsive layouts | ✅ | 1–19 | All pages mobile-responsive |
| Badge system (status indicators) | ✅ | 7 | Standardized across modules (ADR-010, ADR-011) |
| Steps component (workflows) | ✅ | 7 | Grievance steps, benevolence flow |
| Modal patterns (Alpine.js) | ✅ | 10 | Record payment, approve adjustment |
| Card-based dashboards | ✅ | 2+ | Stats cards on all landing pages |
| Data tables with sorting | ✅ | 3+ | Consistent table styling across modules |
| Mobile PWA touch-friendly UI | ✅ | 18 | Bottom nav, larger touch targets |
| Chart.js integration | ✅ | 19 | Analytics dashboard styling |

### DaisyUI Components in Active Use

| Component | Where Used |
|-----------|-----------|
| `btn`, `btn-primary`, `btn-ghost` | All forms, actions |
| `card`, `card-body` | Dashboard stats, landing pages |
| `table`, `table-zebra` | All list views |
| `badge`, `badge-success/warning/error/ghost/info` | Status indicators everywhere |
| `steps`, `step`, `step-primary` | Grievance steps, benevolence workflow |
| `modal` | Payment recording, adjustment approval |
| `drawer` | Mobile navigation |
| `breadcrumbs` | Page navigation hierarchy |
| `stats` | Dashboard metrics |
| `alert` | Flash messages, validation errors |
| `tabs` | Module navigation |
| `collapse` | Expandable detail sections |
| `bottom-navigation` | PWA mobile nav (Week 18) |

## Consequences

### Positive
- **Rapid prototyping** — Build UI quickly with utility classes
- **Consistency** — Design system built into the framework
- **Responsive** — Mobile-first responsive utilities included
- **No context switching** — Styles in same file as markup
- **Documentation** — Excellent docs and community resources
- **Tree-shaking** — Production builds only include used styles
- **DaisyUI semantics** — `btn-primary` is clearer than raw Tailwind utility chains
- **Theme support** — DaisyUI themes allow easy color scheme changes

### Negative
- **Verbose HTML** — Many classes on elements
- **Learning curve** — Need to learn utility class names + DaisyUI components
- **Custom designs** — Harder to deviate from Tailwind/DaisyUI defaults

### Neutral
- Pairs well with HTMX (both work in HTML attributes)
- Can add custom components with `@apply` if needed
- DaisyUI reduces the verbosity problem significantly vs raw Tailwind

## Alternatives Considered

### Bootstrap
- **Rejected:** More opinionated design, harder to customize
- **Rejected:** Heavier bundle size for features we don't need

### Custom CSS
- **Rejected:** Too time-consuming for solo developer
- **Rejected:** Harder to maintain consistency

### No framework (browser defaults)
- **Rejected:** Unprofessional appearance
- **Rejected:** More work for responsive design

## References
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [DaisyUI Documentation](https://daisyui.com/)
- ADR-002: Frontend Framework (Jinja2 + HTMX + Alpine.js)
- ADR-010: Operations Frontend Patterns (badge/steps patterns)
- ADR-011: Dues Frontend Patterns (modal/filter patterns)
- `src/templates/base.html` — CDN includes and base layout
- `src/static/css/` — Any custom CSS overrides

---

## 🔄 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs, update as necessary.

---

Document Version: 2.0
Last Updated: February 3, 2026
Previous Version: 1.0 (2026-01 — original decision, Tailwind only without DaisyUI details)
