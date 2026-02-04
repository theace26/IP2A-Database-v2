# Week 19: Advanced Reporting & Analytics Dashboard

**Version:** 1.0.0  
**Created:** February 2, 2026  
**Branch:** `develop`  
**Estimated Effort:** 8-10 hours (3-4 sessions)  
**Dependencies:** Week 14 (Grant Module), Week 11 (Audit Trail) complete

---

## Overview

This week implements an **advanced analytics dashboard** and **enhanced reporting capabilities** to help union leadership make data-driven decisions. This includes membership trends, dues analytics, training effectiveness metrics, and customizable report builder.

### Objectives

- [ ] Executive dashboard with key metrics
- [ ] Membership analytics (trends, demographics, retention)
- [ ] Dues collection analytics (payment patterns, delinquency)
- [ ] Training program effectiveness metrics
- [ ] Custom report builder
- [ ] Scheduled report delivery (email)
- [ ] Data export in multiple formats

### Out of Scope

- Business intelligence tool integration (Tableau, PowerBI)
- Machine learning predictions
- Real-time streaming analytics

---

## Pre-Flight Checklist

- [ ] On `develop` branch
- [ ] Week 14 (Grant compliance reporting) complete
- [ ] All tests passing
- [ ] Sufficient historical data for meaningful analytics
- [ ] Email configuration ready (for scheduled reports)

---

## Phase 1: Analytics Service Layer (Session 1)

### 1.1 Base Analytics Service

Create `src/services/analytics_service.py`:

