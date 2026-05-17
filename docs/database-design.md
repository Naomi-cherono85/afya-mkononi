# Afya Mkononi — Database Design

> **Status:** Draft v1.0 · **Last updated:** 2026-05-17 · **Companion to:** `solution-design-document.md`

PostgreSQL schema for the v1 MVP. Five user-defined entities plus Django's built-in `User`. No foreign-key chain to a `Patient` entity in v1 — appointments, reminders, and chat sessions are anonymous, identified by name + phone.

---

## Entity-Relationship Diagram

```
┌──────────────────┐      ┌──────────────────┐
│  User            │      │  Appointment     │
│ (Django built-in)│      │                  │
├──────────────────┤      ├──────────────────┤
│ id PK            │      │ id PK            │
│ username         │      │ patient_name     │
│ email            │      │ phone_number     │
│ password (hash)  │      │ email (nullable) │
│ is_superuser     │      │ preferred_date   │
│ ...              │      │ preferred_time   │
└──────────────────┘      │ reason_for_visit │
        │                 │ status           │
        │ (FK, nullable)  │ created_at       │
        │                 │ updated_at       │
        ▼                 └──────────────────┘
┌──────────────────┐
│  ChatSession     │      ┌──────────────────┐
├──────────────────┤      │  Reminder        │
│ session_id PK    │      ├──────────────────┤
│ user_id FK       │      │ id PK            │
│   (nullable)     │      │ patient_name     │
│ started_at       │      │ reminder_type    │
│ last_active_at   │      │ reminder_message │
└──────────────────┘      │ reminder_date    │
        │                 │ reminder_time    │
        │ 1              │ status           │
        │                 │ created_at       │
        │ N              └──────────────────┘
        ▼
┌──────────────────┐
│  ChatMessage     │
├──────────────────┤
│ id PK            │
│ session_id FK    │
│ sender_type      │
│ message_content  │
│ safety_category  │
│ created_at       │
└──────────────────┘
```

**Relationships:**
- `ChatSession.user_id` → `User.id` (nullable; v1 sessions are anonymous)
- `ChatMessage.session_id` → `ChatSession.session_id` (1-to-many; CASCADE on delete)
- `Appointment` and `Reminder` have **no** FK to `User` in v1

---

## Table specifications

### `appointments_appointment`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `BigAutoField` | PK | Django default |
| `patient_name` | `varchar(200)` | NOT NULL | |
| `phone_number` | `varchar(20)` | NOT NULL | Validated at serializer level (digits + optional `+`, 7-15 chars) |
| `email` | `varchar(254)` | NULL allowed | Django `EmailField` |
| `preferred_date` | `date` | NOT NULL | Must be `>= today` (validator) |
| `preferred_time` | `time` | NOT NULL | |
| `reason_for_visit` | `text` | NOT NULL | Max 500 chars (serializer validator) |
| `status` | `varchar(20)` | NOT NULL, default `PENDING` | Choices: `PENDING`, `CONFIRMED`, `CANCELLED`, `COMPLETED` |
| `created_at` | `timestamp` | NOT NULL, auto_now_add | |
| `updated_at` | `timestamp` | NOT NULL, auto_now | |

**Indexes:**
- Default PK index on `id`
- Composite index on `(status, preferred_date)` — covers the most common admin query: "show me PENDING appointments by date"

**Ordering:** `Meta.ordering = ['-created_at']` (newest first)

**Admin config:**
- `list_display = ['patient_name', 'phone_number', 'preferred_date', 'preferred_time', 'status', 'created_at']`
- `list_filter = ['status', 'preferred_date']`
- `search_fields = ['patient_name', 'phone_number']`
- `readonly_fields = ['created_at', 'updated_at']`

### `reminders_reminder`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `BigAutoField` | PK | |
| `patient_name` | `varchar(200)` | NOT NULL | |
| `reminder_type` | `varchar(20)` | NOT NULL | Choices: `MEDICATION`, `APPOINTMENT`, `FOLLOWUP`, `OTHER` |
| `reminder_message` | `text` | NOT NULL | Max 500 chars |
| `reminder_date` | `date` | NOT NULL | Must be `>= today` |
| `reminder_time` | `time` | NOT NULL | |
| `status` | `varchar(20)` | NOT NULL, default `PENDING` | Choices: `PENDING`, `SENT`, `CANCELLED` |
| `created_at` | `timestamp` | NOT NULL, auto_now_add | |

**Note on `status=SENT`:** in v1, no delivery happens — this status exists for v2 to use without a schema migration.

**Indexes:**
- Default PK
- Composite on `(status, reminder_date)`

**Ordering:** `['-created_at']`

**Admin config:**
- `list_display = ['patient_name', 'reminder_type', 'reminder_date', 'reminder_time', 'status']`
- `list_filter = ['reminder_type', 'status']`
- `search_fields = ['patient_name', 'reminder_message']`

### `chatbot_chatsession`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `session_id` | `UUID` | PK | Generated server-side at session creation |
| `user_id` | `integer` | FK to `auth_user`, NULL allowed | v1: always NULL; v2: set when auth lands |
| `started_at` | `timestamp` | NOT NULL, auto_now_add | |
| `last_active_at` | `timestamp` | NOT NULL, auto_now | Updated on every new message in the session |

**Why UUID as PK:** session_ids are exposed to clients in the chat URL pattern `/api/chat/sessions/<uuid>/`. UUIDs don't leak count information (unlike sequential integers) and can be generated client-side if needed.

