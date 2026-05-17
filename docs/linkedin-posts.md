# Afya Mkononi — Draft LinkedIn Posts

> 12 paste-ready posts. Each follows the structure: **Hook → Context → What I Built → What I Learned → Proof → Soft CTA → Hashtags**. Tailor the brackets `[like this]` before posting if you want to add a personal detail.

---

## Post 1 — Mon May 18 (Week 1 Build Update)

**Theme:** Introducing Afya Mkononi
**Asset:** Brand banner or one-line product graphic

---

I'm starting a new build journey: **Afya Mkononi** — an AI-powered healthcare assistant designed to support patients and clinics with routine guidance, appointment booking, and reminders.

Clinics field the same questions every day. Patients wait for answers that could be handled in seconds. Afya Mkononi is meant to absorb that routine load — and, just as importantly, escalate to professional care when something serious shows up.

This week, I'm focused on the foundation:
• Product Requirements Document
• Solution Design Document
• User journeys
• Django + PostgreSQL project setup
• GitHub repo + clean docs

The stack:
Python · Django · Django REST Framework · PostgreSQL · Tailwind CSS · AI via an isolated service layer

A note on the AI: this product will **not** diagnose, **not** prescribe, and **not** replace a clinician. It will give general guidance, support booking and reminders, and escalate emergencies. Those boundaries aren't a footnote — they're product features.

I'll be documenting the build publicly over the next four weeks: Monday for build updates, Wednesday for technical learnings, Friday for proof and demos.

Next: writing the PRD.

#BuildInPublic #Python #Django #PostgreSQL #HealthTech #AI #SoftwareEngineering

---

## Post 2 — Wed May 20 (Week 1 Technical Learning)

**Theme:** Why I'm starting with a PRD instead of jumping into code
**Asset:** Screenshot of the PRD outline (headings only)

---

Before writing a single Django model for **Afya Mkononi**, I'm writing a Product Requirements Document.

It's tempting to skip this — the project is mine, I know what I want, why slow down to document it?

Here's what the PRD is forcing me to decide before I write code:

• **Who exactly is the user?** Patients seeking routine support — not clinicians, not emergency cases.
• **What's in the MVP?** Chatbot, appointment booking, reminder creation, basic admin, deployed demo.
• **What's explicitly OUT?** Diagnosis. Prescriptions. Payments. Hospital integrations. EMR. Insurance. Auth (deferred to v2).
• **What does success look like?** A patient can complete the three core flows without confusion.
• **What are the risks?** AI giving advice it shouldn't. Cost overruns on the AI provider. Scope creep.

What I'm learning: a PRD is not bureaucracy. It's a scope contract with yourself.

The biggest lift is the "Out of Scope" section. Saying no to features now is what makes the four-week timeline real. Otherwise every commit becomes a debate.

Next: Solution Design Document — translating these requirements into architecture.

#BuildInPublic #ProductDevelopment #Django #SoftwareEngineering #HealthTech

---

## Post 3 — Fri May 22 (Week 1 Proof)

**Theme:** Solution Design + architecture
**Asset:** Architecture sketch (text-based diagram in image form, or hand-drawn)

---

Week 1 of **Afya Mkononi** — Solution Design Document is done.

The high-level architecture:

```
Browser
  ↓
Django Web App (templates + views)
  ↓
Django REST Framework APIs
  ↓
Service Layer  ← AI provider isolated here
  ↓
PostgreSQL + AI Provider API
```

Two design decisions worth calling out:

**1. The AI provider lives behind a service layer.**
All AI calls go through `apps/chatbot/services/ai_service.py`. Django views never import the AI SDK directly. This means I can swap providers, change prompts, or add safety checks without touching the rest of the app.

**2. Apps split by responsibility, not by layer.**
Five Django apps: `accounts`, `chatbot`, `appointments`, `reminders`, `core`. Not "models app" + "views app". Each app owns its own slice end-to-end.

What I'm learning: architecture doesn't have to be complex to be useful. For an MVP, the goal is a structure that's easy to read, easy to extend, and hard to corrupt as the codebase grows.

The repo is public from day one. PRD and Solution Design are committed under `docs/`. Anyone clicking through gets the full picture before they read a single line of Python.

Next week: turning these documents into Django models and APIs.

#BuildInPublic #SoftwareArchitecture #Django #Python #PostgreSQL #HealthTech

---

## Post 4 — Mon May 25 (Week 2 Build Update)

