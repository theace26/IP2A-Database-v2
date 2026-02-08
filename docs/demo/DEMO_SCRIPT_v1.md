# UnionCore Demo Script v1

> **Total Runtime:** ~22 minutes
> **Presenter:** Xerxes, Business Representative
> **Audience:** Union leadership, Access DB owner, IT contractor
> **Environment:** Demo environment (docker-compose.demo.yml)
> **Pre-demo:** Start demo environment 10 minutes before. Verify smoke test. Open browser to login page.
> **Demo URL:** http://localhost:8080
> **Demo Accounts:**
> - Dispatcher: `demo_dispatcher@ibew46.demo` / `Demo2026!`
> - Officer: `demo_officer@ibew46.demo` / `Demo2026!`
> - Admin: `demo_admin@ibew46.demo` / `Demo2026!`

---

## Act 1: "The Problem" (2 minutes)

**Logged in as:** Nobody (show login screen)

**Talking points:**
- "Today we manage dispatch with 3 separate systems that don't talk to each other"
- "LaborPower handles referral but it's aging and we can't customize it"
- "The Access database handles employment history and member data, but only one person can maintain it"
- "Dispatchers spend 15-20 minutes every morning manually cross-referencing who's available, who has check marks, and what the employer needs"
- "What I'm going to show you is a single system that handles all of this"

**Visual:** Show the login page at http://localhost:8080

**Action:** Pause. Let the problem sink in. Make eye contact with the Access DB owner and IT contractor.

---

## Act 2: "The Daily Workflow" (10 minutes)

**Log in as:** `demo_dispatcher@ibew46.demo` / `Demo2026!`

### 2a. Morning Dispatch Board (3 min)
- Navigate to: **Dispatch Dashboard** (main landing page after login)
- Point out: **Pending labor requests** from yesterday (submitted before 3 PM cutoff per Rule 3)
- Show: **Morning processing order** visible in the dashboard
  - Wire referrals at 8:30 AM
  - S&C/Marine/Stock/Light Fixture/Residential at 9:00 AM
  - Tradeshow at 9:30 AM
- Click into a **labor request** card → show employer details, skill requirements, agreement type
- **Quote:** "This is what dispatchers see every morning at 8:30. No more spreadsheets."

### 2b. Processing a Referral (3 min)
- Navigate to: **Morning Referral** page (primary dispatch workflow page)
- Show: **Bid queue** sorted by APN (Applicant Priority Number - Excel date + decimal)
- Walk through: Select a member from the queue for an open labor request
- Show: Member's current position on book
- Show: **Check mark status** (this member has 1 of 2 allowed - Rule 10)
- Process the dispatch → show status change to ACTIVE
- **Quote:** "One click. Audit trail automatic. No paper. No phone calls."

### 2c. Book Management (2 min)
- Navigate to: **Referral > Book Status** page
- Show: **WIRE SEATTLE** with registration counts by tier (Book 1, Book 2, Book 3)
- Show: **Cross-regional registrations** (same member on Seattle + Bremerton + Pt. Angeles)
- Show: **STOCKMAN book** → "Notice the contract code is STOCKPERSON, not STOCKMAN"
- Point to Technician book: "Some books don't have a contract code at all - they're multi-classification"
- **Quote:** "We found 8 contract codes, not 7. We found 11 books, not 8. The data analysis before coding saved us months of rework."

### 2d. Enforcement (2 min)
- Navigate to: **Dispatch > Enforcement** page
- Show: **Check mark tracking** table
- Show: A member with 2 check marks (at the limit - next one rolls them off per Rule 10)
- Show: **Exemptions** section (military, medical, union business/salting)
- Show: **Blackout periods** (quit/discharge = 2-week foreperson-by-name blackout per Rule 12)
- **Quote:** "The system enforces the rules from the Referral Procedures automatically. No more manual tracking. No more mistakes."

---

## Act 3: "The Reports" (5 minutes)

