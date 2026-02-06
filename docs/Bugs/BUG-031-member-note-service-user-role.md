# Bug #031: Member Note Service User.role Attribute Error

**Filed:** February 6, 2026 (Week 39 Bug Squash)
**Fixed:** February 6, 2026 (Week 39 Bug Squash)
**Severity:** Medium — 2 test failures, schema drift
**Status:** ✅ RESOLVED
**Category:** Schema drift / API mismatch

## Issue

Member notes API tests failing with AttributeError when service tries to access `user.role`.

## Error

```
AttributeError: 'User' object has no attribute 'role'. Did you mean: 'roles'?
```

**Stack trace:**
```
src/services/member_note_service.py:96: in _get_visible_levels
    if user.role == "admin":
       ^^^^^^^^^
AttributeError: 'User' object has no attribute 'role'
```

## Root Cause

**Schema drift:** The User model API changed in Week 11 to support multiple roles via UserRole junction table, but the member_note_service.py wasn't updated.

### What the User model actually has:

```python
# src/models/user.py (Week 11+)
class User(Base):
    user_roles: Mapped[list["UserRole"]] = relationship(...)

    @property
    def role_names(self) -> list[str]:
        """Return list of role names for this user."""
        return [ur.role.name for ur in self.user_roles if ur.role]

    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return role_name.lower() in [r.lower() for r in self.role_names]
```

**Note:** No `role` attribute — users can have MULTIPLE roles, not a single role.

### What the service tried to do (WRONG):

```python
# src/services/member_note_service.py - BEFORE
def _get_visible_levels(user: User) -> List[str]:
    if user.role == "admin":  # ❌ AttributeError
        return [...]

    if user.role in ["officer", "organizer"]:  # ❌ AttributeError
        return [...]
```

## Solution

Changed to use `has_role()` method:

```python
# src/services/member_note_service.py - AFTER
def _get_visible_levels(user: User) -> List[str]:
    # Admin sees everything
    if user.has_role("admin"):  # ✅ Correct
        return [
            NoteVisibility.STAFF_ONLY,
            NoteVisibility.OFFICERS,
            NoteVisibility.ALL_AUTHORIZED,
        ]

    # Officers see officers and all_authorized
    if user.has_role("officer") or user.has_role("organizer"):  # ✅ Correct
        return [NoteVisibility.OFFICERS, NoteVisibility.ALL_AUTHORIZED]

    # Staff sees only all_authorized
    return [NoteVisibility.ALL_AUTHORIZED]
```

**Also fixed line 76:**
```python
# BEFORE
if current_user.role not in ["admin", "officer"]:  # ❌ AttributeError

# AFTER
if not (current_user.has_role("admin") or current_user.has_role("officer")):  # ✅ Correct
```

## Files Modified

- ✅ `src/services/member_note_service.py` — Fixed 2 occurrences of `user.role`

## Impact

**Fixed 2 test failures:**
- test_get_notes_for_member ✅
- test_get_note_by_id ✅

**Production impact:** This would have caused 500 errors in production when trying to view member notes.

## Prevention

1. **Grep for old attributes after model changes:**
   ```bash
   grep -rn "user\.role\b" src/services/ src/routers/
   ```

2. **Static type checking:** Consider `mypy` or `pyright` to catch attribute errors at dev time

3. **Deprecation warnings:** Add warnings before removing model attributes

4. **Test coverage:** Ensure tests exercise all code paths that use model attributes

## Lessons Learned

- Schema changes must cascade to ALL consumers (services, routers, tests)
- Single-role → multi-role migration is a breaking change
- Always search codebase for attribute references before changing models
- Week 11 migration missed updating this service

## References

- User model changes: Week 11 (multi-role support via UserRole junction table)
- Commit: `f8a566d` (Week 39 bug squash)
- Session log: `docs/reports/session-logs/2026-02-06-week39-bug-squash.md`
- BUGS_LOG.md: Entry #031
