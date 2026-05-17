# Afya Mkononi — Solution Design Document (SDD)

> **Status:** Draft v1.0 · **Owner:** Naomi Cherono · **Last updated:** 2026-05-17 · **Companion to:** `product-requirements-document.md`

This document explains *how* Afya Mkononi will be built. The PRD answers "what and why"; this answers "how."

---

## 1. System Overview

Afya Mkononi is a server-rendered Django web application backed by PostgreSQL, with a clean service-layer abstraction around the AI provider. The architecture is intentionally boring: it's a 4-week MVP, and boring architectures ship.

There are no microservices. There is no separate frontend application. There is no event bus, no queue, no cache layer. There is one Django project, one database, one deployment target. All complexity that exists exists because the product requires it — not because the architecture pattern suggests it.

The application has three surfaces:

1. **Public web pages** — server-rendered with Django templates + Tailwind CSS. Three forms (chat, booking, reminder) and informational pages (home, about).
2. **JSON API** — Django REST Framework endpoints under `/api/` that the chat page calls via fetch and that future mobile apps could reuse.
3. **Admin** — Django admin under `/admin/` for clinic-side data review.

---

## 2. Architecture Diagram

```
┌─────────────────┐
│  User Browser   │  Desktop or mobile, no app install
└────────┬────────┘
         │  HTTPS
         ▼
┌─────────────────────────────────────────────┐
│              Django Web App                  │
│  ┌─────────────────┐  ┌──────────────────┐  │
│  │   Templates     │  │   DRF Views      │  │
│  │  (home, chat,   │  │  /api/chat/      │  │
│  │   book, remind) │  │  /api/appts/     │  │
│  │                 │  │  /api/reminders/ │  │
│  └────────┬────────┘  └────────┬─────────┘  │
│           │                    │            │
│           ▼                    ▼            │
│  ┌─────────────────────────────────────┐    │
│  │       Service Layer                 │    │
│  │  apps/chatbot/services/             │    │
│  │     ai_service.py                   │    │
│  │  ┌─────────────────────────────┐    │    │
│  │  │ Safety detection            │    │    │
│  │  │ System prompt construction  │    │    │
│  │  │ Provider call (isolated)    │    │    │
│  │  └─────────────────────────────┘    │    │
│  └──────┬──────────────────────┬───────┘    │
│         │                      │            │
│         ▼                      ▼            │
│  ┌─────────────┐       ┌──────────────┐    │
│  │  Django     │       │   HTTP       │    │
│  │  ORM        │       │   Client     │    │
│  └──────┬──────┘       └──────┬───────┘    │
└─────────│─────────────────────│─────────────┘
          │                     │
          ▼                     ▼
   ┌────────────┐        ┌──────────────┐
   │ PostgreSQL │        │  AI Provider │
   │ (Render)   │        │  (Claude)    │
   └────────────┘        └──────────────┘
```

**Key principle:** every arrow that crosses the Django process boundary (to Postgres, to the AI provider) goes through a defined service. No template or view code dials a provider directly.

---

## 3. Technology Stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | Django ecosystem; AI SDKs are first-class |
| Web framework | Django 5.x | Batteries-included; admin is free; mature ORM |
| API framework | Django REST Framework 3.14+ | De facto standard for Django JSON APIs |
| Database | PostgreSQL 15+ | Structured/relational fits healthcare data; reliable; Render provides managed instance |
| Templates | Django templates | Server-rendered HTML — no separate frontend build needed for v1 |
| CSS | Tailwind CSS (CDN for MVP) | Fast utility-first styling; CDN avoids build tooling overhead |
| AI provider | Anthropic Claude (via SDK) | Better safety behavior for healthcare framing; clean Python SDK |
| Secrets | `python-decouple` + `.env` | Simple, well-documented |
| Production server | Gunicorn | Standard WSGI server |
| Static files | Whitenoise | Lets Django serve its own static files without a CDN for MVP |
| Rate limiting | django-ratelimit | Lightweight, decorator-based |
| Deployment | Render | Free Postgres + Django works; no DevOps overhead |
| Version control | Git + GitHub | Public repo; portfolio asset |

