# Claude Code Instructions: Fix Dispatch.bid Bug + Update Documentation

**Created:** February 4, 2026
**Purpose:** Fix SQLAlchemy relationship error blocking 25 tests, update lagging documentation
**Context:** UnionCore (IP2A-Database-v2) — IBEW Local 46
**Estimated Time:** 30-45 minutes
**Branch:** `develop`
**Target Version:** v0.9.8-alpha → v0.9.8-alpha (docs sync only)

---

## Pre-Flight

```bash
cd ~/Projects/IP2A-Database-v2
git checkout develop
git pull origin develop
git status  # Should be clean
```

---

## Phase 1: Fix Dispatch.bid Relationship Bug (CRITICAL)

The `Dispatch` model has a relationship to `JobBid` that's missing the `foreign_keys` parameter. This causes SQLAlchemy to fail with:

```
Could not determine join condition between parent/child tables on relationship Dispatch.bid
```

### 1.1 Locate and Read the Current Model

```bash
cat src/models/dispatch.py
```

Look for the `bid` relationship definition. It likely looks something like:

```python
bid = relationship("JobBid", back_populates="dispatch")
```

### 1.2 Fix the Relationship

The `Dispatch` model needs to explicitly specify the foreign key. Update the relationship to:

```python
bid = relationship("JobBid", foreign_keys=[bid_id], back_populates="dispatch")
```

**Important:** The `bid_id` column must be defined BEFORE the relationship in the model class. The pattern should be:

```python
class Dispatch(Base):
    __tablename__ = "dispatches"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    bid_id: Mapped[int | None] = mapped_column(ForeignKey("job_bids.id"), nullable=True)
    # ... other columns ...
    
    # Relationships
    bid: Mapped["JobBid | None"] = relationship(
        "JobBid", 
        foreign_keys=[bid_id], 
        back_populates="dispatch"
    )
```

### 1.3 Also Check the Inverse Relationship

In `src/models/job_bid.py`, verify the `JobBid.dispatch` relationship exists and is configured correctly:

```python
class JobBid(Base):
    __tablename__ = "job_bids"
    
    # ... columns ...
    
    dispatch: Mapped["Dispatch | None"] = relationship(
        "Dispatch",
        back_populates="bid",
        uselist=False
    )
```

If `JobBid` doesn't have a `dispatch` relationship at all, add it. If it has one but no `back_populates`, add that.

### 1.4 Run Tests to Verify Fix

```bash
# Run just the dispatch frontend tests first (these were blocked)
pytest src/tests/test_dispatch_frontend.py -v --tb=short

# If those pass, run full suite
pytest -v --tb=short 2>&1 | tail -20
```

**Expected outcome:** 593 tests passing (568 + 25 that were blocked)

If tests still fail, check:
1. Did you import `ForeignKey` at the top of dispatch.py?
2. Is the column name exactly `bid_id`?
3. Are there any circular import issues?

---

## Phase 2: Update CLAUDE.md ADR Count

The CLAUDE.md file says "15 ADRs" but ADR-016 exists. Fix this.

```bash
# Find the line with ADR count
grep -n "ADR" CLAUDE.md | head -10
```

Update any line that says "15 ADRs" to "16 ADRs".

---

## Phase 3: Update CHANGELOG.md ADR Count

Same issue — says "15 ADRs" instead of 16.

```bash
grep -n "15 ADRs" CHANGELOG.md
```

Update to "16 ADRs".

---

## Phase 4: Deploy Updated Documentation

The user will provide three updated documentation files. Copy them to their correct locations:

| Source File (provided by user) | Destination in Repo |
|-------------------------------|---------------------|
| `IP2A_MILESTONE_CHECKLIST_v3.md` | `docs/IP2A_MILESTONE_CHECKLIST.md` |
| `IP2A_BACKEND_ROADMAP_v5.md` | `docs/IP2A_BACKEND_ROADMAP.md` |
| `hub_README_v2.md` | `docs/README.md` |

```bash
# After user provides files (adjust paths as needed):
cp IP2A_MILESTONE_CHECKLIST_v3.md docs/IP2A_MILESTONE_CHECKLIST.md
cp IP2A_BACKEND_ROADMAP_v5.md docs/IP2A_BACKEND_ROADMAP.md
cp hub_README_v2.md docs/README.md
```

---

## Phase 5: Verification

```bash
# 1. All tests pass
pytest -v --tb=short 2>&1 | tail -10
# Expected: 593 passed

# 2. No more VERIFY markers in docs
grep -rn "VERIFY" docs/README.md docs/IP2A_BACKEND_ROADMAP.md docs/IP2A_MILESTONE_CHECKLIST.md CLAUDE.md
# Expected: 0 results

# 3. ADR count is correct (16)
grep -rn "16 ADRs" CLAUDE.md CHANGELOG.md docs/README.md
# Expected: matches found

# 4. Version is correct (v0.9.8-alpha)
grep -rn "v0.9.8-alpha" docs/README.md docs/IP2A_BACKEND_ROADMAP.md docs/IP2A_MILESTONE_CHECKLIST.md
# Expected: matches found
```

---

## Phase 6: Commit

```bash
git add src/models/dispatch.py src/models/job_bid.py  # If modified
git add CLAUDE.md CHANGELOG.md
git add docs/README.md docs/IP2A_BACKEND_ROADMAP.md docs/IP2A_MILESTONE_CHECKLIST.md

git commit -m "fix: Dispatch.bid relationship + docs sync to v0.9.8-alpha

- Fixed SQLAlchemy foreign_keys parameter on Dispatch.bid relationship
- Unblocked 25 dispatch frontend tests (593 total now passing)
- Updated docs to v0.9.8-alpha (Weeks 26-27 complete)
- Fixed ADR count: 15 → 16 (ADR-016 exists)
- Removed all ⚠️ VERIFY markers from documentation
- Milestone Checklist v3.0, Roadmap v5.0, README v2.0
"

git push origin develop
```

---

## Summary

After this session:
- **Tests:** 593 passing (all green)
- **Version:** v0.9.8-alpha
- **Weeks 26-27:** Reflected in all docs
- **ADRs:** 16 (count fixed everywhere)
- **VERIFY markers:** All removed

---

*Claude Code Instructions — February 4, 2026*
