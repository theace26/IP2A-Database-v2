# Claude Code Diagnostic: Bug #029 — Dispatch Model `status` Field

**Type:** Diagnostic (read-only investigation — NO code changes)
**Estimated Time:** 10-15 minutes
**Spoke:** Spoke 2 (Operations)
**Priority:** High — blocks Week 30 instruction generation

---

## Context

During Week 29 test stabilization, 19 dispatch frontend tests revealed an application bug:

```
AttributeError: type object 'Dispatch' has no attribute 'status'
```

**Location:** `src/services/dispatch_frontend_service.py`, line 82:
```python
.filter(Dispatch.status.in_([
    DispatchStatus.CHECKED_IN,
    DispatchStatus.WORKING
]))
```

The service expects a `status` column on the `Dispatch` model with values from a `DispatchStatus` enum, but the model doesn't have that attribute. We need to understand the full picture before writing a fix.

---

## Tasks

### Task 1: Inspect the Dispatch Model

**File:** `src/models/dispatch.py` (or wherever the Dispatch model is defined)

Report back:
1. The **complete list of columns** on the `Dispatch` model (name, type, nullable, default)
2. Is there ANY field that tracks dispatch lifecycle/state? (e.g., `dispatch_status`, `state`, `result`, `outcome`, etc.)
3. What relationships does the model define?
4. Are there any comments or TODOs in the model file?

### Task 2: Inspect the DispatchStatus Enum

**Likely location:** `src/db/enums/` or within the model file itself

Report back:
1. Does `DispatchStatus` exist? If so, what are ALL its values?
2. Where is it defined? (exact file path)
3. Is it imported anywhere besides `dispatch_frontend_service.py`?

### Task 3: Inspect the Service File

**File:** `src/services/dispatch_frontend_service.py`

Report back:
1. Every reference to `Dispatch.status` or `DispatchStatus` in the file (line numbers)
2. What functions/methods reference this field?
3. Are there other Dispatch model fields used in the service that DO exist on the model?

### Task 4: Check Migrations

**Directory:** `src/db/migrations/versions/`

Report back:
1. Is there any migration that adds a `status` column to the `dispatches` table?
2. What is the most recent migration file related to dispatches?
3. Is there a migration that creates the `dispatches` table? What columns does it define?

### Task 5: Check the Schema

**Likely location:** `src/schemas/` (Pydantic schemas for dispatch)

Report back:
1. Do any Pydantic schemas for Dispatch include a `status` field?
2. If so, what type is it mapped to?

### Task 6: Check the Database (if running)

If you can connect to the dev database:
```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'dispatches'
ORDER BY ordinal_position;
```

If the database isn't running, skip this task and note it.

---

## Output Format

Paste your findings in this structure:

```
## Bug #029 Diagnostic Results

### Dispatch Model Columns
(list all columns)

### Status/Lifecycle Field
- Exists: YES/NO
- If YES: field name = ___, type = ___, values = ___
- If NO: no lifecycle tracking field found

### DispatchStatus Enum
- Exists: YES/NO
- Values: (list)
- Defined in: (path)
- Used in: (list files)

### Service References
- Lines referencing status: (list)
- Other Dispatch fields used that DO exist: (list)

### Migration State
- dispatches table created in: (migration file)
- status column migration: EXISTS/MISSING
- Most recent dispatch migration: (file)

### Schema State
- Pydantic status field: EXISTS/MISSING

### Database State (if checked)
- (paste query results or "skipped")

### My Assessment
(1-2 sentences: is this a missing migration, wrong field name, or incomplete implementation?)
```

---

## Rules

- **DO NOT** modify any files
- **DO NOT** create migrations or add columns
- **DO NOT** fix the bug — just investigate and report
- Report exactly what you find, even if it seems contradictory
- If a file doesn't exist where expected, say so

---

*This diagnostic feeds back to the Hub for Week 30 planning. Accurate reporting here saves time downstream.*