```python
"""Analytics service for aggregated metrics and trends."""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, func, extract, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Member, DuesPayment, Student, AuditLog, DuesPeriod
from src.db.enums import MemberStatus, PaymentStatus, StudentStatus


class AnalyticsService:
    """Service for analytics and metrics calculations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_membership_stats(self) -> dict:
        """Get current membership statistics."""
        total = await self.db.scalar(select(func.count(Member.id)))
        active = await self.db.scalar(
            select(func.count(Member.id))
            .where(Member.status == MemberStatus.ACTIVE)
        )
        
        # New members this month
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        new_this_month = await self.db.scalar(
            select(func.count(Member.id))
            .where(Member.created_at >= month_start)
        )
        
        # Retention rate (active / total who were ever active)
        retention_rate = (active / total * 100) if total > 0 else 0
        
        return {
            "total": total,
            "active": active,
            "inactive": total - active,
            "new_this_month": new_this_month,
            "retention_rate": round(retention_rate, 1),
        }
    
    async def get_membership_trend(self, months: int = 12) -> list[dict]:
        """Get membership count by month for trending."""
        results = []
        now = datetime.utcnow()
        
        for i in range(months - 1, -1, -1):
            # Calculate month boundaries
            month_date = now - timedelta(days=30 * i)
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            if month_date.month == 12:
                month_end = month_date.replace(year=month_date.year + 1, month=1, day=1)
            else:
                month_end = month_date.replace(month=month_date.month + 1, day=1)
            
            # Count members active at end of month
            count = await self.db.scalar(
                select(func.count(Member.id))
                .where(Member.created_at < month_end)
                .where(
                    (Member.status == MemberStatus.ACTIVE) |
                    (Member.updated_at >= month_start)
                )
            )
            
            results.append({
                "month": month_start.strftime("%Y-%m"),
                "label": month_start.strftime("%b %Y"),
                "count": count or 0,
            })
        
        return results
    
    async def get_dues_analytics(self, period_id: Optional[int] = None) -> dict:
        """Get dues collection analytics."""
        # Base query for period
        base_filter = []
        if period_id:
            base_filter.append(DuesPayment.period_id == period_id)
        
        # Total collected
        total_collected = await self.db.scalar(
            select(func.sum(DuesPayment.amount))
            .where(DuesPayment.status == PaymentStatus.COMPLETED)
            .where(*base_filter)
        ) or 0
        
        # Payment count
        payment_count = await self.db.scalar(
            select(func.count(DuesPayment.id))
            .where(DuesPayment.status == PaymentStatus.COMPLETED)
            .where(*base_filter)
        ) or 0
        
        # Average payment
        avg_payment = total_collected / payment_count if payment_count > 0 else 0
        
        # Payment method breakdown
        method_breakdown = await self.db.execute(
            select(
                DuesPayment.payment_method,
                func.count(DuesPayment.id).label('count'),
                func.sum(DuesPayment.amount).label('total')
            )
            .where(DuesPayment.status == PaymentStatus.COMPLETED)
            .where(*base_filter)
            .group_by(DuesPayment.payment_method)
        )
        
        methods = [
            {"method": str(row.payment_method), "count": row.count, "total": float(row.total or 0)}
            for row in method_breakdown.fetchall()
        ]
        
        return {
            "total_collected": float(total_collected),
            "payment_count": payment_count,
            "average_payment": round(avg_payment, 2),
            "payment_methods": methods,
        }
    
    async def get_delinquency_report(self) -> dict:
        """Get members with overdue dues."""
        # Find current period
        now = datetime.utcnow()
        current_period = await self.db.scalar(
            select(DuesPeriod)
            .where(DuesPeriod.start_date <= now.date())
            .where(DuesPeriod.end_date >= now.date())
        )
        
        if not current_period:
            return {"overdue_count": 0, "overdue_amount": 0, "members": []}
        
        # Members without payment for current period
        paid_member_ids = select(DuesPayment.member_id).where(
            DuesPayment.period_id == current_period.id,
            DuesPayment.status == PaymentStatus.COMPLETED
        ).scalar_subquery()
        
        overdue_members = await self.db.execute(
            select(Member)
            .where(Member.status == MemberStatus.ACTIVE)
            .where(Member.id.not_in(paid_member_ids))
            .limit(100)
        )
        
        members_list = overdue_members.scalars().all()
        
        return {
            "overdue_count": len(members_list),
            "period": current_period.name,
            "members": [
                {"id": m.id, "name": f"{m.first_name} {m.last_name}", "member_number": m.member_number}
                for m in members_list[:20]  # Limit for display
            ],
        }
    
    async def get_training_metrics(self) -> dict:
        """Get training program effectiveness metrics."""
        total_students = await self.db.scalar(select(func.count(Student.id)))
        
        active_students = await self.db.scalar(
            select(func.count(Student.id))
            .where(Student.status == StudentStatus.ACTIVE)
        )
        
        completed = await self.db.scalar(
            select(func.count(Student.id))
            .where(Student.status == StudentStatus.COMPLETED)
        )
        
        withdrawn = await self.db.scalar(
            select(func.count(Student.id))
            .where(Student.status == StudentStatus.WITHDRAWN)
        )
        
        completion_rate = (completed / total_students * 100) if total_students > 0 else 0
        
        return {
            "total_students": total_students,
            "active": active_students,
            "completed": completed,
            "withdrawn": withdrawn,
            "completion_rate": round(completion_rate, 1),
        }
    
    async def get_activity_metrics(self, days: int = 30) -> dict:
        """Get system activity metrics."""
        since = datetime.utcnow() - timedelta(days=days)
        
        # Audit log counts by action
        action_counts = await self.db.execute(
            select(
                AuditLog.action,
                func.count(AuditLog.id).label('count')
            )
            .where(AuditLog.created_at >= since)
            .group_by(AuditLog.action)
        )
        
        actions = {str(row.action): row.count for row in action_counts.fetchall()}
        
        # Daily activity for chart
        daily_activity = await self.db.execute(
            select(
                func.date(AuditLog.created_at).label('date'),
                func.count(AuditLog.id).label('count')
            )
            .where(AuditLog.created_at >= since)
            .group_by(func.date(AuditLog.created_at))
            .order_by(func.date(AuditLog.created_at))
        )
        
        daily = [
            {"date": str(row.date), "count": row.count}
            for row in daily_activity.fetchall()
        ]
        
        return {
            "period_days": days,
            "action_breakdown": actions,
            "total_actions": sum(actions.values()),
            "daily_activity": daily,
        }
```

---

## Phase 2: Executive Dashboard (Session 2)

### 2.1 Dashboard Router

Create `src/routers/ui/analytics.py`:

