# Phase 6 Week 9: Document Management UI — Master Instructions

**Version:** 0.7.7 → 0.7.8
**Estimated Time:** 4-6 hours (2 sessions)
**Prerequisites:** Phase 6 Week 8 complete, ~304 tests passing

---

## Overview

Week 9 implements the Document Management frontend:
- Upload interface with drag-drop
- File browser by entity type
- Download via presigned URLs
- Delete with confirmation

This provides UI for the Phase 3 S3/MinIO backend.

---

## Session Breakdown

| Session | Focus | Duration | New Tests |
|---------|-------|----------|-----------|
| A | Upload Interface | 2-3 hrs | 8 |
| B | Browse + Download | 2-3 hrs | 7 |

**Total:** ~15 new tests, bringing frontend tests to ~154

---

## Architecture

### Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/documents` | GET | Documents landing |
| `/documents/upload` | GET | Upload page |
| `/documents/upload` | POST | Handle upload (HTMX) |
| `/documents/browse` | GET | File browser |
| `/documents/browse/{entity_type}/{entity_id}` | GET | Entity documents |
| `/documents/{document_id}/download` | GET | Presigned download |
| `/documents/{document_id}/delete` | POST | Delete document |

### File Structure

```
src/
├── routers/
│   └── documents_frontend.py     # NEW
├── templates/
│   └── documents/
│       ├── index.html            # Landing
│       ├── upload.html           # Upload form
│       ├── browse.html           # File browser
│       └── partials/
│           ├── _file_list.html   # HTMX file list
│           └── _upload_zone.html # Drag-drop zone
└── tests/
    └── test_documents_frontend.py # ~15 tests
```

---

## Session Documents

1. `1-SESSION-A-UPLOAD-INTERFACE.md` — Upload UI with drag-drop
2. `2-SESSION-B-BROWSE-DOWNLOAD.md` — File browser and download

---

## Success Criteria

After Week 9:
- [ ] Documents landing with quick actions
- [ ] Upload page with drag-drop zone
- [ ] File browser by entity type
- [ ] Presigned URL downloads
- [ ] Delete with confirmation
- [ ] ~319 total tests (~154 frontend)
- [ ] ADR-013: Document UI Patterns
- [ ] v0.7.8 tagged

---

## Key Implementation Notes

### Drag-Drop Upload (Alpine.js)
```javascript
<div x-data="{
    isDragging: false,
    files: [],
    handleDrop(e) {
        this.files = [...e.dataTransfer.files];
        this.isDragging = false;
    }
}" ...>
```

### Presigned Download
Frontend calls `/documents/{id}/download` which redirects to S3 presigned URL.

### Entity Types
Documents can be attached to:
- Members
- Students
- Grievances
- Benevolence applications
- SALTing activities

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

*Execute sessions in order.*
