# Afya Mkononi — User Journeys

> **Status:** Draft v1.0 · **Last updated:** 2026-05-17 · **Companion to:** `product-requirements-document.md`

Five named journeys covering the full v1 scope. Each is told from the user's perspective and ends in a defined system state.

---

## Journey 1: Patient asks a routine health question

**Actor:** Amina, 28, has had a mild headache for two days. Unsure if she should visit the clinic.
**Goal:** Get a sensible read on whether to come in or wait it out.

### Steps

1. **Lands on `/`.** Sees the home page with three cards: Chat, Book, Remind. Taps **Chat**.
2. **Arrives at `/chat/`.** Sees:
   - The safety disclaimer above the input: *"Afya Mkononi is not a doctor. For emergencies, call your local emergency line."*
   - Five suggested-prompt chips, including "I have a headache. What should I consider?"
3. **Taps the headache suggestion.** Text auto-fills the input. Taps Send.
4. **System processes.**
   - `POST /api/chat/` with `{message, session_id: null}`.
   - Backend creates a new `ChatSession` (UUID).
   - Persists user `ChatMessage` with `sender_type=USER`, `safety_category=NORMAL` (no emergency keyword match).
   - `AIService.generate_reply()` builds prompt with system instructions, calls Claude, gets reply.
   - Persists AI `ChatMessage` with `sender_type=AI`, `safety_category=NORMAL`.
   - Returns `{session_id, reply}` to frontend.
5. **Sees AI reply** in the AI bubble: general guidance on headaches (rest, hydration, common triggers, when to be concerned), closing with "If the headache is severe, sudden, or accompanied by other symptoms, please see a clinician."
6. **Asks a follow-up:** "Should I take painkillers?"
7. **System processes again.** AI replies with general guidance — does **not** recommend a specific medication or dosage; instead suggests speaking with a pharmacist or clinician about safe OTC options.
8. **Decides to wait it out.** Closes the tab.

### End state
- One `ChatSession` exists with `session_id = <uuid>`.
- Two user `ChatMessage` rows and two AI `ChatMessage` rows, all `safety_category=NORMAL`.
- No appointment, no reminder created.
- A clinic admin can later open Django admin and see the session if they wish.

### Safety acceptance criteria
- ✅ No diagnostic claim ("you have X")
- ✅ No specific medication recommended
- ✅ A "consult a professional" line in at least one reply

---

## Journey 2: Patient books an appointment

**Actor:** Daniel, 45, has been meaning to schedule his annual check-up.
**Goal:** Submit a booking request without phoning the clinic.

### Steps

1. **Lands on `/`.** Taps **Book Appointment**.
2. **Arrives at `/book/`.** Sees a form:
   - Patient name *
   - Phone number *
   - Email address (optional)
   - Preferred date *
   - Preferred time *
   - Reason for visit *
3. **Fills the form.** Forgets to fill phone number.
4. **Taps Submit.** Inline validation fires:
   - Phone field shows: *"Phone number is required."*
   - Form state preserved; other fields not lost.
5. **Adds phone, taps Submit.**
6. **System processes:**
   - `POST /api/appointments/` with the payload.
   - `AppointmentSerializer.is_valid()` runs.
   - Creates `Appointment` row with `status=PENDING`, auto-populated `created_at` and `updated_at`.
   - Returns `201 Created` with the appointment payload.
7. **Sees confirmation:** *"Appointment request received. The clinic will confirm with you shortly. Reference: #A-0042."*

### End state
- One `Appointment` row with `status=PENDING`, all required fields populated.
- The row is visible in Django admin, filterable by status and date.
- No SMS or email goes out — delivery is v2.

### Edge cases handled
- Missing required field → 400 with field-level error
- Date in the past → 400 with "Date must be today or later"
- Invalid phone format → 400

---

## Journey 3: Patient sets a medication reminder

**Actor:** Joyce, 62, was prescribed a new medication and worries about forgetting doses.
**Goal:** Set a daily reminder for 8am.

### Steps

1. **Lands on `/`.** Taps **Set a Reminder**.
2. **Arrives at `/remind/`.** Sees the reminder form:
   - Patient name *
   - Reminder type * (Medication / Appointment / Follow-up / Other)
   - Reminder message *
   - Reminder date *
   - Reminder time *
3. **Selects Medication.** Types "Take blood pressure medication" in the message.
4. **Picks tomorrow's date and 08:00.**
5. **Submits.**
6. **System processes:**
   - `POST /api/reminders/` with the payload.
   - Creates `Reminder` row with `status=PENDING`.
   - Returns `201 Created`.
7. **Sees confirmation:** *"Reminder saved. Note: in this MVP, reminders are stored but not yet delivered by SMS or email — that feature is coming soon."*

### End state
- One `Reminder` row with `status=PENDING`, populated fields, `reminder_type=MEDICATION`.
- Visible in Django admin.

### Important framing
The MVP explicitly does not deliver reminders. The confirmation message tells the user this so expectations are correct. This is a v1 constraint, not a bug.

---

## Journey 4: Emergency keyword detected → urgent care escalation

**Actor:** Peter, 50, suddenly experiencing severe chest pain. Reaches for his phone instead of calling for help.
**Goal:** Get any signal at all that he needs urgent help.

### Steps

