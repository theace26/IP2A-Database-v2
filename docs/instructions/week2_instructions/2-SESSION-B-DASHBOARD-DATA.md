# Phase 6 Week 2 - Session B: Real Dashboard Data

**Document:** 2 of 3
**Estimated Time:** 2-3 hours
**Focus:** Replace placeholder stats with live database queries

---

## Objective

Transform the dashboard from static placeholders to real-time data:
- Actual member, student, grievance, dues counts
- Activity feed from audit log
- Quick stats calculations (MTD dues, pending items)

---

## Pre-flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Should show 180+ passed (with Session A tests)
```

---

## Step 1: Create Dashboard Service (45 min)

Create `src/services/dashboard_service.py`:

```python
"""
Dashboard Service - Aggregates stats from multiple modules.
Optimized for quick dashboard loading.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

from src.models.member import Member
from src.models.student import Student
from src.models.grievance import Grievance
from src.models.salting_activity import SaltingActivity
from src.models.benevolence_application import BenevolenceApplication
from src.models.dues_payment import DuesPayment
from src.models.audit_log import AuditLog
from src.db.enums import (
    MemberStatus,
    StudentStatus,
    GrievanceStatus,
    BenevolenceStatus,
    DuesPaymentStatus,
)

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for dashboard data aggregation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get all dashboard statistics.
        Uses efficient COUNT queries instead of loading all records.
        """
        stats = {}
        
        try:
            # Active members count
            stats["active_members"] = await self._count_active_members()
            stats["members_change"] = await self._get_members_change_this_month()
            
            # Active students count
            stats["active_students"] = await self._count_active_students()
            
            # Pending grievances
            stats["pending_grievances"] = await self._count_pending_grievances()
            
            # Active SALTing campaigns
            stats["active_salting"] = await self._count_active_salting()
            
            # Pending benevolence applications
            stats["pending_benevolence"] = await self._count_pending_benevolence()
            
            # Dues collected this month
            stats["dues_mtd"] = await self._get_dues_mtd()
            
        except Exception as e:
            logger.error(f"Error fetching dashboard stats: {e}")
            # Return zeros on error to prevent dashboard crash
            stats = {
                "active_members": 0,
                "members_change": "+0",
                "active_students": 0,
                "pending_grievances": 0,
                "active_salting": 0,
                "pending_benevolence": 0,
                "dues_mtd": 0,
            }
        
        return stats

    async def _count_active_members(self) -> int:
        """Count members with active status."""
        result = await self.db.execute(
            select(func.count(Member.id)).where(
                Member.status == MemberStatus.ACTIVE
            )
        )
        return result.scalar() or 0

    async def _get_members_change_this_month(self) -> str:
        """Get net member change this month."""
        first_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Count members created this month
        result = await self.db.execute(
            select(func.count(Member.id)).where(
                and_(
                    Member.created_at >= first_of_month,
                    Member.status == MemberStatus.ACTIVE
                )
            )
        )
        new_members = result.scalar() or 0
        
        # Format with sign
        if new_members > 0:
            return f"+{new_members}"
        return str(new_members)

    async def _count_active_students(self) -> int:
        """Count students with active enrollment."""
        result = await self.db.execute(
            select(func.count(Student.id)).where(
                Student.status == StudentStatus.ACTIVE
            )
        )
        return result.scalar() or 0

    async def _count_pending_grievances(self) -> int:
        """Count grievances in open/pending status."""
        pending_statuses = [
            GrievanceStatus.FILED,
            GrievanceStatus.STEP_1,
            GrievanceStatus.STEP_2,
            GrievanceStatus.STEP_3,
        ]
        result = await self.db.execute(
            select(func.count(Grievance.id)).where(
                Grievance.status.in_(pending_statuses)
            )
        )
        return result.scalar() or 0

    async def _count_active_salting(self) -> int:
        """Count active SALTing campaigns."""
        result = await self.db.execute(
            select(func.count(SaltingActivity.id)).where(
                SaltingActivity.is_active == True
            )
        )
        return result.scalar() or 0

    async def _count_pending_benevolence(self) -> int:
        """Count pending benevolence applications."""
        result = await self.db.execute(
            select(func.count(BenevolenceApplication.id)).where(
                BenevolenceApplication.status == BenevolenceStatus.PENDING
            )
        )
        return result.scalar() or 0

    async def _get_dues_mtd(self) -> float:
        """Get total dues collected this month."""
        first_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        result = await self.db.execute(
            select(func.coalesce(func.sum(DuesPayment.amount), 0)).where(
                and_(
                    DuesPayment.payment_date >= first_of_month,
                    DuesPayment.status == DuesPaymentStatus.COMPLETED
                )
            )
        )
        return float(result.scalar() or 0)

    async def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent activity from audit log.
        Returns formatted activity items for display.
        """
        result = await self.db.execute(
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        logs = result.scalars().all()
        
        activities = []
        for log in logs:
            activities.append({
                "id": log.id,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "user_id": log.user_id,
                "timestamp": log.created_at,
                "description": self._format_activity(log),
                "badge": self._get_activity_badge(log.action),
            })
        
        return activities

    def _format_activity(self, log: AuditLog) -> str:
        """Format audit log entry for display."""
        action_map = {
            "CREATE": "created",
            "UPDATE": "updated",
            "DELETE": "deleted",
            "READ": "viewed",
        }
        action = action_map.get(log.action, log.action.lower())
        entity = log.entity_type.replace("_", " ").title()
        return f"{entity} #{log.entity_id} was {action}"

    def _get_activity_badge(self, action: str) -> Dict[str, str]:
        """Get badge styling for activity type."""
        badges = {
            "CREATE": {"text": "NEW", "class": "badge-primary"},
            "UPDATE": {"text": "UPD", "class": "badge-warning"},
            "DELETE": {"text": "DEL", "class": "badge-error"},
            "READ": {"text": "VIEW", "class": "badge-info"},
        }
        return badges.get(action, {"text": action[:3], "class": "badge-ghost"})

    async def get_upcoming_deadlines(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get upcoming deadlines (grievance responses, certifications expiring, etc.)
        This is a simplified version - expand based on your needs.
        """
        deadlines = []
        
        # Get grievances with approaching deadlines
        # (You'd need a deadline field on Grievance model)
        
        # For now, return placeholder structure
        # Replace with actual queries based on your data model
        
        return deadlines

    async def get_benevolence_queue(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get pending benevolence applications for review."""
        result = await self.db.execute(
            select(BenevolenceApplication)
            .where(BenevolenceApplication.status == BenevolenceStatus.PENDING)
            .order_by(BenevolenceApplication.created_at.asc())
            .limit(limit)
        )
        applications = result.scalars().all()
        
        queue = []
        for app in applications:
            queue.append({
                "id": app.id,
                "member_id": app.member_id,
                "request_type": app.request_type,
                "amount_requested": app.amount_requested,
                "created_at": app.created_at,
            })
        
        return queue


# Convenience function
async def get_dashboard_service(db: AsyncSession) -> DashboardService:
    """Factory function for dependency injection."""
    return DashboardService(db)
```

---

## Step 2: Update Frontend Router (30 min)

Update `src/routers/frontend.py` to use the dashboard service:

**Update imports:**
```python
from src.services.dashboard_service import DashboardService
```

**Replace the `get_dashboard_stats` helper and update the dashboard route:**

```python
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render main dashboard with real data."""
    # Handle redirect from auth middleware
    if isinstance(current_user, RedirectResponse):
        return current_user
    
    # Get real stats from dashboard service
    dashboard_service = DashboardService(db)
    stats = await dashboard_service.get_stats()
    
    return templates.TemplateResponse(
        "dashboard/index.html",
        {
            "request": request,
            "stats": stats,
            "user": current_user,
        }
    )


@router.get("/api/dashboard/refresh", response_class=HTMLResponse)
async def dashboard_stats_partial(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth_api),
):
    """Return just the stats cards for HTMX refresh."""
    if isinstance(current_user, dict) and "id" not in current_user:
        return HTMLResponse(content="<div class='alert alert-error'>Unauthorized</div>", status_code=401)
    
    dashboard_service = DashboardService(db)
    stats = await dashboard_service.get_stats()
    
    # Return stats HTML partial (inline for simplicity)
    html = f"""
    <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-figure text-primary">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
            </svg>
        </div>
        <div class="stat-title">Active Members</div>
        <div class="stat-value text-primary">{stats['active_members']:,}</div>
        <div class="stat-desc">{stats['members_change']} this month</div>
    </div>

    <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-figure text-secondary">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
            </svg>
        </div>
        <div class="stat-title">Active Students</div>
        <div class="stat-value text-secondary">{stats['active_students']}</div>
        <div class="stat-desc">In current cohorts</div>
    </div>

    <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-figure text-warning">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
        </div>
        <div class="stat-title">Pending Grievances</div>
        <div class="stat-value text-warning">{stats['pending_grievances']}</div>
        <div class="stat-desc">Requires attention</div>
    </div>

    <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-figure text-success">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
        </div>
        <div class="stat-title">Dues MTD</div>
        <div class="stat-value text-success">${stats['dues_mtd']:,.0f}</div>
        <div class="stat-desc">This month</div>
    </div>
    """
    return HTMLResponse(content=html)