**Deferred (v2):** queue (Celery + Redis), separate frontend (React/Next.js if needed), CDN, error monitoring (Sentry), full CI/CD pipeline.

---

## 4. Application Modules

Django apps, organized under `backend/apps/`. Split by **responsibility**, not by layer.

| Module | Responsibility |
|---|---|
| `core` | Home page, about page, base templates, shared utilities, brand assets, navigation |
| `accounts` | Reserved for v2 auth. In v1, contains nothing meaningful — the app exists so v2 doesn't require a structural refactor. |
| `chatbot` | Chat UI, chat API, `ChatSession` and `ChatMessage` models, `services/ai_service.py`, safety logic, system prompt |
| `appointments` | Booking UI, appointments API, `Appointment` model, admin registration |
| `reminders` | Reminder UI, reminders API, `Reminder` model, admin registration |

Each app owns its own:
- `models.py`
- `views.py`
- `urls.py`
- `serializers.py` (where APIs exist)
- `admin.py`
- `templates/<app>/`
- `tests.py`
- `services/` (where service-layer code exists — currently `chatbot` only)

---

## 5. Database Design

Full schema in `database-design.md`. Summary:

| Entity | Purpose | Key fields |
|---|---|---|
| `User` | Django built-in; superuser only in v1 | Standard Django |
| `Appointment` | Patient booking request | name, phone, email, preferred_date, preferred_time, reason, status |
| `Reminder` | Patient reminder | name, type, message, date, time, status |
| `ChatSession` | Conversation grouping | session_id (UUID), user (nullable), started_at, last_active_at |
| `ChatMessage` | Single message in a session | session FK, sender_type, content, safety_category, created_at |

**Why no shared `Patient` entity:** v1 is anonymous. Tying appointments / reminders / chat sessions to a single patient identity is a v2 problem — solving it now requires auth, which isn't in v1.

**Indexes:**
- `Appointment(status, preferred_date)` — the most common admin query
- `Reminder(status, reminder_date)` — same logic
- `ChatMessage(session_id, created_at)` — for ordered message retrieval

---

## 6. API Design

Full endpoint specification in `api-design.md`. Summary:

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/appointments/` | Create appointment request |
| `GET` | `/api/appointments/` | List appointments (admin-style; not paginated in v1) |
| `POST` | `/api/reminders/` | Create reminder |
| `GET` | `/api/reminders/` | List reminders |
| `POST` | `/api/chat/` | Send a chat message; receive AI reply |
| `GET` | `/api/chat/sessions/<uuid>/` | Get session history |

**Auth:** None in v1. The API is internal-use only; rate limiting compensates for the lack of auth on `/api/chat/`.

**Response format:** JSON. Standard DRF `Serializer` output. Errors follow DRF's default `{ "field": ["error message"] }` shape.

---

## 7. AI Integration Design

### 7.1 The service layer

All AI provider interactions are encapsulated in `backend/apps/chatbot/services/ai_service.py`. This is **non-negotiable** — see `MEMORY.md` and the safety boundaries spec.

```python
# Shape (not final implementation)
class AIService:
    SYSTEM_PROMPT: str = "..."  # see Section 7.3
    EMERGENCY_KEYWORDS: list[str] = [...]  # see Section 7.2

    def generate_reply(self, session: ChatSession, user_message: str) -> tuple[str, str]:
        """Returns (reply_text, safety_category)."""
        ...

    def _detect_safety_category(self, user_message: str) -> str:
        """Pre-LLM keyword check. Returns NORMAL / EMERGENCY."""
        ...

    def _call_provider(self, messages: list[dict]) -> str:
        """The only place the Anthropic/OpenAI SDK is imported."""
        ...
```

**No other module imports the AI SDK.** Views call `AIService().generate_reply(...)` and persist what comes back.

### 7.2 Safety-first flow

```
user_message
     │
     ▼
