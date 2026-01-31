# Phase 6 Week 1: Document 3 - Component Templates

**Execution Order:** 3 of 6
**Estimated Time:** 30-40 minutes
**Goal:** Create reusable UI components
**Prerequisites:** Document 2 complete (base templates exist)

---

## Overview

Components are partial templates included in other templates. By convention, they're prefixed with underscore (`_`) to indicate they're not standalone pages.

We're creating:
1. **_navbar.html** - Top navigation bar
2. **_sidebar.html** - Left sidebar menu
3. **_flash.html** - Flash message display
4. **_modal.html** - Modal container for HTMX

---

## Task 3.1: Create Navbar Component

Top navigation bar with mobile menu toggle, notifications, and user menu.

**File:** `src/templates/components/_navbar.html`

```html
<!-- Top navigation bar -->
<div class="navbar bg-base-100 shadow-lg sticky top-0 z-50">
    <!-- Mobile menu button -->
    <div class="flex-none lg:hidden">
        <label for="sidebar-toggle" class="btn btn-square btn-ghost">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="inline-block w-6 h-6 stroke-current">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
            </svg>
        </label>
    </div>
    
    <!-- Logo/Title -->
    <div class="flex-1">
        <a href="/dashboard" class="btn btn-ghost text-xl">
            <span class="text-primary font-bold">IP2A</span>
            <span class="hidden sm:inline text-base-content">Database</span>
        </a>
    </div>
    
    <!-- Right side: notifications + user menu -->
    <div class="flex-none gap-2">
        <!-- Notifications dropdown -->
        <div class="dropdown dropdown-end">
            <div tabindex="0" role="button" class="btn btn-ghost btn-circle">
                <div class="indicator">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                    </svg>
                    <span class="badge badge-xs badge-primary indicator-item"></span>
                </div>
            </div>
            <ul tabindex="0" class="mt-3 z-[1] p-2 shadow menu menu-sm dropdown-content bg-base-100 rounded-box w-52">
                <li><a>No new notifications</a></li>
            </ul>
        </div>
        
        <!-- User menu dropdown -->
        <div class="dropdown dropdown-end" x-data="{ open: false }">
            <div tabindex="0" role="button" class="btn btn-ghost btn-circle avatar placeholder">
                <div class="bg-primary text-primary-content rounded-full w-10">
                    <span class="text-sm">{{ current_user.first_name[0] if current_user else 'U' }}{{ current_user.last_name[0] if current_user else '' }}</span>
                </div>
            </div>
            <ul tabindex="0" class="mt-3 z-[1] p-2 shadow menu menu-sm dropdown-content bg-base-100 rounded-box w-52">
                <li class="menu-title">
                    <span>{{ current_user.first_name if current_user else 'User' }} {{ current_user.last_name if current_user else '' }}</span>
                </li>
                <li><a href="/profile">Profile</a></li>
                <li><a href="/settings">Settings</a></li>
                <li class="divider"></li>
                <li>
                    <a href="/logout" class="text-error">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                        </svg>
                        Logout
                    </a>
                </li>
            </ul>
        </div>
    </div>
</div>
```

---

## Task 3.2: Create Sidebar Component

Left sidebar with navigation menu organized by section.

**File:** `src/templates/components/_sidebar.html`

