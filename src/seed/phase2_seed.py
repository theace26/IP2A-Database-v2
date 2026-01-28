"""
Phase 2 Seed Data - Union Operations
=====================================
Creates realistic test data for:
- SALTing Activities (organizing at non-union employers)
- Benevolence Applications (financial assistance)
- Benevolence Reviews (approval workflow)
- Grievances with Step Records (formal complaints)

Usage:
    Import and call seed_phase2(db) from run_seed.py

Author: Claude
Date: January 28, 2026
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List

from sqlalchemy.orm import Session

# Import actual enums from src.db.enums
from src.db.enums import (
    SALTingActivityType,
    SALTingOutcome,
    BenevolenceReason,
    BenevolenceStatus,
    BenevolenceReviewLevel,
    BenevolenceReviewDecision,
    GrievanceStep,
    GrievanceStatus,
    GrievanceStepOutcome,
)

# ============================================================================
# SEED DATA GENERATORS
# ============================================================================

# Realistic salting activity types and descriptions
SALTING_ACTIVITY_DATA = {
    SALTingActivityType.OUTREACH: [
        "Initial contact made with workers at shift change",
        "Distributed union information cards to interested workers",
        "Spoke with workers during lunch break about organizing",
        "Made contact with key department leaders",
    ],
    SALTingActivityType.SITE_VISIT: [
        "Observed work site and identified key contact points",
        "Conducted site assessment for organizing potential",
        "Met workers outside facility to discuss conditions",
        "Toured facility with supportive employee",
    ],
    SALTingActivityType.LEAFLETING: [
        "Distributed organizing literature at shift change",
        "Leafleting at main entrance about union benefits",
        "Handed out flyers about upcoming meeting",
        "Posted union information on break room bulletin board",
    ],
    SALTingActivityType.ONE_ON_ONE: [
        "One-on-one conversation with interested worker",
        "Personal meeting to discuss union membership",
        "Coffee meeting with potential supporter",
        "Home visit to discuss organizing concerns",
    ],
    SALTingActivityType.MEETING: [
        "Held off-site meeting at union hall with workers",
        "House meeting with 8 interested workers",
        "Coffee shop meeting with department organizers",
        "Information session about union benefits",
    ],
    SALTingActivityType.PETITION_DRIVE: [
        "Petition drive to demonstrate worker support",
        "Gathered signatures for NLRB petition",
        "Filed NLRB petition with 40% showing of interest",
        "Petition challenge hearing with NLRB",
    ],
    SALTingActivityType.CARD_SIGNING: [
        "Collected authorization cards from interested workers",
        "25 cards distributed, 12 signed and returned",
        "Authorization card drive in progress",
        "Reached threshold for filing petition",
    ],
    SALTingActivityType.INFORMATION_SESSION: [
        "Information session about union benefits and process",
        "Q&A session with workers about organizing",
        "Presentation on contract negotiation process",
        "Educational meeting about worker rights",
    ],
    SALTingActivityType.OTHER: [
        "Follow-up call with interested worker",
        "Legal consultation regarding employer tactics",
        "Coordinated with community support groups",
        "Responded to employer anti-union campaign",
    ],
}

SALTING_NOTES = [
    "Employer hired union avoidance consultant",
    "Strong support in warehouse department",
    "Management surveilling break room conversations",
    "Workers concerned about retaliation",
    "Good momentum after wage theft complaint",
    "Need Spanish-language materials for night shift",
    "Key supporter promoted to supervisor role",
    "Company announced sudden wage increases",
    "NLRB investigation of ULP ongoing",
    "Workers ready to go public with campaign",
]

# Benevolence request descriptions by reason
BENEVOLENCE_DESCRIPTIONS = {
    BenevolenceReason.MEDICAL: [
        "Surgery recovery - unable to work for 6 weeks. Medical bills exceed insurance coverage.",
        "Cancer treatment expenses not covered by insurance. Need assistance with copays and transportation.",
        "Emergency hospitalization resulted in unexpected medical bills. Unable to cover costs.",
        "Spouse's medical emergency requiring extended care. Need help with related expenses.",
        "Child requires ongoing medical treatment. Insurance copays are financially burdensome.",
        "Dental emergency - extraction required immediately. No dental insurance coverage.",
    ],
    BenevolenceReason.DEATH_IN_FAMILY: [
        "Funeral expenses for immediate family member. Need assistance with burial costs.",
        "Travel expenses for family funeral out of state. Lost wages during bereavement.",
        "Loss of spouse - funeral and related expenses exceed available funds.",
        "Unexpected death in family requiring immediate travel and funeral arrangements.",
    ],
    BenevolenceReason.DISASTER: [
        "House fire destroyed home and belongings. Emergency housing and replacement needs.",
        "Flood damage to home not covered by insurance. Need assistance with repairs.",
        "Vehicle destroyed in accident - needed for work commute. Insurance insufficient.",
        "Tornado damage to property. Need help with temporary housing costs.",
        "Wildfire evacuation expenses including emergency lodging and supplies.",
    ],
    BenevolenceReason.HARDSHIP: [
        "Injured on job site awaiting workers' compensation approval. Need rent assistance.",
        "Laid off due to project completion. Behind on bills while seeking new position.",
        "Tools stolen from job site valued at $3,500. Need replacement to continue work.",
        "Behind on rent due to reduced hours. Facing eviction notice.",
        "Utility shutoff notice - need assistance to maintain service.",
        "Car repair needed to get to work. Unable to afford repairs.",
    ],
    BenevolenceReason.OTHER: [
        "Family emergency requiring immediate travel.",
        "Required safety equipment and work boots needed for new position.",
        "Unexpected expenses due to identity theft.",
        "Emergency childcare costs during family crisis.",
    ],
}

# Grievance subjects and violations
GRIEVANCE_DATA = [
    (
        "Overtime Distribution",
        "Employer bypassed seniority roster when assigning weekend overtime",
        "Assign overtime per contract Article 7 Section 3, pay premium for lost opportunity",
    ),
    (
        "Safety Violation",
        "Required to work in confined space without proper PPE or safety watch",
        "Cease unsafe work practice, provide required PPE, pay for time lost",
    ),
    (
        "Wrongful Termination",
        "Terminated without just cause and without following progressive discipline",
        "Reinstate with full back pay and benefits, expunge disciplinary record",
    ),
    (
        "Wage Dispute",
        "Not paid journeyman rate for work performed above helper classification",
        "Pay wage differential for all hours worked at journeyman level",
    ),
    (
        "Seniority Violation",
        "Junior employee given preferred day shift in violation of seniority provisions",
        "Reassign shifts per seniority, compensate for lost shift differential",
    ),
    (
        "Break Time",
        "Employer denied contractual break periods during 10-hour shift",
        "Enforce contract break provisions, penalty pay for denied breaks",
    ),
    (
        "Discrimination",
        "Treated differently and given undesirable assignments due to union activity",
        "Cease discriminatory treatment, make whole for lost opportunities",
    ),
    (
        "Subcontracting",
        "Bargaining unit work given to non-union subcontractor in violation of agreement",
        "Cease subcontracting, pay affected workers for lost hours",
    ),
    (
        "Misclassification",
        "Assigned work outside job classification without appropriate rate adjustment",
        "Pay appropriate rate for work performed, follow classification provisions",
    ),
    (
        "Benefits Denial",
        "Health insurance claim wrongfully denied by employer plan administrator",
        "Process claim properly, reimburse out-of-pocket expenses, penalty per contract",
    ),
]


def seed_salting_activities(
    db: Session, organization_ids: List[int], member_ids: List[int], count: int = 30
) -> List:
    """
    Create SALTing activity records for organizing campaigns.

    Args:
        db: Database session
        organization_ids: List of organization (employer) IDs to target
        member_ids: List of member IDs who can be organizers
        count: Number of activities to create

    Returns:
        List of created SALTingActivity objects
    """
    from src.models import SALTingActivity

    activities = []

    for i in range(count):
        # Choose activity type and description
        activity_type = random.choice(list(SALTingActivityType))
        description = random.choice(SALTING_ACTIVITY_DATA[activity_type])
        note = random.choice(SALTING_NOTES)

        # Random dates within last 2 years
        days_ago = random.randint(0, 730)
        activity_date = datetime.now() - timedelta(days=days_ago)

        # Outcome (70% have outcome, rest still pending)
        outcome = None
        if random.random() > 0.3:
            outcome = random.choice(list(SALTingOutcome))

        # Worker engagement numbers
        workers_contacted = random.randint(0, 50) if random.random() > 0.2 else 0
        cards_signed = random.randint(0, min(25, workers_contacted)) if workers_contacted > 0 else 0

        activity = SALTingActivity(
            organization_id=random.choice(organization_ids),
            member_id=random.choice(member_ids),  # Organizer
            activity_date=activity_date.date(),
            activity_type=activity_type,
            outcome=outcome,
            location=f"Site {random.randint(1, 10)}, {random.choice(['Break room', 'Parking lot', 'Off-site', 'Union hall'])}",
            workers_contacted=workers_contacted,
            cards_signed=cards_signed,
            description=description,
            notes=note,
            created_at=activity_date,
            updated_at=activity_date + timedelta(days=random.randint(0, 30)),
        )

        db.add(activity)
        activities.append(activity)

    db.commit()
    print(f"✅ Created {len(activities)} SALTing activities")
    return activities


def seed_benevolence_applications(
    db: Session, member_ids: List[int], count: int = 25
) -> List:
    """
    Create benevolence fund applications from members.

    Args:
        db: Database session
        member_ids: List of member IDs who can apply
        count: Number of applications to create

    Returns:
        List of created BenevolenceApplication objects
    """
    from src.models import BenevolenceApplication

    applications = []
    reasons = list(BenevolenceReason)
    reason_weights = [0.35, 0.15, 0.10, 0.30, 0.10]  # Medical and hardship most common

    statuses = [
        BenevolenceStatus.DRAFT,
        BenevolenceStatus.SUBMITTED,
        BenevolenceStatus.UNDER_REVIEW,
        BenevolenceStatus.APPROVED,
        BenevolenceStatus.PAID,
        BenevolenceStatus.DENIED,
    ]
    status_weights = [0.05, 0.15, 0.25, 0.30, 0.15, 0.10]

    for i in range(count):
        reason = random.choices(reasons, weights=reason_weights)[0]
        status = random.choices(statuses, weights=status_weights)[0]

        # Get appropriate description for reason
        description = random.choice(BENEVOLENCE_DESCRIPTIONS[reason])

        # Random dates within last year
        days_ago = random.randint(0, 365)
        application_date = datetime.now() - timedelta(days=days_ago)

        # Amount requested varies by reason
        amount_ranges = {
            BenevolenceReason.MEDICAL: (500, 5000),
            BenevolenceReason.DEATH_IN_FAMILY: (1000, 3000),
            BenevolenceReason.DISASTER: (1000, 7500),
            BenevolenceReason.HARDSHIP: (200, 2000),
            BenevolenceReason.OTHER: (100, 1000),
        }
        min_amt, max_amt = amount_ranges.get(reason, (100, 1000))
        amount = Decimal(str(random.randint(min_amt, max_amt)))

        # Amount approved (if approved/paid)
        approved_amount = None
        payment_date = None
        payment_method = None
        if status in [BenevolenceStatus.APPROVED, BenevolenceStatus.PAID]:
            # Usually approve 60-100% of requested
            pct = random.uniform(0.6, 1.0)
            approved_amount = Decimal(str(int(float(amount) * pct)))
            if status == BenevolenceStatus.PAID:
                payment_date = (application_date + timedelta(days=random.randint(14, 60))).date()
                payment_method = random.choice(["check", "direct_deposit", "wire_transfer"])

        application = BenevolenceApplication(
            member_id=random.choice(member_ids),
            application_date=application_date.date(),
            reason=reason,
            description=description,
            amount_requested=amount,
            status=status,
            approved_amount=approved_amount,
            payment_date=payment_date,
            payment_method=payment_method,
            notes=f"Application submitted {application_date.strftime('%Y-%m-%d')}" if random.random() > 0.5 else None,
            created_at=application_date,
            updated_at=application_date + timedelta(days=random.randint(0, 30)),
        )

        db.add(application)
        applications.append(application)

    db.commit()
    print(f"✅ Created {len(applications)} benevolence applications")
    return applications


def seed_benevolence_reviews(
    db: Session, applications: List, reviewer_member_ids: List[int]
) -> List:
    """
    Create review records for benevolence applications.
    Multi-level approval: Staff -> VP -> Admin -> Manager -> President

    Args:
        db: Database session
        applications: List of BenevolenceApplication objects
        reviewer_member_ids: List of member IDs who can review

    Returns:
        List of created BenevolenceReview objects
    """
    from src.models import BenevolenceReview

    reviews = []
    levels = list(BenevolenceReviewLevel)

    for app in applications:
        # Skip draft and submitted - no reviews yet
        if app.status in [BenevolenceStatus.DRAFT, BenevolenceStatus.SUBMITTED]:
            continue

        # Determine how many review levels based on amount and status
        amount = float(app.amount_requested)

        if amount < 500:
            num_levels = random.randint(1, 2)  # Small amounts: 1-2 reviews
        elif amount < 2000:
            num_levels = random.randint(2, 3)  # Medium: 2-3 reviews
        else:
            num_levels = random.randint(3, 5)  # Large: 3-5 reviews

        # Create reviews for each level
        review_date = app.application_date + timedelta(days=1)

        for level_idx in range(min(num_levels, len(levels))):
            level = levels[level_idx]

            # Determine decision based on app status and level
            if app.status in [BenevolenceStatus.APPROVED, BenevolenceStatus.PAID]:
                decision = BenevolenceReviewDecision.APPROVED
            elif app.status == BenevolenceStatus.DENIED:
                # Denied at some level
                if level_idx == num_levels - 1:
                    decision = BenevolenceReviewDecision.DENIED
                else:
                    decision = BenevolenceReviewDecision.DEFERRED
            elif app.status == BenevolenceStatus.UNDER_REVIEW:
                if level_idx == num_levels - 1:
                    decision = BenevolenceReviewDecision.NEEDS_INFO
                else:
                    decision = BenevolenceReviewDecision.DEFERRED
            else:
                decision = random.choice([BenevolenceReviewDecision.APPROVED, BenevolenceReviewDecision.DEFERRED])

            # Get reviewer name (simulated)
            reviewer_num = random.choice(reviewer_member_ids)
            reviewer_name = f"{level.value.replace('_', ' ').title()} Reviewer {reviewer_num}"

            review = BenevolenceReview(
                application_id=app.id,
                reviewer_name=reviewer_name,
                review_level=level,
                decision=decision,
                review_date=review_date,
                comments=_get_review_comment(decision, level),
                created_at=review_date,
            )

            db.add(review)
            reviews.append(review)

            # Next review a few days later
            review_date = review_date + timedelta(days=random.randint(1, 5))

    db.commit()
    print(f"✅ Created {len(reviews)} benevolence reviews")
    return reviews


def _get_review_comment(decision: BenevolenceReviewDecision, level: BenevolenceReviewLevel) -> str:
    """Generate realistic review comment based on decision."""
    comments = {
        BenevolenceReviewDecision.APPROVED: [
            "Verified member in good standing. Approved as requested.",
            "Documentation complete. Recommend full approval.",
            "Meets eligibility criteria. Approved.",
            "Financial need verified. Approved for disbursement.",
        ],
        BenevolenceReviewDecision.DENIED: [
            "Member not in good standing - dues arrears.",
            "Insufficient documentation provided.",
            "Request exceeds annual limit for member.",
            "Does not meet fund eligibility criteria.",
        ],
        BenevolenceReviewDecision.NEEDS_INFO: [
            "Please provide itemized receipts.",
            "Need verification of employment status.",
            "Requesting additional medical documentation.",
            "Please clarify circumstances and relationship.",
        ],
        BenevolenceReviewDecision.DEFERRED: [
            "Amount exceeds my approval authority. Deferring to next level.",
            "Unusual circumstances - recommend higher review.",
            "Forwarding to next level per policy.",
            "Documentation complete, deferring for final approval.",
        ],
    }

    return random.choice(comments[decision])


def seed_grievances(
    db: Session, member_ids: List[int], employer_ids: List[int], count: int = 20
) -> List:
    """
    Create grievance records with progression tracking.

    Args:
        db: Database session
        member_ids: List of member IDs who can file grievances
        employer_ids: List of employer organization IDs
        count: Number of grievances to create

    Returns:
        List of created Grievance objects
    """
    from src.models import Grievance

    grievances = []
    statuses = list(GrievanceStatus)
    status_weights = [0.10, 0.15, 0.20, 0.25, 0.10, 0.10, 0.10]  # Weighted toward settled/closed

    for i in range(count):
        grievance_data = random.choice(GRIEVANCE_DATA)
        subject, violation, remedy = grievance_data
        status = random.choices(statuses, weights=status_weights)[0]

        # Random dates within last 2 years
        days_ago = random.randint(0, 730)
        filed_date = datetime.now() - timedelta(days=days_ago)

        # Incident date 1-30 days before filing
        incident_date = filed_date - timedelta(days=random.randint(1, 30))

        # Generate grievance number (e.g., GR-2026-0001)
        year = filed_date.year
        grievance_number = f"GR-{year}-{(i + 1):04d}"

        # Current step based on status
        if status == GrievanceStatus.OPEN:
            current_step = GrievanceStep.STEP_1
        elif status in [GrievanceStatus.INVESTIGATION, GrievanceStatus.HEARING]:
            current_step = random.choice([GrievanceStep.STEP_1, GrievanceStep.STEP_2])
        elif status == GrievanceStatus.ARBITRATION:
            current_step = GrievanceStep.ARBITRATION
        else:
            current_step = random.choice([GrievanceStep.STEP_2, GrievanceStep.STEP_3])

        # Resolution details if settled/withdrawn/closed
        resolution = None
        resolution_date = None
        settlement_amount = None
        if status in [GrievanceStatus.SETTLED, GrievanceStatus.WITHDRAWN, GrievanceStatus.CLOSED]:
            days_to_resolve = random.randint(14, 180)
            resolution_date = (filed_date + timedelta(days=days_to_resolve)).date()
            resolution = _get_resolution_notes(status)
            if status == GrievanceStatus.SETTLED and random.random() > 0.5:
                settlement_amount = Decimal(str(random.randint(500, 5000)))

        # Assigned rep (typically a business agent or steward)
        assigned_rep = f"Rep {random.randint(1, 10)}"

        grievance = Grievance(
            grievance_number=grievance_number,
            member_id=random.choice(member_ids),
            employer_id=random.choice(employer_ids),
            filed_date=filed_date.date(),
            incident_date=incident_date.date(),
            contract_article=f"Article {random.randint(1, 30)}, Section {random.randint(1, 10)}",
            violation_description=violation,
            remedy_sought=remedy,
            current_step=current_step,
            status=status,
            assigned_rep=assigned_rep,
            resolution=resolution,
            resolution_date=resolution_date,
            settlement_amount=settlement_amount,
            notes=f"Filed by {assigned_rep} on {filed_date.strftime('%Y-%m-%d')}" if random.random() > 0.5 else None,
            created_at=filed_date,
            updated_at=filed_date + timedelta(days=random.randint(0, 60)),
        )

        db.add(grievance)
        grievances.append(grievance)

    db.commit()
    print(f"✅ Created {len(grievances)} grievances")
    return grievances


def _get_resolution_notes(status: GrievanceStatus) -> str:
    """Generate resolution notes based on status."""
    if status == GrievanceStatus.SETTLED:
        notes = [
            "Monetary settlement reached without admission of wrongdoing.",
            "Parties agreed to modified remedy in lieu of arbitration.",
            "Settlement includes policy change and back pay.",
            "Negotiated resolution satisfactory to grievant.",
            "Resolved at Step 2 - employer agreed to make grievant whole.",
            "Settlement reached - member awarded back pay for lost wages.",
        ]
    elif status == GrievanceStatus.WITHDRAWN:
        notes = [
            "Withdrawn per member request after informal resolution.",
            "Withdrawn - member separated from employer.",
            "Withdrawn without prejudice - may refile if needed.",
            "Member and union mutually agreed to withdraw grievance.",
        ]
    else:  # CLOSED
        notes = [
            "Grievance closed - employer corrected violation.",
            "Closed after arbitrator ruled in favor of union.",
            "Closed - remedies implemented per contract.",
            "Case closed after successful mediation.",
            "Grievance sustained - employer complied with remedy.",
        ]

    return random.choice(notes)


def seed_grievance_steps(
    db: Session, grievances: List
) -> List:
    """
    Create step records for grievances showing progression.

    Args:
        db: Database session
        grievances: List of Grievance objects

    Returns:
        List of created GrievanceStepRecord objects
    """
    from src.models import GrievanceStepRecord

    step_records = []

    for grievance in grievances:
        # Determine how many steps based on status
        if grievance.status == GrievanceStatus.OPEN:
            num_steps = 0  # Just filed, no steps yet
        elif grievance.status == GrievanceStatus.INVESTIGATION:
            num_steps = 1
        elif grievance.status == GrievanceStatus.HEARING:
            num_steps = random.randint(1, 2)
        elif grievance.status in [GrievanceStatus.SETTLED, GrievanceStatus.CLOSED]:
            num_steps = random.randint(1, 3)
        elif grievance.status == GrievanceStatus.WITHDRAWN:
            num_steps = random.randint(0, 2)
        elif grievance.status == GrievanceStatus.ARBITRATION:
            num_steps = 4  # All steps including arbitration
        else:
            num_steps = 1

        if num_steps == 0:
            continue

        # Create step records
        step_date = grievance.filed_date
        if isinstance(step_date, datetime):
            step_date = step_date.date()

        for step_num in range(1, min(num_steps + 1, 5)):  # Steps 1-4
            is_final_step = step_num == num_steps

            # Determine outcome
            if grievance.status in [GrievanceStatus.SETTLED, GrievanceStatus.CLOSED] and is_final_step:
                outcome = GrievanceStepOutcome.SETTLED
            elif grievance.status == GrievanceStatus.ARBITRATION and step_num == 4:
                # Arbitration still pending
                outcome = random.choice([GrievanceStepOutcome.SETTLED, GrievanceStepOutcome.DENIED])
            elif not is_final_step:
                outcome = GrievanceStepOutcome.ADVANCED
            else:
                outcome = random.choice([GrievanceStepOutcome.ADVANCED, GrievanceStepOutcome.DENIED])

            step_record = GrievanceStepRecord(
                grievance_id=grievance.id,
                step_number=step_num,
                meeting_date=step_date,
                employer_attendees=_get_employer_attendees(step_num),
                union_attendees=_get_union_attendees(step_num),
                outcome=outcome,
                notes=_get_step_notes(step_num, outcome),
                created_at=datetime.now(),
            )

            db.add(step_record)
            step_records.append(step_record)

            # Next step 7-30 days later
            step_date = step_date + timedelta(days=random.randint(7, 30))

    db.commit()
    print(f"✅ Created {len(step_records)} grievance step records")
    return step_records


def _get_employer_attendees(step_num: int) -> str:
    """Get employer attendees based on step level."""
    attendees = {
        1: "Foreman, Superintendent",
        2: "Project Manager, HR Representative",
        3: "HR Director, Legal Counsel",
        4: "Legal Counsel, HR Director, Company Representative",
    }
    return attendees.get(step_num, "Management Representative")


def _get_union_attendees(step_num: int) -> str:
    """Get union attendees based on step level."""
    attendees = {
        1: "Shop Steward",
        2: "Business Representative, Shop Steward",
        3: "Business Manager, Business Representative",
        4: "Business Manager, Legal Counsel, Business Representative",
    }
    return attendees.get(step_num, "Union Representative")


def _get_step_notes(step_num: int, outcome: GrievanceStepOutcome) -> str:
    """Generate notes for grievance step."""
    if outcome == GrievanceStepOutcome.SETTLED:
        return f"Grievance settled at Step {step_num}. Settlement terms agreed and signed."
    elif outcome == GrievanceStepOutcome.ADVANCED:
        return f"Unable to resolve at Step {step_num}. Advancing to Step {step_num + 1} per contract."
    elif outcome == GrievanceStepOutcome.DENIED:
        return f"Employer denied grievance at Step {step_num}. Union considering arbitration."
    else:
        return f"Step {step_num} meeting held. Awaiting employer written response per contract timeline."


# ============================================================================
# MAIN SEED FUNCTION
# ============================================================================


def seed_phase2(db: Session, verbose: bool = True) -> dict:
    """
    Main function to seed all Phase 2 data.

    PREREQUISITES:
    - Organizations must exist (from Phase 1 seed)
    - Members must exist (from Phase 1 seed)

    Args:
        db: Database session
        verbose: Print progress messages

    Returns:
        Dict with counts of created records
    """
    from src.db.enums import OrganizationType
    from src.models import Member, Organization

    if verbose:
        print("\n" + "=" * 60)
        print("🚀 SEEDING PHASE 2: UNION OPERATIONS")
        print("=" * 60)

    # Get existing data for relationships
    # Employers for SALTing and grievances
    employers = (
        db.query(Organization)
        .filter(Organization.org_type == OrganizationType.EMPLOYER)
        .all()
    )

    if not employers:
        print("❌ No employers found! Run Phase 1 seed first.")
        return {}

    employer_ids = [e.id for e in employers]

    # All organizations for general use
    all_orgs = db.query(Organization).all()
    all_org_ids = [o.id for o in all_orgs]

    # Members for various roles
    members = db.query(Member).all()

    if not members:
        print("❌ No members found! Run Phase 1 seed first.")
        return {}

    member_ids = [m.id for m in members]

    # Use subset for organizers/reviewers/reps (simulating staff)
    staff_member_ids = member_ids[: min(20, len(member_ids))]

    if verbose:
        print(f"📊 Found {len(employers)} employers")
        print(f"📊 Found {len(members)} members")
        print(f"📊 Using {len(staff_member_ids)} members as staff/reps")
        print()

    # 1. SALTing Activities
    if verbose:
        print("📋 Creating SALTing activities...")
    salting = seed_salting_activities(
        db=db,
        organization_ids=employer_ids[:100],  # Target subset of employers
        member_ids=staff_member_ids,
        count=30,
    )

    # 2. Benevolence Applications
    if verbose:
        print("📋 Creating benevolence applications...")
    applications = seed_benevolence_applications(db=db, member_ids=member_ids, count=25)

    # 3. Benevolence Reviews
    if verbose:
        print("📋 Creating benevolence reviews...")
    reviews = seed_benevolence_reviews(
        db=db, applications=applications, reviewer_member_ids=staff_member_ids
    )

    # 4. Grievances
    if verbose:
        print("📋 Creating grievances...")
    grievances = seed_grievances(
        db=db, member_ids=member_ids, employer_ids=employer_ids, count=20
    )

    # 5. Grievance Step Records
    if verbose:
        print("📋 Creating grievance step records...")
    step_records = seed_grievance_steps(db=db, grievances=grievances)

    # Summary
    results = {
        "salting_activities": len(salting),
        "benevolence_applications": len(applications),
        "benevolence_reviews": len(reviews),
        "grievances": len(grievances),
        "grievance_step_records": len(step_records),
    }

    if verbose:
        print("\n" + "=" * 60)
        print("✅ PHASE 2 SEED COMPLETE")
        print("=" * 60)
        for key, count in results.items():
            print(f"  • {key.replace('_', ' ').title()}: {count}")
        print("=" * 60 + "\n")

    return results


# ============================================================================
# STANDALONE EXECUTION
# ============================================================================

if __name__ == "__main__":
    """
    Run Phase 2 seed standalone.

    Usage: python -m src.seed.phase2_seed
    """
    import sys

    sys.path.insert(0, "/app")

    from src.db.session import get_db_session

    print("🔌 Connecting to database...")
    db = get_db_session()

    try:
        results = seed_phase2(db, verbose=True)

        if results:
            total = sum(results.values())
            print(f"\n🎉 Successfully created {total} Phase 2 records!")
        else:
            print("\n❌ Seed failed - check prerequisites")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()
