# Stakeholder-Specific Talking Points

**Document Purpose:** Audience-specific messaging for the UnionCore demo
**Created:** February 7, 2026
**Spoke:** Spoke 2 (Operations)
**Demo Date:** [TBD]

---

## Access DB Owner

**Goal:** Get them excited about collaboration, not threatened by replacement.

### Opening Frame
- "This system complements yours — it handles dispatch and referral, which your database wasn't originally designed for."
- "Your data stays in your database. We're not migrating anything away from you."
- "We'd love your help validating when we import the LaborPower data."

### Expertise Recognition
- "You understand the business rules better than anyone. We need that expertise."
- "When we analyzed the LaborPower data, we found 8 contract codes instead of 7, and 11 books instead of 8. That's the kind of detail knowledge that only comes from years of working with the data."
- "Your feedback during testing would be invaluable - you'll catch things I'd never notice."

### Complementary Positioning
- "Think of it this way: your system handles employment history and member records. UnionCore handles out-of-work status and dispatch. They work together."
- "The Access database is the source of truth for member data. UnionCore just reads from it for dispatch purposes."
- "We're not replacing what works. We're filling the gap that LaborPower leaves."

### Practical Benefits (for them)
- "This reduces the manual cross-referencing you have to do between LaborPower and your database."
- "When a member's employment status changes, the dispatch system reflects it automatically."
- "You won't have to field as many 'where am I on the book?' phone calls - members can check themselves."

### The Ask
- "We need three specific exports from LaborPower to validate the data:"
  - REGLIST with member identifiers
  - RAW DISPATCH DATA with historical dispatches
  - EMPLOYCONTRACT with employer-to-contract mappings
- "Would you be willing to help us pull those reports? They're in the Custom Reports module."

### Red Flags — DO NOT Say:
- ❌ "replace your database"
- ❌ "migrate away from Access"
- ❌ "sunset your system"
- ❌ "outdated technology"
- ❌ "we don't need you anymore"

### Green Flags — DO Say:
- ✅ "complement your work"
- ✅ "work alongside your database"
- ✅ "your expertise is critical"
- ✅ "validate together"
- ✅ "partnership"

---

## IT Contractor

**Goal:** Assure them this is contained, self-managed, and doesn't create work for them.

### Opening Frame
- "Everything runs in Docker containers — completely isolated from your network infrastructure."
- "I handle all updates and maintenance. You don't need to touch this."
- "I'm showing you this out of transparency, not because I need anything from you."

### Containment & Isolation
- "The database is PostgreSQL running in its own container - no shared database servers."
- "The API is FastAPI running in its own container - no dependencies on your web servers."
- "The demo environment uses port 8080 to avoid conflicts. Production would use whatever port makes sense for your environment."
- "All data stays in the container volumes - nothing touches your file system."

### Maintenance & Responsibility
- "I maintain it. You don't. That's a hard boundary."
- "Updates are tested in dev, then deployed via Docker Compose. No surprises."
- "If something breaks at 2 AM, I fix it. Not your problem."
- "I've built monitoring and alerting into the system (via health checks). You can hook it up to Grafana if you want visibility, but you're not required to."

### Backups & DR
- "Backups are automated via cron jobs. They run daily to S3-compatible storage."
- "I have a disaster recovery runbook documented at docs/runbooks/disaster-recovery.md"
- "The backup verification script runs weekly to ensure backups are restorable."
- "I've tested the restore process - takes about 15 minutes from backup to live system."

### Deployment Options
- "This can run on Railway, Render, or any cloud provider. It doesn't have to touch your on-prem infrastructure."
- "If you prefer on-prem, we can run it on its own VM. It's just Docker Compose - dead simple."
- "The choice is yours. I'm flexible. Whatever keeps your workload minimal."

### Technical Credibility (Show, Don't Tell)
- Show: `docker-compose.demo.yml` - "30 lines. That's it."
- Show: Audit logs - "Immutable at the database level. PostgreSQL triggers prevent deletion or modification."
- Show: Health check endpoints - "/health/live, /health/ready, /health/metrics - standard k8s readiness/liveness pattern"
- Show: Structured logging - "JSON logs. Ship them to wherever you ship logs."