┌─────────────────────────────┐
│ Pre-LLM safety check         │
│ (EMERGENCY_KEYWORDS scan)    │
└──────────┬───────────────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
EMERGENCY?      NORMAL?
    │             │
    ▼             ▼
Build escalation Build standard
prompt with     prompt with
explicit        system instructions
urgent-care
language
    │             │
    └──────┬──────┘
           ▼
┌─────────────────────────────┐
│ Call provider (Claude)       │
└──────────┬───────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ Post-LLM safety check        │
│ (verify reply contains       │
│  required escalation if      │
│  category was EMERGENCY)     │
└──────────┬───────────────────┘
           │
           ▼
Persist user message + AI reply with
safety_category. Return reply to caller.
```

Two safety checks (pre and post) is intentional defense-in-depth. The LLM should comply with the system prompt; the pre-check guarantees the prompt itself contains the right urgency; the post-check verifies the reply.

### 7.3 The system prompt

Stored as a code constant (`AIService.SYSTEM_PROMPT`). Versioned with the repo. Never an env var or DB row.

The prompt opens with:

> *You are Afya Mkononi, a healthcare support assistant. Your role is to provide general health guidance, support appointment booking, and help users understand when they should seek professional medical care.*
>
> *You must not diagnose diseases, prescribe medication, or replace a licensed healthcare professional.*
>
> *If a user mentions emergency symptoms such as severe chest pain, difficulty breathing, severe bleeding, loss of consciousness, stroke-like symptoms, severe allergic reaction, or danger in pregnancy, advise them to seek urgent medical care immediately.*
>
> *Keep responses simple, calm, respectful, and easy to understand.*

The full text lives in code, not in this document — the code is the source of truth.

### 7.4 Provider abstraction

The `_call_provider` method takes a list of `{role, content}` messages and returns a string. Swapping Claude for OpenAI is a one-method change. The system prompt and safety logic stay identical.

### 7.5 Cost controls

- Use the cheapest tier model during development (Claude Haiku)
- Set a hard daily spend cap in the provider console
- Log every call's token usage (not message content) for cost visibility
- `/api/chat/` rate-limited to 30 requests/min/IP

---

## 8. Security Considerations

| Concern | Mitigation |
|---|---|
| Secret leakage | All secrets in `.env` locally and env vars in production. `.env` gitignored. `.env.example` documents required keys without values. |
| CSRF | Django CSRF middleware enabled. All forms include CSRF tokens. |
| XSS | All user-submitted chat messages are escaped on render (Django default). No `\|safe` filter on user content. |
| SQL injection | Django ORM only — no raw SQL in v1. |
| Prompt injection / unsafe AI output | Pre-LLM safety check; system prompt re-stated on every request; post-LLM check for emergency-category responses. |
| API abuse | Rate limiting on `/api/chat/` (30 req/min/IP). |
| `DEBUG` leaks in prod | `DEBUG = False` enforced via env var in production. |
| Logging PII | Chat message content never logged at INFO level. Only metadata (session_id, safety_category, token counts). |
| HTTPS | Render provides TLS by default; redirect HTTP → HTTPS. |
| Outdated dependencies | Pin all versions in `requirements.txt`. Re-check before final deploy. |

---

## 9. Deployment Design

### 9.1 Target
Render (web service + managed PostgreSQL). Both on the free tier.

### 9.2 Architecture
```
Internet
   │
   ▼
Render Load Balancer (TLS terminator)
   │
   ▼
Render Web Service (gunicorn + Django + whitenoise)
   │
   ├─→ Render PostgreSQL (managed instance)
   │
   └─→ Anthropic API (Claude)
```

### 9.3 Environment variables (production)
- `SECRET_KEY` — Django secret
- `DEBUG=False`
- `DATABASE_URL` — provided by Render Postgres add-on
- `ALLOWED_HOSTS` — Render service domain
- `AI_API_KEY` — Anthropic key
- `AI_PROVIDER=claude`

### 9.4 Build & start
```
Build:  pip install -r requirements.txt
        python manage.py collectstatic --noinput

