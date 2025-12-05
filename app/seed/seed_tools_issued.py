from sqlalchemy.orm import Session
from faker import Faker
import random

from app.models import ToolsIssued, Student
from .base_seed import add_records

fake = Faker()

TOOL_LIST = [
    "Lineman's Pliers",
    "Side Cutters",
    "Screwdriver Set",
    "Needle Nose Pliers",
    "Tape Measure (25ft)",
    "Voltage Tester",
    "Tool Pouch",
    "Channel Locks",
    "Hammer",
    "Wire Strippers",
    "Utility Knife",
    "Flashlight",
]

def seed_tools_issued(db: Session, count_per_student: int = 3):
    students = db.query(Student).all()

    if not students:
        print("❌ Cannot seed tools — no students found.")
        return

    tools = []

    for student in students:
        for _ in range(count_per_student):
            tools.append(
                ToolsIssued(
                    student_id=student.id,
                    tool_name=random.choice(TOOL_LIST),
                    quantity=random.randint(1, 2),
                    date_issued=fake.date_between(start_date="-6m", end_date="today"),
                    notes=fake.sentence() if random.random() < 0.3 else None,
                )
            )

    add_records(db, tools)
    print(f"Seeded {len(tools)} tools issued.")