```html
<!-- Sidebar -->
<div class="drawer-side z-40">
    <label for="sidebar-toggle" aria-label="close sidebar" class="drawer-overlay"></label>
    
    <aside class="bg-base-100 w-64 min-h-full border-r border-base-300">
        <!-- Sidebar header -->
        <div class="p-4 border-b border-base-300">
            <div class="flex items-center gap-2">
                <div class="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                    <span class="text-primary-content font-bold text-lg">46</span>
                </div>
                <div>
                    <div class="font-bold text-sm">IBEW Local 46</div>
                    <div class="text-xs text-base-content/60">IP2A Database</div>
                </div>
            </div>
        </div>
        
        <!-- Navigation menu -->
        <ul class="menu p-4 gap-1">
            <!-- Dashboard -->
            <li>
                <a href="/dashboard" class="{% if request.url.path == '/dashboard' %}active{% endif %}">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                    </svg>
                    Dashboard
                </a>
            </li>
            
            <li class="menu-title mt-4">
                <span>Union Operations</span>
            </li>
            
            <!-- Members -->
            <li>
                <a href="/members" class="{% if '/members' in request.url.path %}active{% endif %}">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                    Members
                </a>
            </li>
            
            <!-- Dues -->
            <li>
                <a href="/dues" class="{% if '/dues' in request.url.path %}active{% endif %}">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Dues
                </a>
            </li>
            
            <!-- Grievances -->
            <li>
                <a href="/grievances" class="{% if '/grievances' in request.url.path %}active{% endif %}">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Grievances
                </a>
            </li>
            
            <li class="menu-title mt-4">
                <span>Training</span>
            </li>
            
            <!-- Pre-Apprenticeship -->
            <li>
                <details {% if '/training' in request.url.path %}open{% endif %}>
                    <summary>
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                        Pre-Apprenticeship
                    </summary>
                    <ul>
                        <li><a href="/training" class="{% if request.url.path == '/training' %}active{% endif %}">Overview</a></li>
                        <li><a href="/training/students" class="{% if '/training/students' in request.url.path %}active{% endif %}">Students</a></li>
                        <li><a href="/training/courses" class="{% if '/training/courses' in request.url.path %}active{% endif %}">Courses</a></li>
                        <li><a href="/training/attendance" class="{% if '/training/attendance' in request.url.path %}active{% endif %}">Attendance</a></li>
                        <li><a href="/training/grades" class="{% if '/training/grades' in request.url.path %}active{% endif %}">Grades</a></li>
                        <li><a href="/training/certifications" class="{% if '/training/certifications' in request.url.path %}active{% endif %}">Certifications</a></li>
                    </ul>
                </details>
            </li>
            
            <li class="menu-title mt-4">
                <span>Administration</span>
            </li>
            
            <!-- Staff -->
            <li>
                <a href="/staff" class="{% if '/staff' in request.url.path %}active{% endif %}">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                    Staff & Permissions
                </a>
            </li>
            
            <!-- Organizations -->
            <li>
                <a href="/organizations" class="{% if '/organizations' in request.url.path %}active{% endif %}">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                    Organizations
                </a>
            </li>
            
            <!-- Reports -->
            <li>
                <a href="/reports" class="{% if '/reports' in request.url.path %}active{% endif %}">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Reports
                </a>
            </li>
        </ul>
    </aside>
</div>
```

---

## Task 3.3: Create Flash Messages Component

Flash/alert message display with auto-dismiss.

**File:** `src/templates/components/_flash.html`

```html
<!-- Flash messages container -->
{% if messages %}
<div class="space-y-2 mb-4" x-data="{ show: true }" x-show="show" x-init="setTimeout(() => show = false, 5000)">
    {% for category, message in messages %}
    <div class="alert alert-{{ 'success' if category == 'success' else 'error' if category == 'error' else 'warning' if category == 'warning' else 'info' }} shadow-lg">
        <div>
            {% if category == 'success' %}
            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {% elif category == 'error' %}
            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {% else %}
            <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {% endif %}
            <span>{{ message }}</span>
        </div>
        <button class="btn btn-sm btn-ghost" @click="show = false">✕</button>
    </div>
    {% endfor %}
</div>
{% endif %}

<!-- HTMX swap target for dynamic alerts -->
<div id="flash-container" class="space-y-2 mb-4"></div>
```

---

## Task 3.4: Create Modal Component

HTMX-compatible modal container for dynamic content.

**File:** `src/templates/components/_modal.html`

```html
<!-- Modal backdrop and container -->
<div id="modal-backdrop" 
     class="fixed inset-0 bg-black bg-opacity-50 z-50 hidden"
     onclick="closeModal()"
     x-data
     @keydown.escape.window="closeModal()">
</div>

<div id="modal-content" 
     class="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 hidden">
    <!-- Modal content loaded here via HTMX -->
</div>

<script>
function openModal() {
    document.getElementById('modal-backdrop').classList.remove('hidden');
    document.getElementById('modal-content').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('modal-backdrop').classList.add('hidden');
    document.getElementById('modal-content').classList.add('hidden');
    document.getElementById('modal-content').innerHTML = '';
}

// HTMX event listener for modals
document.body.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.target.id === 'modal-content') {
        openModal();
    }
});
</script>
```

---

## Verification

```bash
ls -la src/templates/components/
```

Expected:
```
_flash.html
_modal.html
_navbar.html
_sidebar.html
```

---

## ✅ Document 3 Complete

**Checklist:**
- [ ] `src/templates/components/_navbar.html` created
- [ ] `src/templates/components/_sidebar.html` created
- [ ] `src/templates/components/_flash.html` created
- [ ] `src/templates/components/_modal.html` created

**Next:** Run Document 4 - Page Templates & Static Files

---

## 📝 End-of-Session Documentation (REQUIRED)

> ⚠️ **DO NOT skip this step.** Update *ANY* and *ALL* relevant documents to capture progress made this session.

### Before Ending This Session:

1. **Scan `/docs/*`** - Review all documentation files
2. **Update existing docs** - Reflect changes, progress, and decisions
3. **Create new docs** - If needed for new components or concepts
4. **ADR Review** - Update or create Architecture Decision Records as necessary
5. **Session log entry** - Record what was accomplished

This ensures historical record-keeping and project continuity ("bus factor" protection).

---

*Document 3 of 6 | Phase 6 Week 1*
