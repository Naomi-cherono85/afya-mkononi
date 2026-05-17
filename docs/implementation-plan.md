# Afya Mkononi — Implementation Plan

> 4-week plan to take Afya Mkononi from empty repo to deployed MVP. Each week ends with a working, demoable artifact. Source-of-truth scope is `Documentation/Afya_Mkononi.pdf`; my 360° interpretation is in `afya.md`.

---

## High-level shape

| Week | Dates (2026) | Theme | Demoable at end |
|---|---|---|---|
| 0 | May 17 (Sun) | Pre-flight | Tooling installed, accounts ready |
| 1 | May 18 – May 24 | Foundation + Product Docs | Empty Django project running on PostgreSQL; PRD + SDD merged |
| 2 | May 25 – May 31 | Backend models + APIs | Appointments, Reminders, Chat endpoints returning data via DRF |
| 3 | Jun 1 – Jun 7 | UI + AI Integration | Full chat experience wired to AI service layer; booking + reminder forms working |
| 4 | Jun 8 – Jun 14 | Test, Deploy, Demo | Live deployed URL; demo video; final LinkedIn post |

**Gate rule:** Don't start the next week until the previous week's "demoable at end" works locally. Slipping is fine — skipping isn't.

---

## Week 0 (Sun May 17) — Pre-flight

One-off setup the build assumes is already done. ~2 hours.

- [ ] Python 3.11+ installed; `python --version` works
- [ ] PostgreSQL 15+ installed locally (or Docker Desktop ready)
- [ ] GitHub account; SSH key configured
- [ ] Claude API key obtained (or OpenAI key) — stored somewhere safe, **not** in any repo
- [ ] Render / Railway / Fly.io account picked (Render recommended: free Postgres + Django works out of the box)
- [ ] Code editor with Python + Django extensions
- [ ] Decide brand assets: logo placeholder, color palette (one primary + one accent), tagline confirmed

**Decision needed before Mon:** AI provider — Claude or OpenAI? Either works; pick one and commit. Recommendation: **Claude** (better safety behavior out of the box for healthcare framing).

---

## Week 1 (May 18 – May 24) — Foundation + Product Docs

**Goal:** A clean, documented foundation. By Friday, anyone who clones the repo can read the PRD/SDD and understand the product.

### Day-by-day

**Mon May 18 — Repo + Django scaffold**
- Create GitHub repo `afya-mkononi` (public, MIT license)
- `django-admin startproject afya_mkononi backend/`
- Create venv, install: `django`, `djangorestframework`, `python-decouple`, `psycopg[binary]`
- Write `.gitignore` (Python, venv, `.env`, `*.sqlite3`, `__pycache__`, IDE files)
- Create `.env.example` with `SECRET_KEY`, `DEBUG`, `DATABASE_URL`, `AI_API_KEY`, `AI_PROVIDER`
- Initial README skeleton
- First commit + push
- **Done when:** `python manage.py runserver` → "It worked!" page locally, repo visible on GitHub

**Tue May 19 — PostgreSQL wiring**
- Create local Postgres DB `afya_mkononi_dev`
- Wire `settings.py` to read `DATABASE_URL` from `.env`
- Run `python manage.py migrate` against Postgres (not SQLite)
- Create `python manage.py createsuperuser` and confirm `/admin/` loads
- **Done when:** Django admin loads, Postgres tables (`auth_user`, etc.) visible in psql

**Wed May 20 — PRD**
- Write `docs/product-requirements-document.md` following the 13-section PDF structure: Product Name, Vision, Problem, Users, Pain Points, MVP Scope, Out-of-Scope, Functional Reqs, Non-Functional Reqs, User Journeys, Success Metrics, Risks, Future
- Explicitly enumerate the v1 exclusions (no diagnosis, no prescriptions, no payments, no EMR, no insurance)
- **Done when:** PRD is reviewable by a non-engineer and they understand what's being built

**Thu May 21 — Solution Design + User Journeys**
- Write `docs/solution-design-document.md`: system overview, architecture diagram (text-based ASCII is fine), tech stack, modules, DB design summary, API design summary, AI integration design, security, deployment, testing, risks, scalability
- Write `docs/user-journeys.md`: 3-5 named journeys (Patient asks a symptom question → guidance + escalation rule; Patient books appointment; Patient sets medication reminder; Clinic admin reviews appointments; Emergency keyword → urgent-care escalation)
- **Done when:** A second engineer could pick up the project from these docs alone

