# Phase 6 Week 6 - Session C: Grievance Tracking

**Document:** 3 of 4
**Estimated Time:** 2-3 hours
**Focus:** Grievance list with step indicators, detail page with step timeline

---

## Objective

Create the Grievance Tracking UI:
- Grievance list with step progress indicators
- Filter by status, category, and step
- Grievance detail with step timeline
- Step progression display (1-4 + Arbitration)
- HTMX live search

---

## Pre-flight Checklist

```bash
cd ~/Projects/IP2A-Database-v2
git pull origin main
docker-compose up -d
pytest -v --tb=short | tail -5  # Should show ~238+ passed
```

---

## Step 1: Add Grievance Methods to Service (30 min)

Add to `src/services/operations_frontend_service.py`:

```python
    # ============================================================
    # Grievance Methods (Add after Benevolence methods)
    # ============================================================

    async def get_grievance_stats(self) -> dict:
        """Get grievance stats for list page."""
        total = await self._count_grievances_total()
        open_count = await self._count_grievances_open()

        # Count by status
        filed = await self._count_grievances_by_status(GrievanceStatus.FILED)
        step1 = await self._count_grievances_by_status(GrievanceStatus.STEP_1)
        step2 = await self._count_grievances_by_status(GrievanceStatus.STEP_2)
        step3 = await self._count_grievances_by_status(GrievanceStatus.STEP_3)
        step4 = await self._count_grievances_by_status(GrievanceStatus.STEP_4)
        resolved = await self._count_grievances_by_status(GrievanceStatus.RESOLVED)

        # Resolution rate (resolved / total filed)
        resolution_rate = (resolved / total * 100) if total > 0 else 0

        return {
            "total": total,
            "open": open_count,
            "filed": filed,
            "step_1": step1,
            "step_2": step2,
            "step_3": step3,
            "step_4": step4,
            "resolved": resolved,
            "resolution_rate": round(resolution_rate, 1),
        }

    async def _count_grievances_by_status(self, status: GrievanceStatus) -> int:
        stmt = select(func.count(Grievance.id)).where(
            Grievance.status == status
        )
        return (await self.db.execute(stmt)).scalar() or 0

    async def search_grievances(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Grievance], int, int]:
        """Search grievances with filters."""
        stmt = select(Grievance).options(
            selectinload(Grievance.member),
            selectinload(Grievance.employer),
            selectinload(Grievance.filed_by),
        )

        # Search by grievance number, member name, or employer
        if query and query.strip():
            search_term = f"%{query.strip()}%"
            stmt = stmt.outerjoin(Grievance.member).outerjoin(Grievance.employer).where(
                or_(
                    Grievance.grievance_number.ilike(search_term),
                    Member.first_name.ilike(search_term),
                    Member.last_name.ilike(search_term),
                    func.concat(Member.first_name, ' ', Member.last_name).ilike(search_term),
                    Organization.name.ilike(search_term),
                    Grievance.description.ilike(search_term),
                )
            )

        # Filter by status
        if status and status != "all":
            try:
                status_enum = GrievanceStatus(status)
                stmt = stmt.where(Grievance.status == status_enum)
            except ValueError:
                pass

        # Filter by category
        if category and category != "all":
            try:
                category_enum = GrievanceCategory(category)
                stmt = stmt.where(Grievance.category == category_enum)
            except ValueError:
                pass

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Sort and paginate
        stmt = stmt.order_by(Grievance.filed_at.desc())
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(stmt)
        grievances = list(result.unique().scalars().all())

        total_pages = (total + per_page - 1) // per_page

        return grievances, total, total_pages

    async def get_grievance_by_id(self, grievance_id: int) -> Optional[Grievance]:
        """Get a grievance with all relationships."""
        stmt = select(Grievance).options(
            selectinload(Grievance.member),
            selectinload(Grievance.employer),
            selectinload(Grievance.filed_by),
            selectinload(Grievance.steps).selectinload(GrievanceStep.handled_by),
        ).where(Grievance.id == grievance_id)

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def get_grievance_status_badge_class(status: GrievanceStatus) -> str:
        """Get DaisyUI badge class for grievance status."""
        mapping = {
            GrievanceStatus.FILED: "badge-info",
            GrievanceStatus.STEP_1: "badge-warning",
            GrievanceStatus.STEP_2: "badge-warning",
            GrievanceStatus.STEP_3: "badge-warning",
            GrievanceStatus.STEP_4: "badge-error",  # Arbitration
            GrievanceStatus.RESOLVED: "badge-success",
            GrievanceStatus.WITHDRAWN: "badge-ghost",
        }
        return mapping.get(status, "badge-ghost")

    @staticmethod
    def get_grievance_category_badge_class(category: GrievanceCategory) -> str:
        """Get DaisyUI badge class for grievance category."""
        mapping = {
            GrievanceCategory.CONTRACT: "badge-primary",
            GrievanceCategory.SAFETY: "badge-error",
            GrievanceCategory.DISCRIMINATION: "badge-warning",
            GrievanceCategory.TERMINATION: "badge-secondary",
            GrievanceCategory.OTHER: "badge-ghost",
        }
        return mapping.get(category, "badge-ghost")

    @staticmethod
    def get_step_status_class(step_status) -> str:
        """Get class for step status in timeline."""
        if hasattr(step_status, 'value'):
            status_val = step_status.value
        else:
            status_val = str(step_status)

        mapping = {
            "pending": "text-warning",
            "in_progress": "text-info",
            "completed": "text-success",
            "escalated": "text-error",
        }
        return mapping.get(status_val, "text-base-content/50")
```

