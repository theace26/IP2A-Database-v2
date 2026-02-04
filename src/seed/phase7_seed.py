"""
Phase 7 Seed Data - Referral Books

Created: February 4, 2026 (Week 20)
Based on: IBEW Local 46 Referral Procedures and LaborPower data analysis

Seeds the 11 referral books identified from LaborPower data analysis.
"""
from datetime import time
from sqlalchemy.orm import Session

from src.models import ReferralBook
from src.db.enums import BookClassification, BookRegion
from .base_seed import add_records


# Referral book seed data based on LOCAL46_REFERRAL_BOOKS.md and LaborPower analysis
REFERRAL_BOOKS = [
    # Inside Wireperson - Seattle (8:30 AM referral)
    {
        "name": "Wire Seattle",
        "code": "WIRE_SEA_1",
        "classification": BookClassification.INSIDE_WIREPERSON,
        "book_number": 1,
        "region": BookRegion.SEATTLE,
        "referral_start_time": time(8, 30),
        "re_sign_days": 30,
        "max_check_marks": 2,
        "grace_period_days": 3,
        "max_days_on_book": None,  # No limit
        "internet_bidding_enabled": True,
        "is_active": True,
    },
    {
        "name": "Wire Seattle",
        "code": "WIRE_SEA_2",
        "classification": BookClassification.INSIDE_WIREPERSON,
        "book_number": 2,
        "region": BookRegion.SEATTLE,
        "referral_start_time": time(8, 30),
        "re_sign_days": 30,
        "max_check_marks": 2,
        "grace_period_days": 3,
        "max_days_on_book": None,
        "internet_bidding_enabled": True,
        "is_active": True,
    },
    # Inside Wireperson - Bremerton (8:30 AM referral)
    {
        "name": "Wire Bremerton",
        "code": "WIRE_BREM_1",
        "classification": BookClassification.INSIDE_WIREPERSON,
        "book_number": 1,
        "region": BookRegion.BREMERTON,
        "referral_start_time": time(8, 30),
        "re_sign_days": 30,
        "max_check_marks": 2,
        "grace_period_days": 3,
        "max_days_on_book": None,
        "internet_bidding_enabled": True,
        "is_active": True,
    },
    {
        "name": "Wire Bremerton",
        "code": "WIRE_BREM_2",
        "classification": BookClassification.INSIDE_WIREPERSON,
        "book_number": 2,
        "region": BookRegion.BREMERTON,
        "referral_start_time": time(8, 30),
        "re_sign_days": 30,
        "max_check_marks": 2,
        "grace_period_days": 3,
        "max_days_on_book": None,
        "internet_bidding_enabled": True,
        "is_active": True,
    },
    # Inside Wireperson - Port Angeles (8:30 AM referral)
    {
        "name": "Wire Port Angeles",
        "code": "WIRE_PA_1",
        "classification": BookClassification.INSIDE_WIREPERSON,
        "book_number": 1,
        "region": BookRegion.PORT_ANGELES,
        "referral_start_time": time(8, 30),
        "re_sign_days": 30,
        "max_check_marks": 2,
        "grace_period_days": 3,
        "max_days_on_book": None,
        "internet_bidding_enabled": True,
        "is_active": True,
    },
    {
        "name": "Wire Port Angeles",
        "code": "WIRE_PA_2",
        "classification": BookClassification.INSIDE_WIREPERSON,
        "book_number": 2,
        "region": BookRegion.PORT_ANGELES,
        "referral_start_time": time(8, 30),
        "re_sign_days": 30,
        "max_check_marks": 2,
        "grace_period_days": 3,
        "max_days_on_book": None,
        "internet_bidding_enabled": True,
        "is_active": True,
    },
    # Tradeshow - Seattle (9:00 AM referral)
    {
        "name": "Tradeshow Seattle",
        "code": "TRADE_SEA_1",
        "classification": BookClassification.TRADESHOW,
        "book_number": 1,
        "region": BookRegion.SEATTLE,
        "referral_start_time": time(9, 0),
        "re_sign_days": 30,
        "max_check_marks": 2,
        "grace_period_days": 3,
        "max_days_on_book": None,
        "internet_bidding_enabled": True,
        "is_active": True,
    },
    # Sound & Communication - Seattle (9:30 AM referral)
    {
        "name": "Sound Seattle",
        "code": "SOUND_SEA_1",
        "classification": BookClassification.SOUND_COMM,
        "book_number": 1,
        "region": BookRegion.SEATTLE,
        "referral_start_time": time(9, 30),
        "re_sign_days": 30,
        "max_check_marks": 2,
        "grace_period_days": 3,
        "max_days_on_book": None,
        "internet_bidding_enabled": True,
        "is_active": True,
    },
    # Stockperson - Seattle (9:30 AM referral)
    {
        "name": "Stockperson Seattle",
        "code": "STOCK_SEA_1",
        "classification": BookClassification.STOCKPERSON,
        "book_number": 1,
        "region": BookRegion.SEATTLE,
        "referral_start_time": time(9, 30),
        "re_sign_days": 30,
        "max_check_marks": 2,
        "grace_period_days": 3,
        "max_days_on_book": None,
        "internet_bidding_enabled": True,
        "is_active": True,
    },
    # Residential - Seattle (9:30 AM referral)
    {
        "name": "Residential Seattle",
        "code": "RES_SEA_1",
        "classification": BookClassification.RESIDENTIAL,
        "book_number": 1,
        "region": BookRegion.SEATTLE,
        "referral_start_time": time(9, 30),
        "re_sign_days": 30,
        "max_check_marks": 2,
        "grace_period_days": 3,
        "max_days_on_book": None,
        "internet_bidding_enabled": True,
        "is_active": True,
    },
    # Technician - Seattle (9:30 AM referral)
    {
        "name": "Technician Seattle",
        "code": "TECH_SEA_1",
        "classification": BookClassification.TECHNICIAN,
        "book_number": 1,
        "region": BookRegion.SEATTLE,
        "referral_start_time": time(9, 30),
        "re_sign_days": 30,
        "max_check_marks": 2,
        "grace_period_days": 3,
        "max_days_on_book": None,
        "internet_bidding_enabled": True,
        "is_active": True,
    },
]


def seed_referral_books(db: Session, verbose: bool = False):
    """
    Seed the referral books.

    Based on IBEW Local 46 Referral Procedures and LaborPower data analysis.
    Creates 11 books across 3 regions.
    """
    books = []

    for book_data in REFERRAL_BOOKS:
        book = ReferralBook(**book_data)
        books.append(book)

    add_records(db, books)

    if verbose:
        print(f"  - Seeded {len(books)} referral books")

    return {"books_created": len(books)}


def run_phase7_seed(db: Session, verbose: bool = True):
    """
    Run all Phase 7 seeds.

    Currently seeds:
    - Referral books (11 books)

    Future additions:
    - Sample registrations
    - Sample labor requests
    - Sample dispatches
    """
    print("🔄 Running Phase 7 seeds (Referral & Dispatch)...")

    results = {}

    # Seed referral books
    book_results = seed_referral_books(db, verbose=verbose)
    results.update(book_results)

    print(f"✅ Phase 7 seeding complete: {results['books_created']} referral books created")

    return results