```python
"""Analytics dashboard routes."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_async_session
from src.services.analytics_service import AnalyticsService
from src.routers.dependencies.auth_cookie import get_current_user_from_cookie, require_officer
from src.templates import templates

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_class=HTMLResponse)
@require_officer  # Officers and above can view analytics
async def analytics_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user_from_cookie),
):
    """Executive analytics dashboard."""
    analytics = AnalyticsService(db)
    
    membership = await analytics.get_membership_stats()
    membership_trend = await analytics.get_membership_trend(months=12)
    dues = await analytics.get_dues_analytics()
    training = await analytics.get_training_metrics()
    activity = await analytics.get_activity_metrics(days=30)
    
    return templates.TemplateResponse(
        "analytics/dashboard.html",
        {
            "request": request,
            "user": current_user,
            "membership": membership,
            "membership_trend": membership_trend,
            "dues": dues,
            "training": training,
            "activity": activity,
        }
    )


@router.get("/membership", response_class=HTMLResponse)
@require_officer
async def membership_analytics(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user_from_cookie),
):
    """Detailed membership analytics."""
    analytics = AnalyticsService(db)
    
    stats = await analytics.get_membership_stats()
    trend = await analytics.get_membership_trend(months=24)
    
    return templates.TemplateResponse(
        "analytics/membership.html",
        {
            "request": request,
            "user": current_user,
            "stats": stats,
            "trend": trend,
        }
    )


@router.get("/dues", response_class=HTMLResponse)
@require_officer
async def dues_analytics(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user_from_cookie),
):
    """Detailed dues analytics."""
    analytics = AnalyticsService(db)
    
    dues = await analytics.get_dues_analytics()
    delinquency = await analytics.get_delinquency_report()
    
    return templates.TemplateResponse(
        "analytics/dues.html",
        {
            "request": request,
            "user": current_user,
            "dues": dues,
            "delinquency": delinquency,
        }
    )
```

### 2.2 Dashboard Template

Create `src/templates/analytics/dashboard.html`:

```html
{% extends "base.html" %}
{% block title %}Analytics Dashboard{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-6">
    <h1 class="text-2xl font-bold mb-6">Executive Dashboard</h1>
    
    <!-- Key Metrics Row -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <!-- Membership -->
        <div class="stat bg-base-100 rounded-lg shadow">
            <div class="stat-figure text-primary">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="inline-block w-8 h-8 stroke-current">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z"></path>
                </svg>
            </div>
            <div class="stat-title">Active Members</div>
            <div class="stat-value text-primary">{{ membership.active }}</div>
            <div class="stat-desc">{{ membership.retention_rate }}% retention rate</div>
        </div>
        
        <!-- Dues Collected -->
        <div class="stat bg-base-100 rounded-lg shadow">
            <div class="stat-figure text-success">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="inline-block w-8 h-8 stroke-current">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
                </svg>
            </div>
            <div class="stat-title">Dues Collected</div>
            <div class="stat-value text-success">${{ "%.2f"|format(dues.total_collected) }}</div>
            <div class="stat-desc">{{ dues.payment_count }} payments</div>
        </div>
        
        <!-- Training -->
        <div class="stat bg-base-100 rounded-lg shadow">
            <div class="stat-figure text-info">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="inline-block w-8 h-8 stroke-current">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 14l9-5-9-5-9 5 9 5z"></path>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 14l9-5-9-5-9 5 9 5zm0 0v6"></path>
                </svg>
            </div>
            <div class="stat-title">Active Students</div>
            <div class="stat-value text-info">{{ training.active }}</div>
            <div class="stat-desc">{{ training.completion_rate }}% completion rate</div>
        </div>
        
        <!-- Activity -->
        <div class="stat bg-base-100 rounded-lg shadow">
            <div class="stat-figure text-secondary">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="inline-block w-8 h-8 stroke-current">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                </svg>
            </div>
            <div class="stat-title">Actions (30d)</div>
            <div class="stat-value text-secondary">{{ activity.total_actions }}</div>
            <div class="stat-desc">System activity</div>
        </div>
    </div>
    
    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <!-- Membership Trend Chart -->
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <h2 class="card-title">Membership Trend (12 Months)</h2>
                <div id="membership-chart" class="h-64">
                    <!-- Chart rendered by Alpine/Chart.js -->
                    <canvas id="membershipCanvas"></canvas>
                </div>
            </div>
        </div>
        
        <!-- Payment Methods Breakdown -->
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <h2 class="card-title">Payment Methods</h2>
                <div id="payment-chart" class="h-64">
                    <canvas id="paymentCanvas"></canvas>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Quick Links -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <a href="/analytics/membership" class="card bg-base-100 shadow hover:shadow-lg transition-shadow">
            <div class="card-body">
                <h3 class="card-title text-sm">Membership Analytics →</h3>
                <p class="text-sm text-gray-500">Trends, demographics, retention</p>
            </div>
        </a>
        <a href="/analytics/dues" class="card bg-base-100 shadow hover:shadow-lg transition-shadow">
            <div class="card-body">
                <h3 class="card-title text-sm">Dues Analytics →</h3>
                <p class="text-sm text-gray-500">Collection, delinquency, trends</p>
            </div>
        </a>
        <a href="/reports" class="card bg-base-100 shadow hover:shadow-lg transition-shadow">
            <div class="card-body">
                <h3 class="card-title text-sm">Report Builder →</h3>
                <p class="text-sm text-gray-500">Custom reports and exports</p>
            </div>
        </a>
    </div>
</div>

<!-- Chart.js Integration -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
    // Membership trend chart
    const membershipCtx = document.getElementById('membershipCanvas').getContext('2d');
    new Chart(membershipCtx, {
        type: 'line',
        data: {
            labels: {{ membership_trend | map(attribute='label') | list | tojson }},
            datasets: [{
                label: 'Members',
                data: {{ membership_trend | map(attribute='count') | list | tojson }},
                borderColor: 'rgb(99, 102, 241)',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                fill: true,
                tension: 0.3,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: false } }
        }
    });
    
    // Payment methods chart
    const paymentCtx = document.getElementById('paymentCanvas').getContext('2d');
    new Chart(paymentCtx, {
        type: 'doughnut',
        data: {
            labels: {{ dues.payment_methods | map(attribute='method') | list | tojson }},
            datasets: [{
                data: {{ dues.payment_methods | map(attribute='total') | list | tojson }},
                backgroundColor: [
                    'rgb(99, 102, 241)',
                    'rgb(34, 197, 94)',
                    'rgb(251, 146, 60)',
                    'rgb(236, 72, 153)',
                ],
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
        }
    });
</script>
{% endblock %}
```