Start:  gunicorn afya_mkononi.wsgi:application
```

### 9.5 Database migrations
First deploy: `python manage.py migrate` via Render shell. Subsequent deploys: same command, idempotent.

### 9.6 No CI/CD in v1
Manual deploys. Render auto-deploys on push to `main` — that's the CI. No separate test pipeline in v1; tests run locally before push.

---

## 10. Testing Approach

| Test type | Scope | Tool |
|---|---|---|
| Model tests | Each model's `__str__`, defaults, constraints | Django `TestCase` |
| API tests | Each endpoint: happy path + 1-2 failure cases | DRF `APITestCase` |
| Service tests | `AIService` with mocked provider; emergency keyword detection; safety_category labeling | Django `TestCase` + `unittest.mock` |
| Manual checklist | Every flow from the PRD; mobile responsiveness; safety scenarios | Human, against the testing checklist in `implementation-plan.md` |

**Coverage target:** > 60% on models and views/services. Not a hard gate — a sanity check.

**No e2e (Selenium/Playwright) tests in v1.** The manual checklist covers full flows; e2e overhead isn't worth it for a four-week MVP.

**Safety tests are first-class.** Specifically:
- Every emergency keyword from the spec must trigger escalation in the reply
- The AI must not produce a diagnosis for symptom queries (tested with 3-5 representative prompts)
- The AI must not recommend specific medications (tested with 2-3 prompts asking "what should I take?")

---

## 11. Risks and Mitigations (technical)

| Risk | Mitigation |
|---|---|
| AI provider rate limits during dev | Daily spend cap; cheap model; log tokens |
| Postgres-on-Windows setup pain | Docker Postgres documented as fallback in `implementation-plan.md` |
| Render free tier spins down on inactivity (cold starts) | Acceptable for an MVP. Mention in the demo post that the first request after idle can take ~30s. |
| Migration conflicts mid-build | Solo developer; low risk. Mitigation: never edit committed migrations; new column → new migration. |
| Tailwind CDN unavailable | Switch to `django-tailwind` (build pipeline) if CDN ever flakes. Low priority for v1. |
| AI provider API change during build | Pin SDK version in `requirements.txt`. |
| Static files not served correctly in prod | Whitenoise + `collectstatic` step covers this. Smoke-test in Week 4. |

---

## 12. Future Scalability

What the architecture supports without rewriting:

- **More concurrent users** — Render scales horizontally; Postgres can move to a paid tier
- **Different AI provider** — swap `_call_provider` in `ai_service.py`; rest of the app unchanged
- **Additional clinical modules** — add new Django apps; the pattern is consistent
- **Authentication** — Django's auth system is already wired; v2 enables it
- **Native mobile app** — DRF APIs already exist; mobile can consume them with no backend change
- **Message queue for SMS/email reminders** — add Celery + Redis when delivery becomes scope; the `Reminder` model is already shaped for it

What the architecture explicitly *doesn't* support without rewriting:
- Multi-tenancy (separate clinic accounts with isolated data) — would need a `Clinic` foreign key on every model
- Real-time chat updates (websockets) — would require Django Channels + ASGI
- High-volume EMR-grade reliability (audit trails, point-in-time recovery, BAA-compliant hosting) — requires a different deployment target and significantly more engineering

These are intentional v2+ decisions, not oversights.

---

## Document conventions

- Cross-references: `product-requirements-document.md`, `user-journeys.md`, `database-design.md`, `api-design.md`, `implementation-plan.md`, `branding.md`
- When architecture changes during the build, update this document **before** writing the code, and log the change in the decision log below.

## Decision log

| Date | Change | Why |
|---|---|---|
| 2026-05-17 | Initial draft | Foundation document for the four-week MVP build |
| 2026-05-17 | Chose Claude over OpenAI as primary AI provider | Better default safety behavior in healthcare framing; clean SDK; cheap Haiku tier available for dev |
| 2026-05-17 | Render selected as deploy target | Free Django + Postgres; minimal DevOps overhead |
