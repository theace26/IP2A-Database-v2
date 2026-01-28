# ADR-005: CSS Framework

## Status
Accepted

## Date
2026-01

## Context

IP2A Database needs consistent styling for the web interface. Constraints:

1. **Rapid development** - Limited time for custom CSS
2. **Consistency** - Professional appearance without a designer
3. **Responsiveness** - Must work on various screen sizes
4. **Maintainability** - Easy to update and modify
5. **Bundle size** - Should not slow down page loads

## Decision

Use **Tailwind CSS** with:
- **CDN** for development (instant setup, no build step)
- **Tailwind CLI** for production (tree-shaking, smaller bundle)
- **Utility-first approach** - Classes in HTML, minimal custom CSS

## Consequences

### Positive
- **Rapid prototyping** - Build UI quickly with utility classes
- **Consistency** - Design system built into the framework
- **Responsive** - Mobile-first responsive utilities included
- **No context switching** - Styles in same file as markup
- **Documentation** - Excellent docs and community resources
- **Tree-shaking** - Production builds only include used styles

### Negative
- **Verbose HTML** - Many classes on elements
- **Learning curve** - Need to learn utility class names
- **Custom designs** - Harder to deviate from Tailwind's defaults

### Neutral
- Pairs well with HTMX (both work in HTML)
- Can add custom components with `@apply` if needed

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

---

*Tailwind integrates naturally with Jinja2 templates and HTMX (ADR-002).*