**Fri May 22 — Database + API design docs**
- Write `docs/database-design.md`: ERD (text-based), each entity with fields, types, constraints, indexes
- Write `docs/api-design.md`: every endpoint with method, path, request body, response shape, status codes, auth requirements (none for v1)
- Update README with setup instructions
- Tag `v0.1.0-docs`
- **Done when:** Models can be implemented next week without re-thinking

**Sat–Sun:** Buffer. Catch-up day if anything slipped. Otherwise, rest.

### Week 1 acceptance criteria
- [ ] Repo public on GitHub with README explaining the project
- [ ] Django + Postgres running locally; admin accessible
- [ ] All five `docs/*.md` files written and committed
- [ ] `.env.example` complete; real `.env` never committed
- [ ] Tagged `v0.1.0-docs`

### Risks this week
- **Postgres setup pain on Windows.** Mitigation: fall back to Docker Postgres if local install fights.
- **PRD perfectionism.** Mitigation: timebox to 90 minutes; mark `[TBD]` for anything that needs more thought; don't block on it.

---

## Week 2 (May 25 – May 31) — Backend models + APIs

**Goal:** All four core models live in Postgres, registered in admin, and exposed through DRF endpoints. No UI yet.

### Day-by-day

**Mon May 25 — App scaffolding**
- `python manage.py startapp accounts` (then `core`, `chatbot`, `appointments`, `reminders`)
- Move each into `backend/apps/<name>/`; fix `apps.py` `name = "apps.<name>"`
- Add all 5 to `INSTALLED_APPS`
- Add `rest_framework` to `INSTALLED_APPS`
- **Done when:** `python manage.py check` passes; empty apps registered

**Tue May 26 — Appointment model**
- Fields: `patient_name` (CharField, 200), `phone_number` (CharField, 20, validated), `email` (EmailField, optional), `preferred_date` (DateField), `preferred_time` (TimeField), `reason_for_visit` (TextField, 500), `status` (CharField with choices: `PENDING/CONFIRMED/CANCELLED/COMPLETED`, default `PENDING`), `created_at`, `updated_at` (auto)
- `Meta`: `ordering = ['-created_at']`, indexes on `(status, preferred_date)`
- `AppointmentAdmin`: list_display, list_filter on status, search by name/phone
- Migration + test
- **Done when:** Can create an appointment via admin and it persists

**Wed May 27 — Reminder model**
- Fields: `patient_name`, `reminder_type` (choices: `MEDICATION/APPOINTMENT/FOLLOWUP/OTHER`), `reminder_message` (TextField), `reminder_date`, `reminder_time`, `status` (choices: `PENDING/SENT/CANCELLED`), `created_at`
- Admin + migration + test
- **Done when:** Same as appointment

**Thu May 28 — ChatSession + ChatMessage**
- `ChatSession`: `session_id` (UUIDField, primary), `user` (FK to User, nullable for anonymous v1), `started_at`, `last_active_at`
- `ChatMessage`: `session` (FK), `sender_type` (choices: `USER/AI/SYSTEM`), `message_content` (TextField), `safety_category` (choices: `NORMAL/EMERGENCY/REFUSED/ESCALATED`), `created_at`
- Admin views: inline messages on session
- Migrations + tests
- **Done when:** Can create a session in admin, add messages, query the conversation

**Fri May 29 — DRF: Appointments + Reminders**
- `AppointmentSerializer`, `AppointmentViewSet` (List + Create only — no Update/Delete in v1)
- Same for Reminder
- URL routing via `DefaultRouter` at `/api/`
- Add CORS if needed (likely not, same-origin Django templates)
- Test with `curl` or DRF browsable API:
  - `POST /api/appointments/` returns 201
  - `GET /api/appointments/` returns list
- **Done when:** Browsable API at `/api/` shows both endpoints; round-trip works

**Sat May 30 — Chat endpoints**
- `POST /api/chat/` — accepts `{session_id?, message}`. Creates session if `session_id` missing, persists user message, returns `{session_id, reply}` (reply will be a placeholder for now — AI wiring comes Week 3)
- `GET /api/chat/sessions/<id>/` — returns session + ordered messages
- **Done when:** Can carry on a stubbed "conversation" via API

**Sun May 31 — Tests + buffer**
- Unit tests for each model's `__str__` and key constraints
- API tests: create appointment with missing required field → 400; valid → 201; list returns array
- Coverage target: > 60% on models and views (not a hard gate, but a check)

### Week 2 acceptance criteria
- [ ] Four models live; all visible in `/admin/`
- [ ] All endpoints in `api-design.md` return real data
- [ ] Tests pass: `python manage.py test`
- [ ] Tagged `v0.2.0-backend`

