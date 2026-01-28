# Claude Code Instructions: Phase 6 - Frontend UI

**Document Version:** 1.0
**Created:** January 28, 2026
**Estimated Time:** 8-12 hours (across multiple sessions)
**Priority:** High (makes system usable)
**Target Version:** v0.8.0

---

## Objective

Build a functional web interface for IP2A using Jinja2 templates, HTMX for dynamic interactions, Alpine.js for client-side state, and Tailwind CSS for styling. This follows ADR-002 (Frontend Framework Choice).

---

## Why This Stack?

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| **Jinja2** | Server-side HTML templates | Built into FastAPI, simple |
| **HTMX** | Dynamic updates without JS | HTML attributes, no build step |
| **Alpine.js** | Client-side interactions | Lightweight, declarative |
| **Tailwind CSS** | Styling | Utility-first, rapid development |

**Benefits:**
- Single deployment (FastAPI serves everything)
- No complex JavaScript build pipeline
- HTML/CSS skills are sufficient
- 10+ year stability (HTML attributes don't break)

---

## Architecture Overview

```
Browser Request → FastAPI Router → Jinja2 Template → HTML Response
                                        ↓
                              HTMX triggers partial updates
                                        ↓
                              Alpine.js handles UI state
```

### Request Flow Examples

**Full Page Load:**
```
GET /members → members.py router → list.html template → Full HTML page
```

**HTMX Partial Update:**
```
GET /members/search?q=smith → members.py router → _search_results.html → HTML fragment
(HTMX swaps into #results div)
```

---

## Step-by-Step Implementation

### Step 1: Create Directory Structure

```bash
cd ~/Projects/IP2A-Database-v2

# Create template directories
mkdir -p src/templates/{auth,dashboard,members,training,dues,documents,components,errors,layouts}

# Create static directories
mkdir -p src/static/{css,js,images}
```

**Final Structure:**
```
src/
├── templates/
│   ├── layouts/
│   │   └── base.html           # Master layout
│   ├── components/
│   │   ├── _navbar.html        # Navigation bar
│   │   ├── _sidebar.html       # Sidebar menu
│   │   ├── _flash.html         # Flash messages
│   │   ├── _pagination.html    # Pagination controls
│   │   ├── _modal.html         # Modal container
│   │   ├── _table.html         # Reusable table
│   │   └── _card.html          # Card component
│   ├── auth/
│   │   ├── login.html
│   │   └── forgot_password.html
│   ├── dashboard/
│   │   └── index.html          # Main dashboard
│   ├── members/
│   │   ├── list.html
│   │   ├── detail.html
│   │   ├── form.html           # Create/Edit form
│   │   └── _search_results.html # HTMX partial
│   ├── training/
│   │   ├── students/
│   │   ├── courses/
│   │   └── enrollments/
│   ├── dues/
│   │   ├── payments/
│   │   ├── periods/
│   │   └── adjustments/
│   ├── documents/
│   │   └── list.html
│   └── errors/
│       ├── 404.html
│       └── 500.html
├── static/
│   ├── css/
│   │   ├── input.css           # Tailwind input
│   │   └── output.css          # Compiled (generated)
│   ├── js/
│   │   └── app.js              # Alpine.js components
│   └── images/
│       └── logo.png
```

### Step 2: Install Dependencies

**File:** `requirements.txt`

Add:
```
jinja2>=3.1.0
python-multipart>=0.0.6
aiofiles>=23.0.0
```

For Tailwind CSS (optional but recommended):
```bash
# Install Node.js dependencies (run from project root)
npm init -y
npm install -D tailwindcss
npx tailwindcss init
```

### Step 3: Configure FastAPI for Templates

**File:** `src/config/templates.py`

```python
"""Jinja2 template configuration."""
from pathlib import Path

from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles

# Template directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
STATIC_DIR = Path(__file__).parent.parent / "static"

# Initialize Jinja2
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Custom filters
def format_currency(value):
    """Format decimal as currency."""
    if value is None:
        return "$0.00"
    return f"${value:,.2f}"

def format_date(value, format="%b %d, %Y"):
    """Format date for display."""
    if value is None:
        return ""
    return value.strftime(format)

# Register custom filters
templates.env.filters["currency"] = format_currency
templates.env.filters["date"] = format_date
```

**File:** `src/main.py`

Add static files and template configuration:

```python
from fastapi.staticfiles import StaticFiles
from src.config.templates import STATIC_DIR

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
```

### Step 4: Create Base Layout

**File:** `src/templates/layouts/base.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}IP2A{% endblock %} - IBEW Local 46</title>
    
    <!-- Tailwind CSS -->
    <link href="{{ url_for('static', path='css/output.css') }}" rel="stylesheet">
    
    <!-- HTMX -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    
    <!-- Alpine.js -->
    <script defer src="https://unpkg.com/alpinejs@3.13.3/dist/cdn.min.js"></script>
    
    <!-- HTMX loading indicator -->
    <style>
        .htmx-request .htmx-indicator { display: inline; }
        .htmx-indicator { display: none; }
    </style>
    
    {% block head %}{% endblock %}
</head>
<body class="bg-gray-100 min-h-screen" x-data="{ sidebarOpen: true }">
    
    <!-- Top Navigation -->
    {% include 'components/_navbar.html' %}
    
    <div class="flex">
        <!-- Sidebar -->
        {% include 'components/_sidebar.html' %}
        
        <!-- Main Content -->
        <main class="flex-1 p-6" :class="{ 'ml-64': sidebarOpen, 'ml-0': !sidebarOpen }">
            <!-- Flash Messages -->
            {% include 'components/_flash.html' %}
            
            <!-- Page Content -->
            {% block content %}{% endblock %}
        </main>
    </div>
    
    <!-- Modal Container (for HTMX) -->
    <div id="modal" class="hidden fixed inset-0 bg-black bg-opacity-50 z-50">
        <div id="modal-content" class="bg-white rounded-lg shadow-xl max-w-2xl mx-auto mt-20 p-6">
            <!-- HTMX will load modal content here -->
        </div>
    </div>
    
    <!-- App JavaScript -->
    <script src="{{ url_for('static', path='js/app.js') }}"></script>
    
    {% block scripts %}{% endblock %}
</body>
</html>
```

### Step 5: Create Navigation Components

**File:** `src/templates/components/_navbar.html`

```html
<nav class="bg-blue-800 text-white shadow-lg fixed top-0 left-0 right-0 z-40">
    <div class="px-4 py-3 flex items-center justify-between">
        <!-- Logo & Toggle -->
        <div class="flex items-center space-x-4">
            <button @click="sidebarOpen = !sidebarOpen" class="p-2 rounded hover:bg-blue-700">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
                </svg>
            </button>
            <a href="/dashboard" class="text-xl font-bold">IP2A - IBEW Local 46</a>
        </div>
        
        <!-- User Menu -->
        <div class="flex items-center space-x-4" x-data="{ userMenuOpen: false }">
            <span class="text-sm">{{ current_user.email if current_user else 'Guest' }}</span>
            <div class="relative">
                <button @click="userMenuOpen = !userMenuOpen" class="p-2 rounded hover:bg-blue-700">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                </button>
                <div x-show="userMenuOpen" @click.away="userMenuOpen = false" 
                     class="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 text-gray-800">
                    <a href="/auth/profile" class="block px-4 py-2 hover:bg-gray-100">Profile</a>
                    <a href="/auth/logout" class="block px-4 py-2 hover:bg-gray-100">Logout</a>
                </div>
            </div>
        </div>
    </div>
</nav>
```

**File:** `src/templates/components/_sidebar.html`

```html
<aside x-show="sidebarOpen" 
       x-transition:enter="transition ease-out duration-200"
       x-transition:enter-start="-translate-x-full"
       x-transition:enter-end="translate-x-0"
       class="fixed left-0 top-14 bottom-0 w-64 bg-gray-800 text-white overflow-y-auto z-30">
    <nav class="p-4 space-y-2">
        <!-- Dashboard -->
        <a href="/dashboard" class="flex items-center space-x-3 px-4 py-2 rounded hover:bg-gray-700 {{ 'bg-gray-700' if request.url.path == '/dashboard' else '' }}">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
            </svg>
            <span>Dashboard</span>
        </a>
        
        <!-- Members -->
        <div x-data="{ open: false }">
            <button @click="open = !open" class="w-full flex items-center justify-between px-4 py-2 rounded hover:bg-gray-700">
                <span class="flex items-center space-x-3">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
                    </svg>
                    <span>Members</span>
                </span>
                <svg class="w-4 h-4 transition-transform" :class="{ 'rotate-90': open }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
            </button>
            <div x-show="open" class="ml-8 mt-1 space-y-1">
                <a href="/members" class="block px-4 py-2 rounded hover:bg-gray-700">All Members</a>
                <a href="/members/new" class="block px-4 py-2 rounded hover:bg-gray-700">Add Member</a>
            </div>
        </div>
        
        <!-- Training -->
        <div x-data="{ open: false }">
            <button @click="open = !open" class="w-full flex items-center justify-between px-4 py-2 rounded hover:bg-gray-700">
                <span class="flex items-center space-x-3">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                    </svg>
                    <span>Training</span>
                </span>
                <svg class="w-4 h-4 transition-transform" :class="{ 'rotate-90': open }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
            </button>
            <div x-show="open" class="ml-8 mt-1 space-y-1">
                <a href="/training/students" class="block px-4 py-2 rounded hover:bg-gray-700">Students</a>
                <a href="/training/courses" class="block px-4 py-2 rounded hover:bg-gray-700">Courses</a>
                <a href="/training/enrollments" class="block px-4 py-2 rounded hover:bg-gray-700">Enrollments</a>
                <a href="/training/attendance" class="block px-4 py-2 rounded hover:bg-gray-700">Attendance</a>
            </div>
        </div>
        
        <!-- Dues -->
        <div x-data="{ open: false }">
            <button @click="open = !open" class="w-full flex items-center justify-between px-4 py-2 rounded hover:bg-gray-700">
                <span class="flex items-center space-x-3">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    <span>Dues</span>
                </span>
                <svg class="w-4 h-4 transition-transform" :class="{ 'rotate-90': open }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
            </button>
            <div x-show="open" class="ml-8 mt-1 space-y-1">
                <a href="/dues/payments" class="block px-4 py-2 rounded hover:bg-gray-700">Payments</a>
                <a href="/dues/periods" class="block px-4 py-2 rounded hover:bg-gray-700">Periods</a>
                <a href="/dues/rates" class="block px-4 py-2 rounded hover:bg-gray-700">Rates</a>
                <a href="/dues/adjustments" class="block px-4 py-2 rounded hover:bg-gray-700">Adjustments</a>
            </div>
        </div>
        
        <!-- Union Operations -->
        <div x-data="{ open: false }">
            <button @click="open = !open" class="w-full flex items-center justify-between px-4 py-2 rounded hover:bg-gray-700">
                <span class="flex items-center space-x-3">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
                    </svg>
                    <span>Union Ops</span>
                </span>
                <svg class="w-4 h-4 transition-transform" :class="{ 'rotate-90': open }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
            </button>
            <div x-show="open" class="ml-8 mt-1 space-y-1">
                <a href="/salting" class="block px-4 py-2 rounded hover:bg-gray-700">SALTing</a>
                <a href="/benevolence" class="block px-4 py-2 rounded hover:bg-gray-700">Benevolence</a>
                <a href="/grievances" class="block px-4 py-2 rounded hover:bg-gray-700">Grievances</a>
            </div>
        </div>
        
        <!-- Documents -->
        <a href="/documents" class="flex items-center space-x-3 px-4 py-2 rounded hover:bg-gray-700">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
            </svg>
            <span>Documents</span>
        </a>
    </nav>
</aside>
```

### Step 6: Create Dashboard

**File:** `src/templates/dashboard/index.html`

```html
{% extends 'layouts/base.html' %}

{% block title %}Dashboard{% endblock %}

{% block content %}
<div class="mt-14">
    <h1 class="text-2xl font-bold text-gray-800 mb-6">Dashboard</h1>
    
    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <!-- Active Members -->
        <div class="bg-white rounded-lg shadow p-6">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm text-gray-500">Active Members</p>
                    <p class="text-3xl font-bold text-gray-800">{{ stats.active_members }}</p>
                </div>
                <div class="bg-blue-100 p-3 rounded-full">
                    <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
                    </svg>
                </div>
            </div>
            <a href="/members" class="text-sm text-blue-600 hover:underline mt-2 inline-block">View all →</a>
        </div>
        
        <!-- Students Enrolled -->
        <div class="bg-white rounded-lg shadow p-6">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm text-gray-500">Students Enrolled</p>
                    <p class="text-3xl font-bold text-gray-800">{{ stats.enrolled_students }}</p>
                </div>
                <div class="bg-green-100 p-3 rounded-full">
                    <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                    </svg>
                </div>
            </div>
            <a href="/training/students" class="text-sm text-green-600 hover:underline mt-2 inline-block">View all →</a>
        </div>
        
        <!-- Dues This Month -->
        <div class="bg-white rounded-lg shadow p-6">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm text-gray-500">Dues Collected (Month)</p>
                    <p class="text-3xl font-bold text-gray-800">{{ stats.dues_collected | currency }}</p>
                </div>
                <div class="bg-yellow-100 p-3 rounded-full">
                    <svg class="w-8 h-8 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                </div>
            </div>
            <a href="/dues/payments" class="text-sm text-yellow-600 hover:underline mt-2 inline-block">View all →</a>
        </div>
        
        <!-- Open Grievances -->
        <div class="bg-white rounded-lg shadow p-6">
            <div class="flex items-center justify-between">
                <div>
                    <p class="text-sm text-gray-500">Open Grievances</p>
                    <p class="text-3xl font-bold text-gray-800">{{ stats.open_grievances }}</p>
                </div>
                <div class="bg-red-100 p-3 rounded-full">
                    <svg class="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                    </svg>
                </div>
            </div>
            <a href="/grievances" class="text-sm text-red-600 hover:underline mt-2 inline-block">View all →</a>
        </div>
    </div>
    
    <!-- Quick Actions -->
    <div class="bg-white rounded-lg shadow p-6 mb-8">
        <h2 class="text-lg font-semibold text-gray-800 mb-4">Quick Actions</h2>
        <div class="flex flex-wrap gap-3">
            <a href="/members/new" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">+ Add Member</a>
            <a href="/training/students/new" class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">+ Add Student</a>
            <a href="/dues/payments/new" class="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700">+ Record Payment</a>
            <a href="/grievances/new" class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">+ File Grievance</a>
        </div>
    </div>
    
    <!-- Recent Activity -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Recent Members -->
        <div class="bg-white rounded-lg shadow">
            <div class="px-6 py-4 border-b">
                <h2 class="text-lg font-semibold text-gray-800">Recent Members</h2>
            </div>
            <div class="p-6">
                <div hx-get="/members/recent" hx-trigger="load" hx-swap="innerHTML">
                    <p class="text-gray-500">Loading...</p>
                </div>
            </div>
        </div>
        
        <!-- Pending Adjustments -->
        <div class="bg-white rounded-lg shadow">
            <div class="px-6 py-4 border-b">
                <h2 class="text-lg font-semibold text-gray-800">Pending Approvals</h2>
            </div>
            <div class="p-6">
                <div hx-get="/dues/adjustments/pending-widget" hx-trigger="load" hx-swap="innerHTML">
                    <p class="text-gray-500">Loading...</p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### Step 7: Create View Router for Dashboard

**File:** `src/routers/views/dashboard.py`

```python
"""Dashboard view routes."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from src.config.templates import templates
from src.db.session import get_db
from src.routers.dependencies.auth import get_current_user_optional

router = APIRouter(tags=["Views - Dashboard"])


@router.get("/dashboard")
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """Render dashboard page."""
    # Gather stats (import services as needed)
    from src.services import member_service, dues_payment_service
    from src.db.enums import MemberStatus, StudentStatus, GrievanceStatus
    from src.models.member import Member
    from src.models.student import Student
    from src.models.grievance import Grievance
    
    stats = {
        "active_members": db.query(Member).filter(Member.status == MemberStatus.ACTIVE).count(),
        "enrolled_students": db.query(Student).filter(Student.status == StudentStatus.ENROLLED).count(),
        "dues_collected": 12500.00,  # TODO: Calculate from current period
        "open_grievances": db.query(Grievance).filter(
            Grievance.status.in_(["filed", "step_1", "step_2", "step_3"])
        ).count(),
    }
    
    return templates.TemplateResponse(
        "dashboard/index.html",
        {
            "request": request,
            "current_user": current_user,
            "stats": stats,
        }
    )
```

### Step 8: Create Tailwind Config and CSS

**File:** `tailwind.config.js`

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/templates/**/*.html",
    "./src/static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        'ibew-blue': '#003366',
        'ibew-gold': '#FFD700',
      },
    },
  },
  plugins: [],
}
```

**File:** `src/static/css/input.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom components */
@layer components {
  .btn-primary {
    @apply px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors;
  }
  
  .btn-secondary {
    @apply px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors;
  }
  
  .btn-danger {
    @apply px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors;
  }
  
  .form-input {
    @apply w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500;
  }
  
  .form-label {
    @apply block text-sm font-medium text-gray-700 mb-1;
  }
  
  .card {
    @apply bg-white rounded-lg shadow p-6;
  }
  
  .table-header {
    @apply px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider;
  }
  
  .table-cell {
    @apply px-6 py-4 whitespace-nowrap text-sm text-gray-900;
  }
}
```

**Build CSS:**
```bash
npx tailwindcss -i ./src/static/css/input.css -o ./src/static/css/output.css --watch
```

### Step 9: Create Login Page

**File:** `src/templates/auth/login.html`

```html
{% extends 'layouts/base.html' %}

{% block title %}Login{% endblock %}

{% block content %}
<div class="min-h-screen flex items-center justify-center bg-gray-100 -mt-14">
    <div class="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <div class="text-center mb-8">
            <h1 class="text-2xl font-bold text-gray-800">IP2A - IBEW Local 46</h1>
            <p class="text-gray-600">Sign in to your account</p>
        </div>
        
        <form hx-post="/auth/login" hx-target="#login-error" hx-swap="innerHTML" class="space-y-6">
            <div id="login-error"></div>
            
            <div>
                <label for="email" class="form-label">Email</label>
                <input type="email" id="email" name="email" required 
                       class="form-input" placeholder="your.email@example.com">
            </div>
            
            <div>
                <label for="password" class="form-label">Password</label>
                <input type="password" id="password" name="password" required 
                       class="form-input" placeholder="••••••••">
            </div>
            
            <div class="flex items-center justify-between">
                <label class="flex items-center">
                    <input type="checkbox" name="remember" class="rounded text-blue-600">
                    <span class="ml-2 text-sm text-gray-600">Remember me</span>
                </label>
                <a href="/auth/forgot-password" class="text-sm text-blue-600 hover:underline">Forgot password?</a>
            </div>
            
            <button type="submit" class="w-full btn-primary">
                Sign In
                <span class="htmx-indicator ml-2">
                    <svg class="animate-spin h-4 w-4 inline" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                    </svg>
                </span>
            </button>
        </form>
    </div>
</div>
{% endblock %}
```

### Step 10: Register View Routers

**File:** `src/routers/views/__init__.py`

```python
"""View routers for HTML pages."""
from fastapi import APIRouter

from src.routers.views.dashboard import router as dashboard_router
from src.routers.views.auth import router as auth_views_router
from src.routers.views.members import router as members_views_router

views_router = APIRouter()
views_router.include_router(dashboard_router)
views_router.include_router(auth_views_router)
views_router.include_router(members_views_router)
```

**File:** `src/main.py`

Add:
```python
from src.routers.views import views_router

app.include_router(views_router)
```

---

## Implementation Phases

### Phase 6.1: Core Setup (2-3 hours)
- Directory structure
- Base layout template
- Navigation components
- Tailwind configuration
- Static file serving

### Phase 6.2: Authentication Views (1-2 hours)
- Login page
- Logout flow
- Session management with templates

### Phase 6.3: Dashboard (2-3 hours)
- Dashboard with stats
- HTMX widgets for dynamic content
- Quick action buttons

### Phase 6.4: CRUD Pages (3-4 hours)
- Members list/detail/form
- Students list/detail/form
- Dues payments list/record

---

## Checklist

- [ ] Create directory structure
- [ ] Add Jinja2 dependencies
- [ ] Configure templates in FastAPI
- [ ] Create base layout
- [ ] Create navbar component
- [ ] Create sidebar component
- [ ] Setup Tailwind CSS
- [ ] Create dashboard page
- [ ] Create dashboard router
- [ ] Create login page
- [ ] Create auth view router
- [ ] Test full page load
- [ ] Test HTMX partial updates
- [ ] Create members list page
- [ ] Create members form page
- [ ] Update CLAUDE.md

---

## Expected Outcome

- Functional dashboard with stats
- Working navigation sidebar
- Login/logout flow
- At least one CRUD flow (Members)
- Responsive design (mobile-friendly)
- HTMX dynamic updates working

---

*End of Instructions*
