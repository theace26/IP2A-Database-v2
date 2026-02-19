# Frontend Development Workflow

> **TL;DR:** Browser refresh (Cmd+R) is enough for templates, Python code, and Tailwind classes. Hard refresh (Cmd+Shift+R) is needed for changes to `custom.css`, `mobile.css`, or `app.js`.

---

## How It Works Now

### Tailwind CSS: CDN Play Script (NO build step)

Tailwind and DaisyUI are loaded entirely from CDN — there is no build pipeline, no `package.json`, no `node_modules`. The Tailwind Play CDN script scans HTML on load and generates CSS on the fly.

**Source:** `src/templates/base.html`, lines 20–21
```html
<link href="https://cdn.jsdelivr.net/npm/daisyui@4.6.0/dist/full.min.css" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
```

**Implication:** Adding or changing Tailwind utility classes in any `.html` template takes effect on the next browser refresh. No compilation or watch process needed.

### Uvicorn: Hot-reload enabled

The API container runs with `--reload` so it watches Python source files and restarts automatically.

**Source:** `docker-compose.yml`, line 61
```yaml
command: ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Source files: Volume-mounted into the container

Your local project directory is bind-mounted into the container, so edits on the host are immediately visible inside the container.

**Source:** `docker-compose.yml`, lines 50–51
```yaml
volumes:
  - .:/app:cached
```

### Templates: Jinja2 auto-reload

Jinja2 recompiles templates on each request in development. Combined with the volume mount, editing an `.html` file and refreshing the browser gives you the updated output immediately — no container restart needed.

**Source:** `src/main.py`, line 154 (StaticFiles) + throughout for `Jinja2Templates`.

### Static files: Served by FastAPI StaticFiles

**Source:** `src/main.py`, line 154
```python
app.mount("/static", StaticFiles(directory="src/static"), name="static")
```

| File | Path |
|------|------|
| Custom styles | `src/static/css/custom.css` |
| Mobile styles | `src/static/css/mobile.css` |
| App JavaScript | `src/static/js/app.js` |

No cache-control headers are set. The browser uses its default caching behavior, which means a **hard refresh** (Cmd+Shift+R) is required to force it to re-fetch these files after changes.

---

## How To See Changes

| What You Changed | What To Do | Why |
|---|---|---|
| Jinja2 template (`.html`) | Normal refresh — Cmd+R | Volume mount + Jinja2 auto-reload = instant |
| Tailwind utility classes in templates | Normal refresh — Cmd+R | CDN Play script regenerates CSS on page load |
| `custom.css` or `mobile.css` | Hard refresh — Cmd+Shift+R | Browser caches static files; force-reload bypasses cache |
| `app.js` | Hard refresh — Cmd+Shift+R | Same — browser caches static JS |
| Python route / service code | Normal refresh — Cmd+R | Uvicorn `--reload` restarts automatically; wait ~1–2 seconds |
| Model or schema changes | Restart container + run migration | Schema changes require Alembic migration + seed |
| Static images or other assets | Hard refresh — Cmd+Shift+R | Browser caches static files |

> **Hard refresh on Mac:** `Cmd+Shift+R` in Chrome/Firefox/Safari
> **Hard refresh on Windows/Linux:** `Ctrl+Shift+F5` or `Ctrl+F5`

---

## Recommendations (Optional Improvements)

The current setup works well. These are quality-of-life improvements only — none are required.

### 1. Switch from CDN to Tailwind CLI (if bundle size matters for production)

The CDN Play script is ideal for development and for an internal business app with a small user base. If you ever need smaller payloads or offline-first production builds:

```bash
npm install -D tailwindcss
npx tailwindcss init
# Add content paths to tailwind.config.js
npx tailwindcss -i ./src/static/css/input.css -o ./src/static/css/output.css --watch
```

**Not recommended now** — the CDN approach is simpler and maintenance-free. The trade-off (slightly slower initial load) is irrelevant for an internal app.

### 2. Add `cache_busting` to static file URLs (optional dev-only QoL)

To avoid needing hard refreshes after every CSS/JS change, you can append a version query string to static file links:

```html
<!-- In base.html, replace: -->
<link rel="stylesheet" href="/static/css/custom.css">

<!-- With: -->
<link rel="stylesheet" href="/static/css/custom.css?v={{ config.APP_VERSION }}">
```

Or add a timestamp-based cache buster Jinja2 global in `main.py`. This makes normal refreshes sufficient even for static file changes.

### 3. Sticky header offset if banner height changes

If the impersonation banner height is ever changed, update `src/static/css/custom.css` lines 85–93:

```css
.table.table-pin-rows thead tr {
    top: 64px;  /* navbar height — update if navbar height changes */
}

body.impersonation-active .table.table-pin-rows thead tr {
    top: 128px;  /* navbar + banner — update if banner height changes */
}
```

---

## Quick Reference: Start Environment

```bash
cd ~/Projects/IP2A-Database-v2
docker-compose up -d          # Start all services
docker-compose logs -f api    # Tail API logs (see reload events)
```

App runs at: `http://localhost:8000`
