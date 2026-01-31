"""Seed expenses data - program purchases and costs."""

from datetime import timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from faker import Faker

from src.models.expense import Expense
from src.models.grant import Grant
from src.models.student import Student
from src.models.location import Location
from src.db.enums import PaymentMethod
from .base_seed import add_records

fake = Faker()


def seed_expenses(db: Session, count: int = 200):
    """
    Seed expense records linked to grants, students, and locations.
    """
    # Get existing records to link
    grants = db.query(Grant).filter(Grant.deleted_at.is_(None)).all()
    students = db.query(Student).filter(Student.deleted_at.is_(None)).all()
    locations = db.query(Location).filter(Location.deleted_at.is_(None)).all()

    if not grants:
        print("No grants found - skipping expense seeding")
        return []

    expenses = []

    expense_items = [
        {"item": "Hand Tools Set", "category": "tools", "price_range": (150, 500)},
        {"item": "Power Drill", "category": "tools", "price_range": (100, 300)},
        {"item": "Multimeter", "category": "tools", "price_range": (50, 200)},
        {"item": "Wire Strippers", "category": "tools", "price_range": (20, 80)},
        {"item": "Safety Glasses", "category": "safety", "price_range": (15, 50)},
        {"item": "Hard Hat", "category": "safety", "price_range": (25, 75)},
        {"item": "Work Gloves", "category": "safety", "price_range": (15, 45)},
        {"item": "Electrical Wire (500ft)", "category": "supplies", "price_range": (100, 300)},
        {"item": "Conduit Bundle", "category": "supplies", "price_range": (50, 150)},
        {"item": "Junction Boxes (20 pack)", "category": "supplies", "price_range": (40, 120)},
        {"item": "Textbook - NEC Code", "category": "materials", "price_range": (80, 150)},
        {"item": "Training Manual", "category": "materials", "price_range": (30, 80)},
        {"item": "First Aid Certification", "category": "certifications", "price_range": (50, 100)},
        {"item": "OSHA 10 Certification", "category": "certifications", "price_range": (75, 150)},
        {"item": "Travel Reimbursement", "category": "travel", "price_range": (50, 200)},
        {"item": "Classroom Supplies", "category": "instruction", "price_range": (100, 500)},
        {"item": "Equipment Rental", "category": "equipment", "price_range": (200, 800)},
    ]

    vendors = [
        "Home Depot",
        "Lowes",
        "Grainger",
        "Platt Electric",
        "Amazon Business",
        "IBEW Supply Co",
        "Safety First Inc",
        "Training Materials LLC",
    ]

    payment_methods = list(PaymentMethod)

    for i in range(count):
        item_template = fake.random_element(expense_items)

        # Determine linkages (some expenses link to grants, students, locations)
        grant = fake.random_element(grants) if fake.boolean(chance_of_getting_true=70) else None
        student = fake.random_element(students) if students and fake.boolean(chance_of_getting_true=40) else None
        location = fake.random_element(locations) if locations and fake.boolean(chance_of_getting_true=50) else None

        quantity = fake.random_int(min=1, max=5)
        unit_price = Decimal(fake.random_int(
            min=item_template["price_range"][0],
            max=item_template["price_range"][1]
        ))
        total_price = unit_price * quantity

        # Sometimes add tax
        tax = None
        if fake.boolean(chance_of_getting_true=60):
            tax = (total_price * Decimal("0.10")).quantize(Decimal("0.01"))

        purchased_at = fake.date_between(start_date="-1y", end_date="today")

        expense = Expense(
            student_id=student.id if student else None,
            location_id=location.id if location else None,
            grant_id=grant.id if grant else None,
            item=item_template["item"],
            description=fake.sentence() if fake.boolean(chance_of_getting_true=30) else None,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price + (tax or Decimal("0")),
            tax=tax,
            category=item_template["category"],
            vendor=fake.random_element(vendors),
            payment_method=fake.random_element(payment_methods),
            receipt_number=f"RCP-{fake.random_int(min=10000, max=99999)}" if fake.boolean(chance_of_getting_true=70) else None,
            purchased_at=purchased_at,
            notes=fake.sentence() if fake.boolean(chance_of_getting_true=20) else None,
        )
        expenses.append(expense)

    if expenses:
        add_records(db, expenses)

    print(f"Seeded {len(expenses)} expenses.")
    return expenses
