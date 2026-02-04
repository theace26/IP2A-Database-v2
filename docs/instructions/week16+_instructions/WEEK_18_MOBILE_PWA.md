# Week 18: Mobile Optimization & Progressive Web App (PWA)

**Version:** 1.0.0  
**Created:** February 2, 2026  
**Branch:** `develop`  
**Estimated Effort:** 6-8 hours (2-3 sessions)  
**Dependencies:** Week 16 (Production Hardening) complete

---

## Overview

This week focuses on **mobile optimization** and implementing **Progressive Web App (PWA)** features so union members can access the system effectively from their phones on job sites. Members often need to check dues status, view training schedules, or report issues while in the field.

### Objectives

- [ ] Responsive design audit and fixes
- [ ] Touch-friendly UI improvements
- [ ] PWA manifest and service worker
- [ ] Offline capability for key pages
- [ ] Mobile-specific navigation
- [ ] Performance optimization for slow connections

### Out of Scope

- Native iOS/Android apps
- Push notifications (future enhancement)
- Background sync (future enhancement)

---

## Pre-Flight Checklist

- [ ] On `develop` branch
- [ ] Production system stable
- [ ] All tests passing
- [ ] Mobile device available for testing (or browser dev tools)
- [ ] Lighthouse audit baseline captured

---

## Phase 1: Responsive Design Audit (Session 1)

### 1.1 Run Lighthouse Audit

```bash
# Using Chrome DevTools
# 1. Open site in Chrome
# 2. DevTools → Lighthouse tab
# 3. Select "Mobile" and all categories
# 4. Generate report
# 5. Save baseline scores
```

Document baseline in `docs/reports/lighthouse-baseline.md`.

### 1.2 Responsive Breakpoint Review

DaisyUI uses Tailwind breakpoints. Ensure all pages work at:

| Breakpoint | Width | Target Devices |
|------------|-------|----------------|
| `sm` | 640px | Large phones |
| `md` | 768px | Tablets |
| `lg` | 1024px | Laptops |
| `xl` | 1280px | Desktops |

### 1.3 Mobile Navigation

Update `src/templates/components/_navbar.html`:

```html
<!-- Mobile hamburger menu -->
<div class="navbar bg-base-100 lg:hidden">
    <div class="flex-none">
        <label for="mobile-drawer" class="btn btn-square btn-ghost drawer-button">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" 
                 class="inline-block w-6 h-6 stroke-current">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M4 6h16M4 12h16M4 18h16"></path>
            </svg>
        </label>
    </div>
    <div class="flex-1">
        <a class="btn btn-ghost text-xl" href="/dashboard">UnionCore</a>
    </div>
</div>
```

Create `src/templates/components/_mobile_drawer.html`:

```html
<!-- Mobile side drawer -->
<div class="drawer lg:drawer-open">
    <input id="mobile-drawer" type="checkbox" class="drawer-toggle" />
    <div class="drawer-content">
        <!-- Page content here -->
        {% block mobile_content %}{% endblock %}
    </div>
    <div class="drawer-side">
        <label for="mobile-drawer" class="drawer-overlay"></label>
        <ul class="menu p-4 w-64 min-h-full bg-base-200 text-base-content">
            <!-- Sidebar content -->
            <li><a href="/dashboard">Dashboard</a></li>
            <li><a href="/members">Members</a></li>
            <li><a href="/dues">Dues</a></li>
            <li><a href="/training">Training</a></li>
            <li><a href="/operations">Operations</a></li>
            <li><a href="/reports">Reports</a></li>
            {% if user.role == 'admin' %}
            <li><a href="/admin/audit-logs">Audit Logs</a></li>
            {% endif %}
            <li class="mt-auto"><a href="/logout">Logout</a></li>
        </ul>
    </div>
</div>
```

### 1.4 Touch-Friendly Buttons

Ensure all interactive elements meet minimum touch target size (48x48px):

