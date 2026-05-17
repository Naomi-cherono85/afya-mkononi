# Afya Mkononi — LinkedIn Calendar

> 12 posts over 4 weeks. 3 per week: Monday (build update), Wednesday (technical learning), Friday (proof / reflection / demo). Drafts are in `linkedin-posts.md`.

---

## The cadence rule

| Day | Post type | Purpose | Hiring signal |
|---|---|---|---|
| **Mon** | Build update | What I built / shipped this week | Consistency + execution |
| **Wed** | Technical learning | One concept I applied with depth | Technical understanding |
| **Fri** | Proof / reflection / demo | Screenshot, fix, lesson, or demo | Problem-solving + shipping |

A post is ready to publish when it has **at least 3** of:
- Clear progress update
- Specific technical detail (named file, model, endpoint)
- Visual asset (screenshot / diagram / code / demo)
- Lesson learned
- Next step
- Relevant hashtags (4-7)
- Professional tone — no "just" or "only learning" framing

---

## The 4-week calendar

### Week 1 — Foundation + Product Docs (May 18 – May 24)

| # | Date | Day | Type | Topic | Asset to capture | Hiring signal |
|---|---|---|---|---|---|---|
| 1 | Mon May 18 | Mon | Build Update | Introducing Afya Mkononi | Brand banner / one-line product graphic | Product ambition |
| 2 | Wed May 20 | Wed | Technical Learning | Why I'm starting with a PRD | Screenshot of `docs/product-requirements-document.md` outline | Requirements thinking |
| 3 | Fri May 22 | Fri | Proof | Solution Design + architecture diagram | Architecture sketch (text or hand-drawn) | Technical planning |

### Week 2 — Backend foundation (May 25 – May 31)

| # | Date | Day | Type | Topic | Asset to capture | Hiring signal |
|---|---|---|---|---|---|---|
| 4 | Mon May 25 | Mon | Build Update | Django + PostgreSQL wired up; 5 apps scaffolded | Screenshot of `INSTALLED_APPS` or admin login | Backend foundation |
| 5 | Wed May 27 | Wed | Technical Learning | Designing the Appointment model | Code snippet of the model + admin | Data modeling |
| 6 | Fri May 29 | Fri | Proof | First DRF endpoint live | DRF browsable API screenshot + curl response | API capability |

### Week 3 — UI + AI Integration (Jun 1 – Jun 7)

| # | Date | Day | Type | Topic | Asset to capture | Hiring signal |
|---|---|---|---|---|---|---|
| 7 | Mon Jun 1 | Mon | Build Update | Chatbot UI is live (stubbed AI) | Chat page screenshot | Frontend awareness |
| 8 | Wed Jun 3 | Wed | Technical Learning | The AI service layer + safety prompt | `ai_service.py` code snippet + system prompt excerpt | Responsible AI |
| 9 | Fri Jun 5 | Fri | Proof | A bug I fixed this week | Before/after code or terminal screenshot | Problem-solving |

### Week 4 — Test, Deploy, Demo (Jun 8 – Jun 14)

| # | Date | Day | Type | Topic | Asset to capture | Hiring signal |
|---|---|---|---|---|---|---|
| 10 | Mon Jun 8 | Mon | Build Update | Testing the core flows | Testing checklist screenshot | Quality mindset |
| 11 | Wed Jun 10 | Wed | Technical Learning | Deploying Django + Postgres to Render | Live URL screenshot or deploy log | Shipping ability |
| 12 | Fri Jun 12 | Fri | Final Demo | **Afya Mkononi MVP is live** | 60-90s demo video, GitHub link, live link | Portfolio proof + job CTA |

---

## Asset prep checklist (do these BEFORE the post is due)

For each week, capture assets *while* you're building — not the night before posting.

### Week 1
- [ ] Simple brand banner (Canva, 1200×628)
- [ ] PRD outline screenshot (just the headings list)
- [ ] Architecture diagram — text-based in a code block works fine; or sketch on paper and photograph

