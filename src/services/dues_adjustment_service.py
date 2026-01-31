"""Service for dues adjustment operations."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from src.db.enums import AdjustmentStatus
from src.models.dues_adjustment import DuesAdjustment
from src.models.dues_payment import DuesPayment
from src.schemas.dues_adjustment import DuesAdjustmentCreate


def get_adjustment(db: Session, adjustment_id: int) -> Optional[DuesAdjustment]:
    """Get an adjustment by ID."""
    return db.query(DuesAdjustment).filter(DuesAdjustment.id == adjustment_id).first()


def get_pending_adjustments(db: Session) -> list[DuesAdjustment]:
    """Get all pending adjustments."""
    return db.query(DuesAdjustment).filter(
        DuesAdjustment.status == AdjustmentStatus.PENDING
    ).order_by(DuesAdjustment.created_at).all()


def get_member_adjustments(db: Session, member_id: int) -> list[DuesAdjustment]:
    """Get all adjustments for a member."""
    return db.query(DuesAdjustment).filter(
        DuesAdjustment.member_id == member_id
    ).order_by(DuesAdjustment.created_at.desc()).all()


def get_all_adjustments(
    db: Session,
    status: Optional[AdjustmentStatus] = None,
    skip: int = 0,
    limit: int = 100
) -> list[DuesAdjustment]:
    """Get all adjustments with optional filtering."""
    query = db.query(DuesAdjustment)
    if status:
        query = query.filter(DuesAdjustment.status == status)
    return query.order_by(DuesAdjustment.created_at.desc()).offset(skip).limit(limit).all()


def create_adjustment(
    db: Session,
    data: DuesAdjustmentCreate,
    requested_by_id: int
) -> DuesAdjustment:
    """Create a new adjustment request."""
    adjustment = DuesAdjustment(
        **data.model_dump(),
        requested_by_id=requested_by_id,
        status=AdjustmentStatus.PENDING
    )
    db.add(adjustment)
    db.commit()
    db.refresh(adjustment)
    return adjustment


def approve_adjustment(
    db: Session,
    adjustment_id: int,
    approved_by_id: int,
    approved: bool
) -> Optional[DuesAdjustment]:
    """Approve or deny an adjustment."""
    adjustment = get_adjustment(db, adjustment_id)
    if not adjustment or adjustment.status != AdjustmentStatus.PENDING:
        return None

    adjustment.status = AdjustmentStatus.APPROVED if approved else AdjustmentStatus.DENIED
    adjustment.approved_by_id = approved_by_id
    adjustment.approved_at = datetime.utcnow()

    # If approved and linked to a payment, apply the adjustment
    if approved and adjustment.payment_id:
        payment = db.query(DuesPayment).filter(DuesPayment.id == adjustment.payment_id).first()
        if payment:
            # Negative amount = credit (reduces amount due)
            # Positive amount = charge (increases amount due)
            payment.amount_due = Decimal(str(payment.amount_due)) + Decimal(str(adjustment.amount))

    db.commit()
    db.refresh(adjustment)
    return adjustment


def delete_adjustment(db: Session, adjustment_id: int) -> bool:
    """Delete an adjustment (only if pending)."""
    adjustment = get_adjustment(db, adjustment_id)
    if not adjustment or adjustment.status != AdjustmentStatus.PENDING:
        return False
    db.delete(adjustment)
    db.commit()
    return True
