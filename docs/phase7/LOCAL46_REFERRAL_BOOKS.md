# IBEW Local 46 Referral Books (Out-of-Work Lists)

> **Document Created:** February 2, 2026
> **Last Updated:** February 3, 2026
> **Version:** 2.0
> **Status:** Draft — Needs Verification (see Open Questions below)
> **Project Version:** v0.9.4-alpha (Feature-Complete Weeks 1-19)
> **Data Source:** LaborPower screenshots

---

## Purpose

This document captures the referral book (out-of-work list) structure for IBEW Local 46 as observed in LaborPower screenshots. It serves as the seed data reference for Phase 7, Phase 1 (Session 20A) when creating the `referral_books` table and populating initial data.

### Related Documents

| Document | Purpose |
|---|---|
| `LABORPOWER_GAP_ANALYSIS.md` | Gap #1: Out-of-Work List / Dispatch System schema |
| `LABORPOWER_IMPLEMENTATION_PLAN.md` | Session 20A: Referral Books model creation |
| `PHASE7_REFERRAL_DISPATCH_PLAN.md` | Referral & dispatch system deep-dive |
| `LABORPOWER_REFERRAL_REPORTS_INVENTORY.md` | Reports that depend on referral book data |

---

## ⚠️ Open Questions (Must Resolve Before Implementation)

> **These questions must be answered before Session 20A seed data can be finalized.** Only the WIRE books below are confirmed from screenshots. Everything else is assumed from typical IBEW local structure.

1. **Are there Sound & Communication books?** Most locals have separate S&C out-of-work lists.
2. **VDV (Voice/Data/Video) books?** Some locals have separate VDV classifications.
3. **Residential books?** Does Local 46 have residential wireman classification?
4. **Apprentice books?** How are apprentices tracked — through the JATC or regular dispatch?
5. **Other regions?** Are there other geographical regions beyond Seattle, Bremerton, Port Angeles?
6. **Book rules?** Are the 90-day max, 14-day re-sign, 3-day grace period accurate for all books?

---

## Confirmed Books (from Screenshots)

| Book Name | Code | Skill Type | Region | Book # |
|-----------|------|------------|--------|--------|
| WIRE SEATTLE | WIRE_SEA | wire | Seattle | 1, 2 |
| WIRE BREMERTON | WIRE_BREM | wire | Bremerton | 1, 2 |
| WIRE PT ANGELES | WIRE_PA | wire | Port Angeles | 1, 2 |

### Book Number Meaning

From the screenshots, members can be qualified for multiple books. For example, a member record shows qualified for: WIRE SEATTLE [1], WIRE BREMERTON [1], WIRE PT ANGELES [1].

This confirms:
- **Book 1** = Local members (A-card holders from Local 46)
- **Book 2** = Travelers (members from other IBEW locals)

The "Qualified Books" tab determines which lists a member CAN sign, separate from which lists they ARE CURRENTLY signed on. This maps to the `member_qualified_books` table in the gap analysis.

---

## Typical IBEW Local Structure (to Verify with Local 46)

Most IBEW locals have books for the following classifications. These are listed as candidates for seed data, pending verification:

### Inside Wireman (Wire) — ✅ CONFIRMED
- Book 1: Journeyman Inside Wiremen (JIW) — members of this local
- Book 2: Journeyman from other IBEW locals (travelers)

### Sound & Communication — ❓ UNCONFIRMED
- Sound Book 1: Sound technicians from this local
- Sound Book 2: Sound technicians from other locals

### Residential — ❓ UNCONFIRMED
- Residential Book 1: Residential wiremen from this local
- Residential Book 2: Travelers

### Apprentices — ❓ UNCONFIRMED
- Apprentice books (managed separately, tied to JATC)

> **Note:** The existing JATC/training module (Weeks 5-6) tracks student educational progress. If apprentice dispatch is handled through the referral system rather than JATC, a separate apprentice book type would be needed. This reinforces the Member ≠ Student separation.

---

## Seed Data Template

