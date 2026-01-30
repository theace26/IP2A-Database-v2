# 6. Leadership Demo Walkthrough

**Duration:** 15-20 minutes presentation
**Goal:** Demonstrate IP2A-v2 value to leadership for project approval

---

## Pre-Demo Setup (Day Before)

### 1. Wake Up the App
If using Render free tier, visit the URL 30 minutes before demo to wake it:
```bash
curl https://YOUR-APP.onrender.com/health
```

### 2. Complete First-Time Setup (if needed)
On fresh deployment, the system requires setup:
- Navigate to `/setup`
- Create your administrator account (cannot use `admin@ibew46.com`)
- Optionally disable the default admin account (recommended for production)
- The default admin (`admin@ibew46.com`) exists for recovery but should be disabled

### 3. Verify Demo Data Exists
Login and confirm:
- At least 10 members visible
- Some students enrolled
- A few grievances in different stages
- Sample dues periods and payments

### 3. Prepare Browser
- Use Chrome or Firefox
- Clear cache/cookies for fresh experience
- Open app in one tab, have backup URL ready
- Close unnecessary tabs

### 4. Test Equipment
- MacOS display working
- HDMI/USB-C adapter ready if projecting
- Wi-Fi connected and stable
- Phone backup (can demo mobile responsiveness)

---

## Demo Script

### Opening (2 minutes)

> "Today I'm showing you a working prototype of our new membership database system. This replaces our spreadsheets and manual tracking with a modern, web-based platform."

**Show:** Login page

> "The system is secure, accessible from any browser, and works on phones and tablets. Let me log in as an administrator."

**Action:** Login with admin credentials

---

### Dashboard Overview (2 minutes)

> "This is the main dashboard. At a glance, you can see our key metrics."

**Point out:**
- Active members count
- Students in training
- Open grievances
- Dues collected this month

> "Everything updates in real-time. The activity feed shows recent system activity - who logged in, what records were created or updated."

**Show:** Activity feed scrolling

---

### Member Management (3 minutes)

> "Let's look at member management."

**Navigate:** Members → Overview

> "Here's our membership breakdown - active, inactive, by classification. This gives officers an instant snapshot of our workforce."

**Navigate:** Members → List

> "The member list supports instant search."

**Action:** Type a name in search box

> "Notice the table updates immediately - no page reload. You can filter by status, classification, anything."

**Click** on a member name

> "Each member has a detailed profile with contact info, employment history, and dues status. All in one place, no more hunting through spreadsheets."

---

### Training Management (2 minutes)

> "For our pre-apprenticeship program..."

**Navigate:** Training → Overview

> "We track students, courses, enrollments, attendance, and certifications."

**Navigate:** Training → Students

> "Here's our current student roster. We can see who's enrolled, their status, and completion progress."

**Navigate:** Training → Courses

> "Course management with enrollment counts. Click any course to see enrolled students and their progress."

---

### Union Operations (3 minutes)

> "The system also handles our organizing and welfare activities."

**Navigate:** Operations → Overview

> "Three modules here: SALTing, Benevolence, and Grievances."

**Click:** SALTing Activities

> "We track all organizing activities - site visits, contacts, outcomes. This builds our institutional knowledge."

**Click:** Benevolence Applications

> "Member assistance requests flow through a documented approval process."

**Navigate:** Grievances

> "Grievances are tracked through each step of the process. No more losing track of where a case stands."

**Show:** A grievance detail with step progress

> "Everything is documented with dates and notes. This protects us legally and ensures nothing falls through the cracks."

---

### Dues Management (3 minutes)

> "Financial tracking is critical for any union. Here's our dues system."

**Navigate:** Dues → Overview

> "At a glance: what we've collected this month, this year, who's overdue, and pending waivers."

**Navigate:** Dues → Periods

> "We can generate billing periods for the entire year with one click."

**Navigate:** Dues → Payments

> "Every payment is recorded - amount, method, date. Search by member or filter by status."

**Navigate:** Dues → Adjustments

> "Hardship waivers and credits go through an approval workflow. Full audit trail."

---

### Documents & Reports (2 minutes)