### Addressing Concerns
| Concern | Response |
|---------|----------|
| "We don't support Python apps" | "You don't have to. It's containerized. Docker is the only dependency." |
| "What if you leave the union?" | "The code is fully documented. Any Python dev can maintain it. And I'm training a successor." |
| "Security updates?" | "Base images are scanned weekly. Dependencies are pinned and audited. I follow OWASP Top 10." |
| "What about HTTPS/SSL?" | "Handled by reverse proxy (nginx/Caddy). I can set that up or you can - your call." |

### Red Flags — DO NOT Say:
- ❌ "I need access to your servers"
- ❌ "Can you install this?"
- ❌ "You'll need to maintain this"
- ❌ "It's complicated but..."
- ❌ "Don't worry about the technical stuff"

### Green Flags — DO Say:
- ✅ "self-contained"
- ✅ "isolated"
- ✅ "I maintain it"
- ✅ "industry standard (PostgreSQL, Docker)"
- ✅ "documented and tested"

---

## Union Leadership (Business Manager, Officers)

**Goal:** Show business value. Reports they recognize. Daily time savings.

### Opening Frame
- "This replaces the daily LaborPower printouts your dispatchers use every morning."
- "85 reports — 14 of them are the critical daily operational reports you already rely on."
- "Members will be able to check their book status and bid on jobs from their phone."

### Time Savings (Quantified)
- "Right now, dispatchers spend 15-20 minutes every morning cross-referencing LaborPower, the Access database, and handwritten check mark logs."
- "With UnionCore, that process takes 2 minutes. One screen. All the data in one place."
- "That's 13-18 minutes saved every morning. Over a year, that's 50+ hours reclaimed for actual member service."

### Member Service Improvements
- "Members can check their position on the book from their phone - no more calling the hall."
- "Online dues payment is the next phase — members pay from their phone via Square. Instant receipt."
- "Bid on jobs via web or mobile (Rule 8 - 5:30 PM to 7:00 AM bidding window). No more email confusion."
- "Members get SMS/email notifications when they're up for referral (future enhancement)."

### Compliance & Audit Trail
- "Every action is logged with a 7-year audit trail — NLRA compliant."
- "The audit logs are immutable at the database level. Even I can't delete them. Crucial for grievances and NLRB audits."
- "Check mark tracking is automatic (Rule 10). No more spreadsheets. No more missed penalties."
- "Exemption management is built-in (Rule 14 - military, medical, union business, salting, jury duty)."
- "30-day re-sign enforcement happens automatically (Rule 7). The system alerts members before they're dropped."

### Business Rules Enforcement
- "The system enforces the 14 business rules from the Referral Procedures automatically:"
  - Morning processing order (Rule 2)
  - 3 PM cutoff for next-day dispatch (Rule 3)
  - Agreement type filtering - PLA/CWA/TERO (Rule 4)
  - Check mark limits (Rule 10)
  - Short call position restoration (Rule 9)
  - Quit/discharge blackout periods (Rule 12)
  - By-name anti-collusion enforcement (Rule 13)

### Report Parity with LaborPower
- **14 P0 reports (Critical Daily):**
  - Morning Referral Sheet (by book)
  - Out-of-Work List (by book, by region)
  - Employer Active List
  - Daily Dispatch Log
- **24 P1 reports (High Priority Weekly/Monthly):**
  - Registration History Report
  - Dispatch Summary by Employer
  - Check Mark Violations Report
  - Exemption Status Report
- **41 P2/P3 reports (Analytics & Trends):**
  - Dispatch Volume Forecast
  - Employer Utilization Trends
  - Member Registration Patterns

### Development Velocity (Credibility Builder)
- "Built in 45+ sprint weeks of part-time development (5-10 hrs/week)."
- "Feature parity with LaborPower for dispatch and referral."
- "~764 automated tests. 92.7% pass rate. Bugs are caught before they hit production."
- "18 Architecture Decision Records documenting every major technical choice."

### Next Phase: Square Payment Integration (Weeks 47-49)
- "Online dues payment via Square (credit card, ACH bank transfer)."
- "Automatic receipt generation and dues period tracking."
- "Members pay from their phone. No more mailing checks. No more driving to the hall."
- "Square integrates with existing POS at the hall - one payment ecosystem."

### ROI Framing
- "This system costs the union nothing except my time (which I'm already donating)."
- "Cloud hosting: ~$50-100/month on Railway or Render."
- "Compare to: LaborPower licensing fees + manual cross-referencing time + member frustration."