**Log in as:** `demo_officer@ibew46.demo` / `Demo2026!`

### 3a. P0 Reports — Daily Operational (2 min)
- Navigate to: **Reports** section
- Generate: **Morning Referral Sheet** (PDF) - P0 priority
  - Show: Book-by-book queue listing with APNs
  - Show: Check marks and exemptions displayed inline
  - **Quote:** "This is what dispatchers print every morning"
- Generate: **Out-of-Work List for WIRE SEATTLE** (Excel) - P0 priority
  - Show: All registrants sorted by APN with current status
  - **Quote:** "This replaces the LaborPower printout"

### 3b. P1 Reports — Weekly/Monthly (1.5 min)
- Generate: **Employer Active List** (Excel) - P1 priority
  - Show: Which employers are currently hiring, how many dispatches, contract types
  - **Quote:** "Officers get this monthly — who's hiring, who's not, contract compliance tracking"
- Generate: **Registration History Report** (PDF) - P1 priority
  - Show: Member's registration timeline with re-signs, exemptions, roll-offs
  - **Quote:** "We can see a member's entire out-of-work history. Useful for grievances and compliance."

### 3c. P2/P3 Reports — Analytics (1.5 min)
- Generate: **Dispatch Trend Report** (PDF) - P2 priority
  - Show: Historical dispatch volume by book and month
  - **Quote:** "85 reports total. 14 critical daily reports. 30 high-priority reports. All built."
- Show: **Report Inventory** page (if exists) or list of available reports
  - **Quote:** "Historical data going back 90+ days for forecasting and trend analysis"

---

## Act 4: "Under the Hood" (3 minutes)

**Target audience:** IT contractor

**Switch to:** Terminal or file explorer

- Show: `deployment/docker-compose.demo.yml` file
  - **Quote:** "It's 30 lines. All self-contained. PostgreSQL database, FastAPI backend, all isolated."
- Show: `deployment/DEMO_README.md`
  - **Quote:** "Complete setup instructions. Start command, stop command, that's it."
- Navigate to: **Admin > Audit Logs** (logged in as demo_admin or demo_officer)
  - Show: Every action logged with user, timestamp, before/after values
  - **Quote:** "Every action is logged. 7-year retention. NLRA compliant. Immutable at the database level - not even I can delete these."
- Show: Docker containers running (if possible via terminal)
  - **Quote:** "It runs in its own container — isolated from everything else. Your servers are untouched."
  - **Quote:** "You don't maintain this. I do. You can monitor it if you want via Grafana (future), but you don't have to."

**Key messages for IT:**
- Self-contained Docker environment
- PostgreSQL (industry standard, not proprietary)
- Automated backups documented
- Disaster recovery plan documented (docs/runbooks/)
- You don't touch it, I maintain it

---

## Act 5: "What's Next" (2 minutes)

**Talking points:**

### The Ask (LaborPower Data Access)
- "Right now this runs on demo data - fictional members, fictional employers."
- "To go live, we need the LaborPower data export - specifically 3 reports:"
  - **REGLIST** with member identifiers
  - **RAW DISPATCH DATA** with historical dispatches
  - **EMPLOYCONTRACT** with employer-to-contract mappings
- **[Direct address to Access DB owner]:** "[Name], your expertise would be invaluable for validating the data migration. You know the business rules better than anyone. This system complements your database - it handles dispatch and referral, your system keeps handling what it does best."

### The Roadmap
- **Phase 7 complete:** Referral & Dispatch system (what you just saw)
- **Next phase:** Online dues payment through Square
  - Members pay from their phone via credit card or ACH
  - Automatic receipt generation
  - Integration with existing dues tracking
- **Timeline:** Built in 45+ sprint weeks of part-time development (5-10 hrs/week)
- **Feature parity:** LaborPower dispatch features + 85 reports + audit compliance

