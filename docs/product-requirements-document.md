# Afya Mkononi — Product Requirements Document (PRD)

> **Status:** Draft v1.0 · **Owner:** Naomi Cherono · **Last updated:** 2026-05-17

This document defines what Afya Mkononi is, who it's for, what's in v1, and what is explicitly *not* in v1. It is the scope contract for the four-week MVP build.

---

## 1. Product Name

**Afya Mkononi** *(Swahili: "health in hand")*

---

## 2. Product Vision

Afya Mkononi is an AI-powered healthcare assistant that helps patients access general health guidance, book clinic appointments, and set reminders — while clearly directing them to professional care when symptoms warrant it. The product reduces routine administrative load on clinics so clinical staff can focus on the patient interactions that actually need human judgment.

**One-liner:** *"AI-powered patient support for smarter clinic workflows."*

---

## 3. Problem Statement

Clinics — particularly small and mid-sized ones — field the same routine inquiries every day: "What time are you open?", "I forgot my appointment, can I reschedule?", "I have a headache, should I come in?", "When do I take this medication again?". These queries are essential to patient care but consume disproportionate amounts of clinical time.

At the same time, patients delay seeking help because they're unsure whether their symptoms warrant a visit, and miss appointments and medications because reminders rely on memory.

The result: clinics absorb avoidable workload, patients receive slower care, and serious symptoms occasionally get under-triaged.

Afya Mkononi creates a 24/7 digital channel that handles the routine layer of this work — and, critically, escalates anything that looks emergent to immediate professional care.

---

## 4. Target Users

### Primary: Patients
- Adults seeking general health information and clinic services
- People managing ongoing care (medication schedules, follow-up appointments)
- People uncertain whether their symptoms require a clinical visit

### Secondary: Clinic staff
- Clinical officers and nurses fielding repetitive questions
- Clinic administrators managing appointment books
- Owners of small private clinics seeking lighter-weight digital tools (no full EMR)