**Theme:** Backend foundation is up
**Asset:** Screenshot of project structure / Django admin login

---

Week 2 of **Afya Mkononi**: backend foundation.

What's now working:
• Django project running on PostgreSQL (not SQLite — production-shaped from day one)
• Five apps scaffolded: `accounts`, `chatbot`, `appointments`, `reminders`, `core`
• `.env` flow wired up — secrets out of code, `.env.example` documents what's needed
• Django admin accessible with a superuser
• First migration committed

One small decision that's already paying off: I split the project into apps by **responsibility**, not by **type**. The chatbot's models, views, services, and templates all live under `apps/chatbot/`. Same for appointments and reminders.

When I need to find something, I go to the feature folder — not hunt through a top-level `models.py` shared by everything.

This is the kind of decision that costs nothing on day 1 and saves real time by day 30.

What I'm doing today: building the Appointment model.

Next: Wednesday's post will walk through the model design choices.

#BuildInPublic #Django #Python #PostgreSQL #BackendDevelopment

---

## Post 5 — Wed May 27 (Week 2 Technical Learning)

**Theme:** Designing the Appointment model
**Asset:** Code snippet of the model + admin registration

---

Today I designed the `Appointment` model for **Afya Mkononi**.

It looks simple — patient name, phone, date, time, reason, status — but every field is a small decision.

A few of them:

**`status` as choices, not a free-text field.**
Choices: `PENDING`, `CONFIRMED`, `CANCELLED`, `COMPLETED`. Choices give me admin filters, validation, and a clear state machine. A free-text "status" field is how products end up with `pending`, `Pending`, `PENDIING` all in the same column three months in.

**Separate `preferred_date` (DateField) and `preferred_time` (TimeField).**
A combined DateTimeField would be cleaner — but the form needs two distinct inputs, and the user thinks about date and time separately. The model should mirror how users think.

**No FK to a User yet.**
v1 is anonymous. `patient_name` and `phone_number` are plain fields. Auth is v2. Solving authentication for an MVP that no one is logging into yet would be premature.

**Indexes on `(status, preferred_date)`.**
The most common admin query will be "show me PENDING appointments ordered by date." Index for the question you'll actually ask.

What I'm learning: model design forces you to think about the real-world workflow before you write much code. Every choice constrains the future. Worth slowing down for.

Next: API endpoints with Django REST Framework.

#BuildInPublic #Django #PostgreSQL #BackendDevelopment #DataModeling

---

## Post 6 — Fri May 29 (Week 2 Proof)

**Theme:** First DRF endpoint live
**Asset:** DRF browsable API screenshot + curl response

---

Small Afya Mkononi proof-of-work moment: the first real API endpoint is live (locally).

`POST /api/appointments/` accepts an appointment request, validates it, and persists it to PostgreSQL.
`GET /api/appointments/` returns the list.

Stack inside the request:
View (DRF `ViewSet`) → Serializer (validation) → Model → PostgreSQL.

