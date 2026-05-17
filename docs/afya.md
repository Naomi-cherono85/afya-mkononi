# My 360° Understanding of the Afya Mkononi Build Journey

## What this document actually is

The PDF (filed under `Afya_Mkononi.pdf`, but internally titled **Afya Mkononi Build Journey**) is **not a typical spec**. It is a **dual-purpose playbook** that fuses two things into one plan:

1. A **4-week software build plan** to take an MVP from idea → deployed product.
2. A **LinkedIn documentation + job-search strategy** designed to convert that build into visible proof for an entry-level developer role.

Everything in the document is engineered to serve both tracks at once: each technical milestone has a matching content artifact (post, screenshot, demo, lesson).

---

## The product in one paragraph

**Afya Mkononi** is an AI-powered healthcare assistant for patients and clinics. It answers routine health questions, lets patients book appointments, creates reminders, and offers basic guidance — explicitly **not** a replacement for clinicians. The product's job is to absorb repetitive patient inquiries, reduce admin workload, and route users to professional care when symptoms warrant it. Tagline: *"AI-powered patient support for smarter clinic workflows."*

### Users
- **Primary:** patients needing basic info, bookings, reminders.
- **Secondary:** clinics, clinical officers, nurses, admins who want to deflect repetitive Q&A and improve follow-up.

---

## Technical architecture (the chosen stack)

| Layer | Choice |
|---|---|
| Backend | Python + Django |
| API | Django REST Framework |
| Database | PostgreSQL |
| Frontend (MVP) | Django templates + Tailwind CSS |
| Frontend (later) | React on top of DRF |
| AI | OpenAI or Claude via an isolated **service layer** |
| Dev accelerator | Claude Code |
| Deploy | Render / Railway / Fly.io |
| VCS | Git + GitHub |

**Request flow:** Browser → Django Web App → DRF APIs → Service Layer → PostgreSQL + AI Provider API.

**Why this stack:** Django gives auth, admin, ORM, and routing out of the box; Postgres fits the structured/relational nature of healthcare data; DRF makes the chatbot/appointments/reminders APIs reusable for a future mobile client; Claude Code compresses boilerplate, review, and test-writing time.

### Django apps (modules)
- `accounts` — users / auth (future-ready)
- `chatbot` — patient conversations with the AI
- `appointments` — booking requests
- `reminders` — appointment / medication reminders
- `core` — shared utilities, homepage, base templates
- Django admin used as the v1 admin UI

### Core database entities
`User`, `PatientProfile`, `ChatSession`, `ChatMessage` (with `sender_type` + `safety_category`), `Appointment` (status-driven), `Reminder`.

### Core APIs
- `POST/GET /api/appointments/`
- `POST/GET /api/reminders/`
- `POST /api/chat/`
- `GET /api/chat/sessions/{id}/`

---

## The 4-week timeline

### Week 1 — Product foundation (think before code)
Deliverables: **PRD**, **Solution Design Document**, user journeys, initial DB sketch, GitHub repo, Claude Code workflow defined. The PRD covers vision, problem, MVP scope, what's **out of scope** (no diagnosis, no prescriptions, no payments, no EMR integration, no insurance), success metrics, risks.

### Week 2 — Backend foundation
Django apps scaffolded, Postgres wired, models + migrations + admin registration, first DRF endpoints. Lesson framing: *"good backend starts with clear product thinking."*

### Week 3 — UI + AI integration
Pages (home, chat, appointments, reminders, about), chat UI (bubbles, input, loading, suggested prompts, **safety disclaimer**), and a **dedicated `ai_service.py`** that isolates the AI provider behind a service layer. Safety prompt is explicit: no diagnosis, no prescriptions, escalate emergency symptoms (chest pain, breathing, bleeding, stroke signs, etc.), keep responses calm and simple.

### Week 4 — Test, deploy, demo
Testing checklist across chatbot/safety/forms/DB/admin/API/mobile/live. Deployment checklist (env vars, migrations, superuser, static files, live URL test, README update, demo video). Final MVP demo post on LinkedIn.

### MVP done = 13 boxes ticked
PRD, SDD, working Django project, Postgres set up, chatbot UI, appointment flow, reminder flow, AI safety prompt, Django admin, README, GitHub repo, deployed live demo, final LinkedIn demo post.

---

## The non-negotiable: AI safety boundaries

The chatbot is intentionally bounded. It must:
- Give **general** guidance only — never diagnose, never prescribe.
- **Escalate emergencies** (severe chest pain, breathing trouble, severe bleeding, loss of consciousness, stroke signs, severe allergic reactions, pregnancy danger) to urgent care.
- Encourage professional consultation, stay calm/simple, avoid harvesting unnecessary sensitive info.

This is enforced at two layers: (1) the **system prompt** content, and (2) the **architectural choice** to isolate AI calls in a service layer so the prompt, provider, and safety logic live in one swappable place.

---

## The Claude Code workflow (not vibe-coding)

The document is firm about this: Claude Code is an **accelerator, not a substitute for understanding**. The prescribed loop:

1. Write the requirement → 2. Ask for an implementation plan → 3. Review it → 4. Generate/modify code → 5. Run locally → 6. Manual test → 7. Ask for tests → 8. Review tests → 9. Commit → 10. Document the lesson on LinkedIn.

