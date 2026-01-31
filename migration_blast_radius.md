# Migration Blast Radius Report

- Migrations dir: `src/db/migrations/versions`

| Migration | Legacy | Risk | Categories | Ops | Destructive |
|---------|--------|------|------------|-----|-------------|
| `0001_baseline.py` | Yes | **LOW** | — | 0 | 0 |
| `2b9a7b051766_add_user_model.py` | Yes | **MEDIUM** | RELATIONAL, TOPOLOGICAL | 2 | 0 |
| `2c57ac3bf854_add_instructor_model_and_link_to_cohorts.py` | Yes | **MEDIUM** | STRUCTURAL, RELATIONAL, TOPOLOGICAL | 4 | 0 |
| `3ed3114af8c3_expand_student_phone_length.py` | Yes | **MEDIUM** | STRUCTURAL | 1 | 1 |
| `3fdbc35c6e52_add_class_sessions_table.py` | Yes | **MEDIUM** | RELATIONAL, TOPOLOGICAL | 2 | 0 |
| `4653519832ea_add_tools_issued_credentials_jatc_.py` | Yes | **MEDIUM** | RELATIONAL, TOPOLOGICAL | 6 | 0 |
| `48c5009efd3d_add_capacity_to_location_table.py` | Yes | **MEDIUM** | STRUCTURAL | 5 | 4 |
| `5c629a6db098_add_grants_table_and_expense_grant_id.py` | Yes | **MEDIUM** | RELATIONAL, TOPOLOGICAL | 2 | 0 |
| `6945f65ab264_add_hours_entries_relationship_to_.py` | Yes | **LOW** | — | 0 | 0 |
| `8858fad4109a_add_attendance_table.py` | Yes | **MEDIUM** | RELATIONAL, TOPOLOGICAL | 2 | 0 |
| `8fc125e0b053_expand_instructor_phone_and_.py` | Yes | **MEDIUM** | STRUCTURAL | 2 | 2 |
| `99b57fe87dfb_add_location_model_and_cohort_location_.py` | Yes | **MEDIUM** | STRUCTURAL, RELATIONAL, TOPOLOGICAL | 4 | 0 |
| `9e22daecc7c5_add_student_model.py` | Yes | **MEDIUM** | RELATIONAL, TOPOLOGICAL | 2 | 0 |
| `a7f0648adb7d_update_cohort_model_for_m2m_instructors.py` | Yes | **LOW** | — | 0 | 0 |
| `a9b228e41051_add_instructor_cohort_m2m_and_primary_.py` | Yes | **MEDIUM** | STRUCTURAL, RELATIONAL, TOPOLOGICAL | 5 | 1 |
| `b22ffcf7b09f_add_cohort_id_foreign_key_to_students.py` | Yes | **MEDIUM** | STRUCTURAL, RELATIONAL | 2 | 0 |
| `bd9a2dbfec34_add_cohort_model.py` | Yes | **MEDIUM** | RELATIONAL, TOPOLOGICAL | 2 | 0 |
| `c2e76c575cc3_add_expenses_table.py` | Yes | **MEDIUM** | RELATIONAL, TOPOLOGICAL | 2 | 0 |
| `c8997d54c438_add_date_issued_to_tools_issued.py` | Yes | **MEDIUM** | STRUCTURAL | 3 | 2 |
| `e1e6f2e3b927_add_grant_id_fk_to_expenses.py` | Yes | **MEDIUM** | STRUCTURAL, RELATIONAL | 2 | 0 |
| `f307d39a8205_add_instructor_hours_table.py` | Yes | **MEDIUM** | RELATIONAL, TOPOLOGICAL | 2 | 0 |

## Risk Legend
- **LOW** — Non-structural or metadata-only changes
- **MEDIUM** — Schema expansion or legacy destructive patterns
- **HIGH** — Destructive upgrade operations on new migrations (prod-gated)

## Category Legend
- **DATA** — Data/seed-oriented operations (or unknown op types)
- **STRUCTURAL** — Column/type/nullability changes
- **RELATIONAL** — Constraints, FKs, indexes, relationship changes
- **TOPOLOGICAL** — Table creation/removal (schema topology changes)