What's working:
✅ Missing required field → 400 with a clear error
✅ Invalid date format → 400
✅ Valid payload → 201 with the created record
✅ Browsable API renders the schema (DRF's killer feature for debugging)

What's *not* there yet:
- Pagination (the list will be small for a while — fine for now)
- Auth (deferred to v2)
- Update/Delete endpoints (the MVP only needs Create + List)

One thing I keep reminding myself: DRF gives you a lot for free — but you still have to **decide** what to enable. Defaults aren't decisions.

Next week: chatbot UI and the AI service layer.

#BuildInPublic #Django #DjangoRESTFramework #APIDesign #PostgreSQL #BackendDevelopment

---

## Post 7 — Mon Jun 1 (Week 3 Build Update)

**Theme:** Chatbot UI is live (with a stubbed AI for now)
**Asset:** Chat page screenshot, mobile + desktop

---

Week 3 of **Afya Mkononi** — the product is starting to feel like a product.

The chat page is now live:
• Message bubbles (user / AI / system)
• Input + send
• Loading state while waiting for a reply
• Five suggested prompts as quick-tap chips
• **Safety disclaimer right above the input** — not in a footer, where it would disappear

The AI reply is currently stubbed — the real provider gets wired in on Friday. But the UI, the API plumbing, and the conversation persistence (`ChatSession` + `ChatMessage` models) are all real.

One design choice I want to call out: the safety disclaimer's placement.

Most apps put disclaimers in the footer. For a healthcare chatbot, that's the wrong place — by the time a user is typing, they've already scrolled past the footer. The disclaimer needs to be where the user's eye is when they're about to ask the AI something.

Small UX call, but it changes how seriously the boundary feels.

Next: the AI service layer and the safety prompt.

#BuildInPublic #Django #Python #HealthTech #UIDesign

---

## Post 8 — Wed Jun 3 (Week 3 Technical Learning)

**Theme:** The AI service layer + safety prompt
**Asset:** Code snippet of `ai_service.py` structure + system prompt excerpt

---

The most important file in **Afya Mkononi** isn't a model or a view. It's `apps/chatbot/services/ai_service.py`.

This is where every AI call goes through. No Django view ever imports the AI SDK directly.

Why does this matter for a healthcare product?

**1. Provider swappability.**
If Claude doesn't fit, I can swap to OpenAI, or vice versa, by editing one file. The rest of the app doesn't know or care which provider is on the other end.

**2. Prompt control.**
The system prompt — the one telling the AI what it can and can't do — lives in this file as a code constant. Not an env variable. Not a database row. Code. Which means every change is tracked, reviewed, and versioned.

**3. Safety logic is co-located.**
Detection of emergency keywords (chest pain, breathing trouble, severe bleeding, stroke signs, severe allergic reactions, pregnancy danger) happens here. Refusal to diagnose happens here. The Django views just persist what comes back.

The system prompt opens with:

> *"You are Afya Mkononi, a healthcare support assistant. You must not diagnose diseases, prescribe medication, or replace a licensed healthcare professional..."*

And explicitly enumerates emergency symptoms that must trigger an escalation response.

What I'm learning: integrating AI responsibly isn't a coding problem. It's a product design problem that shows up in your architecture. Once the service layer exists, "be safe" stops being a hope and becomes a structure.

Next: wiring it end-to-end on Friday.

#BuildInPublic #AI #ResponsibleAI #Python #Django #HealthTech

---

## Post 9 — Fri Jun 5 (Week 3 Proof)

**Theme:** A bug I fixed this week
**Asset:** Terminal screenshot showing failing → passing, or git diff

---

Today's **Afya Mkononi** lesson: debugging is half the job.

The bug: chat messages were saving to the database, but the AI reply was returning before the user message had been persisted. Race-condition-shaped — except this is Django, sync code, so it shouldn't have been.

What I checked:
• Order of operations in the view
• Transaction boundaries
• Whether `ChatSession.last_active_at` was actually updating
• The serializer (red herring, fine)
• The service layer's return shape (the real culprit)

The actual cause: I was returning the AI reply from `AIService.generate_reply` **before** writing the AI message to the database. The user message saved fine. The AI reply rendered fine. But if you refreshed mid-conversation, the AI message wasn't there.

Fix: invert the order. Persist first, then return. Two lines moved.

What I'm taking from this: bugs in AI features rarely look like AI bugs. They look like ordering, persistence, and state-management bugs. The fact that an AI is involved is incidental.

Also: the bug was 20 minutes to find, 30 seconds to fix. That ratio is the job.

Added a test so it can't regress.

Next: the final week — testing pass, deploy, demo.

#BuildInPublic #Django #Debugging #Python #SoftwareEngineering

---

## Post 10 — Mon Jun 8 (Week 4 Build Update)

**Theme:** Testing the core flows
**Asset:** Testing checklist screenshot

---

Week 4 of **Afya Mkononi** — the final week before MVP launch.

Today's focus: testing every flow end-to-end before deploying anything.

The checklist:
✅ Chat returns sensible replies for the five suggested prompts
✅ Emergency keywords (chest pain, severe bleeding, etc.) trigger escalation language
✅ Appointment form rejects missing required fields with a clear error
✅ Reminder form persists correctly
✅ Django admin shows all four entity types
✅ API endpoints return correct status codes for both success and validation failure
✅ UI works at 375px (phone) width
✅ Safety disclaimer is visible on every chat page load

The most interesting tests aren't the happy-path ones. They're the "what does the chatbot do when someone asks it to diagnose them?" and "what happens when a user types an emergency keyword in the middle of a normal conversation?"

Those tests are the product. If they fail, nothing else matters.

A few small bugs found, fixed, and turned into regression tests. Nothing major — that's the value of testing weekly instead of only at the end.

Next: deploying to Render. Wednesday's post will walk through the deploy.

#BuildInPublic #Django #Testing #HealthTech #SoftwareEngineering

---

## Post 11 — Wed Jun 10 (Week 4 Technical Learning)

**Theme:** Deploying Django + PostgreSQL to Render
**Asset:** Live URL screenshot or deploy log

---

**Afya Mkononi** is now deployed.

Walking through what it took to get a Django + PostgreSQL app from local to live:

**1. Production settings.**
`DEBUG = False`. `ALLOWED_HOSTS` configured. `SECRET_KEY` from env, never in code. `CSRF_TRUSTED_ORIGINS` set to the prod URL.

**2. Static files.**
Local development serves static files lazily. Production doesn't. Added `whitenoise` so Django can serve its own static files without a separate CDN for the MVP.

**3. WSGI server.**
Local: `runserver`. Production: `gunicorn`. Different worlds — `runserver` was never meant for prod traffic.

**4. Database.**
Render provisions a managed PostgreSQL instance. `DATABASE_URL` becomes an env var. The Django side doesn't change — `python-decouple` reads it and Django connects.

**5. Migrations on prod.**
First deploy: run migrations through Render's shell. Create the superuser. Don't bake the superuser into code.

**6. Smoke test as a stranger.**
Open the live URL in an incognito window. Walk every flow. Find what's broken in production that worked locally — usually static files, env vars, or `ALLOWED_HOSTS`.

What I'm learning: deployment is a separate skill from development. Things that "work locally" only mean they work *in your specific local setup*. Production is a different environment with different defaults, and the difference is where most first-deploy bugs live.

Next: Friday — the final MVP demo.

#BuildInPublic #Django #Deployment #PostgreSQL #DevOps

---

## Post 12 — Fri Jun 12 (Week 4 Final Demo)

**Theme:** Afya Mkononi MVP is live
**Asset:** 60-90s demo video + GitHub link + live URL

---

**Afya Mkononi MVP is live.**

Over the past four weeks, I built an AI-powered healthcare assistant from idea to deployed product — in public, on this feed.

What it does:
🤖 Patient chatbot with general healthcare guidance
📅 Appointment booking
⏰ Medication and follow-up reminders
🛡️ AI safety boundaries — no diagnosis, no prescriptions, explicit emergency escalation
👩‍💼 Django admin dashboard for clinic-side review

The stack:
Python · Django · Django REST Framework · PostgreSQL · Tailwind CSS · Claude API · Render

What I practiced:
• Product Requirements Document
• Solution Design Document
• Backend development (Django apps, models, migrations, admin)
• API design (DRF serializers, viewsets, routes)
• Database modeling (PostgreSQL with proper indexes and constraints)
• AI integration through a clean service layer
• Responsible AI (system prompt, safety boundaries, emergency escalation)
• Testing (manual checklist + automated tests)
• Deployment (Django + PostgreSQL on Render)
• Documentation (PRD, SDD, README, API docs)

The biggest lesson: **building a useful AI product is mostly not about the AI.** It's about clear requirements, thoughtful data modeling, safe defaults, and disciplined scope. The AI provider is one file in the codebase. Everything else is the actual product.

Demo video below. 90 seconds — chat, booking, reminders, admin.

🔗 **GitHub:** [link]
🌐 **Live demo:** [link]

---

I'm open to entry-level software developer roles, internships, and apprenticeships — especially backend or full-stack opportunities where I can contribute using Python, Django, PostgreSQL, and AI-enabled development.

If you're a developer, hiring manager, recruiter, or founder working on Python/Django, HealthTech, or AI products — I'd love to connect.

#BuildInPublic #Python #Django #PostgreSQL #AI #HealthTech #SoftwareEngineering #EntryLevelDeveloper #OpenToWork

---

## Posting tips that apply to all 12

1. **First two lines are the post.** LinkedIn truncates after ~210 characters on mobile. The first two lines need to make someone tap "see more."
2. **One idea per post.** If you have two strong ideas, save the second for next week.
3. **Avoid "just" and "only."** "Today I *just* learned…" undersells the work. "Today I learned…" lands differently.
4. **Native upload for videos.** LinkedIn's algorithm rewards native video over YouTube links. Upload the demo directly.
5. **Reply to comments within 24h.** The algorithm boosts posts with active comment threads. Show up.
6. **Don't repost an old post.** If you missed a day, post the next one on the next day. No catch-up batches.
7. **The job CTA appears once.** Post 12. That's it. Discipline = signal.