---

## Phase 3: Custom Report Builder (Session 3)

### 3.1 Report Builder Service

Create `src/services/report_builder_service.py`:

```python
"""Custom report builder service."""
from datetime import datetime, date
from typing import Any, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import json

from src.models import Member, Student, DuesPayment, Grant, AuditLog


class ReportBuilderService:
    """Service for building custom reports."""
    
    AVAILABLE_ENTITIES = {
        "members": {
            "model": Member,
            "fields": ["id", "member_number", "first_name", "last_name", "status", "classification", "created_at"],
            "label": "Members",
        },
        "students": {
            "model": Student,
            "fields": ["id", "first_name", "last_name", "status", "cohort_id", "created_at"],
            "label": "Students",
        },
        "payments": {
            "model": DuesPayment,
            "fields": ["id", "member_id", "amount", "payment_date", "payment_method", "status"],
            "label": "Dues Payments",
        },
        "grants": {
            "model": Grant,
            "fields": ["id", "name", "funder", "budget", "status", "start_date", "end_date"],
            "label": "Grants",
        },
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def get_available_entities(self) -> list[dict]:
        """Get list of entities available for reporting."""
        return [
            {"key": key, "label": config["label"], "fields": config["fields"]}
            for key, config in self.AVAILABLE_ENTITIES.items()
        ]
    
    async def build_report(
        self,
        entity: str,
        fields: list[str],
        filters: Optional[dict] = None,
        order_by: Optional[str] = None,
        limit: int = 1000,
    ) -> dict:
        """Build a custom report based on parameters."""
        if entity not in self.AVAILABLE_ENTITIES:
            raise ValueError(f"Unknown entity: {entity}")
        
        config = self.AVAILABLE_ENTITIES[entity]
        model = config["model"]
        
        # Validate fields
        valid_fields = [f for f in fields if f in config["fields"]]
        if not valid_fields:
            valid_fields = config["fields"][:5]  # Default to first 5 fields
        
        # Build query
        columns = [getattr(model, f) for f in valid_fields]
        query = select(*columns)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(model, field):
                    column = getattr(model, field)
                    if isinstance(value, dict):
                        if "gte" in value:
                            query = query.where(column >= value["gte"])
                        if "lte" in value:
                            query = query.where(column <= value["lte"])
                        if "eq" in value:
                            query = query.where(column == value["eq"])
                    else:
                        query = query.where(column == value)
        
        # Apply ordering
        if order_by and hasattr(model, order_by.lstrip("-")):
            order_field = order_by.lstrip("-")
            order_col = getattr(model, order_field)
            if order_by.startswith("-"):
                query = query.order_by(order_col.desc())
            else:
                query = query.order_by(order_col.asc())
        
        # Apply limit
        query = query.limit(limit)
        
        # Execute
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        # Format results
        data = []
        for row in rows:
            row_dict = {}
            for i, field in enumerate(valid_fields):
                value = row[i]
                # Serialize dates
                if isinstance(value, (datetime, date)):
                    value = value.isoformat()
                row_dict[field] = value
            data.append(row_dict)
        
        return {
            "entity": entity,
            "fields": valid_fields,
            "filters": filters,
            "count": len(data),
            "data": data,
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    async def export_to_csv(self, report: dict) -> str:
        """Convert report to CSV format."""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=report["fields"])
        writer.writeheader()
        writer.writerows(report["data"])
        
        return output.getvalue()
    
    async def export_to_excel(self, report: dict) -> bytes:
        """Convert report to Excel format."""
        from openpyxl import Workbook
        from io import BytesIO
        
        wb = Workbook()
        ws = wb.active
        ws.title = report["entity"].title()
        
        # Header row
        ws.append(report["fields"])
        
        # Data rows
        for row in report["data"]:
            ws.append([row.get(f) for f in report["fields"]])
        
        # Style header
        from openpyxl.styles import Font
        for cell in ws[1]:
            cell.font = Font(bold=True)
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        return output.getvalue()
```