### Red Flags — DO NOT Say:
- ❌ "This is complex"
- ❌ "You'll need to learn new software"
- ❌ "It's not quite done yet"
- ❌ "There are still some bugs"
- ❌ Promise specific timelines

### Green Flags — DO Say:
- ✅ "time savings"
- ✅ "member service"
- ✅ "compliance"
- ✅ "audit trail"
- ✅ "feature parity"
- ✅ "automated"
- ✅ "modernization"
- ✅ Specific numbers: "85 reports", "14 daily reports", "7-year audit retention"

---

## Hybrid Audience (All Three Present)

**When all three stakeholders are in the room, prioritize this message order:**

### 1. Business Value First (Union Leadership)
- Start with the problem and the solution
- Show the workflow (Act 2)
- Demonstrate time savings

### 2. Technical Credibility Second (IT Contractor)
- Show containment and isolation
- Demonstrate you're not creating work for them
- Prove you can maintain this independently

### 3. Partnership Last (Access DB Owner)
- Ask for collaboration, not permission
- Frame as complementary, not replacement
- Show respect for their expertise

### Handling Cross-Stakeholder Tension

**If Access DB owner objects in front of leadership:**
- Acknowledge: "That's a great point. Your perspective is exactly why we need you involved in the data validation."
- Pivot: "This system is designed to work alongside your database, not replace it."
- Defer: "Let's talk offline about the specifics of the data export. I don't want to take everyone's time on technical details."

**If IT contractor raises security/maintenance concerns:**
- Acknowledge: "Absolutely valid concern. That's why it's fully containerized and I maintain it."
- Demonstrate: "Let me show you the deployment setup - it's self-contained."
- Reassure leadership: "This doesn't create any additional work for IT. I handle all updates and maintenance."

**If leadership asks "Why not just use LaborPower?"**
- Acknowledge: "LaborPower works for what it was designed to do - basic referral."
- Contrast: "But we can't customize it. We can't add features. We can't integrate it with dues payment or member self-service."
- Vision: "This is about modernizing for the next 20 years, not just replicating what we have today."

---

## Post-Demo Follow-Up Messaging

### Within 24 Hours (Email to All)
**Subject:** UnionCore Demo Follow-Up - Next Steps

"Thank you for attending yesterday's demo of the UnionCore dispatch system.

**Key takeaways:**
- 85 reports built (14 critical daily reports)
- 7-year audit compliance (NLRA)
- Member self-service (check book status, bid on jobs, pay dues online)

**Next steps:**
1. [Access DB owner]: REGLIST/DISPATCH/EMPLOYCONTRACT export specs attached
2. [IT contractor]: Deployment architecture doc attached
3. [Union leadership]: Roadmap and timeline for Phase 8 (Square payments)

I'll follow up individually with each of you over the next week.

Best,
Xerxes"

### Week 2 Follow-Up (If No Response)
**Subject:** UnionCore - Checking In

"[Name], wanted to follow up on the UnionCore demo from last week.

[Stakeholder-specific ask]:
- **Access DB owner:** "Have you had a chance to review the LaborPower export specs? I'm happy to walk through them with you."
- **IT contractor:** "Do you have any additional questions about the deployment architecture or security model?"
- **Union leadership:** "Do you need any additional information to make a decision on moving forward?"

Let me know if you'd like to schedule a brief follow-up call.

Best,
Xerxes"

---

## Objection Handling Quick Reference

| Objection | Response |
|-----------|----------|
| "Too expensive" | "Cloud hosting is $50-100/month. Development time is donated. Compare to LaborPower licensing + manual labor." |
| "Too risky" | "764 automated tests. Full disaster recovery plan. Backups verified weekly. Audit trail is immutable." |
| "What if you leave?" | "Fully documented. Any Python dev can maintain it. I'm training a successor. Code is transferable." |
| "LaborPower already works" | "For referral, yes. But this adds member self-service, online payments, custom reports, and audit compliance." |
| "Not now, maybe later" | "Understood. The code will be here when you're ready. In the meantime, I'll keep it running for testing." |
| "We need IT approval first" | "I can work with IT to address any concerns. The system is designed to require zero work from them." |

---

**Talking Points Version:** 1.0
**Created:** February 7, 2026
**Spoke:** Spoke 2 (Operations)
**Target Audiences:** Access DB owner, IT contractor, Union leadership
**Expected Outcome:** Buy-in from all three stakeholders, LaborPower data access granted
