"""Enums for dues tracking system."""
from enum import Enum


class DuesPaymentMethod(str, Enum):
    """How dues were paid."""
    PAYROLL_DEDUCTION = "payroll_deduction"
    CHECK = "check"
    CASH = "cash"
    MONEY_ORDER = "money_order"
    CREDIT_CARD = "credit_card"
    ACH_TRANSFER = "ach_transfer"
    ONLINE = "online"
    # Stripe payment methods (added Phase 2)
    STRIPE_CARD = "stripe_card"          # Credit/debit via Stripe Checkout
    STRIPE_ACH = "stripe_ach"            # ACH bank transfer via Stripe
    STRIPE_OTHER = "stripe_other"        # Future Stripe methods (Apple Pay, etc.)
    OTHER = "other"


class DuesPaymentStatus(str, Enum):
    """Status of a dues payment."""
    PENDING = "pending"          # Not yet due
    DUE = "due"                  # Due, not paid
    PARTIAL = "partial"          # Partially paid
    PAID = "paid"                # Paid in full
    OVERDUE = "overdue"          # Past grace period
    WAIVED = "waived"            # Waived (e.g., hardship)
    WRITTEN_OFF = "written_off"  # Uncollectable


class DuesAdjustmentType(str, Enum):
    """Type of dues adjustment."""
    WAIVER = "waiver"              # Full or partial waiver
    HARDSHIP = "hardship"          # Hardship reduction
    CREDIT = "credit"              # Credit for overpayment
    CORRECTION = "correction"      # Error correction
    LATE_FEE = "late_fee"          # Late payment fee
    REINSTATEMENT = "reinstatement"  # Reinstatement fee
    OTHER = "other"


class AdjustmentStatus(str, Enum):
    """Approval status for adjustments."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