1. **Lands on `/chat/` directly** (perhaps from a previous session).
2. **Types:** *"I have severe chest pain and trouble breathing."*
3. **Taps Send.**
4. **System processes:**
   - `POST /api/chat/`.
   - `AIService.generate_reply()`:
     - Pre-LLM safety check matches `severe chest pain` and `difficulty breathing` keywords.
     - `safety_category = EMERGENCY` is set immediately.
     - Builds a prompt that prepends an explicit instruction: *"This user has reported an emergency symptom. Your reply MUST advise them to seek urgent medical care immediately."*
     - Calls Claude.
   - Receives AI reply.
   - Post-LLM check verifies the reply contains escalation language (presence of "urgent" / "emergency" / "immediately"). Passes.
   - Persists messages with `safety_category=EMERGENCY` on both user and AI rows.
5. **Sees a visibly distinct reply:**
   - Accent-Green left border on the bubble (per `branding.md`)
   - Opening line: *"Please seek urgent medical care immediately."*
   - Includes guidance: call local emergency services, do not drive yourself, have someone with you if possible.
6. **(Hopefully)** Calls emergency services.

### End state
- The `ChatSession` and its messages are persisted with `safety_category=EMERGENCY`.
- In Django admin, sessions with EMERGENCY-tagged messages are sortable / filterable for clinic review.
- The product has done its job: it didn't try to diagnose or reassure; it escalated.

### Safety acceptance criteria (non-negotiable)
- ✅ Escalation language appears in the reply
- ✅ Persisted records reflect `safety_category=EMERGENCY`
- ✅ The visual treatment of the bubble communicates urgency without panic-coloring
- ✅ If the AI provider call fails, the fallback message **still** contains escalation language: *"I'm having trouble responding right now, but based on what you described, please seek urgent medical care immediately."*

### Emergency keyword list (source of truth lives in `ai_service.py`)
- severe chest pain
- difficulty breathing / trouble breathing / can't breathe
- severe bleeding
- loss of consciousness / unconscious / passed out
- stroke / stroke-like symptoms (face drooping, arm weakness, slurred speech)
- severe allergic reaction / anaphylaxis
- pregnancy danger (severe bleeding in pregnancy, no fetal movement, severe abdominal pain)
- suicide / self-harm references

The list is conservative on purpose. False positives are acceptable; false negatives are not.

---

## Journey 5: Clinic admin reviews the day's bookings

**Actor:** Faith, the clinic receptionist. Opens her laptop at 8am to see what came in overnight.
**Goal:** Review and confirm new appointments.

### Steps

1. **Navigates to `/admin/`.** Logs in with the clinic superuser credentials.
2. **Sees the Django admin dashboard** with the registered models: Appointments, Reminders, Chat sessions, Chat messages.
3. **Clicks Appointments.**
4. **Sees a list, default-ordered by `created_at` descending.** Columns: patient name, phone, preferred date, preferred time, status (`PENDING` / `CONFIRMED` / etc.).
5. **Filters by `status = PENDING`.** Now sees only new requests.
6. **Clicks into a row.**
7. **Reviews the details.** Calls the patient (out of band) to confirm.
8. **Updates `status` to `CONFIRMED`. Saves.**
9. **Returns to list. The row now shows `CONFIRMED`.**
10. **Optionally:** clicks **Chat sessions**, filters for any with `safety_category=EMERGENCY`, and follows up if appropriate.

### End state
- One `Appointment` row's `status` is updated to `CONFIRMED`.
- `updated_at` reflects the change.
- The patient is contacted out-of-band (no automated comms in v1).

### Admin features required (from FR-ADM-1..4 in the PRD)
- ✅ Sortable / filterable lists
- ✅ Search by patient name and phone
- ✅ Status field editable
- ✅ Chat sessions show inline messages

---

## Cross-journey notes

### What's deliberately missing
- **Patient log-in** — none of these journeys require it
- **Multi-step wizards** — every flow is a single page
- **Notifications back to the patient** — bookings and reminders are *captured*, not *delivered*

### Naming convention for screens
| Path | Template | Owner app |
|---|---|---|
| `/` | `core/home.html` | `core` |
| `/about/` | `core/about.html` | `core` |
| `/chat/` | `chatbot/chat.html` | `chatbot` |
| `/book/` | `appointments/book.html` | `appointments` |
| `/remind/` | `reminders/remind.html` | `reminders` |
| `/admin/` | Django admin | (built-in) |

### Mapping to FRs
| Journey | Primary FRs exercised |
|---|---|
| 1. Routine question | FR-CHAT-1..9 |
| 2. Appointment | FR-APPT-1..8 |
| 3. Reminder | FR-REM-1..5 |
| 4. Emergency | FR-CHAT-4, FR-CHAT-5, NFR-REL-1 |
| 5. Admin | FR-ADM-1..4 |

---

## Suggested-prompt set (chat page chips)

The five chips shown on `/chat/`, in order:

1. "I have a headache. What should I consider?"
2. "How do I prepare for a clinic visit?"
3. "When should I seek urgent medical care?"
4. "Can I book an appointment?"
5. "Can you remind me to take my medication?"

Tapping a chip auto-fills the input but does **not** auto-send — the user still presses Send. This gives them a chance to edit, and signals that the chips are starting points, not menu items.