### Risks this week
- **Model creep** — adding fields the PRD doesn't require. Mitigation: stick to the PDF's field list verbatim for v1.
- **Auth confusion** — v1 is anonymous. Don't add login flows. Reminders/appointments are keyed by phone/name for now.

---

## Week 3 (Jun 1 – Jun 7) — UI + AI Integration

**Goal:** The product is usable end-to-end. A patient can open the site, chat with the AI, book an appointment, and set a reminder.

### Day-by-day

**Mon Jun 1 — Base template + home**
- Tailwind via CDN (simpler than build pipeline for MVP) or via `django-tailwind` (cleaner long-term — pick one and commit)
- `templates/base.html` — navbar, footer, brand "Afya Mkononi"
- `templates/home.html` — hero, three cards (Chat, Book, Remind), safety disclaimer in footer
- `core/views.py` — `home_view`
- URL: `/`
- **Done when:** Home page loads on phone + desktop; nav links work (even if target pages are stubs)

**Tue Jun 2 — Appointment booking page**
- `templates/appointments/book.html` — form matching `Appointment` fields
- View: render on GET, POST to `/api/appointments/` via HTMX or fetch
- Success: show confirmation message + appointment ID
- Validation errors: show inline
- URL: `/book/`
- **Done when:** Submitting the form creates a row in Postgres; refresh-safe

**Wed Jun 3 — Reminder page**
- Same shape as booking page
- URL: `/remind/`
- **Done when:** Same as above

**Thu Jun 4 — Chat UI**
- `templates/chatbot/chat.html` with:
  - Message list (user bubble right, AI bubble left)
  - Input + send button
  - **Visible safety disclaimer above the input** ("Afya Mkononi is not a doctor. For emergencies, call your local emergency line.")
  - Suggested prompts as clickable chips (the 5 from the PDF)
  - Loading indicator while AI responds
- Reply still stubbed — wiring tomorrow
- URL: `/chat/`
- **Done when:** UI matches what you'd send to a friend for feedback

**Fri Jun 5 — AI service layer (the centerpiece)**
- `backend/apps/chatbot/services/ai_service.py`:
  ```python
  class AIService:
      SYSTEM_PROMPT = "..."  # the prompt from PDF section 7
      EMERGENCY_KEYWORDS = [...]
      def generate_reply(self, session, user_message): ...
      def _detect_safety_category(self, user_message): ...
  ```
- Provider call isolated in a single private method `_call_provider(...)` — Claude or OpenAI client lives here only
- Returns `(reply_text, safety_category)` so the caller persists both
- **Done when:** `AIService().generate_reply(...)` returns a sensible reply from a real API call

**Sat Jun 6 — Wire chat end-to-end**
- `POST /api/chat/` now calls `AIService.generate_reply`
- Persists user message → calls AI → persists AI message with safety_category → returns reply
- Frontend chat page now calls real backend
- Test the 5 suggested prompts; test the 7 emergency scenarios from the safety boundaries memory
- **Done when:** Real conversation works; emergency keywords produce escalation language

**Sun Jun 7 — About + polish + tests**
- About page explaining what Afya Mkononi is, what it isn't, who built it
- Mobile responsiveness pass (test in browser devtools at 375px width)
- Add tests for AI service: mocked provider call; emergency keyword detection
- Tagged `v0.3.0-mvp`

### Week 3 acceptance criteria
- [ ] All 5 pages render and work
- [ ] Chat returns real AI replies
- [ ] Emergency keywords trigger escalation messaging (verified manually + with tests)
- [ ] No AI provider import outside `services/ai_service.py`
- [ ] Tagged `v0.3.0-mvp`

### Risks this week
- **AI provider rate-limits / cost.** Mitigation: log every call; set a hard daily spend cap in the provider console; use a cheap model (Haiku / GPT-4o-mini) for dev.
- **Prompt drift.** Mitigation: the system prompt is a constant in code, not an env var; changes are version-controlled.
- **Safety regression.** Mitigation: write the 7 emergency-keyword tests Day 1 of the AI work, not at the end.

---

## Week 4 (Jun 8 – Jun 14) — Test, Deploy, Demo

**Goal:** Live URL, demo video, final LinkedIn post.

### Day-by-day

**Mon Jun 8 — Manual + automated test pass**
- Walk through every flow from the PDF testing checklist
- Fix every issue found before doing anything else
- Add tests for any bug that took > 10 minutes to find
- **Done when:** Testing checklist is fully checked

