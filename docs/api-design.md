# Afya Mkononi — API Design

> **Status:** Draft v1.0 · **Last updated:** 2026-05-17 · **Companion to:** `solution-design-document.md`, `database-design.md`

Six endpoints in v1. JSON over HTTPS. No authentication. Rate limiting on the chat endpoint only.

---

## Conventions

- **Base URL (local):** `http://localhost:8000/api/`
- **Base URL (prod):** `https://<render-domain>/api/`
- **Content-Type:** `application/json` for all requests with a body
- **Auth:** None in v1
- **Versioning:** None in v1. v2 may introduce `/api/v2/` if breaking changes are needed
- **Date format:** ISO 8601 (`YYYY-MM-DD`)
- **Time format:** 24-hour (`HH:MM` or `HH:MM:SS`)
- **Timestamps:** ISO 8601 with timezone (`2026-05-18T08:30:00Z`)

### Standard error shape (DRF default)

For validation errors, DRF returns:
```json
{
  "field_name": ["This field is required."],
  "another_field": ["Enter a valid email address."]
}
```

For non-field errors:
```json
{ "detail": "Not found." }
```

The frontend code should handle both shapes.

### Rate limiting

`/api/chat/` is rate-limited via `django-ratelimit`:
- **30 requests per minute per IP**
- On limit hit: HTTP `429 Too Many Requests` with body `{"detail": "Too many requests. Please slow down."}`

Other endpoints are not rate-limited in v1.

---

## Endpoints

### 1. `POST /api/appointments/`

Create a new appointment request.

**Request body:**
```json
{
  "patient_name": "Daniel Otieno",
  "phone_number": "+254712345678",
  "email": "daniel@example.com",
  "preferred_date": "2026-06-01",
  "preferred_time": "10:30",
  "reason_for_visit": "Annual check-up"
}
```

**Required fields:** `patient_name`, `phone_number`, `preferred_date`, `preferred_time`, `reason_for_visit`
**Optional fields:** `email`

**Response — 201 Created:**
```json
{
  "id": 42,
  "patient_name": "Daniel Otieno",
  "phone_number": "+254712345678",
  "email": "daniel@example.com",
  "preferred_date": "2026-06-01",
  "preferred_time": "10:30:00",
  "reason_for_visit": "Annual check-up",
  "status": "PENDING",
  "created_at": "2026-05-18T08:30:00Z",
  "updated_at": "2026-05-18T08:30:00Z"
}
```

**Validation rules:**
- `phone_number`: 7-15 chars, digits + optional leading `+`
- `email`: standard email validation (if provided)
- `preferred_date`: must be `>= today`
- `reason_for_visit`: max 500 chars

**Error cases:**
- `400` with field-level errors if validation fails
- `429` if rate limit (none currently, but reserved)

---

### 2. `GET /api/appointments/`

List all appointments. Admin-style; not paginated in v1.

**Query parameters:** None in v1.

**Response — 200 OK:**
```json
[
  {
    "id": 42,
    "patient_name": "Daniel Otieno",
    "phone_number": "+254712345678",
    "email": "daniel@example.com",
    "preferred_date": "2026-06-01",
    "preferred_time": "10:30:00",
    "reason_for_visit": "Annual check-up",
    "status": "PENDING",
    "created_at": "2026-05-18T08:30:00Z",
    "updated_at": "2026-05-18T08:30:00Z"
  },
  { "...": "..." }
]
```

Ordered by `-created_at` (newest first).

**v2 plan:** add pagination, status filter, date range filter, and require auth.

---

### 3. `POST /api/reminders/`

Create a new reminder.

**Request body:**
```json
{
  "patient_name": "Joyce Mwangi",
  "reminder_type": "MEDICATION",
  "reminder_message": "Take blood pressure medication",
  "reminder_date": "2026-05-19",
  "reminder_time": "08:00"
}
```

**Required fields:** all of the above
**`reminder_type` enum:** `MEDICATION` · `APPOINTMENT` · `FOLLOWUP` · `OTHER`

**Response — 201 Created:**
```json
{
  "id": 17,
  "patient_name": "Joyce Mwangi",
  "reminder_type": "MEDICATION",
  "reminder_message": "Take blood pressure medication",
  "reminder_date": "2026-05-19",
  "reminder_time": "08:00:00",
  "status": "PENDING",
  "created_at": "2026-05-18T09:15:00Z"
}
```

**Validation rules:**
- `reminder_type`: must be one of the four enum values
- `reminder_date`: must be `>= today`
- `reminder_message`: max 500 chars

**v1 caveat:** the reminder is stored but not delivered. The frontend confirmation message must make this clear to the user.

---

### 4. `GET /api/reminders/`

List all reminders.

**Response — 200 OK:**
```json
[
  {
    "id": 17,
    "patient_name": "Joyce Mwangi",
    "reminder_type": "MEDICATION",
    "reminder_message": "Take blood pressure medication",
    "reminder_date": "2026-05-19",
    "reminder_time": "08:00:00",
    "status": "PENDING",
    "created_at": "2026-05-18T09:15:00Z"
  }
]
```

Ordered by `-created_at`.

---

### 5. `POST /api/chat/`

Send a chat message; receive an AI reply. **Rate-limited: 30/min/IP.**

**Request body — new session:**
```json
{
  "message": "I have a headache. What should I consider?",
  "session_id": null
}
```

**Request body — continuing session:**
```json
{
  "message": "Should I take painkillers?",
  "session_id": "8b3c5a1e-9d24-4b7f-bf41-2f0c8f9a3e21"
}
```