---

## Step 2: Add Grievance Routes (25 min)

Add to `src/routers/operations_frontend.py`:

```python
# ============================================================
# Grievance Routes
# ============================================================

@router.get("/grievances", response_class=HTMLResponse)
async def grievances_list_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render grievances list page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = OperationsFrontendService(db)
    stats = await service.get_grievance_stats()
    all_statuses = [s.value for s in GrievanceStatus]
    all_categories = [c.value for c in GrievanceCategory]

    return templates.TemplateResponse(
        "operations/grievances/index.html",
        {
            "request": request,
            "user": current_user,
            "stats": stats,
            "all_statuses": all_statuses,
            "all_categories": all_categories,
            "get_status_badge_class": service.get_grievance_status_badge_class,
            "get_category_badge_class": service.get_grievance_category_badge_class,
        }
    )


@router.get("/grievances/search", response_class=HTMLResponse)
async def grievances_search_partial(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
    q: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
):
    """HTMX partial: Grievances table body."""
    if isinstance(current_user, RedirectResponse):
        return HTMLResponse("Session expired", status_code=401)

    service = OperationsFrontendService(db)
    grievances, total, total_pages = await service.search_grievances(
        query=q,
        status=status,
        category=category,
        page=page,
    )

    return templates.TemplateResponse(
        "operations/grievances/partials/_table.html",
        {
            "request": request,
            "grievances": grievances,
            "total": total,
            "total_pages": total_pages,
            "current_page": page,
            "query": q or "",
            "status_filter": status or "all",
            "category_filter": category or "all",
            "get_status_badge_class": service.get_grievance_status_badge_class,
            "get_category_badge_class": service.get_grievance_category_badge_class,
        }
    )


@router.get("/grievances/{grievance_id}", response_class=HTMLResponse)
async def grievance_detail_page(
    request: Request,
    grievance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """Render grievance detail page."""
    if isinstance(current_user, RedirectResponse):
        return current_user

    service = OperationsFrontendService(db)
    grievance = await service.get_grievance_by_id(grievance_id)

    if not grievance:
        return templates.TemplateResponse(
            "errors/404.html",
            {"request": request, "message": "Grievance not found"},
            status_code=404
        )

    all_statuses = [s.value for s in GrievanceStatus]

    return templates.TemplateResponse(
        "operations/grievances/detail.html",
        {
            "request": request,
            "user": current_user,
            "grievance": grievance,
            "all_statuses": all_statuses,
            "get_status_badge_class": service.get_grievance_status_badge_class,
            "get_category_badge_class": service.get_grievance_category_badge_class,
            "get_step_status_class": service.get_step_status_class,
        }
    )
```

---

## Step 3: Create Grievances List Page (25 min)

Create `src/templates/operations/grievances/index.html`:

```html
{% extends "base.html" %}

{% block title %}Grievances - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/operations">Operations</a></li>
            <li>Grievances</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
            <h1 class="text-2xl font-bold">Grievances</h1>
            <p class="text-base-content/60">Contract enforcement and dispute resolution</p>
        </div>
        <button class="btn btn-primary">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
            </svg>
            File Grievance
        </button>
    </div>

    <!-- Stats Cards -->
    <div class="stats stats-vertical lg:stats-horizontal shadow w-full">
        <div class="stat">
            <div class="stat-title">Total Filed</div>
            <div class="stat-value">{{ stats.total }}</div>
        </div>
        <div class="stat">
            <div class="stat-title">Open Cases</div>
            <div class="stat-value text-warning">{{ stats.open }}</div>
        </div>
        <div class="stat">
            <div class="stat-title">Step 1</div>
            <div class="stat-value text-info">{{ stats.step_1 }}</div>
        </div>
        <div class="stat">
            <div class="stat-title">Arbitration</div>
            <div class="stat-value text-error">{{ stats.step_4 }}</div>
        </div>
        <div class="stat">
            <div class="stat-title">Resolution Rate</div>
            <div class="stat-value text-success">{{ stats.resolution_rate }}%</div>
        </div>
    </div>

    <!-- Search and Filters -->
    <div class="card bg-base-100 shadow">
        <div class="card-body p-4">
            <div class="flex flex-col lg:flex-row gap-4">
                <!-- Search -->
                <div class="flex-1">
                    <div class="relative">
                        <input
                            type="search"
                            name="q"
                            placeholder="Search by grievance #, member, or employer..."
                            class="input input-bordered w-full pl-10"
                            hx-get="/operations/grievances/search"
                            hx-trigger="input changed delay:300ms, search"
                            hx-target="#table-container"
                            hx-include="[name='status'], [name='category']"
                            hx-indicator="#search-spinner"
                        />
                        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-base-content/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                        </svg>
                        <span id="search-spinner" class="loading loading-spinner loading-sm absolute right-3 top-1/2 -translate-y-1/2 htmx-indicator"></span>
                    </div>
                </div>

                <!-- Status Filter -->
                <div class="w-full lg:w-48">
                    <select
                        name="status"
                        class="select select-bordered w-full"
                        hx-get="/operations/grievances/search"
                        hx-trigger="change"
                        hx-target="#table-container"
                        hx-include="[name='q'], [name='category']"
                    >
                        <option value="all">All Status</option>
                        {% for status in all_statuses %}
                        <option value="{{ status }}">{{ status.replace('_', ' ') | title }}</option>
                        {% endfor %}
                    </select>
                </div>

                <!-- Category Filter -->
                <div class="w-full lg:w-48">
                    <select
                        name="category"
                        class="select select-bordered w-full"
                        hx-get="/operations/grievances/search"
                        hx-trigger="change"
                        hx-target="#table-container"
                        hx-include="[name='q'], [name='status']"
                    >
                        <option value="all">All Categories</option>
                        {% for category in all_categories %}
                        <option value="{{ category }}">{{ category | title }}</option>
                        {% endfor %}
                    </select>
                </div>
            </div>
        </div>
    </div>

    <!-- Grievances Table -->
    <div class="card bg-base-100 shadow overflow-hidden">
        <div
            id="table-container"
            hx-get="/operations/grievances/search"
            hx-trigger="load"
        >
            <div class="flex justify-center py-12">
                <span class="loading loading-spinner loading-lg"></span>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Step 4: Create Grievances Table Partial (20 min)

Create `src/templates/operations/grievances/partials/_table.html`:

```html
{# Grievances table #}

<div class="overflow-x-auto">
    <table class="table table-zebra">
        <thead>
            <tr class="bg-base-200">
                <th>Grievance #</th>
                <th>Member</th>
                <th>Employer</th>
                <th>Category</th>
                <th>Step Progress</th>
                <th>Status</th>
                <th>Filed</th>
                <th class="w-24">Actions</th>
            </tr>
        </thead>
        <tbody>
            {% if grievances %}
                {% for grv in grievances %}
                <tr class="hover">
                    <!-- Grievance Number -->
                    <td>
                        <span class="font-mono font-bold">{{ grv.grievance_number or 'GRV-' ~ grv.id }}</span>
                    </td>

                    <!-- Member -->
                    <td>
                        <div class="flex items-center gap-2">
                            <div class="avatar placeholder">
                                <div class="bg-neutral text-neutral-content rounded-full w-8">
                                    <span class="text-xs">
                                        {{ grv.member.first_name[0] | upper if grv.member else '?' }}{{ grv.member.last_name[0] | upper if grv.member else '' }}
                                    </span>
                                </div>
                            </div>
                            <span class="text-sm">
                                {{ grv.member.first_name if grv.member else 'N/A' }} {{ grv.member.last_name if grv.member else '' }}
                            </span>
                        </div>
                    </td>

                    <!-- Employer -->
                    <td>
                        <span class="text-sm">{{ grv.employer.name if grv.employer else 'Unknown' }}</span>
                    </td>

                    <!-- Category -->
                    <td>
                        <span class="badge {{ get_category_badge_class(grv.category) }} badge-sm">
                            {{ grv.category.value | title }}
                        </span>
                    </td>

                    <!-- Step Progress (mini steps) -->
                    <td>
                        <ul class="steps steps-horizontal">
                            <li class="step {{ 'step-primary' if grv.current_step >= 1 else '' }} text-xs" data-content="1"></li>
                            <li class="step {{ 'step-primary' if grv.current_step >= 2 else '' }} text-xs" data-content="2"></li>
                            <li class="step {{ 'step-primary' if grv.current_step >= 3 else '' }} text-xs" data-content="3"></li>
                            <li class="step {{ 'step-error' if grv.current_step >= 4 else '' }} text-xs" data-content="A"></li>
                        </ul>
                    </td>

                    <!-- Status -->
                    <td>
                        <span class="badge {{ get_status_badge_class(grv.status) }}">
                            {{ grv.status.value.replace('_', ' ') | title }}
                        </span>
                    </td>

                    <!-- Filed Date -->
                    <td>
                        {{ grv.filed_at.strftime('%b %d, %Y') if grv.filed_at else '—' }}
                    </td>

                    <!-- Actions -->
                    <td>
                        <a href="/operations/grievances/{{ grv.id }}" class="btn btn-ghost btn-sm">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                            </svg>
                        </a>
                    </td>
                </tr>
                {% endfor %}
            {% else %}
            <tr>
                <td colspan="8" class="text-center py-12">
                    <div class="text-base-content/50">
                        <svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                        </svg>
                        <p class="text-lg">No grievances found</p>
                    </div>
                </td>
            </tr>
            {% endif %}
        </tbody>
    </table>
</div>

{% if grievances %}
<!-- Pagination -->
<div class="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 border-t border-base-200">
    <div class="text-sm text-base-content/60">
        Showing {{ ((current_page - 1) * 20) + 1 }} - {{ ((current_page - 1) * 20) + grievances|length }} of {{ total }}
    </div>

    <div class="join">
        {% if current_page > 1 %}
        <button
            class="join-item btn btn-sm"
            hx-get="/operations/grievances/search?page={{ current_page - 1 }}&q={{ query }}&status={{ status_filter }}&category={{ category_filter }}"
            hx-target="#table-container"
        >«</button>
        {% else %}
        <button class="join-item btn btn-sm btn-disabled">«</button>
        {% endif %}

        <button class="join-item btn btn-sm btn-active">{{ current_page }}</button>

        {% if current_page < total_pages %}
        <button
            class="join-item btn btn-sm"
            hx-get="/operations/grievances/search?page={{ current_page + 1 }}&q={{ query }}&status={{ status_filter }}&category={{ category_filter }}"
            hx-target="#table-container"
        >»</button>
        {% else %}
        <button class="join-item btn btn-sm btn-disabled">»</button>
        {% endif %}
    </div>
</div>
{% endif %}
```

---

## Step 5: Create Grievance Detail Page (30 min)

Create `src/templates/operations/grievances/detail.html`:

```html
{% extends "base.html" %}

{% block title %}{{ grievance.grievance_number or 'Grievance' }} - IP2A{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Breadcrumb -->
    <div class="text-sm breadcrumbs">
        <ul>
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/operations">Operations</a></li>
            <li><a href="/operations/grievances">Grievances</a></li>
            <li>{{ grievance.grievance_number or 'Case #' ~ grievance.id }}</li>
        </ul>
    </div>

    <!-- Page Header -->
    <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
        <div>
            <div class="flex items-center gap-3">
                <h1 class="text-2xl font-bold font-mono">{{ grievance.grievance_number or 'GRV-' ~ grievance.id }}</h1>
                <span class="badge {{ get_status_badge_class(grievance.status) }} badge-lg">
                    {{ grievance.status.value.replace('_', ' ') | title }}
                </span>
                <span class="badge {{ get_category_badge_class(grievance.category) }}">
                    {{ grievance.category.value | title }}
                </span>
            </div>
            <p class="text-base-content/60 mt-1">
                vs. {{ grievance.employer.name if grievance.employer else 'Unknown Employer' }}
            </p>
        </div>
        <div class="flex gap-2">
            <a href="/operations/grievances" class="btn btn-ghost">← Back</a>
            {% if grievance.status.value not in ['resolved', 'withdrawn'] %}
            <button class="btn btn-primary">Escalate to Step {{ grievance.current_step + 1 }}</button>
            {% endif %}
        </div>
    </div>

    <!-- Step Progress -->
    <div class="card bg-base-100 shadow">
        <div class="card-body">
            <h2 class="card-title text-lg">Grievance Progress</h2>
            <ul class="steps steps-horizontal w-full mt-4">
                <li class="step step-primary" data-content="✓">Filed</li>
                <li class="step {{ 'step-primary' if grievance.current_step >= 1 else '' }}" data-content="{{ '✓' if grievance.current_step > 1 else '1' }}">
                    Step 1
                    <span class="text-xs block">Supervisor</span>
                </li>
                <li class="step {{ 'step-primary' if grievance.current_step >= 2 else '' }}" data-content="{{ '✓' if grievance.current_step > 2 else '2' }}">
                    Step 2
                    <span class="text-xs block">HR/Manager</span>
                </li>
                <li class="step {{ 'step-primary' if grievance.current_step >= 3 else '' }}" data-content="{{ '✓' if grievance.current_step > 3 else '3' }}">
                    Step 3
                    <span class="text-xs block">Director</span>
                </li>
                <li class="step {{ 'step-error' if grievance.current_step >= 4 else '' }}" data-content="{{ '⚖' if grievance.current_step >= 4 else '4' }}">
                    Arbitration
                </li>
                <li class="step {{ 'step-success' if grievance.status.value == 'resolved' else '' }}" data-content="{{ '✓' if grievance.status.value == 'resolved' else '?' }}">
                    Resolution
                </li>
            </ul>
        </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Main Content -->
        <div class="lg:col-span-2 space-y-6">
            <!-- Case Details -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title">Case Details</h2>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                        <div>
                            <label class="text-sm text-base-content/60">Grievant</label>
                            <p class="font-medium">
                                {{ grievance.member.first_name if grievance.member else 'N/A' }}
                                {{ grievance.member.last_name if grievance.member else '' }}
                            </p>
                        </div>
                        <div>
                            <label class="text-sm text-base-content/60">Employer</label>
                            <p class="font-medium">{{ grievance.employer.name if grievance.employer else 'Unknown' }}</p>
                        </div>
                        <div>
                            <label class="text-sm text-base-content/60">Category</label>
                            <p>
                                <span class="badge {{ get_category_badge_class(grievance.category) }}">
                                    {{ grievance.category.value | title }}
                                </span>
                            </p>
                        </div>
                        <div>
                            <label class="text-sm text-base-content/60">Filed By</label>
                            <p>{{ grievance.filed_by.email if grievance.filed_by else 'N/A' }}</p>
                        </div>
                    </div>

                    <div class="mt-4">
                        <label class="text-sm text-base-content/60">Description</label>
                        <p class="mt-1 whitespace-pre-wrap bg-base-200 p-4 rounded-lg">{{ grievance.description }}</p>
                    </div>

                    {% if grievance.resolution %}
                    <div class="mt-4">
                        <label class="text-sm text-base-content/60">Resolution</label>
                        <div class="alert alert-success mt-1">
                            <svg class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span>{{ grievance.resolution }}</span>
                        </div>
                    </div>
                    {% endif %}
                </div>
            </div>

            <!-- Step Timeline -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <div class="flex items-center justify-between">
                        <h2 class="card-title">Step History</h2>
                        <button class="btn btn-sm btn-primary">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                            </svg>
                            Add Step Note
                        </button>
                    </div>

                    {% if grievance.steps %}
                    <ul class="timeline timeline-vertical mt-4">
                        {% for step in grievance.steps | sort(attribute='step_number') %}
                        <li>
                            {% if not loop.first %}
                            <hr class="{{ 'bg-primary' if step.status and step.status.value == 'completed' else 'bg-base-300' }}"/>
                            {% endif %}

                            <div class="timeline-start text-sm">
                                {{ step.started_at.strftime('%b %d, %Y') if step.started_at else '—' }}
                            </div>

                            <div class="timeline-middle">
                                {% if step.status and step.status.value == 'completed' %}
                                <svg class="w-5 h-5 text-success" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                                </svg>
                                {% elif step.status and step.status.value == 'escalated' %}
                                <svg class="w-5 h-5 text-error" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-11a1 1 0 10-2 0v3.586L7.707 9.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 10.586V7z" clip-rule="evenodd"/>
                                </svg>
                                {% else %}
                                <svg class="w-5 h-5 text-warning" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"/>
                                </svg>
                                {% endif %}
                            </div>

                            <div class="timeline-end timeline-box">
                                <div class="flex items-center justify-between gap-2">
                                    <span class="font-bold">Step {{ step.step_number }}{% if step.step_number == 4 %} (Arbitration){% endif %}</span>
                                    {% if step.status %}
                                    <span class="badge badge-sm {{ get_step_status_class(step.status) }}">
                                        {{ step.status.value | title }}
                                    </span>
                                    {% endif %}
                                </div>
                                {% if step.outcome %}
                                <p class="text-sm mt-1">{{ step.outcome }}</p>
                                {% endif %}
                                {% if step.notes %}
                                <p class="text-xs text-base-content/60 mt-1">{{ step.notes }}</p>
                                {% endif %}
                                <div class="text-xs text-base-content/50 mt-2">
                                    Handled by: {{ step.handled_by.email if step.handled_by else 'N/A' }}
                                </div>
                            </div>

                            {% if not loop.last %}
                            <hr class="{{ 'bg-primary' if step.status and step.status.value == 'completed' else 'bg-base-300' }}"/>
                            {% endif %}
                        </li>
                        {% endfor %}
                    </ul>
                    {% else %}
                    <div class="text-center py-8 text-base-content/50">
                        <p>No step history recorded</p>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>

        <!-- Sidebar -->
        <div class="space-y-6">
            <!-- Status Card -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title text-lg">Update Status</h2>
                    <select class="select select-bordered w-full mt-2">
                        {% for status in all_statuses %}
                        <option value="{{ status }}" {{ 'selected' if grievance.status.value == status }}>
                            {{ status.replace('_', ' ') | title }}
                        </option>
                        {% endfor %}
                    </select>
                    <button class="btn btn-primary btn-sm mt-2">Update</button>
                </div>
            </div>

            <!-- Timeline Card -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title text-lg">Timeline</h2>
                    <div class="space-y-3 text-sm mt-2">
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Filed</span>
                            <span>{{ grievance.filed_at.strftime('%b %d, %Y') if grievance.filed_at else '—' }}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Current Step</span>
                            <span class="font-bold">{{ grievance.current_step }}</span>
                        </div>
                        {% if grievance.resolved_at %}
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Resolved</span>
                            <span>{{ grievance.resolved_at.strftime('%b %d, %Y') }}</span>
                        </div>
                        {% endif %}
                        <div class="divider my-2"></div>
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Created</span>
                            <span>{{ grievance.created_at.strftime('%b %d, %Y') }}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-base-content/60">Updated</span>
                            <span>{{ grievance.updated_at.strftime('%b %d, %Y') }}</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Related Links -->
            <div class="card bg-base-100 shadow">
                <div class="card-body">
                    <h2 class="card-title text-lg">Related</h2>
                    <div class="space-y-2 mt-2">
                        {% if grievance.member %}
                        <a href="/members/{{ grievance.member.id }}" class="btn btn-outline btn-sm btn-block">
                            View Member Profile
                        </a>
                        {% endif %}
                        <button class="btn btn-outline btn-sm btn-block">
                            View Documents
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Step 6: Commit Session C

```bash
git add -A
git status

git commit -m "feat(operations): Phase 6 Week 6 Session C - Grievance Tracking

- Add grievance methods to OperationsFrontendService
- Add grievance routes (list, search, detail)
- Grievances list with step progress indicators
- Step progress visualization (steps component)
- Grievance detail with step timeline
- Filter by status and category
- HTMX live search
- Mini-steps progress in table rows

Stats: total, open, by step, resolution rate
Steps: 1 (Supervisor), 2 (HR), 3 (Director), 4 (Arbitration)"

git push origin main
```

---

## Session C Checklist

- [ ] Added grievance methods to service
- [ ] Added grievance routes to router
- [ ] Created `operations/grievances/index.html`
- [ ] Created `operations/grievances/detail.html`
- [ ] Created `operations/grievances/partials/_table.html`
- [ ] Step progress indicators in table
- [ ] Step timeline in detail page
- [ ] Search and filters working
- [ ] Committed changes

---

*Session C complete. Proceed to Session D for Tests + Documentation + ADRs.*