### Out of scope for v1
- Children (no pediatric-specific guidance)
- Patients with chronic complex conditions requiring care coordination
- Insurance / billing workflows
- Emergency-only users (the product escalates, it doesn't handle them)

---

## 5. User Pain Points

| Pain | Who feels it | How Afya Mkononi addresses it |
|---|---|---|
| Long phone wait times for routine questions | Patients | 24/7 AI chat for general guidance |
| Uncertainty whether to visit a clinic | Patients | Triage-style guidance + clear escalation language for emergencies |
| Forgotten appointments and medications | Patients | Self-serve reminder creation |
| Reception staff drowning in routine queries | Clinics | Deflects routine asks to the AI |
| Difficulty booking outside business hours | Patients | Online appointment requests at any time |
| No structured record of patient inquiries | Clinics | Every chat session and booking is persisted in PostgreSQL |

---

## 6. MVP Scope (v1)

The first version includes:

1. **Public home page** — explains what Afya Mkononi is, with three primary CTAs (Chat, Book, Remind)
2. **Patient chatbot** — conversational interface for general health questions with persisted session history
3. **Appointment booking form** — patient can submit a request specifying name, contact, preferred date/time, and reason
4. **Reminder creation form** — patient can create medication, appointment, or follow-up reminders
5. **Django admin** — clinic-side view of all appointments, reminders, and chat sessions
6. **AI safety boundaries** — system prompt that prevents diagnosis/prescription and explicit emergency escalation
7. **PostgreSQL database** — all data persisted reliably
8. **Deployed live demo** — accessible at a public URL

---

## 7. Out of Scope for v1

These are real product needs that are explicitly **deferred** to v2 or beyond. They are not lost — they are parked.

1. ❌ **Medical diagnosis** of any kind
2. ❌ **Prescription generation** — the assistant must not recommend specific medications or dosages
3. ❌ **Emergency medical handling** beyond "seek urgent care immediately"
4. ❌ **Insurance claims** or coverage workflows
5. ❌ **Payment integration**
6. ❌ **Hospital / EMR / clinic management system integration**
7. ❌ **Patient medical record integration**
8. ❌ **User authentication** — v1 is anonymous, keyed by phone + name on bookings/reminders
9. ❌ **SMS / Email delivery of reminders** — the *intent* is captured; delivery is v2
10. ❌ **Multilingual support** — English only in v1 (Swahili UI for v2)
11. ❌ **Native mobile apps** — responsive web only
12. ❌ **Role-based access control** — Django admin via superuser only

This list is the most important section of the PRD. Every feature creep request during the build should be checked against this list first.

---

## 8. Functional Requirements

### 8.1 Chatbot
- **FR-CHAT-1** The user can start a chat session without signing in.
- **FR-CHAT-2** Each session has a unique session ID (UUID) persisted server-side.
- **FR-CHAT-3** Every user message and AI reply is persisted in `ChatMessage` linked to a `ChatSession`.
- **FR-CHAT-4** Every persisted message has a `safety_category` (`NORMAL`, `EMERGENCY`, `REFUSED`, `ESCALATED`).
- **FR-CHAT-5** When the user's message matches an emergency keyword (severe chest pain, difficulty breathing, severe bleeding, loss of consciousness, stroke-like symptoms, severe allergic reaction, pregnancy danger), the AI response must contain an explicit "seek urgent medical care immediately" instruction.
- **FR-CHAT-6** The chat UI displays a visible safety disclaimer at all times — placed above the input field, not in the footer.
- **FR-CHAT-7** The chat UI surfaces 5 suggested prompts (listed in `user-journeys.md`) as one-tap chips.
- **FR-CHAT-8** The chat UI shows a loading indicator while waiting for an AI reply.
- **FR-CHAT-9** The AI must never produce a final diagnosis or a specific medication recommendation.

### 8.2 Appointment booking
- **FR-APPT-1** The user can submit an appointment request via a form.
- **FR-APPT-2** Required fields: patient name, phone number, preferred date, preferred time, reason for visit.
- **FR-APPT-3** Optional: email address.
- **FR-APPT-4** Phone number must be validated (length, allowed characters).
- **FR-APPT-5** On submission, the system creates an `Appointment` record with `status = PENDING`.
- **FR-APPT-6** The user sees a confirmation screen with the appointment ID.
- **FR-APPT-7** Validation failures show inline errors without losing form state.
- **FR-APPT-8** All appointments are visible in Django admin, filterable by status and date.

### 8.3 Reminders
- **FR-REM-1** The user can create a reminder via a form.
- **FR-REM-2** Required: patient name, reminder type (Medication / Appointment / Follow-up / Other), message, date, time.
- **FR-REM-3** Reminders are stored with `status = PENDING`.
- **FR-REM-4** Delivery (SMS/email) is **out of scope** for v1; the intent is captured for v2 to act on.
- **FR-REM-5** All reminders are visible in Django admin, filterable by type, status, and date.

### 8.4 Admin
- **FR-ADM-1** A clinic superuser can view all appointments, reminders, and chat sessions.
- **FR-ADM-2** Chat sessions show all messages inline, ordered chronologically.
- **FR-ADM-3** Appointment status can be updated by an admin (`PENDING → CONFIRMED / CANCELLED / COMPLETED`).
- **FR-ADM-4** Filters and search are enabled on key fields (status, date, patient name, phone).

---

## 9. Non-Functional Requirements

### 9.1 Performance
- **NFR-PERF-1** The home, chat, booking, and reminder pages must render in < 2s on a 3G connection on first load.
- **NFR-PERF-2** AI chat responses should arrive in < 5s under normal load; UI shows a loading state during the wait.

### 9.2 Security
- **NFR-SEC-1** No secret keys (Django `SECRET_KEY`, AI provider key, database credentials) appear in source code or version control.
- **NFR-SEC-2** All form submissions are CSRF-protected.
- **NFR-SEC-3** `DEBUG = False` in all non-development environments.
- **NFR-SEC-4** `/api/chat/` is rate-limited to 30 requests/minute/IP.
- **NFR-SEC-5** User-submitted content is sanitized before rendering (no HTML execution from chat history).
- **NFR-SEC-6** Full chat message contents are **not** logged at INFO level (PII concern).

### 9.3 Reliability
- **NFR-REL-1** Failed AI provider calls must not crash the app. The user sees a graceful "I'm having trouble right now — please try again or contact the clinic directly" message; the failure is logged.
- **NFR-REL-2** All database writes (chat messages, appointments, reminders) are committed in a transaction so partial writes don't leave orphan rows.

### 9.4 Accessibility
- **NFR-A11Y-1** All forms have associated `<label>` elements.
- **NFR-A11Y-2** Color contrast meets WCAG AA against the brand palette (see `branding.md`).
- **NFR-A11Y-3** Chat is usable via keyboard only.

### 9.5 Usability
- **NFR-USA-1** The product works on mobile widths from 375px upward.
- **NFR-USA-2** A user can complete each of the three core flows (chat, book, remind) in under 60 seconds.
- **NFR-USA-3** The safety disclaimer is visible in the user's viewport at all times during chat.

### 9.6 Maintainability
- **NFR-MAINT-1** AI provider calls live only in `apps/chatbot/services/ai_service.py`. No other module imports the AI SDK.
- **NFR-MAINT-2** The system prompt is a code constant inside `ai_service.py` — not an env var, not a database row.
- **NFR-MAINT-3** Django apps are split by responsibility (chatbot, appointments, reminders, accounts, core), not by layer.

---

## 10. User Journeys

The full user journeys are documented in `user-journeys.md`. Five journeys are in scope:

1. **Patient asks a routine health question** → general guidance + "consult a professional" close
2. **Patient books an appointment** → form submission → admin sees a `PENDING` row
3. **Patient sets a medication reminder** → form submission → reminder row created
4. **Patient mentions an emergency symptom** → AI escalates to urgent care messaging
5. **Clinic admin reviews the day's bookings** → Django admin, filtered by status + date

---

## 11. Success Metrics

For an MVP, "success" is functional, not commercial. Real product-market-fit metrics come later.

### Build success (the only metrics that matter for v1)
- ✅ Live URL is accessible from any browser
- ✅ A stranger can complete all three core flows without help
- ✅ Emergency keywords reliably produce escalation messaging (tested with all 7 from the safety spec)
- ✅ Django admin shows real data from real user submissions
- ✅ The 13 Definition-of-Done items in `implementation-plan.md` are all checked

### Stretch metrics (post-launch, qualitative)
- A clinical professional reviews the chat behavior and says "I'd let a patient use this for routine questions"
- A non-technical friend can use the product on their phone without instructions
- The final demo post receives substantive engagement (comments, not just likes) from at least one developer / hiring manager / founder

---

## 12. Risks and Assumptions

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| AI provider produces unsafe medical advice despite the system prompt | Medium | High | Defense-in-depth: explicit emergency keyword detection in `ai_service.py` *before* the LLM sees the message; system prompt re-enforces refusal of diagnosis/prescription; safety_category persisted for audit |
| Provider rate limits / cost overruns during dev | Medium | Medium | Use the cheapest model (Claude Haiku / GPT-4o-mini) during dev; set a hard daily spend cap in the provider console; log every call |
| Scope creep into v2 features during the four-week build | High | High | Section 7 (Out of Scope) is the canonical reference; check every "should we add X?" against it |
| Postgres setup pain on Windows blocking Week 1 | Medium | Low | Docker Postgres fallback documented in `implementation-plan.md` |
| Deployment failure on first Render deploy | High | Low | Expected — Week 4 Day 4 explicitly budgets time for first-deploy debugging |
| The user (builder) overcommits and misses LinkedIn cadence | Medium | Medium | `linkedin-calendar.md` rule: missed-by-a-week → skip, don't catch up |
| Safety regression in late-stage UI changes | Low | High | Emergency-keyword tests are written Day 1 of Week 3 AI work, not Day 7 |

### Assumptions
- The user has reliable internet access during the build window.
- Render's free tier remains available with PostgreSQL.
- Claude API access is available in the user's region.
- No regulatory compliance burden (HIPAA, GDPR healthcare clauses, etc.) applies — this is a portfolio/MVP project, not a deployed-to-real-patients product. The README must state this clearly.

---

## 13. Future Enhancements (v2 backlog)

Parked, ordered by likely priority:

1. **User authentication** — Patient and clinic-admin login; tie appointments/reminders to user accounts
2. **SMS reminder delivery** — Africa's Talking / Twilio integration
3. **Email reminder delivery**
4. **Multilingual support** — Swahili first, then expand
5. **Better triage flows** — structured decision trees layered on top of the AI chat
6. **Clinic admin dashboard** — custom (not just Django admin) with metrics, filters, bulk actions
7. **Appointment status workflow** — auto-confirmation, cancellation flow, reschedule
8. **Patient profile management** — medical history (not full EMR), allergies, current medications
9. **Role-based access control** — clinic admin vs. clinical officer vs. read-only
10. **Audit logs** — who saw what, when (compliance-ready)
11. **Analytics dashboard** — query volume, common symptoms, peak hours
12. **Integration with clinic management systems** — for clinics that already use one
13. **Native mobile apps** — iOS + Android
14. **Voice interface** — for patients with low literacy

---

## Document conventions

- **Status terms:** `Draft`, `Approved`, `Frozen` (Frozen means no changes during the four-week build)
- **Cross-references:** `implementation-plan.md`, `solution-design-document.md`, `user-journeys.md`, `database-design.md`, `api-design.md`, `branding.md`
- **Decisions log:** When a requirement changes mid-build, add an entry at the bottom of this doc with the date, what changed, and why. Don't quietly edit and re-commit.

## Decision log

| Date | Change | Why |
|---|---|---|
| 2026-05-17 | Initial draft | Foundation document for the four-week MVP build |