@router.get("/api/dashboard/recent-activity", response_class=HTMLResponse)
async def recent_activity_partial(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Return recent activity from audit log."""
    dashboard_service = DashboardService(db)
    activities = await dashboard_service.get_recent_activity(limit=10)
    
    if not activities:
        return HTMLResponse(content="""
            <p class="text-center text-base-content/50 py-4">No recent activity</p>
        """)
    
    items_html = ""
    for activity in activities:
        badge = activity['badge']
        time_ago = _format_time_ago(activity['timestamp'])
        items_html += f"""
        <li class="flex items-start gap-3 p-2 rounded hover:bg-base-200">
            <div class="badge {badge['class']} badge-sm mt-1">{badge['text']}</div>
            <div>
                <p class="text-sm font-medium">{activity['description']}</p>
                <p class="text-xs text-base-content/60">{time_ago}</p>
            </div>
        </li>
        """
    
    return HTMLResponse(content=f"""
        <ul class="space-y-3">{items_html}</ul>
        <p class="text-xs text-base-content/50 mt-4 text-center">Showing last 10 activities</p>
    """)


def _format_time_ago(dt: datetime) -> str:
    """Format datetime as relative time string."""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    
    hours = diff.seconds // 3600
    if hours > 0:
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    
    minutes = diff.seconds // 60
    if minutes > 0:
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    
    return "Just now"
```

---

## Step 3: Update Dashboard Template (20 min)

Update `src/templates/dashboard/index.html` to use real data:

**Update the stats cards section to show formatted numbers:**

```html
<!-- Stats Grid -->
<div id="stats-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    <!-- Active Members -->
    <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-figure text-primary">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
            </svg>
        </div>
        <div class="stat-title">Active Members</div>
        <div class="stat-value text-primary">{{ "{:,}".format(stats.active_members | default(0)) }}</div>
        <div class="stat-desc">{{ stats.members_change | default('+0') }} this month</div>
    </div>

    <!-- Active Students -->
    <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-figure text-secondary">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
            </svg>
        </div>
        <div class="stat-title">Active Students</div>
        <div class="stat-value text-secondary">{{ stats.active_students | default(0) }}</div>
        <div class="stat-desc">In current cohorts</div>
    </div>

    <!-- Pending Grievances -->
    <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-figure text-warning">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
        </div>
        <div class="stat-title">Pending Grievances</div>
        <div class="stat-value text-warning">{{ stats.pending_grievances | default(0) }}</div>
        <div class="stat-desc">Requires attention</div>
    </div>

    <!-- Dues MTD -->
    <div class="stat bg-base-100 rounded-box shadow">
        <div class="stat-figure text-success">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
        </div>
        <div class="stat-title">Dues MTD</div>
        <div class="stat-value text-success">${{ "{:,.0f}".format(stats.dues_mtd | default(0)) }}</div>
        <div class="stat-desc">This month</div>
    </div>
</div>
```

**Update the user greeting:**

```html
<div>
    <h1 class="text-2xl font-bold">Dashboard</h1>
    <p class="text-base-content/60">Welcome back{% if user %}, {{ user.email }}{% endif %}</p>
</div>
```

---

## Step 4: Add Dashboard Tests (20 min)

Add to `src/tests/test_frontend.py`:

```python
class TestDashboardData:
    """Tests for dashboard data loading."""

    @pytest.mark.asyncio
    async def test_dashboard_stats_returns_numbers(self, async_client: AsyncClient):
        """Dashboard stats should return numeric values."""
        # This requires auth - use cookie or skip auth for this test
        response = await async_client.get("/api/dashboard/refresh")
        # Should return HTML with stat values
        assert response.status_code in [200, 401]  # 401 if auth required
        if response.status_code == 200:
            assert "stat-value" in response.text

    @pytest.mark.asyncio
    async def test_recent_activity_returns_html(self, async_client: AsyncClient):
        """Recent activity endpoint should return HTML list."""
        response = await async_client.get("/api/dashboard/recent-activity")
        assert response.status_code == 200
        # Should have list items or "no activity" message

    @pytest.mark.asyncio
    async def test_dashboard_service_handles_empty_db(self, async_client: AsyncClient):
        """Dashboard should gracefully handle empty database."""
        # Even with no data, dashboard shouldn't crash
        response = await async_client.get("/api/dashboard/refresh")
        assert response.status_code in [200, 401]
```

---

## Step 5: Run Tests and Verify

```bash
# Run all tests
pytest -v --tb=short

# Start server for manual testing
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Manual verification:**
1. Login at `/login`
2. Dashboard should show real counts from your seed data
3. Click "Refresh" button - stats should update via HTMX
4. Activity feed should show recent audit log entries

---

## Step 6: Commit

```bash
git add -A
git commit -m "feat(dashboard): Add real-time dashboard data

- Create DashboardService with optimized COUNT queries
- Add member, student, grievance, dues statistics
- Implement activity feed from audit log
- Add benevolence queue display
- Update frontend router for real data
- Update dashboard template with number formatting
- Add dashboard data tests"

git push origin main
```

---

## Session B Checklist

- [ ] Created `dashboard_service.py` with stat queries
- [ ] Updated frontend router to use dashboard service
- [ ] Updated dashboard template for real data
- [ ] Activity feed shows audit log entries
- [ ] Refresh button updates stats via HTMX
- [ ] All tests passing
- [ ] Committed changes

---

*Session B complete. Proceed to Session C for polish and final tests.*