**Required:** `message`
**Optional:** `session_id` (UUID). If null/absent, a new session is created.

**Response — 200 OK:**
```json
{
  "session_id": "8b3c5a1e-9d24-4b7f-bf41-2f0c8f9a3e21",
  "reply": "Headaches have many common causes...",
  "safety_category": "NORMAL"
}
```

**Response — 200 OK (emergency case):**
```json
{
  "session_id": "8b3c5a1e-9d24-4b7f-bf41-2f0c8f9a3e21",
  "reply": "Please seek urgent medical care immediately. Based on what you described...",
  "safety_category": "EMERGENCY"
}
```

The `safety_category` lets the frontend apply different visual treatment (per `branding.md`: Accent Green left border on emergency bubbles).

**Error cases:**
- `400` — missing `message`
- `400` — `session_id` provided but doesn't exist or is malformed
- `429` — rate limit
- `503` — AI provider unavailable (graceful failure):
  ```json
  {
    "session_id": "<uuid>",
    "reply": "I'm having trouble responding right now. Please try again, or contact the clinic directly. If this is an emergency, seek urgent medical care immediately.",
    "safety_category": "ESCALATED"
  }
  ```
  Note: the 503 fallback message **always** includes the emergency-care line. Safety doesn't have a fallback mode.

**Server-side behavior:**
1. Validate input
2. If `session_id` is null, create a new `ChatSession`
3. Run pre-LLM safety check on the message → assign `safety_category`
4. Persist user `ChatMessage`
5. Call `AIService.generate_reply()`
6. Persist AI `ChatMessage` (also tagged with `safety_category`)
7. Update `ChatSession.last_active_at`
8. Return the response

All steps 4-7 happen in a database transaction so partial writes don't leave the conversation in a torn state.

---

### 6. `GET /api/chat/sessions/<uuid>/`

Get full message history for a session.

**Path parameter:** `uuid` — the session ID

**Response — 200 OK:**
```json
{
  "session_id": "8b3c5a1e-9d24-4b7f-bf41-2f0c8f9a3e21",
  "started_at": "2026-05-18T10:00:00Z",
  "last_active_at": "2026-05-18T10:05:32Z",
  "messages": [
    {
      "id": 1,
      "sender_type": "USER",
      "message_content": "I have a headache. What should I consider?",
      "safety_category": "NORMAL",
      "created_at": "2026-05-18T10:00:05Z"
    },
    {
      "id": 2,
      "sender_type": "AI",
      "message_content": "Headaches have many common causes...",
      "safety_category": "NORMAL",
      "created_at": "2026-05-18T10:00:09Z"
    }
  ]
}
```

Messages ordered by `created_at` ascending (conversation order, top-to-bottom).

**Error cases:**
- `404` — session not found
- `400` — malformed UUID

---

## URL routing summary

```python
# afya_mkononi/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),                  # /, /about/
    path('chat/', include('apps.chatbot.urls')),          # /chat/ (template page)
    path('book/', include('apps.appointments.urls')),     # /book/ (template page)
    path('remind/', include('apps.reminders.urls')),      # /remind/ (template page)
    path('api/', include('apps.<module>.api_urls')),      # JSON endpoints
]
```

Each app exposes both:
- `urls.py` — template-rendering routes (HTML pages)
- `api_urls.py` — DRF router routes (JSON)

This keeps page routes and API routes cleanly separated in code.

---

## Status code conventions

| Code | When |
|---|---|
| `200` | Successful `GET` |
| `201` | Successful `POST` (resource created) |
| `400` | Validation failure on request |
| `404` | Resource not found (e.g., bad session UUID) |
| `429` | Rate limit exceeded |
| `500` | Unhandled server error (shouldn't happen; if it does, fix it) |
| `503` | AI provider unavailable (graceful failure on `/api/chat/`) |

---

## Frontend client expectations

The chat page calls `/api/chat/` via `fetch`. It must:
1. Show a loading state while the request is pending
2. Handle `safety_category=EMERGENCY` by applying the emergency bubble style
3. Handle `503` by showing the fallback reply *and* the emergency-care line (the API includes both — the frontend just renders)
4. Handle `429` by showing "You're sending messages too quickly. Please wait a moment."
5. Handle network errors with a retryable error message
6. Persist `session_id` in `sessionStorage` so refreshing the page continues the conversation

The booking and reminder pages submit standard HTML forms via `POST`; the API endpoints exist primarily to:
- Provide a JSON contract that a future mobile/Next.js client could consume
- Make end-to-end testing easier (test the API, not the form)

---

## What's out of scope for v1

- Authentication & API keys
- Pagination
- Filtering & search via query parameters
- Bulk endpoints (e.g., `DELETE /api/appointments/?status=CANCELLED`)
- Webhooks (e.g., notify clinic when a new appointment is created)
- API versioning
- OpenAPI / Swagger docs (DRF browsable API serves this need for v1)
- WebSockets / Server-Sent Events (no streaming chat in v1; full reply returned at once)
- File uploads
- PATCH / PUT on appointments via API (status updates happen in Django admin)

All of these are valid v2 candidates.

---

## Decision log

| Date | Change | Why |
|---|---|---|
| 2026-05-17 | Initial draft | Foundation for Week 2 API implementation |
| 2026-05-17 | No pagination on list endpoints in v1 | Volume will be low; pagination adds complexity for no current value |
| 2026-05-17 | `safety_category` returned to client | Lets the frontend apply visual treatment without needing to re-parse the reply |
| 2026-05-17 | `/api/chat/` 503 fallback always includes emergency line | Safety doesn't have a degraded mode — even on provider failure, the user gets the escalation message |