### 3.2 Report Builder UI

Create `src/templates/reports/builder.html`:

```html
{% extends "base.html" %}
{% block title %}Report Builder{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-6" x-data="reportBuilder()">
    <h1 class="text-2xl font-bold mb-6">Custom Report Builder</h1>
    
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Configuration Panel -->
        <div class="lg:col-span-1">
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">Report Configuration</h2>
                    
                    <!-- Entity Selection -->
                    <div class="form-control mb-4">
                        <label class="label">
                            <span class="label-text">Data Source</span>
                        </label>
                        <select class="select select-bordered" x-model="entity" @change="loadFields()">
                            <option value="">Select...</option>
                            {% for e in entities %}
                            <option value="{{ e.key }}">{{ e.label }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    
                    <!-- Field Selection -->
                    <div class="form-control mb-4" x-show="availableFields.length > 0">
                        <label class="label">
                            <span class="label-text">Fields to Include</span>
                        </label>
                        <template x-for="field in availableFields">
                            <label class="label cursor-pointer justify-start gap-2">
                                <input type="checkbox" class="checkbox checkbox-sm" 
                                       :value="field" x-model="selectedFields">
                                <span class="label-text" x-text="field"></span>
                            </label>
                        </template>
                    </div>
                    
                    <!-- Filters -->
                    <div class="form-control mb-4" x-show="entity">
                        <label class="label">
                            <span class="label-text">Filters</span>
                        </label>
                        <select class="select select-bordered select-sm mb-2" x-model="filterStatus">
                            <option value="">All statuses</option>
                            <option value="active">Active only</option>
                            <option value="inactive">Inactive only</option>
                        </select>
                    </div>
                    
                    <!-- Limit -->
                    <div class="form-control mb-4">
                        <label class="label">
                            <span class="label-text">Max Records</span>
                        </label>
                        <input type="number" class="input input-bordered" x-model="limit" min="1" max="10000">
                    </div>
                    
                    <!-- Generate Button -->
                    <button class="btn btn-primary" @click="generateReport()" :disabled="!entity || loading">
                        <span x-show="loading" class="loading loading-spinner"></span>
                        <span x-show="!loading">Generate Report</span>
                    </button>
                </div>
            </div>
        </div>
        
        <!-- Results Panel -->
        <div class="lg:col-span-2">
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <div class="flex justify-between items-center mb-4">
                        <h2 class="card-title">
                            Results 
                            <span x-show="reportData" class="badge badge-primary" x-text="reportData?.count + ' records'"></span>
                        </h2>
                        <div class="flex gap-2" x-show="reportData">
                            <button class="btn btn-sm btn-outline" @click="exportCSV()">
                                Export CSV
                            </button>
                            <button class="btn btn-sm btn-outline" @click="exportExcel()">
                                Export Excel
                            </button>
                        </div>
                    </div>
                    
                    <!-- Results Table -->
                    <div class="overflow-x-auto" x-show="reportData">
                        <table class="table table-zebra table-sm">
                            <thead>
                                <tr>
                                    <template x-for="field in reportData?.fields">
                                        <th x-text="field"></th>
                                    </template>
                                </tr>
                            </thead>
                            <tbody>
                                <template x-for="row in reportData?.data.slice(0, 50)">
                                    <tr>
                                        <template x-for="field in reportData?.fields">
                                            <td x-text="row[field]"></td>
                                        </template>
                                    </tr>
                                </template>
                            </tbody>
                        </table>
                        <p x-show="reportData?.count > 50" class="text-sm text-gray-500 mt-2">
                            Showing first 50 of <span x-text="reportData?.count"></span> records. Export to see all.
                        </p>
                    </div>
                    
                    <!-- Empty State -->
                    <div x-show="!reportData && !loading" class="text-center py-12 text-gray-500">
                        <p>Configure your report and click "Generate Report"</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
function reportBuilder() {
    return {
        entity: '',
        availableFields: [],
        selectedFields: [],
        filterStatus: '',
        limit: 1000,
        loading: false,
        reportData: null,
        
        loadFields() {
            const entities = {{ entities | tojson }};
            const entity = entities.find(e => e.key === this.entity);
            this.availableFields = entity?.fields || [];
            this.selectedFields = [...this.availableFields];
        },
        
        async generateReport() {
            this.loading = true;
            try {
                const filters = {};
                if (this.filterStatus) {
                    filters.status = { eq: this.filterStatus };
                }
                
                const response = await fetch('/api/v1/reports/build', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        entity: this.entity,
                        fields: this.selectedFields,
                        filters: filters,
                        limit: this.limit,
                    })
                });
                
                this.reportData = await response.json();
            } catch (error) {
                console.error('Report generation failed:', error);
            } finally {
                this.loading = false;
            }
        },
        
        async exportCSV() {
            // Trigger CSV download
            window.location.href = `/api/v1/reports/export/csv?entity=${this.entity}&fields=${this.selectedFields.join(',')}`;
        },
        
        async exportExcel() {
            // Trigger Excel download
            window.location.href = `/api/v1/reports/export/excel?entity=${this.entity}&fields=${this.selectedFields.join(',')}`;
        }
    }
}
</script>
{% endblock %}
```

