# Phase 6 Week 1: Document 4 - Pages & Static Files

**Execution Order:** 4 of 6
**Estimated Time:** 45-60 minutes
**Goal:** Create page templates and static CSS/JS files
**Prerequisites:** Document 3 complete (components exist)

---

## Overview

This document creates:
- **Auth pages:** login.html, forgot_password.html
- **Dashboard:** index.html
- **Error pages:** 404.html, 500.html
- **Static files:** custom.css, app.js

---

## Task 4.1: Create Login Page

HTMX-powered login form that authenticates against the existing JWT API.

**File:** `src/templates/auth/login.html`

```html
{% extends "base_auth.html" %}

{% block title %}Login{% endblock %}

{% block content %}
<div class="card bg-base-100 shadow-xl">
    <div class="card-body">
        <!-- Logo and title -->
        <div class="text-center mb-6">
            <div class="w-16 h-16 bg-primary rounded-xl mx-auto flex items-center justify-center mb-4">
                <span class="text-primary-content font-bold text-2xl">46</span>
            </div>
            <h1 class="text-2xl font-bold">IBEW Local 46</h1>
            <p class="text-base-content/60">IP2A Database</p>
        </div>
        
        <!-- Error message display -->
        <div id="login-error" class="hidden">
            <div class="alert alert-error mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span id="login-error-message">Invalid credentials</span>
            </div>
        </div>
        
        <!-- Login form -->
        <form id="login-form" 
              hx-post="/api/auth/login" 
              hx-target="#login-error"
              hx-swap="none"
              x-data="{ loading: false }"
              @htmx:before-request="loading = true"
              @htmx:after-request="loading = false">
            
            <!-- Email field -->
            <div class="form-control mb-4">
                <label class="label" for="email">
                    <span class="label-text">Email</span>
                </label>
                <input type="email" 
                       id="email" 
                       name="email" 
                       placeholder="you@local46.org" 
                       class="input input-bordered w-full"
                       required
                       autofocus>
            </div>
            
            <!-- Password field -->
            <div class="form-control mb-6">
                <label class="label" for="password">
                    <span class="label-text">Password</span>
                </label>
                <input type="password" 
                       id="password" 
                       name="password" 
                       placeholder="••••••••" 
                       class="input input-bordered w-full"
                       required>
                <label class="label">
                    <a href="/forgot-password" class="label-text-alt link link-hover">Forgot password?</a>
                </label>
            </div>
            
            <!-- Submit button -->
            <button type="submit" 
                    class="btn btn-primary w-full"
                    :class="{ 'loading': loading }"
                    :disabled="loading">
                <span x-show="!loading">Log In</span>
                <span x-show="loading">Logging in...</span>
            </button>
        </form>
        
        <!-- Footer -->
        <div class="divider mt-6">Need help?</div>
        <p class="text-center text-sm text-base-content/60">
            Contact your administrator or call the union hall.
        </p>
    </div>
</div>

<script>
// Handle login response
document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.pathInfo.requestPath === '/api/auth/login') {
        if (evt.detail.successful) {
            // Redirect to dashboard on success
            window.location.href = '/dashboard';
        } else {
            // Show error message
            const errorDiv = document.getElementById('login-error');
            const errorMsg = document.getElementById('login-error-message');
            errorDiv.classList.remove('hidden');
            
            try {
                const response = JSON.parse(evt.detail.xhr.responseText);
                errorMsg.textContent = response.detail || 'Invalid email or password';
            } catch {
                errorMsg.textContent = 'Invalid email or password';
            }
        }
    }
});
</script>
{% endblock %}
```

---

## Task 4.2: Create Forgot Password Page

Password reset request form.

**File:** `src/templates/auth/forgot_password.html`

```html
{% extends "base_auth.html" %}

{% block title %}Forgot Password{% endblock %}

{% block content %}
<div class="card bg-base-100 shadow-xl">
    <div class="card-body">
        <!-- Header -->
        <div class="text-center mb-6">
            <h1 class="text-2xl font-bold">Reset Password</h1>
            <p class="text-base-content/60 mt-2">Enter your email and we'll send you a reset link.</p>
        </div>
        
        <!-- Success message (hidden by default) -->
        <div id="success-message" class="hidden">
            <div class="alert alert-success mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>If an account exists with that email, you will receive a reset link shortly.</span>
            </div>
        </div>
        
        <!-- Form -->
        <form id="forgot-form" 
              hx-post="/api/auth/forgot-password" 
              hx-swap="none"
              x-data="{ loading: false, submitted: false }"
              @htmx:before-request="loading = true"
              @htmx:after-request="loading = false; submitted = true">
            
            <div class="form-control mb-6">
                <label class="label" for="email">
                    <span class="label-text">Email Address</span>
                </label>
                <input type="email" 
                       id="email" 
                       name="email" 
                       placeholder="you@local46.org" 
                       class="input input-bordered w-full"
                       required
                       autofocus
                       :disabled="submitted">
            </div>
            
            <button type="submit" 
                    class="btn btn-primary w-full"
                    :class="{ 'loading': loading }"
                    :disabled="loading || submitted"
                    x-show="!submitted">
                <span x-show="!loading">Send Reset Link</span>
                <span x-show="loading">Sending...</span>
            </button>
            
            <div x-show="submitted" class="text-center">
                <p class="text-success mb-4">Check your email for the reset link.</p>
            </div>
        </form>
        
        <!-- Back to login -->
        <div class="divider mt-6"></div>
        <a href="/login" class="btn btn-ghost w-full">
            ← Back to Login
        </a>
    </div>
</div>

<script>
document.body.addEventListener('htmx:afterRequest', function(evt) {
    if (evt.detail.pathInfo.requestPath === '/api/auth/forgot-password') {
        // Always show success (don't reveal if email exists)
        document.getElementById('success-message').classList.remove('hidden');
    }
});
</script>
{% endblock %}
```

