# Phase 6 Week 1: Document 2 - Base Templates

**Execution Order:** 2 of 6
**Estimated Time:** 20-30 minutes
**Goal:** Create the two master layout templates
**Prerequisites:** Document 1 complete (directories exist)

---

## Overview

We're creating two base templates:
1. **base.html** - Full layout with sidebar (authenticated pages)
2. **base_auth.html** - Centered layout (login/error pages)

Both use CDN links for DaisyUI, Tailwind, HTMX, and Alpine.js. No build step needed.

---

## Task 2.1: Create base.html

This is the master layout for authenticated pages with sidebar navigation.

**File:** `src/templates/base.html`

```html
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}IP2A{% endblock %} | IBEW Local 46</title>
    
    <!-- Favicon -->
    <link rel="icon" type="image/x-icon" href="{{ url_for('static', path='images/favicon.ico') }}">
    
    <!-- DaisyUI + Tailwind CSS (CDN - no build required) -->
    <link href="https://cdn.jsdelivr.net/npm/daisyui@4.6.0/dist/full.min.css" rel="stylesheet" type="text/css">
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- HTMX for dynamic updates -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    
    <!-- Alpine.js for small interactions -->
    <script defer src="https://unpkg.com/alpinejs@3.13.5/dist/cdn.min.js"></script>
    
    <!-- Custom styles -->
    <link rel="stylesheet" href="{{ url_for('static', path='css/custom.css') }}">
    
    {% block head %}{% endblock %}
</head>
<body class="min-h-screen bg-base-200" hx-boost="true">
    
    {% block body %}
    <!-- Drawer layout: sidebar + main content -->
    <div class="drawer lg:drawer-open">
        <input id="sidebar-toggle" type="checkbox" class="drawer-toggle">
        
        <!-- Main content area -->
        <div class="drawer-content flex flex-col">
            <!-- Top navbar -->
            {% include 'components/_navbar.html' %}
            
            <!-- Page content -->
            <main class="flex-1 p-6">
                <!-- Flash messages -->
                {% include 'components/_flash.html' %}
                
                <!-- Page-specific content -->
                {% block content %}{% endblock %}
            </main>
            
            <!-- Footer -->
            <footer class="footer footer-center p-4 bg-base-300 text-base-content">
                <div>
                    <p>© 2026 IBEW Local 46 - IP2A Database</p>
                </div>
            </footer>
        </div>
        
        <!-- Sidebar -->
        {% include 'components/_sidebar.html' %}
    </div>
    
    <!-- Modal container for HTMX -->
    <div id="modal-container"></div>
    {% endblock %}
    
    <!-- Custom scripts -->
    <script src="{{ url_for('static', path='js/app.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

---

## Task 2.2: Create base_auth.html

Simplified centered layout for login, password reset, and error pages.

**File:** `src/templates/base_auth.html`

```html
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Login{% endblock %} | IP2A - IBEW Local 46</title>
    
    <!-- Favicon -->
    <link rel="icon" type="image/x-icon" href="{{ url_for('static', path='images/favicon.ico') }}">
    
    <!-- DaisyUI + Tailwind CSS -->
    <link href="https://cdn.jsdelivr.net/npm/daisyui@4.6.0/dist/full.min.css" rel="stylesheet" type="text/css">
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- HTMX -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    
    <!-- Alpine.js -->
    <script defer src="https://unpkg.com/alpinejs@3.13.5/dist/cdn.min.js"></script>
    
    <!-- Custom styles -->
    <link rel="stylesheet" href="{{ url_for('static', path='css/custom.css') }}">
    
    {% block head %}{% endblock %}
</head>
<body class="min-h-screen bg-base-200 flex items-center justify-center">
    
    <div class="w-full max-w-md px-4">
        {% block content %}{% endblock %}
    </div>
    
    {% block scripts %}{% endblock %}
</body>
</html>
```

---

## Verification

The templates reference components that don't exist yet (navbar, sidebar, flash). That's OK - we'll create those in Document 3. For now, just verify the files exist:

```bash
ls -la src/templates/base*.html
```

Expected:
```
src/templates/base.html
src/templates/base_auth.html
```

---

## ✅ Document 2 Complete

**Checklist:**
- [ ] `src/templates/base.html` created
- [ ] `src/templates/base_auth.html` created

**Note:** Don't commit yet - wait until components are created so the app doesn't error on include statements.

**Next:** Run Document 3 - Component Templates

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

*Document 2 of 6 | Phase 6 Week 1*