```python
# src/seed/referral_books_seed.py

REFERRAL_BOOKS = [
    # Inside Wireman - Seattle
    {
        "name": "WIRE SEATTLE",
        "code": "WIRE_SEA_1",
        "book_number": 1,
        "skill_type": "wire",
        "region": "Seattle",
        "max_days_on_book": 90,
        "re_sign_days": 14,
        "grace_period_days": 3,
        "is_active": True,
    },
    {
        "name": "WIRE SEATTLE",
        "code": "WIRE_SEA_2",
        "book_number": 2,
        "skill_type": "wire",
        "region": "Seattle",
        "max_days_on_book": 90,
        "re_sign_days": 14,
        "grace_period_days": 3,
        "is_active": True,
    },
    
    # Inside Wireman - Bremerton
    {
        "name": "WIRE BREMERTON",
        "code": "WIRE_BREM_1",
        "book_number": 1,
        "skill_type": "wire",
        "region": "Bremerton",
        "max_days_on_book": 90,
        "re_sign_days": 14,
        "grace_period_days": 3,
        "is_active": True,
    },
    {
        "name": "WIRE BREMERTON",
        "code": "WIRE_BREM_2",
        "book_number": 2,
        "skill_type": "wire",
        "region": "Bremerton",
        "max_days_on_book": 90,
        "re_sign_days": 14,
        "grace_period_days": 3,
        "is_active": True,
    },
    
    # Inside Wireman - Port Angeles
    {
        "name": "WIRE PT ANGELES",
        "code": "WIRE_PA_1",
        "book_number": 1,
        "skill_type": "wire",
        "region": "Port Angeles",
        "max_days_on_book": 90,
        "re_sign_days": 14,
        "grace_period_days": 3,
        "is_active": True,
    },
    {
        "name": "WIRE PT ANGELES",
        "code": "WIRE_PA_2",
        "book_number": 2,
        "skill_type": "wire",
        "region": "Port Angeles",
        "max_days_on_book": 90,
        "re_sign_days": 14,
        "grace_period_days": 3,
        "is_active": True,
    },
    
    # ──────────────────────────────────────────────
    # UNCOMMENT AFTER VERIFICATION WITH LOCAL 46
    # ──────────────────────────────────────────────
    
    # Sound & Communication - Seattle (if applicable)
    # {
    #     "name": "SOUND SEATTLE",
    #     "code": "SOUND_SEA_1",
    #     "book_number": 1,
    #     "skill_type": "sound",
    #     "region": "Seattle",
    #     "max_days_on_book": 90,
    #     "re_sign_days": 14,
    #     "grace_period_days": 3,
    #     "is_active": True,
    # },
    # {
    #     "name": "SOUND SEATTLE",
    #     "code": "SOUND_SEA_2",
    #     "book_number": 2,
    #     "skill_type": "sound",
    #     "region": "Seattle",
    #     "max_days_on_book": 90,
    #     "re_sign_days": 14,
    #     "grace_period_days": 3,
    #     "is_active": True,
    # },
]
```

### Seed Data Integration Notes

- Seed data follows the existing registry-based seed ordering pattern (see `docs/architecture/diagrams/seeds.mmd` updated in Batch 2).
- `referral_books` has no FK dependencies, so it can be seeded early in the chain.
- `member_qualified_books` depends on both `members` and `referral_books` — seed after both.
- The `book_number` and `max_days_on_book`/`re_sign_days`/`grace_period_days` fields are in the seed data template but need to be confirmed as columns on the `referral_books` model. The gap analysis schema does not include them directly — they may belong on the model or on a separate `book_rules` configuration. Decide during Session 20A.

---

## 📝 End-of-Session Documentation (MANDATORY)

**Before completing ANY session:**

> Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. Do not forget about ADRs — update as necessary.

See `/docs/standards/END_OF_SESSION_DOCUMENTATION.md` for full checklist.

---

Document Version: 2.0
Last Updated: February 3, 2026
Previous Version: 1.0 (February 2, 2026 — Initial referral book inventory from LaborPower screenshots)