---

## Task 4.3: Create Dashboard Page

Main dashboard with stats cards and quick actions.

**File:** `src/templates/dashboard/index.html`

```html
{% extends "base.html" %}

{% block title %}Dashboard{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Page header -->
    <div class="flex justify-between items-center">
        <div>
            <h1 class="text-2xl font-bold">Dashboard</h1>
            <p class="text-base-content/60">Welcome back, {{ current_user.first_name if current_user else 'User' }}</p>
        </div>
        <div class="text-sm text-base-content/60">
            {{ now.strftime('%A, %B %d, %Y') if now else '' }}
        </div>
    </div>
    
    <!-- Stats cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- Members card -->
        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-figure text-primary">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
            </div>
            <div class="stat-title">Total Members</div>
            <div class="stat-value text-primary">{{ stats.member_count if stats else '—' }}</div>
            <div class="stat-desc">Active members</div>
        </div>
        
        <!-- Students card -->
        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-figure text-secondary">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
            </div>
            <div class="stat-title">Students</div>
            <div class="stat-value text-secondary">{{ stats.student_count if stats else '—' }}</div>
            <div class="stat-desc">In pre-apprenticeship</div>
        </div>
        
        <!-- Grievances card -->
        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-figure text-warning">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
            </div>
            <div class="stat-title">Open Grievances</div>
            <div class="stat-value text-warning">{{ stats.open_grievances if stats else '—' }}</div>
            <div class="stat-desc">Requiring attention</div>
        </div>
        
        <!-- Dues card -->
        <div class="stat bg-base-100 rounded-box shadow">
            <div class="stat-figure text-success">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            </div>
            <div class="stat-title">Dues MTD</div>
            <div class="stat-value text-success">${{ '{:,.0f}'.format(stats.dues_mtd) if stats and stats.dues_mtd else '—' }}</div>
            <div class="stat-desc">Collected this month</div>
        </div>
    </div>
    
    <!-- Quick actions + Recent activity -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Quick actions -->
        <div class="card bg-base-100 shadow">
            <div class="card-body">
                <h2 class="card-title">Quick Actions</h2>
                <div class="grid grid-cols-2 gap-2 mt-2">
                    <a href="/members/new" class="btn btn-outline btn-sm">+ New Member</a>
                    <a href="/training/students/new" class="btn btn-outline btn-sm">+ New Student</a>
                    <a href="/training/attendance" class="btn btn-outline btn-sm">Attendance</a>
                    <a href="/reports" class="btn btn-outline btn-sm">Reports</a>
                </div>
            </div>
        </div>
        
        <!-- Recent activity -->
        <div class="card bg-base-100 shadow lg:col-span-2">
            <div class="card-body">
                <h2 class="card-title">Recent Activity</h2>
                <div class="overflow-x-auto">
                    <table class="table table-sm">
                        <tbody>
                            {% if activities %}
                            {% for activity in activities %}
                            <tr>
                                <td>
                                    <span class="badge badge-ghost badge-sm">{{ activity.action }}</span>
                                </td>
                                <td>{{ activity.description }}</td>
                                <td class="text-base-content/60 text-xs">{{ activity.timestamp }}</td>
                            </tr>
                            {% endfor %}
                            {% else %}
                            <tr>
                                <td class="text-base-content/60">No recent activity</td>
                            </tr>
                            {% endif %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## Task 4.4: Create Error Pages

### 404 Page

**File:** `src/templates/errors/404.html`

```html
{% extends "base_auth.html" %}

{% block title %}Page Not Found{% endblock %}

{% block content %}
<div class="card bg-base-100 shadow-xl text-center">
    <div class="card-body">
        <div class="text-8xl font-bold text-base-content/20 mb-4">404</div>
        <h1 class="text-2xl font-bold mb-2">Page Not Found</h1>
        <p class="text-base-content/60 mb-6">The page you're looking for doesn't exist or has been moved.</p>
        <a href="/dashboard" class="btn btn-primary">Back to Dashboard</a>
    </div>