```css
/* src/static/css/mobile.css */

/* Minimum touch target size */
@media (max-width: 768px) {
    .btn {
        min-height: 48px;
        min-width: 48px;
    }
    
    .btn-sm {
        min-height: 44px;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* Larger form inputs on mobile */
    input, select, textarea {
        font-size: 16px !important; /* Prevents iOS zoom */
        min-height: 48px;
    }
    
    /* Table touch improvements */
    .table td, .table th {
        padding: 0.75rem;
    }
    
    /* Card spacing */
    .card {
        margin-bottom: 1rem;
    }
}
```

---

## Phase 2: PWA Implementation (Session 2)

### 2.1 Web App Manifest

Create `src/static/manifest.json`:

```json
{
    "name": "UnionCore - IBEW Local 46",
    "short_name": "UnionCore",
    "description": "Union operations management for IBEW Local 46",
    "start_url": "/dashboard",
    "display": "standalone",
    "background_color": "#1d232a",
    "theme_color": "#570df8",
    "orientation": "portrait-primary",
    "icons": [
        {
            "src": "/static/icons/icon-72.png",
            "sizes": "72x72",
            "type": "image/png"
        },
        {
            "src": "/static/icons/icon-96.png",
            "sizes": "96x96",
            "type": "image/png"
        },
        {
            "src": "/static/icons/icon-128.png",
            "sizes": "128x128",
            "type": "image/png"
        },
        {
            "src": "/static/icons/icon-144.png",
            "sizes": "144x144",
            "type": "image/png"
        },
        {
            "src": "/static/icons/icon-152.png",
            "sizes": "152x152",
            "type": "image/png"
        },
        {
            "src": "/static/icons/icon-192.png",
            "sizes": "192x192",
            "type": "image/png",
            "purpose": "any maskable"
        },
        {
            "src": "/static/icons/icon-384.png",
            "sizes": "384x384",
            "type": "image/png"
        },
        {
            "src": "/static/icons/icon-512.png",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "any maskable"
        }
    ]
}
```

### 2.2 Service Worker

Create `src/static/sw.js`:

```javascript
const CACHE_NAME = 'unioncore-v1';
const OFFLINE_URL = '/offline';

// Assets to cache immediately
const PRECACHE_ASSETS = [
    '/',
    '/offline',
    '/static/css/custom.css',
    '/static/css/mobile.css',
    '/static/js/main.js',
    '/static/manifest.json',
    'https://cdn.jsdelivr.net/npm/daisyui@4.5.0/dist/full.min.css',
    'https://cdn.tailwindcss.com',
    'https://unpkg.com/htmx.org@1.9.10',
    'https://unpkg.com/alpinejs@3.13.3/dist/cdn.min.js'
];

// Install event - cache core assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(PRECACHE_ASSETS);
        })
    );
    self.skipWaiting();
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch event - network first, fallback to cache
self.addEventListener('fetch', (event) => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') return;
    
    // Skip API calls (always need fresh data)
    if (event.request.url.includes('/api/')) return;
    
    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // Clone and cache successful responses
                if (response.ok) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseClone);
                    });
                }
                return response;
            })
            .catch(() => {
                // Network failed, try cache
                return caches.match(event.request).then((cachedResponse) => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    // If no cache and it's a navigation, show offline page
                    if (event.request.mode === 'navigate') {
                        return caches.match(OFFLINE_URL);
                    }
                });
            })
    );
});
```

### 2.3 Offline Page

Create `src/templates/offline.html`:

```html
{% extends "base.html" %}
{% block title %}Offline - UnionCore{% endblock %}

{% block content %}
<div class="min-h-screen flex items-center justify-center bg-base-200">
    <div class="text-center p-8">
        <div class="text-6xl mb-4">📡</div>
        <h1 class="text-2xl font-bold mb-2">You're Offline</h1>
        <p class="text-gray-600 mb-6">
            Check your internet connection and try again.
        </p>
        <button onclick="location.reload()" class="btn btn-primary">
            Try Again
        </button>
    </div>
</div>
{% endblock %}
```

