"""Tests for Dues Tracking endpoints (Phase 4)."""

import uuid
import time


# Sequential counter for guaranteed uniqueness within a test run
# Use nanoseconds to get a unique base that changes each run
_base = time.time_ns() % 1_000_000_000
_call_counter = 0


def get_unique_date(base_year: int = 2100) -> str:
    """Generate a unique future date for testing to avoid constraint violations.

    Uses years in the 2500-2999 range (valid dates but won't conflict with seed data).
    """
    global _call_counter
    _call_counter += 1
    # Year range 2500-2999: avoids seed data (2025-2100) and stays within 4-digit years
    unique_val = (_base + _call_counter) % 500
    year = 2500 + unique_val
    month = (_call_counter % 12) + 1
    day = (_call_counter % 28) + 1
    return f"{year}-{month:02d}-{day:02d}"


def get_unique_year_month() -> tuple[int, int]:
    """Generate a unique future year/month combo for testing to avoid constraint violations.

    Uses years in 2090-2100 range with nanosecond-based uniqueness.
    Schema limits period_year to 2000-2100.
    """
    global _call_counter
    _call_counter += 1
    # Map to year range 2090-2100 (11 years) × 12 months = 132 combinations
    # Use nanoseconds + counter for uniqueness
    unique_val = (_base + _call_counter)
    year = 2090 + (unique_val % 11)  # 2090-2100
    month = ((unique_val // 11) % 12) + 1  # 1-12
    return year, month


# ============================================================================
# DUES RATES TESTS
# ============================================================================

async def test_create_dues_rate(async_client):
    """Test creating a new dues rate."""
    # Use a unique future date to avoid constraint violations
    payload = {
        "classification": "journeyman",
        "monthly_amount": "75.00",
        "effective_date": get_unique_date(2200),
        "end_date": None,
        "description": "Test journeyman rate"
    }

    response = await async_client.post("/dues-rates/", json=payload)
    assert response.status_code in (200, 201), f"Failed: {response.json()}"
    data = response.json()
    assert data["classification"] == "journeyman"
    assert "id" in data


async def test_get_dues_rate(async_client):
    """Test getting a dues rate by ID."""
    # Create rate first with unique date
    payload = {
        "classification": "apprentice_1",
        "monthly_amount": "35.00",
        "effective_date": get_unique_date(2300),
    }
    create_response = await async_client.post("/dues-rates/", json=payload)
    assert create_response.status_code in (200, 201), f"Create failed: {create_response.json()}"
    created = create_response.json()

    # Get the rate
    response = await async_client.get(f"/dues-rates/{created['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["classification"] == "apprentice_1"


async def test_list_dues_rates(async_client):
    """Test listing dues rates."""
    response = await async_client.get("/dues-rates/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_update_dues_rate(async_client):
    """Test updating a dues rate."""
    # Create rate first
    unique = str(uuid.uuid4())[:8]
    payload = {
        "classification": "foreman",
        "monthly_amount": "80.00",
        "effective_date": get_unique_date(2400),
    }
    create_response = await async_client.post("/dues-rates/", json=payload)
    assert create_response.status_code in (200, 201), f"Create failed: {create_response.json()}"
    created = create_response.json()

    # Update it
    update_payload = {
        "monthly_amount": "85.00",
        "description": "Updated foreman rate"
    }
    response = await async_client.put(
        f"/dues-rates/{created['id']}", json=update_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["monthly_amount"] == "85.00"


async def test_delete_dues_rate(async_client):
    """Test deleting a dues rate."""
    # Create rate first
    unique = str(uuid.uuid4())[:8]
    payload = {
        "classification": "retiree",
        "monthly_amount": "25.00",
        "effective_date": get_unique_date(2500),
    }
    create_response = await async_client.post("/dues-rates/", json=payload)
    assert create_response.status_code in (200, 201), f"Create failed: {create_response.json()}"
    created = create_response.json()

    # Delete it
    response = await async_client.delete(f"/dues-rates/{created['id']}")
    assert response.status_code == 200

    # Verify it's gone
    get_response = await async_client.get(f"/dues-rates/{created['id']}")
    assert get_response.status_code == 404


# ============================================================================
# DUES PERIODS TESTS
# ============================================================================

async def test_create_dues_period(async_client):
    """Test creating a new dues period."""
    unique_year, unique_month = get_unique_year_month()
    payload = {
        "period_year": unique_year,
        "period_month": unique_month,
        "due_date": f"{unique_year}-{unique_month:02d}-01",
        "grace_period_end": f"{unique_year}-{unique_month:02d}-15",
    }

    response = await async_client.post("/dues-periods/", json=payload)
    assert response.status_code in (200, 201), f"Failed: {response.json()}"
    data = response.json()
    assert data["period_year"] == unique_year
    assert data["period_month"] == unique_month
    assert "id" in data


async def test_get_dues_period(async_client):
    """Test getting a dues period by ID."""
    unique_year, unique_month = get_unique_year_month()
    payload = {
        "period_year": unique_year,
        "period_month": unique_month,
        "due_date": f"{unique_year}-{unique_month:02d}-01",
        "grace_period_end": f"{unique_year}-{unique_month:02d}-15",
    }
    create_response = await async_client.post("/dues-periods/", json=payload)
    assert create_response.status_code in (200, 201), f"Create failed: {create_response.json()}"
    created = create_response.json()

    # Get the period
    response = await async_client.get(f"/dues-periods/{created['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]


async def test_get_period_by_month(async_client):
    """Test getting a dues period by year and month."""
    unique_year, unique_month = get_unique_year_month()
    payload = {
        "period_year": unique_year,
        "period_month": unique_month,
        "due_date": f"{unique_year}-{unique_month:02d}-01",
        "grace_period_end": f"{unique_year}-{unique_month:02d}-15",
    }
    create_response = await async_client.post("/dues-periods/", json=payload)
    assert create_response.status_code in (200, 201), f"Create failed: {create_response.json()}"

    # Get by month
    response = await async_client.get(f"/dues-periods/by-month/{unique_year}/{unique_month}")
    assert response.status_code == 200
    data = response.json()
    assert data["period_year"] == unique_year
    assert data["period_month"] == unique_month


async def test_list_dues_periods(async_client):
    """Test listing dues periods."""
    response = await async_client.get("/dues-periods/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_close_dues_period(async_client):
    """Test closing a dues period."""
    unique_year, unique_month = get_unique_year_month()
    payload = {
        "period_year": unique_year,
        "period_month": unique_month,
        "due_date": f"{unique_year}-{unique_month:02d}-01",
        "grace_period_end": f"{unique_year}-{unique_month:02d}-15",
    }
    create_response = await async_client.post("/dues-periods/", json=payload)
    assert create_response.status_code in (200, 201), f"Create failed: {create_response.json()}"
    created = create_response.json()

    # Close it (closed_by_id is nullable since no users in test DB)
    close_payload = {"closed_by_id": None}
    response = await async_client.post(
        f"/dues-periods/{created['id']}/close", json=close_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_closed"] is True


# ============================================================================
# DUES PAYMENTS TESTS
# ============================================================================

async def test_create_dues_payment(async_client):
    """Test creating a new dues payment record."""
    # First create a period
    unique_year, unique_month = get_unique_year_month()
    period_payload = {
        "period_year": unique_year,
        "period_month": unique_month,
        "due_date": f"{unique_year}-{unique_month:02d}-01",
        "grace_period_end": f"{unique_year}-{unique_month:02d}-15",
    }
    period_response = await async_client.post("/dues-periods/", json=period_payload)
    assert period_response.status_code in (200, 201), f"Create period failed: {period_response.json()}"
    period = period_response.json()

    # Create member
    unique = str(uuid.uuid4())[:8]
    member_payload = {
        "member_number": f"M{unique}",
        "first_name": "Test",
        "last_name": "Member",
        "classification": "journeyman",
    }
    member_response = await async_client.post("/members/", json=member_payload)
    assert member_response.status_code in (200, 201)
    member = member_response.json()

    # Create payment
    payment_payload = {
        "member_id": member["id"],
        "period_id": period["id"],
        "amount_due": "75.00",
    }
    response = await async_client.post("/dues-payments/", json=payment_payload)
    assert response.status_code in (200, 201), f"Failed: {response.json()}"
    data = response.json()
    assert data["member_id"] == member["id"]


async def test_get_dues_payment(async_client):
    """Test getting a dues payment by ID."""
    # Create payment first
    unique_year, unique_month = get_unique_year_month()
    period_payload = {
        "period_year": unique_year,
        "period_month": unique_month,
        "due_date": f"{unique_year}-{unique_month:02d}-01",
        "grace_period_end": f"{unique_year}-{unique_month:02d}-15",
    }
    period_response = await async_client.post("/dues-periods/", json=period_payload)
    assert period_response.status_code in (200, 201), f"Create period failed: {period_response.json()}"
    period = period_response.json()

    unique = str(uuid.uuid4())[:8]
    member_payload = {
        "member_number": f"M{unique}",
        "first_name": "Test",
        "last_name": "Member2",
        "classification": "apprentice_1",
    }
    member_response = await async_client.post("/members/", json=member_payload)
    assert member_response.status_code in (200, 201)
    member = member_response.json()

    payment_payload = {
        "member_id": member["id"],
        "period_id": period["id"],
        "amount_due": "35.00",
    }
    create_response = await async_client.post("/dues-payments/", json=payment_payload)
    assert create_response.status_code in (200, 201)
    created = create_response.json()

    # Get the payment
    response = await async_client.get(f"/dues-payments/{created['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]


async def test_list_dues_payments(async_client):
    """Test listing dues payments."""
    response = await async_client.get("/dues-payments/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_update_overdue_status(async_client):
    """Test updating overdue payment statuses."""
    response = await async_client.post("/dues-payments/update-overdue")
    assert response.status_code == 200
    data = response.json()
    assert "Updated" in data["message"]


# ============================================================================
# DUES ADJUSTMENTS TESTS
# ============================================================================

async def test_create_dues_adjustment(async_client):
    """Test creating a new dues adjustment."""
    # Create member first
    unique = str(uuid.uuid4())[:8]
    member_payload = {
        "member_number": f"M{unique}",
        "first_name": "Adjust",
        "last_name": "Test",
        "classification": "journeyman",
    }
    member_response = await async_client.post("/members/", json=member_payload)
    assert member_response.status_code in (200, 201)
    member = member_response.json()

    # Create adjustment
    adjustment_payload = {
        "member_id": member["id"],
        "adjustment_type": "waiver",
        "amount": "-25.00",
        "reason": "Hardship waiver request",
    }
    response = await async_client.post(
        "/dues-adjustments/",
        json=adjustment_payload,
            )
    assert response.status_code in (200, 201), f"Failed: {response.json()}"
    data = response.json()
    assert data["member_id"] == member["id"]
    assert data["adjustment_type"] == "waiver"
    assert data["status"] == "pending"


async def test_get_dues_adjustment(async_client):
    """Test getting an adjustment by ID."""
    # Create member
    unique = str(uuid.uuid4())[:8]
    member_payload = {
        "member_number": f"M{unique}",
        "first_name": "Get",
        "last_name": "Adjust",
        "classification": "apprentice_2",
    }
    member_response = await async_client.post("/members/", json=member_payload)
    assert member_response.status_code in (200, 201)
    member = member_response.json()

    # Create adjustment
    adjustment_payload = {
        "member_id": member["id"],
        "adjustment_type": "credit",
        "amount": "-15.00",
        "reason": "Overpayment credit",
    }
    create_response = await async_client.post(
        "/dues-adjustments/",
        json=adjustment_payload,
            )
    assert create_response.status_code in (200, 201)
    created = create_response.json()

    # Get the adjustment
    response = await async_client.get(f"/dues-adjustments/{created['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]


async def test_list_dues_adjustments(async_client):
    """Test listing dues adjustments."""
    response = await async_client.get("/dues-adjustments/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_list_pending_adjustments(async_client):
    """Test listing pending adjustments."""
    response = await async_client.get("/dues-adjustments/pending")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


async def test_approve_adjustment(async_client):
    """Test approving an adjustment."""
    # Create member
    unique = str(uuid.uuid4())[:8]
    member_payload = {
        "member_number": f"M{unique}",
        "first_name": "Approve",
        "last_name": "Test",
        "classification": "foreman",
    }
    member_response = await async_client.post("/members/", json=member_payload)
    assert member_response.status_code in (200, 201)
    member = member_response.json()

    # Create adjustment
    adjustment_payload = {
        "member_id": member["id"],
        "adjustment_type": "hardship",
        "amount": "-50.00",
        "reason": "Hardship reduction",
    }
    create_response = await async_client.post(
        "/dues-adjustments/",
        json=adjustment_payload,
            )
    assert create_response.status_code in (200, 201)
    created = create_response.json()

    # Approve it
    approve_payload = {
        "approved_by_id": None,
        "approved": True
    }
    response = await async_client.post(
        f"/dues-adjustments/{created['id']}/approve", json=approve_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"


async def test_deny_adjustment(async_client):
    """Test denying an adjustment."""
    # Create member
    unique = str(uuid.uuid4())[:8]
    member_payload = {
        "member_number": f"M{unique}",
        "first_name": "Deny",
        "last_name": "Test",
        "classification": "apprentice_3",
    }
    member_response = await async_client.post("/members/", json=member_payload)
    assert member_response.status_code in (200, 201)
    member = member_response.json()

    # Create adjustment
    adjustment_payload = {
        "member_id": member["id"],
        "adjustment_type": "waiver",
        "amount": "-75.00",
        "reason": "Full waiver request",
    }
    create_response = await async_client.post(
        "/dues-adjustments/",
        json=adjustment_payload,
            )
    assert create_response.status_code in (200, 201)
    created = create_response.json()

    # Deny it
    deny_payload = {
        "approved_by_id": None,
        "approved": False
    }
    response = await async_client.post(
        f"/dues-adjustments/{created['id']}/approve", json=deny_payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "denied"


async def test_delete_pending_adjustment(async_client):
    """Test deleting a pending adjustment."""
    # Create member
    unique = str(uuid.uuid4())[:8]
    member_payload = {
        "member_number": f"M{unique}",
        "first_name": "Delete",
        "last_name": "Adjust",
        "classification": "apprentice_4",
    }
    member_response = await async_client.post("/members/", json=member_payload)
    assert member_response.status_code in (200, 201)
    member = member_response.json()

    # Create adjustment
    adjustment_payload = {
        "member_id": member["id"],
        "adjustment_type": "correction",
        "amount": "10.00",
        "reason": "Billing correction",
    }
    create_response = await async_client.post(
        "/dues-adjustments/",
        json=adjustment_payload,
            )
    assert create_response.status_code in (200, 201)
    created = create_response.json()

    # Delete it
    response = await async_client.delete(f"/dues-adjustments/{created['id']}")
    assert response.status_code == 200

    # Verify it's gone
    get_response = await async_client.get(f"/dues-adjustments/{created['id']}")
    assert get_response.status_code == 404
