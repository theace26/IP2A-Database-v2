"""Dues payments router for API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.db.session import get_db
from src.db.enums import DuesPaymentStatus
from src.schemas.dues_payment import (
    DuesPaymentCreate,
    DuesPaymentRecord,
    DuesPaymentUpdate,
    DuesPaymentRead,
    DuesPaymentWithMember,
    MemberDuesSummary,
)
from src.services.dues_payment_service import (
    create_payment_record,
    get_payment,
    get_member_payments,
    get_period_payments,
    get_all_payments,
    update_payment,
    delete_payment,
    record_payment,
    generate_period_dues,
    update_overdue_status,
    get_member_dues_summary,
)

router = APIRouter(prefix="/dues-payments", tags=["Dues Payments"])


@router.post("/", response_model=DuesPaymentRead, status_code=201)
def create(data: DuesPaymentCreate, db: Session = Depends(get_db)):
    """Create a new dues payment record."""
    return create_payment_record(db, data)


@router.post("/generate/{period_id}", response_model=List[DuesPaymentRead], status_code=201)
def generate_for_period(period_id: int, db: Session = Depends(get_db)):
    """Generate dues payment records for all active members for a period."""
    try:
        payments = generate_period_dues(db, period_id)
        if not payments:
            raise HTTPException(
                status_code=400,
                detail="No payments generated. Period may not exist or no active members."
            )
        return payments
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{payment_id}/record", response_model=DuesPaymentRead)
def record(
    payment_id: int,
    data: DuesPaymentRecord,
    processed_by_id: int = Query(..., description="User ID of the processor"),
    db: Session = Depends(get_db)
):
    """Record a payment against an existing dues record."""
    payment = record_payment(db, payment_id, data, processed_by_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Dues payment not found")
    return payment


@router.post("/update-overdue")
def mark_overdue(db: Session = Depends(get_db)):
    """Update all overdue payment statuses."""
    count = update_overdue_status(db)
    return {"message": f"Updated {count} payments to overdue status"}


@router.get("/member/{member_id}", response_model=List[DuesPaymentRead])
def read_member_payments(member_id: int, db: Session = Depends(get_db)):
    """Get all payments for a member."""
    return get_member_payments(db, member_id)


@router.get("/member/{member_id}/summary", response_model=MemberDuesSummary)
def read_member_summary(member_id: int, db: Session = Depends(get_db)):
    """Get dues summary for a member."""
    summary = get_member_dues_summary(db, member_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Member not found")
    return summary


@router.get("/period/{period_id}", response_model=List[DuesPaymentWithMember])
def read_period_payments(period_id: int, db: Session = Depends(get_db)):
    """Get all payments for a period."""
    return get_period_payments(db, period_id)


@router.get("/{payment_id}", response_model=DuesPaymentRead)
def read(payment_id: int, db: Session = Depends(get_db)):
    """Get a dues payment by ID."""
    payment = get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Dues payment not found")
    return payment


@router.get("/", response_model=List[DuesPaymentRead])
def list_all(
    status: Optional[DuesPaymentStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all dues payments with optional filtering."""
    return get_all_payments(db, status, skip, limit)


@router.put("/{payment_id}", response_model=DuesPaymentRead)
def update(payment_id: int, data: DuesPaymentUpdate, db: Session = Depends(get_db)):
    """Update a dues payment."""
    payment = update_payment(db, payment_id, data)
    if not payment:
        raise HTTPException(status_code=404, detail="Dues payment not found")
    return payment


@router.delete("/{payment_id}")
def delete(payment_id: int, db: Session = Depends(get_db)):
    """Delete a dues payment (soft delete)."""
    if not delete_payment(db, payment_id):
        raise HTTPException(status_code=404, detail="Dues payment not found")
    return {"message": "Dues payment deleted"}