> "The system stores documents securely in the cloud."

**Navigate:** Documents

> "Upload files attached to members, students, grievances - anything. Organized automatically by date."

**Navigate:** Reports

> "Generate reports for meetings and compliance."

**Show:** Generate a Member Roster PDF

> "PDF reports for printing, Excel for analysis. All the data is already here - no more compiling spreadsheets."

---

### Mobile Demo (1 minute)

> "One more thing - this works on your phone."

**Action:** Pull out phone, navigate to app

> "Officers in the field can look up members, log activities, check grievance status. Same data, any device."

---

### Closing (2 minutes)

> "What you're seeing is a working prototype. The core functionality is built and tested."

**Key points:**
- Modern web technology (works in any browser)
- Secure (role-based access, audit trails for NLRA compliance)
- Mobile-friendly
- Replaces multiple spreadsheets
- Protects our data and processes
- **330 tests passing** - this is production-quality code

> "To move forward, I need approval to continue development and eventually deploy this for the local. Next steps would be refinement based on officer feedback and a phased rollout."

**What's already planned next (Week 11):**
- Complete audit trail UI (view who changed what, when)
- Member notes system
- Compliance export for legal/arbitration

**Ask:** "What questions do you have?"

---

## Handling Questions

### "How secure is this?"

> "All data is encrypted in transit and at rest. Users have role-based access - a shop steward sees different options than an officer. Every action is logged for accountability. We have a complete audit trail that meets NLRA's 7-year record retention requirement. If we ever need to show who changed what for arbitration or legal discovery, it's all there."

### "What about our current data?"

> "We can import existing member data from Excel. I've built the import process to handle our current spreadsheet format."

### "What does this cost?"

> "Hosting is approximately $15-20/month for database and server. No per-user fees. Compare that to commercial union management software at $500+/month."

### "Who maintains this?"

> "I built it, and I'm documenting everything so others can help. The code is version-controlled and backed up. Long-term, we could train additional staff or hire occasional help."

### "When can we start using it?"

> "With approval today, we could have a pilot group using it within 2-3 weeks. Full rollout after we gather feedback and make adjustments."

---

## Demo URLs to Bookmark

```
Production (Railway):   https://xxx.up.railway.app
Backup (Render):        https://xxx.onrender.com

Login:                  /login
Dashboard:              /dashboard
Members:                /members
Training:               /training
Operations:             /operations
Dues:                   /dues
Documents:              /documents
Reports:                /reports
Health Check:           /health
```

---

## Emergency Backup Plan

If live demo fails:

1. **Screenshots** - Have screenshots of each screen saved
2. **Video** - Record a 5-minute walkthrough video beforehand
3. **Local** - Run Docker locally as final backup:
   ```bash
   cd ~/Projects/IP2A-Database-v2
   docker-compose up -d
   # Navigate to http://localhost:8000
   ```

---

## Post-Demo Follow-Up

Same day or next day:

1. Send summary email with:
   - Demo URLs
   - Feature overview document
   - Next steps if approved
   - Timeline for pilot

2. Note any feedback or feature requests from discussion

3. Update project documentation with leadership decisions

---

## Continuing Development After Demo

Your branch setup protects the demo while you keep building:

```bash
# On Windows (your dev machine)
git checkout develop

# Continue building new features
# ... work on Week 11, deployment polish, etc. ...

git add -A && git commit -m "feat: new feature"
git push origin develop

# Demo stays frozen on main
# Leadership sees stable v0.8.0

# When ready for next demo update:
git checkout main
git merge develop
git push origin main  # Auto-deploys to Railway/Render
git checkout develop  # Back to work
```

**Key point:** Demo URL never breaks mid-development.

---

## Success Metrics

Your demo succeeded if leadership:
- ✅ Understands what the system does
- ✅ Sees value over current spreadsheets
- ✅ Approves continued development
- ✅ Identifies a pilot user group
- ✅ Provides feedback on priorities

---

**You're ready to present!** 🎉

Good luck with the demo. The prototype speaks for itself - 330 tests passing, every feature you showed actually works. You've built something real.