---

## Phase 4: Scheduled Reports (Session 4)

### 4.1 Report Schedule Model

Add to `src/models/report_schedule.py`:

```python
"""Scheduled report configuration."""
from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.db.base import Base


class ReportSchedule(Base):
    """Scheduled report configuration."""
    __tablename__ = "report_schedules"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    
    # Report configuration (stored as JSON)
    report_config = Column(JSON, nullable=False)
    # {entity, fields, filters, order_by, limit}
    
    # Schedule
    frequency = Column(String(20), nullable=False)  # daily, weekly, monthly
    day_of_week = Column(Integer)  # 0-6 for weekly
    day_of_month = Column(Integer)  # 1-31 for monthly
    time_of_day = Column(String(5), default="08:00")  # HH:MM
    
    # Delivery
    recipients = Column(JSON, default=list)  # List of email addresses
    format = Column(String(10), default="excel")  # csv, excel, pdf
    
    # Status
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    
    # Owner
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_by = relationship("User")
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

### 4.2 Report Scheduler Task

Create `src/tasks/report_scheduler.py`:

```python
"""Background task for scheduled reports."""
import asyncio
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import async_session_factory
from src.models.report_schedule import ReportSchedule
from src.services.report_builder_service import ReportBuilderService
from src.services.email_service import EmailService