### Week 2
- [ ] Screenshot of project tree in IDE (shows the 5 apps)
- [ ] Screenshot of `models.py` for Appointment (with status choices visible)
- [ ] Screenshot of DRF browsable API at `/api/appointments/`
- [ ] Terminal screenshot of successful `curl POST`

### Week 3
- [ ] Chat page screenshot (mobile + desktop)
- [ ] `ai_service.py` code snippet (the class structure, not the full code)
- [ ] Excerpt of the system prompt (with the safety rules visible)
- [ ] Bug fix screenshot — git diff or terminal output of failing → passing test

### Week 4
- [ ] Filled-in testing checklist
- [ ] Live URL screenshot (in browser, with URL bar visible)
- [ ] **Demo video** — 60-90s, screen recording, no need for narration; captions optional. Show: home → chat (one normal question + one emergency keyword) → book appointment → set reminder → quick admin view
- [ ] Final post graphic (optional but helps — Canva, project-summary style)

---

## Hashtag sets

Use **4-7 per post**. Mix from the relevant set.

**Core (always 3 of these):**
`#BuildInPublic` `#Python` `#Django` `#PostgreSQL` `#SoftwareDevelopment` `#HealthTech` `#AI`

**Backend-heavy posts:**
`#BackendDevelopment` `#DjangoRESTFramework` `#APIDesign`

**AI-heavy posts:**
`#ResponsibleAI` `#AIDevelopment` `#AIIntegration`

**Job-search posts (use sparingly — final demo only):**
`#SoftwareEngineering` `#EntryLevelDeveloper` `#TechCareers` `#WomenInTech` `#OpenToWork`

---

## CTA discipline

Every post ends with a soft close. **Only Post 12** uses the hard "I'm open to roles" CTA.

| Post # | CTA strength |
|---|---|
| 1-3 | Soft: "Next, I'll work on [X]" |
| 4-6 | Soft: "Next, I'll work on [X]" |
| 7-9 | Soft: "Next, I'll work on [X]" |
| 10-11 | Soft: "Next, I'll work on [X]" |
| **12** | **Hard:** "I'm open to entry-level developer roles, internships, apprenticeships — Python, Django, PostgreSQL, AI-enabled development." |

This isn't fake humility — it's CTA fatigue management. If every post begs for a job, none of them land. By Post 12, anyone who's been reading the journey already knows the score.

---

## Engagement plan (do this weekly, not just on post days)

Spend ~20 minutes/week commenting substantively on posts by:

- Software engineers (any stack — but especially Python/Django folks)
- Engineering managers + tech leads
- Tech recruiters (selectively — not every recruiter post)
- Startup founders (especially HealthTech)
- Other build-in-public folks

**What "substantive" means:** A comment that adds an idea, asks a real question, or references your own build. Not "Great post!" — that's noise.

**Template:** "This resonates. While building Afya Mkononi (an AI healthcare assistant), I'm running into [related thing]. Curious how you handled [specific aspect]."

This is what turns posts → DMs → conversations → interviews.

---

## Profile prep (do this before Post 1)

Before Monday May 18, the LinkedIn profile should already say:

**Headline:**
`Software Developer | Python, Django, PostgreSQL | Building AI-Powered HealthTech`

**About section opening line:**
> I'm a software developer focused on backend and AI-enabled product development. I'm currently building **Afya Mkononi**, an AI-powered healthcare assistant, in public — using Python, Django, PostgreSQL, and a clean service-layer architecture for AI integration.

**Featured section:** add as they exist
- GitHub repo (after Mon May 18)
- PRD/SDD link (after Fri May 22)
- Live demo (after Thu Jun 11)
- Final demo post (after Fri Jun 12)

---

## What to do if you miss a post

- **Missed by a day:** post it the next day. No apologies in the post itself.
- **Missed by a week:** skip that post entirely; pick up the next week's cadence. Don't double-post.
- **Missed the final demo:** finish the MVP first; the demo post is non-negotiable.

Consistency beats catching up. A 11-of-12 streak with a clean ending beats 12-of-12 with a panicky catch-up.