**Tue Jun 9 — Safety hardening**
- Validate inputs server-side (don't trust frontend)
- Add rate limiting on `/api/chat/` (django-ratelimit, 30/min/IP)
- Confirm secrets are env vars, not committed
- Confirm `DEBUG = False` in production settings
- `ALLOWED_HOSTS` configured
- CSRF working on form posts
- **Done when:** Security checklist passes (see Cross-cutting concerns below)

**Wed Jun 10 — Deployment prep**
- Sign up / log in to Render
- Create Postgres instance
- Configure env vars in Render dashboard
- Add `gunicorn` to requirements
- Add `whitenoise` for static files
- Test `python manage.py collectstatic --noinput`
- Write `render.yaml` or use dashboard config
- **Done when:** Deploy config is ready but not yet deployed

**Thu Jun 11 — Deploy + smoke test**
- First deploy. Expect issues — that's normal.
- Run migrations on prod DB via Render shell
- Create prod superuser
- Smoke test live URL: every page, every form, chat with real AI
- Fix what's broken (likely: static files, CORS, env vars, missing migrations)
- **Done when:** Live URL works end-to-end for a stranger

**Fri Jun 12 — Polish + demo recording + final post**
- README: setup, env vars, migration, testing, deploy notes, demo link, GitHub link, future improvements
- Record demo video: 60-90 seconds, screen-only, no audio needed (captions optional). Flow: home → chat (ask a question + emergency demo) → book → remind → admin view
- Final LinkedIn post (Post 12 — see linkedin-posts.md)
- Tag `v1.0.0-mvp`
- **Done when:** Posted publicly

**Sat–Sun:** Reflection. Write `docs/lessons-learned.md`. Sketch v2 backlog from `Future Enhancements` in the PDF.

### Week 4 acceptance criteria
- [ ] Live URL accessible from any browser
- [ ] README complete
- [ ] Demo video published (LinkedIn native upload, not YouTube link)
- [ ] Final post live with GitHub + live demo + clear job CTA
- [ ] Tagged `v1.0.0-mvp`

---

## Cross-cutting concerns

### Security checklist (continuous, hard-gate before Week 4 deploy)
- [ ] `SECRET_KEY` in env, not in code
- [ ] `DEBUG = False` in production
- [ ] `ALLOWED_HOSTS` set
- [ ] AI API key in env, never logged
- [ ] User-submitted messages sanitized before persisting (no HTML execution risk in chat history rendering)
- [ ] Forms have CSRF tokens
- [ ] Rate limiting on `/api/chat/`
- [ ] No PII in logs (no full chat messages logged at INFO level)

### Testing strategy
- **Model tests** — `__str__`, constraints, default values
- **API tests** — happy path + 1-2 failure cases per endpoint
- **Service tests** — `AIService` with mocked provider; emergency keyword detection
- **No e2e tests for MVP** — too much overhead vs. value; manual checklist covers it

### Secrets management
- `.env` for local dev (gitignored)
- Render env vars for prod
- `.env.example` documents what's needed but contains no values

### Dependencies (`requirements.txt`)
```
Django>=5.0,<6.0
djangorestframework>=3.14
python-decouple>=3.8
psycopg[binary]>=3.1
anthropic>=0.40    # or openai>=1.50
gunicorn>=22.0
whitenoise>=6.6
django-ratelimit>=4.1
```
Pin versions before deploying.

---

## Definition of Done (the MVP)

From the PDF, the 13 boxes that must be ticked:

1. [ ] PRD merged
2. [ ] Solution Design Document merged
3. [ ] Working Django project
4. [ ] PostgreSQL database set up
5. [ ] Chatbot interface
6. [ ] Appointment booking flow
7. [ ] Reminder creation flow
8. [ ] AI safety prompt enforced
9. [ ] Django admin view functional
10. [ ] README documentation complete
11. [ ] GitHub repository public
12. [ ] Deployed live demo URL
13. [ ] Final LinkedIn demo post live

If even one is missing, the MVP isn't done — don't post the final demo until they all are.

---

## What I will NOT do in v1 (scope guard)

The PDF is explicit. When tempted to add any of these, push back:

- ❌ Medical diagnosis
- ❌ Prescription generation
- ❌ Emergency handling beyond "go seek urgent care"
- ❌ Insurance claims
- ❌ Payment integration
- ❌ Hospital / EMR integration
- ❌ Patient medical record integration
- ❌ User authentication (deferred to v2)
- ❌ SMS / Email reminder delivery (model captures intent; delivery is v2)
- ❌ Multilingual support (v2)

Every one of these is in the v2 backlog. They're not lost — they're parked.
