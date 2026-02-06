# Bug #033: Referral Frontend Test Fixture Isolation

**Filed:** February 6, 2026 (Week 39 Bug Squash)
**Fixed:** February 6, 2026 (Week 39 Bug Squash)
**Severity:** Medium — 4 test failures
**Status:** ✅ RESOLVED
**Category:** Test infrastructure / Fixture isolation

## Issue

Referral frontend tests failing because test data not rendered in HTML responses.

## Error

```
AssertionError: assert b'Test Book' in response.content
  where b'Test Book' = <built-in method encode of str object>.encode()
  and response.content = b'<!DOCTYPE html>...empty page...'
```

**Expected:** HTML contains "Test Book"
**Actual:** HTML renders but empty — no book data

## Root Cause

**Fixture isolation:** Same as Bug #032, but with synchronous TestClient.

### The Problem:

```python
# test_referral_frontend.py - BEFORE
@pytest.fixture
def test_book(db):  # 'db' is alias for db_session (transactional)
    book = ReferralBook(
        name="Test Book",
        code="TEST_BOOK_1",
        classification=BookClassification.INSIDE_WIREPERSON,
        ...
    )
    db.add(book)
    db.commit()  # ← Commits to TRANSACTION, not real database
    return book

client = TestClient(app)  # Module-level client

def test_books_list_renders(auth_cookies, test_book):
    response = client.get("/referral/books", cookies=auth_cookies)
    assert b"Test Book" in response.content  # ❌ FAILS
```

### Why it failed:

1. **`test_book(db)` creates book in transactional session:**
   ```python
   # conftest.py
   @pytest.fixture
   def db_session():
       connection = engine.connect()
       transaction = connection.begin()
       session = TestingSessionLocal(bind=connection)
       yield session
       transaction.rollback()  # ← Data destroyed, never in real DB
   ```

2. **Module-level `client` uses FastAPI app's normal `get_db()`:**
   ```python
   # src/db/session.py
   def get_db():
       db = SessionLocal()  # ← NEW connection to real database
       try:
           yield db
       finally:
           db.close()
   ```

3. **Backend queries for books → finds nothing:**
   ```python
   # src/routers/referral_frontend.py
   @router.get("/referral/books")
   async def books_list(db: Session = Depends(get_db)):
       books = db.query(ReferralBook).all()  # ← Empty! Book only in transaction
       return templates.TemplateResponse("referral/books.html", {"books": books})
   ```

4. **Template renders with empty list → test assertion fails**

### Why not use `async_client_with_db`?

These are synchronous tests with module-level `client = TestClient(app)`. Converting to async would require rewriting all tests. Easier to fix the fixture.

## Solution

**Rewrote `test_book` fixture to commit to REAL database:**

### Before (Transaction, Invisible to Client):
```python
@pytest.fixture
def test_book(db):  # Uses transactional db_session
    book = ReferralBook(name="Test Book", ...)
    db.add(book)
    db.commit()  # Transaction commit only
    return book
```

### After (Real DB, Visible to Client):
```python
@pytest.fixture(scope="function")
def test_book():
    """Create test referral book outside of test transaction."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.config.settings import settings

    # Create NEW session that commits to REAL database
    engine = create_engine(str(settings.DATABASE_URL), echo=False)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Clean up any existing test book
        existing = db.query(ReferralBook).filter(
            ReferralBook.code == "TEST_BOOK_1"
        ).first()
        if existing:
            db.delete(existing)
            db.commit()

        # Create test book
        book = ReferralBook(
            name="Test Book",
            code="TEST_BOOK_1",
            classification=BookClassification.INSIDE_WIREPERSON,
            book_number=1,
            region=BookRegion.SEATTLE,
            re_sign_days=30,
            max_check_marks=2,
            is_active=True,
        )
        db.add(book)
        db.commit()  # ✅ Real commit to database
        db.refresh(book)

        yield book  # Test runs with book visible in DB

        # Cleanup AFTER test
        db.delete(book)
        db.commit()
    finally:
        db.close()
```

### Key Changes:

1. **No `db` parameter** — creates own engine/session
2. **Real database commits** — not transactional
3. **Yield pattern** — cleanup happens after test
4. **Delete in finally** — ensures cleanup even if test fails
5. **Pre-cleanup check** — handles leftover data from failed previous tests

## Files Modified

- ✅ `src/tests/test_referral_frontend.py` — Rewrote `test_book` fixture

## Impact

**Fixed 4 test failures:**
- test_books_list_renders ✅
- test_book_detail_renders ✅
- test_books_overview_partial_returns_html ✅
- test_registration_detail_renders ✅

## Trade-offs

### Pros:
- ✅ Simple fix — just one fixture
- ✅ No need to rewrite all tests to async
- ✅ Follows same pattern as other frontend tests

### Cons:
- ❌ Uses real database, not transaction isolation
- ❌ Slower than transactional tests (real DB commits)
- ❌ Risk of data leaking if cleanup fails

### Mitigation:
- Use unique test codes (TEST_BOOK_1) that won't collide with real data
- Pre-cleanup before creating test data
- Cleanup in finally block to handle test failures

## Alternative Solutions

### Option A: Convert to `async_client_with_db` (NOT CHOSEN)
```python
async def test_books_list_renders(async_client_with_db, test_book):
    client, db_session = async_client_with_db
    # Create book in db_session...
    response = await client.get("/referral/books")
```
**Rejected:** Too much test rewriting for minimal benefit.

### Option B: Use cleanup fixture (Bug #030 pattern)
**Rejected:** Cleanup doesn't help if client can't see data in first place.

### Option C: Commit to real DB (CHOSEN ✅)
**Benefit:** Simple, works with existing synchronous tests.

## Prevention

1. **Rule:** For frontend tests using TestClient, fixtures must commit to real DB
2. **Pattern:** Create separate engine/session for fixture data
3. **Cleanup:** Always use yield + finally block
4. **Alternative:** Convert frontend tests to async with `async_client_with_db`

## Lessons Learned

- TestClient + `db_session` fixtures = recipe for failure
- Two solutions: shared session (async) OR real DB commits (sync)
- Real DB commits are simpler but slower
- Always cleanup in finally block

## References

- Similar issue: Bug #032 (member notes API — different solution)
- Cleanup pattern: Bug #030 (dues test cleanup fixture)
- Commit: `f8a566d` (Week 39 bug squash)
- Session log: `docs/reports/session-logs/2026-02-06-week39-bug-squash.md`
- BUGS_LOG.md: Entry #033
