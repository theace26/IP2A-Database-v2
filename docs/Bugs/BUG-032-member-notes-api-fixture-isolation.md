# Bug #032: Member Notes API Fixture Isolation

**Filed:** February 6, 2026 (Week 39 Bug Squash)
**Fixed:** February 6, 2026 (Week 39 Bug Squash)
**Severity:** High — 5 test failures, auth blocking
**Status:** ✅ RESOLVED
**Category:** Test infrastructure / Fixture isolation

## Issue

All member notes API tests failing with 401 Unauthorized despite using valid `auth_headers` and `test_user` fixtures.

## Error

```
AssertionError: assert 401 == 201
  where 401 = <Response [401 Unauthorized]>.status_code
```

**Expected:** 201 Created
**Actual:** 401 Unauthorized

## Root Cause

**Fixture isolation:** Test fixtures created data in one database session, but HTTP client used a completely separate session.

### The Problem Flow:

1. **Test uses 3 fixtures:**
   ```python
   def test_create_note(client, auth_headers, test_user):
   ```

2. **`test_user` fixture (conftest.py):**
   ```python
   @pytest.fixture
   def test_user(db_session):  # Transaction A (isolated)
       user = User(email="test@example.com", ...)
       db_session.add(user)
       db_session.commit()  # Commits to TRANSACTION, not real DB
       return user
   ```

3. **`auth_headers` fixture:**
   ```python
   @pytest.fixture
   def auth_headers(test_user):
       token = create_access_token(subject=test_user.id, ...)
       return {"Authorization": f"Bearer {token}"}
   ```

4. **`client` fixture:**
   ```python
   @pytest.fixture
   def client():
       return TestClient(app)  # Uses FastAPI app's get_db() dependency
   ```

5. **What happens when test runs:**
   ```
   Test makes request → FastAPI app receives JWT token with user_id
                     → get_current_user() queries for user_id in Session B
                     → User not found (only exists in Session A's transaction)
                     → Raises 401 Unauthorized
   ```

### Why Sessions Don't Share Data:

```python
# conftest.py
@pytest.fixture
def db_session():
    """Each test runs in a transaction that is rolled back after the test."""
    connection = engine.connect()
    transaction = connection.begin()  # ← Isolation boundary
    session = TestingSessionLocal(bind=connection)

    yield session  # Test runs here

    transaction.rollback()  # ← Data destroyed, never visible to other sessions
```

**Key insight:** `db_session` transactions are NEVER committed to the real database, so `client` (which uses real DB) can't see the data.

## Solution

**Converted tests to use `async_client_with_db` which shares the transaction:**

### Before (Synchronous, Separate Sessions):
```python
def test_create_note_endpoint(client, auth_headers, test_member):
    response = client.post("/api/v1/member-notes/",
                          json={...},
                          headers=auth_headers)
    assert response.status_code == 201  # ❌ FAILS: 401
```

### After (Async, Shared Session):
```python
async def test_create_note_endpoint(async_client_with_db):
    client, db_session = async_client_with_db  # Same session!

    # Create user in SAME session as client will use
    from src.models.user import User
    from src.models.role import Role
    from src.models.user_role import UserRole
    from src.core.security import hash_password

    admin_role = db_session.query(Role).filter(Role.name == "admin").first()
    test_user = User(
        email="test_api@example.com",
        password_hash=hash_password("testpass"),
        first_name="API",
        last_name="Test",
        is_active=True,
        is_verified=True,
    )
    db_session.add(test_user)
    db_session.flush()

    user_role = UserRole(user_id=test_user.id, role_id=admin_role.id)
    db_session.add(user_role)
    db_session.flush()

    # Create member in same session
    from src.models.member import Member
    from src.db.enums import MemberStatus, MemberClassification

    test_member = Member(
        first_name="Test",
        last_name="Member",
        member_number="API_TEST_001",
        email="api_member@test.com",
        status=MemberStatus.ACTIVE,
        classification=MemberClassification.JOURNEYMAN,
    )
    db_session.add(test_member)
    db_session.flush()

    # Create auth headers
    from src.core.jwt import create_access_token
    token = create_access_token(
        subject=test_user.id,
        additional_claims={"email": test_user.email, "roles": ["admin"]},
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Now client can see test_user!
    response = await client.post("/api/v1/member-notes/",
                                 json={
                                     "member_id": test_member.id,
                                     "note_text": "API test note",
                                     "visibility": "staff_only",
                                 },
                                 headers=headers)
    assert response.status_code == 201  # ✅ SUCCESS
```

### How `async_client_with_db` Works:

```python
# conftest.py
@pytest_asyncio.fixture
async def async_client_with_db():
    engine = get_test_engine()
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Override FastAPI's get_db() to use OUR session
    def override_get_db():
        yield session  # Same session as test uses!

    app.dependency_overrides[get_db] = override_get_db

    # Return BOTH client and session to test
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client, session  # ← Test gets both

    # Cleanup
    app.dependency_overrides.clear()
    transaction.rollback()
```

**Key insight:** Dependency override makes FastAPI use the test's session instead of creating a new one.

## Files Modified

- ✅ `src/tests/test_member_notes.py` — Converted 5 API tests to async with shared session

## Impact

**Fixed 5 test failures:**
- test_create_note_endpoint ✅
- test_get_notes_for_member ✅
- test_get_note_by_id ✅
- test_update_note_endpoint ✅
- test_delete_note_endpoint ✅

All 7 member notes API tests now passing (includes 2 auth tests that were already passing).

## Prevention

1. **Rule:** For API tests that need fixtures, ALWAYS use `async_client_with_db`
2. **Avoid:** Mixing `client` + `db_session` fixtures
3. **Alternative:** Create ALL test data via API calls (not fixtures)
4. **Documentation:** conftest.py has clear notes about session isolation

## Lessons Learned

- FastAPI TestClient creates separate database sessions by default
- Test fixtures using `db_session` are isolated from HTTP client
- `async_client_with_db` solves this by sharing the transaction
- Fixture isolation is the #1 cause of "works locally, fails in suite" test issues

## References

- Similar issue: Bug #030 (dues tests), Bug #033 (referral frontend)
- Fixture: `src/tests/conftest.py::async_client_with_db`
- Commit: `f8a566d` (Week 39 bug squash)
- Session log: `docs/reports/session-logs/2026-02-06-week39-bug-squash.md`
- BUGS_LOG.md: Entry #032
