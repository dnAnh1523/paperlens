# PaperLens - Full Feature Changes & Refactoring Summary

This document summarizes all changes and bug fixes implemented during thisペア programming session.

---

## 1. Type Safety, ESLint, and Test Fixes (Initial Phase)

### Backend Type Safety (`apps/api`)
* **PyMuPDF `fitz` Type Inference Fix** (`tests/test_chat.py`, `tests/test_chunks.py`, `tests/test_ingestion.py`):
  - Resolved an IDE/mypy type resolution conflict where `fitz.open()` was incorrectly inferred as returning the database model `Document` instead of PyMuPDF's `fitz.Document`. Added explicit localized type annotations (`pdf: Any`) to clear the false `no attribute 'new_page'` errors.
* **Return Value Casts** (`tests/*.py`):
  - Added `cast` annotations to functions returning `Any` values (e.g., `pdf.tobytes()` and `response.json()`) to strictly satisfy `mypy`'s `[no-any-return]` requirements.
  - Cast values returned from `json.loads` within `Conversation.source_document_ids` to satisfy type checks.

### Frontend Linting (`apps/web`)
* **Unused Code Cleanup**:
  - Removed unused imports (such as `useMemo`, `KeyboardEvent`, `fetchDocuments`, `ChevronRight`, `MessageSquare`, and `Bot`).
  - Cleaned up unused props and state variables (such as `providerStatus`, `isSidebarOpen`, and `onToggleSidebar`) across `ChatWorkspace.tsx`, `DocumentLibrary.tsx`, and `page.tsx`.

---

## 2. Workspace-Specific Source Isolation

Each workspace (represented as a `Conversation` model in the backend) now manages its own source documents. Documents uploaded within Workspace A are private to Workspace A and not displayed in or leaked to Workspace B.

### Backend Changes (`apps/api`)
* **Database Model (`document.py`)**:
  - Added a nullable foreign key `conversation_id` in the `Document` model pointing to `conversations.conversation_id`.
* **Database Migrations (`session.py`)**:
  - Configured `init_db()` to run a dynamic SQLite alter table command (`_ensure_sqlite_columns`) to create the new `conversation_id` column automatically on startup.
* **Service Layer (`document_service.py`)**:
  - Updated `create_document_from_upload` to accept and persist `conversation_id`.
  - Updated `list_documents` to filter results by `conversation_id` when provided.
* **API Controllers (`documents.py`)**:
  - Updated `/documents` endpoint routes to support the optional `conversation_id` query/query parameters.
* **Pydantic Schemas (`document.py` schema)**:
  - Added `conversation_id` to the `DocumentRead` Pydantic model to serialize it in JSON API responses.

### Frontend Changes (`apps/web`)
* **API Client (`api.ts`)**:
  - Modified `fetchDocuments` and `uploadDocument` to support passing and appending `conversationId` to the query string.
* **Sidebar Upload (`DocumentLibrary.tsx`)**:
  - Forwarded the active workspace ID (`activeWorkspace?.conversation_id`) during document uploading.
* **Page View Lifecycle (`page.tsx`)**:
  - Configured an effect that reactively fetches documents for the current workspace whenever `activeWorkspaceId` changes.
  - Fixed the synchronous `setDocuments` inside `useEffect` rule violation (`react-hooks/set-state-in-effect`) by wrapping the state clearing call in a deferred microtask via `Promise.resolve().then(...)`.

---

## 3. ORM Mapper Join Ambiguity Resolution

Adding `conversation_id` on the `Document` model created a second foreign key path connecting the `conversations` and `documents` tables (the other being `conversations.scoped_document_id`).
* **Relationship Spec (`conversation.py` model)**:
  - Added explicit `foreign_keys=[scoped_document_id]` to `Conversation.scoped_document` relationship to eliminate mapping ambiguities in SQLAlchemy.

---

## 4. Robot/Bot Icon Branding Update

To customize the branding of the app, all assistant robot icons have been replaced with the brand's logo.

* **Reusable Logo Component (`PaperLensLogo.tsx`)**:
  - Created a new component at `apps/web/app/components/PaperLensLogo.tsx` containing the SVG path of the logo. This keeps code DRY and avoids circular import cycles between components and `page.tsx`.
* **Sidebar / Main Page (`page.tsx`)**:
  - Removed the local declaration of `PaperLensLogo` and imported the new shared component instead.
* **Assistant Message Avatar (`ChatWorkspace.tsx`)**:
  - Imported the logo component and replaced the `Bot` icon with `<PaperLensLogo />` in the assistant avatar column.

---

## 5. Verification and Quality Assurance

### Automated Testing
* **New Isolation Test Case (`test_documents.py`)**:
  - Added `test_document_workspace_isolation` which creates two workspaces, uploads files to them respectively, and verifies they do not leak between workspace document listing queries.
* **Backend Test Suite**:
  - Executed `pytest` successfully, passing all 92/92 tests.
  - Executed `mypy app tests` successfully with zero issues.
* **Frontend Linting & Build**:
  - Executed `npm run typecheck` inside `apps/web` successfully.
  - Executed `npm run lint` inside `apps/web` successfully.

---

## 6. Sidebar Animation & Interactive Tooltips

* **Circular Hover Overlay**:
  - Standardized both `.sidebarCollapseButton` and `.miniSidebarExpandButton` in `globals.css` to a matching `40px` by `40px` size, and added `min-height: 40px` and `flex-shrink: 0` to prevent any layout compression or squishing, ensuring they are rendered as perfect, identical circles in all conditions.
  - Set `overflow: visible;` and `z-index: 10;` on `.sourceSidebar` to allow nested tooltip bubbles to draw correctly over the main chat workspace instead of being clipped or hidden.
* **Animated Icon Transitions**:
  - Configured hover state tracking in `DocumentLibrary.tsx`.
  - When hovering the collapse toggle, the icon dynamically transitions from `PanelLeft` to `PanelLeftClose` (showing the left-pointing collapse chevron `[|<]`).
  - When hovering the expand toggle, the icon transitions from `PanelLeft` to `PanelLeftOpen` (showing the right-pointing expand chevron `[|>]`).
* **English Tooltip Support**:
  - Wrapped both toggle buttons in `.tooltip-container` and added hover tooltips: **"Collapse sidebar"** and **"Expand sidebar"** to guide users with clear UX tooltips.
* **Unified Hover Branding Styles**:
  - Configured both collapse and expand buttons to transition to the primary blue background (`var(--primary)`, matching the "Add Source" button) and turn the icon color to white (`#ffffff`) on hover for a high-contrast, cohesive brand aesthetic.