</div>
{% endblock %}
```

### 500 Page

**File:** `src/templates/errors/500.html`

```html
{% extends "base_auth.html" %}

{% block title %}Server Error{% endblock %}

{% block content %}
<div class="card bg-base-100 shadow-xl text-center">
    <div class="card-body">
        <div class="text-8xl font-bold text-error/20 mb-4">500</div>
        <h1 class="text-2xl font-bold mb-2">Something Went Wrong</h1>
        <p class="text-base-content/60 mb-6">We're having trouble processing your request. Please try again later.</p>
        <a href="/dashboard" class="btn btn-primary">Back to Dashboard</a>
    </div>
</div>
{% endblock %}
```

---

## Task 4.5: Create Custom CSS

**File:** `src/static/css/custom.css`

```css
/* IP2A Custom Styles */

/* Loading indicator for HTMX requests */
.htmx-request .htmx-indicator {
    display: inline-block;
}

.htmx-indicator {
    display: none;
}

/* Smooth transitions for sidebar */
.drawer-side {
    transition: transform 0.3s ease-in-out;
}

/* Active menu item highlight */
.menu li > a.active {
    background-color: hsl(var(--p) / 0.1);
    color: hsl(var(--p));
}

/* Table row hover effect */
.table tbody tr:hover {
    background-color: hsl(var(--b2));
}

/* Card hover effect */
.card-hover:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px -5px rgb(0 0 0 / 0.1);
    transition: all 0.2s ease;
}

/* Form input focus states */
.input:focus {
    outline: none;
    border-color: hsl(var(--p));
    box-shadow: 0 0 0 2px hsl(var(--p) / 0.2);
}

/* Loading spinner */
@keyframes spin {
    to { transform: rotate(360deg); }
}

.loading-spinner {
    animation: spin 1s linear infinite;
}

/* Responsive adjustments */
@media (max-width: 1024px) {
    .stat-value {
        font-size: 1.5rem;
    }
}

/* Stats card enhancement */
.stat {
    padding: 1.5rem;
}

/* Better alert spacing */
.alert + .alert {
    margin-top: 0.5rem;
}
```

---

## Task 4.6: Create Custom JavaScript

**File:** `src/static/js/app.js`

```javascript
/* IP2A Custom JavaScript */

// HTMX configuration
document.body.addEventListener('htmx:configRequest', function(evt) {
    // Add CSRF token to all requests if available
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    if (csrfToken) {
        evt.detail.headers['X-CSRF-Token'] = csrfToken.content;
    }
});

// Global error handler for HTMX
document.body.addEventListener('htmx:responseError', function(evt) {
    console.error('HTMX Error:', evt.detail);
    
    // Show error toast
    showToast('An error occurred. Please try again.', 'error');
});

// Toast notification helper
function showToast(message, type = 'info') {
    const container = document.getElementById('flash-container');
    if (!container) return;
    
    const alertClass = {
        'success': 'alert-success',
        'error': 'alert-error',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';
    
    const alert = document.createElement('div');
    alert.className = `alert ${alertClass} shadow-lg`;
    alert.innerHTML = `
        <div>
            <span>${message}</span>
        </div>
        <button class="btn btn-sm btn-ghost" onclick="this.parentElement.remove()">✕</button>
    `;
    
    container.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentElement) {
            alert.remove();
        }
    }, 5000);
}

// Keyboard shortcuts
document.addEventListener('keydown', function(evt) {
    // Ctrl/Cmd + K for search (future feature)
    if ((evt.ctrlKey || evt.metaKey) && evt.key === 'k') {
        evt.preventDefault();
        console.log('Search shortcut triggered');
    }
});

// Confirm before leaving page with unsaved changes
let formDirty = false;

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('change', () => formDirty = true);
        form.addEventListener('submit', () => formDirty = false);
    });
});

window.addEventListener('beforeunload', function(evt) {
    if (formDirty) {
        evt.preventDefault();
        evt.returnValue = '';
    }
});

// Utility: Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Utility: Format date
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}
```

---

## Verification

```bash
# Check all files exist
ls -la src/templates/auth/
ls -la src/templates/dashboard/
ls -la src/templates/errors/
ls -la src/static/css/
ls -la src/static/js/
```

Expected files:
```
src/templates/auth/login.html
src/templates/auth/forgot_password.html
src/templates/dashboard/index.html
src/templates/errors/404.html
src/templates/errors/500.html
src/static/css/custom.css
src/static/js/app.js
```

---

## ✅ Document 4 Complete

**Checklist:**
- [ ] Login page created
- [ ] Forgot password page created
- [ ] Dashboard page created
- [ ] 404 error page created
- [ ] 500 error page created
- [ ] Custom CSS created
- [ ] Custom JavaScript created

**Next:** Run Document 5 - Router & Integration

---

*Document 4 of 6 | Phase 6 Week 1*