async def run_scheduled_reports():
    """Check and run due scheduled reports."""
    async with async_session_factory() as db:
        now = datetime.utcnow()
        
        # Find due reports
        due_reports = await db.execute(
            select(ReportSchedule)
            .where(ReportSchedule.is_active == True)
            .where(ReportSchedule.next_run <= now)
        )
        
        for schedule in due_reports.scalars():
            try:
                # Generate report
                builder = ReportBuilderService(db)
                config = schedule.report_config
                
                report = await builder.build_report(
                    entity=config["entity"],
                    fields=config["fields"],
                    filters=config.get("filters"),
                    order_by=config.get("order_by"),
                    limit=config.get("limit", 1000),
                )
                
                # Export to requested format
                if schedule.format == "csv":
                    content = await builder.export_to_csv(report)
                    filename = f"{schedule.name}_{now.strftime('%Y%m%d')}.csv"
                    content_type = "text/csv"
                else:
                    content = await builder.export_to_excel(report)
                    filename = f"{schedule.name}_{now.strftime('%Y%m%d')}.xlsx"
                    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                
                # Send email to recipients
                email_service = EmailService()
                for recipient in schedule.recipients:
                    await email_service.send_report_email(
                        to=recipient,
                        subject=f"Scheduled Report: {schedule.name}",
                        report_name=schedule.name,
                        attachment=content,
                        filename=filename,
                        content_type=content_type,
                    )
                
                # Update schedule
                schedule.last_run = now
                schedule.next_run = calculate_next_run(schedule)
                
            except Exception as e:
                # Log error but continue with other reports
                print(f"Error running scheduled report {schedule.id}: {e}")
        
        await db.commit()


def calculate_next_run(schedule: ReportSchedule) -> datetime:
    """Calculate next run time based on frequency."""
    from datetime import timedelta
    now = datetime.utcnow()
    
    if schedule.frequency == "daily":
        return now + timedelta(days=1)
    elif schedule.frequency == "weekly":
        days_ahead = schedule.day_of_week - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return now + timedelta(days=days_ahead)
    elif schedule.frequency == "monthly":
        # Next month, same day
        if now.month == 12:
            return now.replace(year=now.year + 1, month=1, day=schedule.day_of_month)
        return now.replace(month=now.month + 1, day=schedule.day_of_month)
    
    return now + timedelta(days=1)
```

---

## Testing Requirements

### Test Files

- `src/tests/test_analytics_service.py`
- `src/tests/test_report_builder.py`
- `src/tests/test_analytics_ui.py`

### Test Scenarios

1. **Analytics Service**
   - Membership stats calculated correctly
   - Trend data returns expected months
   - Dues analytics sum correctly

2. **Report Builder**
   - Valid entity/fields accepted
   - Invalid entity rejected
   - Filters applied correctly
   - Export formats work

3. **Dashboard UI**
   - Charts render with data
   - Empty states handled
   - Role-based access enforced

---

## Acceptance Criteria

### Required

- [ ] Executive dashboard with 4 key metrics
- [ ] Membership trend chart (12 months)
- [ ] Dues collection analytics
- [ ] Custom report builder functional
- [ ] CSV/Excel export working
- [ ] Role-based access (officers+)
- [ ] 15-20 new tests passing

### Optional

- [ ] Scheduled report delivery
- [ ] PDF export
- [ ] Dashboard customization
- [ ] Saved report configurations

---

## 📝 MANDATORY: End-of-Session Documentation

> **REQUIRED:** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. **Do not forget about ADRs—update as necessary.**

### Quick Checklist

- [ ] `/CHANGELOG.md` — Version bump (v0.9.3-alpha)
- [ ] `/CLAUDE.md` — Note analytics features
- [ ] `/docs/IP2A_MILESTONE_CHECKLIST.md` — Mark Week 19 complete
- [ ] `/docs/reports/session-logs/YYYY-MM-DD-analytics.md` — **Create session log**
- [ ] Consider ADR for report builder architecture decisions

---

*Last Updated: February 2, 2026*