**Indexes:**
- Default PK on `session_id`
- Index on `last_active_at` (for "show me recent sessions" admin queries)

**Ordering:** `['-last_active_at']`

**Admin config:**
- `list_display = ['session_id', 'started_at', 'last_active_at']`
- `readonly_fields = ['session_id', 'started_at', 'last_active_at']`
- `inlines = [ChatMessageInline]` (see below)

### `chatbot_chatmessage`

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | `BigAutoField` | PK | |
| `session_id` | `UUID` | FK to `chatbot_chatsession.session_id`, NOT NULL, ON DELETE CASCADE | |
| `sender_type` | `varchar(10)` | NOT NULL | Choices: `USER`, `AI`, `SYSTEM` |
| `message_content` | `text` | NOT NULL | No fixed max; clinical messages can be long |
| `safety_category` | `varchar(20)` | NOT NULL, default `NORMAL` | Choices: `NORMAL`, `EMERGENCY`, `REFUSED`, `ESCALATED` |
| `created_at` | `timestamp` | NOT NULL, auto_now_add | |

**Indexes:**
- Default PK
- Composite index on `(session_id, created_at)` — covers ordered retrieval of messages within a session
- Index on `safety_category` — admin queries for emergency sessions

**Ordering:** `['created_at']` (oldest first, so message lists render top-to-bottom in conversation order)

**Admin config (inline on ChatSession):**
- `class ChatMessageInline(admin.TabularInline)`
- `readonly_fields = ['sender_type', 'message_content', 'safety_category', 'created_at']`
- `extra = 0` (don't show empty input rows)

---

## Choice enums (single source of truth in `models.py`)

```python
class Appointment.Status(models.TextChoices):
    PENDING   = 'PENDING',   'Pending'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    CANCELLED = 'CANCELLED', 'Cancelled'
    COMPLETED = 'COMPLETED', 'Completed'

class Reminder.Type(models.TextChoices):
    MEDICATION  = 'MEDICATION',  'Medication'
    APPOINTMENT = 'APPOINTMENT', 'Appointment'
    FOLLOWUP    = 'FOLLOWUP',    'Follow-up'
    OTHER       = 'OTHER',       'Other'

class Reminder.Status(models.TextChoices):
    PENDING   = 'PENDING',   'Pending'
    SENT      = 'SENT',      'Sent'
    CANCELLED = 'CANCELLED', 'Cancelled'

class ChatMessage.SenderType(models.TextChoices):
    USER   = 'USER',   'User'
    AI     = 'AI',     'AI'
    SYSTEM = 'SYSTEM', 'System'

class ChatMessage.SafetyCategory(models.TextChoices):
    NORMAL    = 'NORMAL',    'Normal'
    EMERGENCY = 'EMERGENCY', 'Emergency'
    REFUSED   = 'REFUSED',   'Refused'  # AI refused to answer (e.g., diagnosis request)
    ESCALATED = 'ESCALATED', 'Escalated'  # Post-LLM detected escalation language
```

Storing the string value (not an integer) keeps the database human-readable in psql and admin.

---

## Migration plan (Week 2)

Five migrations, in dependency order:

1. **0001_initial (`accounts`)** — Empty for v1; reserves the app for v2 auth changes
2. **0001_initial (`core`)** — Empty; reserves the app
3. **0001_initial (`appointments`)** — Creates `Appointment` table
4. **0001_initial (`reminders`)** — Creates `Reminder` table
5. **0001_initial (`chatbot`)** — Creates `ChatSession` and `ChatMessage` tables

Plus Django's built-in migrations for `auth`, `admin`, `contenttypes`, `sessions`.

**Rule for the build:** never edit a committed migration. New column → new migration.

---

## What's deliberately not modeled in v1

- **`Patient` entity** — would require auth to be useful. v2.
- **`Clinic` / multi-tenancy** — single-tenant in v1.
- **`MessageDelivery` / outbox** — no delivery in v1.
- **Audit log table** — Django admin tracks `LogEntry` automatically; that's enough for v1.
- **Soft-delete / `is_active`** — admins can update `status` to `CANCELLED`; full soft-delete isn't worth the complexity yet.
- **Encrypted fields for PII** — phone numbers are PII but encrypting them at rest requires `django-cryptography` or similar. Out of scope for the MVP; documented as a v2 gap in the README.

---

## Data privacy note

The README must clearly state:

> Afya Mkononi v1 is a portfolio MVP. It is not deployed to handle real patient data under any regulatory regime (HIPAA, GDPR healthcare clauses, Kenya Data Protection Act, etc.). The demo data is for demonstration only. Do not enter real personal health information.

This isn't a database design rule, but it constrains everything else: it's why field-level encryption isn't in v1, why we don't ship a BAA, why we're on Render free tier, and why the user authentication story is a v2 problem.

---

## Decision log

| Date | Change | Why |
|---|---|---|
| 2026-05-17 | Initial draft | Foundation for Week 2 model implementation |
| 2026-05-17 | UUID PK on `ChatSession` (instead of int) | Session IDs are exposed in URLs; UUIDs avoid leaking session counts and allow client-side generation if needed |
| 2026-05-17 | No `Patient` table in v1 | Would require auth; v1 is anonymous by design |
| 2026-05-17 | `status=SENT` choice on `Reminder` despite no delivery | Lets v2 add delivery without a schema migration |
