# IP2A Backend Roadmap

## Phase 1 — Foundations ✅
- [x] src/ layout migration
- [x] Import graph validation
- [x] Alembic env src-awareness
- [x] Seed registry + integrity
- [x] CI pipeline
- [x] Pre-commit enforcement

---

## Phase 2 — Migration Safety ✅
- [x] Migration naming enforcement
- [x] Legacy migration freeze
- [x] Breaking change detection
- [x] Alembic wrapper for timestamped generation
- [x] Migration dependency graph (FK-based)
- [x] Auto-detect destructive downgrades

---

## Phase 3 — Schema Intelligence
- [ ] Model → Migration diff report (human-readable)
- [ ] Blast-radius estimation for migrations
- [ ] Prod compatibility guard (dev → prod drift)
- [ ] Schema version watermarking

---

## Phase 4 — Seed Intelligence
- [ ] Auto-derived seed order via FK graph
- [ ] Seed idempotency validation
- [ ] Seed dry-run mode
- [ ] Seed data invariants

---

## Phase 5 — Observability & DX
- [ ] Auto-generate ARCHITECTURE.md from code
- [ ] Mermaid graph generation in CI
- [ ] Seed + migration timelines
- [ ] Developer health dashboard

---

## Non-Goals (Explicit)
- ❌ Silent migrations
- ❌ Implicit seed ordering
- ❌ Runtime schema guessing
- ❌ “Fix it later” database changes