### The Vision
- "Everything I've shown you was built part-time while working full-time as a Business Rep."
- "This system is designed to last. Modern tech stack. Fully documented. Fully tested."
- "The union hall can run this independently or we can host it. Your choice."

**Closing:**
- "Questions?"
- [Handle Q&A]
- "Thank you for your time. I'll send over the REGLIST/DISPATCH/EMPLOYCONTRACT export specs after this meeting."

---

## Contingency Plans

| Problem | Recovery |
|---------|----------|
| Docker won't start | Fall back to local uvicorn: `uvicorn src.main:app --port 8000` (requires migration + seed) |
| PDF report fails | Show the web version of the report instead (all reports have HTML view) |
| Login fails | Use `demo_admin` as fallback; all roles visible with admin account |
| Projector won't connect | Have screenshots in `docs/demo/screenshots/` as backup |
| "That's not how we do it" pushback | "Great feedback - that's exactly why we need your expertise to validate the data migration" |
| Tough question you can't answer | "Great question. Let me look into that and follow up with documentation." |
| Access DB owner feels threatened | Pivot to "This complements your system" talking points (see STAKEHOLDER_TALKING_POINTS.md) |
| IT contractor objects to hosting | "We can run this on Railway or any cloud provider. It doesn't have to touch your infrastructure." |

---

## Pre-Demo Checklist (Run 10 Minutes Before)

```bash
cd ~/Projects/IP2A-Database-v2/deployment
docker-compose -f docker-compose.demo.yml down -v  # Clean slate
docker-compose -f docker-compose.demo.yml up -d     # Start fresh
sleep 15  # Wait for services to stabilize
docker-compose -f docker-compose.demo.yml ps        # Verify all "Up" or "healthy"
```

**Browser pre-checks:**
- [ ] Open http://localhost:8080 - login page loads
- [ ] Login as `demo_dispatcher@ibew46.demo` / `Demo2026!` - dashboard loads
- [ ] Navigate to Dispatch Dashboard - pending requests visible
- [ ] Navigate to Reports - P0 report generates as PDF
- [ ] Logout and login as `demo_officer@ibew46.demo` - reports section visible

---

## Post-Demo Actions

**Immediately after demo:**
- [ ] Capture verbal feedback from each stakeholder
- [ ] Note any objections or concerns raised
- [ ] Document access granted/blocked (did Access DB owner agree?)
- [ ] Follow up email with REGLIST/DISPATCH/EMPLOYCONTRACT export specs

**Within 1 week:**
- [ ] Update roadmap based on feedback
- [ ] Create Hub handoff document with demo outcomes
- [ ] If access granted → begin Week 47+ (data collection + import)
- [ ] If access blocked → create mitigation plan

---

## Notes for Presenter

**Pacing:**
- Act 1: Slow and deliberate. Let the problem statement land.
- Act 2: Faster. Show the workflow, don't narrate every click.
- Act 3: Medium. Reports are impressive but don't dwell.
- Act 4: Conversational. IT contractor wants to see competence, not complexity.
- Act 5: End strong. Clear ask. Clear vision.

**Energy:**
- High energy in Act 2 (the workflow)
- Calm confidence in Act 4 (technical credibility)
- Measured ask in Act 5 (respectful, not desperate)

**Body Language:**
- Make eye contact with Access DB owner during "your expertise" moments
- Make eye contact with IT contractor during "isolated, I maintain it" moments
- Make eye contact with union leadership during "time savings" and "compliance" moments

**Red Flags to Avoid:**
- ❌ Don't say "replace" — say "complement"
- ❌ Don't promise timelines — say "I'll follow up with estimates"
- ❌ Don't oversell — let the demo speak for itself
- ❌ Don't get defensive — acknowledge concerns and document for follow-up

---

**Demo Script Version:** 1.0
**Created:** February 7, 2026
**Spoke:** Spoke 2 (Operations)
**Target Audience:** Union leadership, Access DB owner, IT contractor
**Expected Outcome:** LaborPower data access granted, organizational buy-in secured