Every step has a human review gate. Prompts are concrete and reference the PRD/SDD by path.

---

## The LinkedIn strategy (the second half of the document)

This is roughly half the PDF and is more strategically detailed than the build plan itself.

### Strategic intent
Posts are **proof artifacts for a job search** — not a learning diary. Every post should prove one of five things: she can (1) think through a product problem, (2) translate requirements into software, (3) write and explain code, (4) debug independently, (5) ship a working project.

### Cadence — 3 posts/week
- **Monday:** build update (progress)
- **Wednesday:** technical learning (depth)
- **Friday:** proof / reflection / demo (evidence)

### Five content pillars
1. **Product thinking** → "this person can build with purpose"
2. **Backend engineering** → "can do real backend tasks"
3. **Problem-solving & debugging** → "can troubleshoot and keep going"
4. **AI integration & responsible AI** → "can integrate AI responsibly"
5. **Proof of work / shipping** → "can finish, not just start"

### Positioning rules (very explicit)
| Avoid | Use |
|---|---|
| "I'm just a junior trying to learn" | "I am building Afya Mkononi in public to strengthen my software engineering, product, and AI skills." |
| "Small practice project" | "An MVP exploring how AI can support routine patient engagement and clinic workflow efficiency." |
| "I used AI to write the code" | "I used Claude Code as a development accelerator for planning, scaffolding, debugging, testing, and documentation — while reviewing every implementation decision." |
| "Today I learned Django." | "Today I used Django models to design how appointment requests will be stored in Afya Mkononi." |

### Profile alignment (before posting)
- Headline: *"Software Developer | Python, Django, PostgreSQL | Building AI-Powered HealthTech Products"*
- About: stack, Afya Mkononi as portfolio, open to entry-level / internships / apprenticeships.
- Featured: GitHub, live demo, final MVP post, PRD/case study, demo video.

### Post template (every post)
Hook → Context → What I built → What I learned → Proof (screenshot/code/diagram) → Soft CTA.

### CTA discipline
Job-search CTAs are **rare and intentional**, mostly reserved for milestone/demo posts. Otherwise positioning is implied through consistency, quality, and proof — not begging.

### Engagement loop
Comment weekly on posts by engineers, eng managers, recruiters, founders, HealthTech builders, Django devs — with substantive comments that reference her own build.

### The hiring funnel it builds
**LinkedIn post → Profile → Featured project → GitHub → Live demo → Interview conversation.**

---

## How the two tracks reinforce each other

This is the cleverest part of the plan:

| Build artifact | Becomes content artifact |
|---|---|
| PRD | "Why I started with a PRD" post (Week 1 Wed) |
| Solution Design | Architecture sketch post (Week 1 Fri) |
| Django + Postgres setup | GitHub screenshot post (Week 2 Mon) |
| Appointment model | Database design post (Week 2 Wed) |
| First DRF endpoint | API screenshot (Week 2 Fri) |
| Chat UI | Chat UI screenshot (Week 3 Mon) |
| Safety prompt | Responsible AI post (Week 3 Wed) |
| AI service layer | Code screenshot post (Week 3 Fri) |
| Testing checklist | Quality-mindset post (Week 4 Mon) |
| Deployment | Live app screenshot (Week 4 Wed) |
| Final MVP | Demo video + clear job CTA (Week 4 Fri) |

Nothing is wasted. Every commit has a publishable angle.

---

## What this means for me (as the assistant helping build it)

1. **Documentation lives in `docs/`** — PRD, SDD, user journeys, API design, DB design, LinkedIn plan are all expected files. I should write to those when asked, not invent ad-hoc places.
2. **Folder structure is prescribed** — `backend/afya_mkononi/`, `backend/apps/{accounts, chatbot, appointments, reminders, core}/`, `templates/`, `static/`, plus `docs/`, `screenshots/`, README, `.gitignore`, `.env.example`.
3. **The AI service layer is non-optional** — `apps/chatbot/services/ai_service.py` must isolate provider logic. Don't sprinkle OpenAI/Claude calls through views.
4. **Safety prompt is product, not afterthought** — when building the chatbot, the system prompt with its boundaries is a first-class artifact.
5. **Scope discipline matters** — v1 explicitly excludes diagnosis, prescriptions, emergency handling beyond escalation, insurance, payments, hospital integration, EMR. I should push back if asked to add these to v1.
6. **The Claude Code workflow has a plan-first step** — when asked to implement features, propose a plan, get review, then write code. Don't jump straight to editing.
7. **Naming:** the product is **Afya Mkononi** (Swahili for "health in hand"). The repo/folder uses `Afya_Mkononi` with an underscore; the brand uses a space. The PDF was originally authored under a different working name ("AfyaFlow AI") but has been unified to Afya Mkononi.

---

## The throughline

Strip away the structure and the document is making one argument: **build a real product end-to-end, in public, and let the artifacts of doing that work be the proof you're hireable.** The healthcare angle isn't incidental — it forces real product judgment (safety, scope, escalation), which is exactly the kind of judgment that's hard to fake on a resume and easy to demonstrate in a post.