### 2.4 Register Service Worker

Update `src/templates/base.html`:

```html
<head>
    <!-- ... existing head content ... -->
    <link rel="manifest" href="/static/manifest.json">
    <meta name="theme-color" content="#570df8">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <link rel="apple-touch-icon" href="/static/icons/icon-192.png">
</head>

<body>
    <!-- ... existing body content ... -->
    
    <script>
        // Register service worker
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/static/sw.js')
                    .then((registration) => {
                        console.log('SW registered:', registration.scope);
                    })
                    .catch((error) => {
                        console.log('SW registration failed:', error);
                    });
            });
        }
    </script>
</body>
```

---

## Phase 3: Mobile-Specific Features (Session 3)

### 3.1 Swipe Actions for Tables

Add swipe-to-action for mobile tables using Alpine.js:

```html
<!-- src/templates/components/_mobile_table_row.html -->
<div x-data="{ swiped: false, startX: 0 }"
     @touchstart="startX = $event.touches[0].clientX"
     @touchmove="if ($event.touches[0].clientX - startX < -50) swiped = true"
     @touchend="if (swiped) setTimeout(() => swiped = false, 3000)"
     class="relative overflow-hidden">
    
    <div class="flex items-center p-4 bg-base-100 transition-transform"
         :class="{ '-translate-x-20': swiped }">
        {% block row_content %}{% endblock %}
    </div>
    
    <!-- Swipe actions -->
    <div class="absolute right-0 top-0 h-full flex items-center bg-primary text-white px-4"
         x-show="swiped">
        {% block swipe_actions %}
        <button class="btn btn-ghost btn-sm">View</button>
        {% endblock %}
    </div>
</div>
```

### 3.2 Bottom Navigation Bar

Create `src/templates/components/_bottom_nav.html`:

```html
<!-- Mobile bottom navigation - shown only on small screens -->
<nav class="btm-nav lg:hidden">
    <button class="{{ 'active' if request.path == '/dashboard' }}" 
            onclick="location.href='/dashboard'">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
        <span class="btm-nav-label">Home</span>
    </button>
    <button class="{{ 'active' if '/members' in request.path }}"
            onclick="location.href='/members'">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
        <span class="btm-nav-label">Members</span>
    </button>
    <button class="{{ 'active' if '/dues' in request.path }}"
            onclick="location.href='/dues'">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="btm-nav-label">Dues</span>
    </button>
    <button class="{{ 'active' if '/profile' in request.path }}"
            onclick="location.href='/profile'">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
        <span class="btm-nav-label">Profile</span>
    </button>
</nav>
```

### 3.3 Quick Actions FAB

Create `src/templates/components/_fab.html`:

```html
<!-- Floating Action Button for quick actions on mobile -->
<div class="fixed bottom-20 right-4 lg:hidden z-50" 
     x-data="{ open: false }">
    
    <!-- FAB Menu -->
    <div x-show="open" 
         x-transition:enter="transition ease-out duration-200"
         x-transition:enter-start="opacity-0 scale-75"
         x-transition:enter-end="opacity-100 scale-100"
         class="flex flex-col gap-2 mb-2">
        <a href="/dues/pay" class="btn btn-circle btn-secondary shadow-lg">💳</a>
        <a href="/members/search" class="btn btn-circle btn-secondary shadow-lg">🔍</a>
        <a href="/operations/grievance/new" class="btn btn-circle btn-secondary shadow-lg">📝</a>
    </div>
    
    <!-- Main FAB -->
    <button @click="open = !open" 
            class="btn btn-circle btn-primary btn-lg shadow-lg">
        <span x-text="open ? '✕' : '+'"></span>
    </button>
</div>
```

---

## Phase 4: Performance Optimization (Session 3)

### 4.1 Image Optimization

Add responsive images helper:

```python
# src/utils/images.py
def responsive_image_srcset(base_url: str, sizes: list[int] = [320, 640, 1024]) -> str:
    """Generate srcset for responsive images."""
    srcset_parts = []
    for size in sizes:
        srcset_parts.append(f"{base_url}?w={size} {size}w")
    return ", ".join(srcset_parts)
```

### 4.2 Lazy Loading

Enable native lazy loading for images:

```html
<img src="{{ image_url }}" 
     loading="lazy" 
     decoding="async"
     alt="{{ image_alt }}">
```

### 4.3 Reduce Initial Bundle

Split non-critical CSS:

```html
<!-- Critical CSS inline -->
<style>
    /* Minimal layout styles for above-the-fold content */
    body { margin: 0; font-family: system-ui, sans-serif; }
    .loading { display: flex; justify-content: center; align-items: center; height: 100vh; }
</style>

<!-- Non-critical CSS loaded async -->
<link rel="preload" href="/static/css/custom.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="/static/css/custom.css"></noscript>
```

---

## Testing Requirements

### Manual Testing Checklist

Test on actual devices or browser emulation:

- [ ] iPhone SE (smallest common phone)
- [ ] iPhone 14 Pro (modern iPhone)
- [ ] Samsung Galaxy S21 (Android)
- [ ] iPad (tablet)

### Automated Tests

Create `src/tests/test_mobile.py`:

```python
"""Mobile responsiveness tests."""
import pytest
from fastapi.testclient import TestClient

class TestMobileEndpoints:
    """Test mobile-specific endpoints."""
    
    def test_offline_page_renders(self, client: TestClient):
        response = client.get("/offline")
        assert response.status_code == 200
        assert "You're Offline" in response.text
    
    def test_manifest_served(self, client: TestClient):
        response = client.get("/static/manifest.json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
    
    def test_service_worker_served(self, client: TestClient):
        response = client.get("/static/sw.js")
        assert response.status_code == 200
        assert "serviceWorker" in response.text or "CACHE_NAME" in response.text
```

### Lighthouse Targets

| Metric | Target |
|--------|--------|
| Performance | > 80 |
| Accessibility | > 90 |
| Best Practices | > 90 |
| SEO | > 80 |
| PWA | Installable |

---

## Acceptance Criteria

### Required

- [ ] All pages responsive at 320px width
- [ ] Touch targets minimum 48x48px
- [ ] Mobile navigation working (hamburger + bottom nav)
- [ ] PWA installable on iOS and Android
- [ ] Offline page displays when disconnected
- [ ] Service worker caches static assets
- [ ] Lighthouse mobile score > 80

### Optional

- [ ] Swipe actions on table rows
- [ ] FAB for quick actions
- [ ] Pull-to-refresh on list pages

---

## App Store Considerations (Future)

While not building native apps now, PWA enables:

1. **iOS**: "Add to Home Screen" from Safari
2. **Android**: Chrome prompts for installation
3. **Windows**: Edge can install as app

For future native app consideration, document in ADR.

---

## 📝 MANDATORY: End-of-Session Documentation

> **REQUIRED:** Update *ANY* and *ALL* relevant documents to capture progress made this session. Scan `/docs/*` and make or create any relevant updates/documents to keep a historical record as the project progresses. **Do not forget about ADRs—update as necessary.**

### Quick Checklist

- [ ] `/CHANGELOG.md` — Version bump (v0.9.2-alpha)
- [ ] `/CLAUDE.md` — Note PWA implementation
- [ ] `/docs/IP2A_MILESTONE_CHECKLIST.md` — Mark Week 18 complete
- [ ] `/docs/reports/lighthouse-*.md` — Create Lighthouse report
- [ ] `/docs/reports/session-logs/YYYY-MM-DD-mobile-pwa.md` — **Create session log**
- [ ] Consider ADR if significant mobile architecture decisions made

---

*Last Updated: February 2, 2026*
