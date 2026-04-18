# Vunoh Global — AI Internship Practical Test (AI-Powered Diaspora Assistant)

This project is an AI-powered web assistant that helps Kenyans living abroad initiate and track important tasks back home. The assistant understands a plain-English request, extracts intent + entities, scores risk, generates a structured task, assigns it to the correct internal team, and produces confirmation messages in formats customers actually use.

**Live Demo:** https://ai-intern-practical-test.onrender.com/

---

## Problem Context (Why this exists)

Kenyans in the diaspora often rely on informal channels (calls, WhatsApp, relatives) to get things done back home. Those channels are slow and provide no audit trail. This app provides:

- **Structured task creation**
- **Risk scoring grounded in real Kenya context**
- **Team routing (Finance / Operations / Legal)**
- **A dashboard + status history** for traceability
- **Customer follow-up using a task code**

Core services supported:
- Sending money
- Hiring local services (cleaners, plumbers, errands, etc.)
- Verifying documents (land titles, IDs, certificates)

---

## Tech Stack (per test requirements)

| Layer | Choice |
|---|---|
| Backend | **Django (Python)** |
| Frontend | **HTML + CSS + Vanilla JavaScript** (no frameworks) |
| Database | **SQLite** (local + included dump) |
| AI Brain | **Groq API (LLaMA 3.3 70B)** |
| Hosting | Render (Gunicorn + WhiteNoise) |

---

## Project Structure

```text
AI_Intern_Practical_Test/
├── assistant/                 # Django app: models, views, prompt, risk logic
│   ├── templates/
│   │   └── index.html         # Single-page UI: new request + dashboard + modal
│   ├── models.py              # Task + TaskStatusHistory
│   ├── views.py               # API endpoints + risk scoring + persistence
│   └── utils.py               # Groq prompt + JSON enforcement
├── vunoh_backend/             # Django project: settings + URL routing
├── manage.py
├── requirements.txt
├── Procfile                   # Render entry point (gunicorn)
├── db.sqlite3                 # Local SQLite database file (dev)
├── schema.sql                 # SQL dump: schema + sample tasks + status history
└── readme.md
```

---

## Local Setup (Run it locally)

### Prerequisites
- Python 3.10+
- pip

### 1) Clone and install dependencies
```bash
git clone https://github.com/Nephyedge/AI_Intern_Practical_Test.git
cd AI_Intern_Practical_Test

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2) Create a `.env` file
Create `.env` in the repository root:

```bash
touch .env
```

Add:

```env
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=your_django_secret_key_here
DEBUG=True
```

> Get a free Groq API key from the Groq console.

### 3) Run migrations and start the server
```bash
python manage.py migrate
python manage.py runserver
```

Open:
- http://127.0.0.1:8000

### (Optional) Load the sample database dump
If you want to load the included sample tasks into your local DB:

```bash
sqlite3 db.sqlite3 < schema.sql
```

---

## How to Use (User Flow)

### A) Create a new request
1. Go to **New Request**
2. Type a message like:
   - “I need to send KES 15,000 to my mother in Kisumu urgently.”
   - “Please verify my land title deed for the plot in Karen.”
   - “Can someone clean my apartment in Westlands on Friday?”
3. Click **Analyze & Process**

The UI displays:
- Task code (e.g., `VN-ABC123`)
- Risk score
- Intent + assigned team
- WhatsApp + Email + SMS confirmation messages

### B) Check status by task code (customer follow-up)
1. Enter a task code in the **Check status** box
2. Click **Check Status**
3. You’ll get the latest task status + messages

### C) Operations Dashboard
1. Open **Task Dashboard**
2. View all tasks (task code, intent, risk, team, status, created time)
3. Change a task status (Pending / In Progress / Completed)
4. Click any row to open details:
   - **AI Logic Analysis** (LLM reasoning)
   - **Status history** (audit trail)

---

## Feature Checklist (Mapped to the Test Spec)

### 1. User Input ✅
- Simple plain-text input on the frontend.

### 2. AI Intent Extraction ✅
The AI returns structured JSON containing:
- `intent`: one of  
  `send_money`, `get_airport_transfer`, `hire_service`, `verify_document`, `check_status`
- `entities`: extracted operational data (amount, recipient, location, document type, urgency)

### 3. Risk Scoring ✅
A 0–100 risk score is calculated and stored with each task and displayed in the UI.

### 4. Task Creation ✅
Each request creates a DB record with:
- unique task code (`VN-XXXXXX`)
- intent + entities
- risk score
- status
- created timestamp

### 5. Step Generation ✅
The AI generates a logical step sequence to fulfil the task and it is persisted to the database.

### 6. Three-Format Messages ✅
For each task, the system generates and stores:
- WhatsApp-style message (conversational, line breaks, may include emoji)
- Email-style message (formal + structured, includes task code)
- SMS-style message (<=160 chars, includes task code + key action)

All messages are:
- saved to the database
- displayed in the UI

### 7. Employee Assignment ✅
AI assigns a team category:
- `send_money` → Finance
- `hire_service` / `get_airport_transfer` → Operations
- `verify_document` → Legal

Stored in DB and visible in UI.

### 8. Task Dashboard ✅
Dashboard lists all tasks with:
- task code
- intent
- status
- risk
- assigned team
- created time

Status updates persist immediately.

### 9. Database Persistence + SQL Dump ✅
Everything is persisted:
- tasks
- extracted entities
- generated steps
- three messages
- risk scores
- assignments
- **status history**

A full SQL dump is included at repo root:
- `schema.sql` contains schema + sample tasks with complete data.

---

## Risk Scoring Logic (High-level explanation)

Risk is computed from signals that matter in Kenyan diaspora operations:

- **Money transfer amount**
  - Small transfers are low-risk
  - Large transfers increase risk substantially
  - Amounts are normalized to KES with approximate exchange rates for scoring

- **Urgency**
  - “urgent / asap / high urgency” increases risk (often associated with scams or pressure)

- **Intent-based base risk**
  - Document verification carries higher baseline risk than service hires

- **Document type modifier**
  - Land/title-related verification increases risk further due to common land fraud risk in Kenya

The score is capped at **100**.

---

## API Endpoints (for reference)

- `GET /` — UI (single page)
- `POST /api/process/` — create a new task from plain English
- `POST /api/check-status/` — check an existing task by task code
- `GET /api/tasks/` — list tasks for dashboard
- `POST /api/tasks/<id>/status/` — update status
- `GET /api/tasks/<id>/history/` — get status history audit trail
- `GET /healthz` — health check

---

## Decisions I Made and Why

### Which AI tools I used (and where)
- **Groq (LLaMA 3.3 70B)** as the main LLM:
  - intent extraction
  - entity extraction
  - step generation
  - message generation
  - employee assignment
  - reasoning generation (AI Logic Analysis)
- Used developer tooling/AI assistance during build for iteration speed and refactors (prompt tightening, UI polish, endpoint adjustments).

### System prompt design (what I included and why)
I designed the system prompt to be strict and parseable:
- JSON-only output with a fixed schema
- constrained enums for intent, urgency, and employee assignment
- explicit message formatting rules for WhatsApp / Email / SMS
- a strong **reasoning requirement**: 5–8 bullet points, each starting with `- `, covering:
  - exact trigger words
  - why the chosen intent over an alternative
  - key entities extracted and operational importance
  - why the team assignment makes sense in Kenya context
  - risk signals noticed

This reduced inconsistent outputs and made backend parsing reliable.

### What I excluded deliberately
- I avoided frontend frameworks (per instructions) and kept UI as one HTML file with vanilla JS.
- I avoided complex “employee tables” since the test explicitly allows a simplified assignment model.

### One decision where I overrode what AI suggested
Early risk scoring suggestions tended to be too generic (low/medium/high buckets). I replaced that with an additive scoring approach so risk is a real numeric spectrum (0–100) influenced by amount, urgency, and document type.

### One thing that didn’t work as expected (and how I resolved it)
Sometimes LLM outputs can be too short or skip constraints (especially reasoning detail). To fix this:
- the prompt enforces a bullet-count requirement for reasoning
- if the model output is insufficient, the backend retries once with a stricter nudge

This produced consistently detailed “AI Logic Analysis” in the dashboard.

---

## Deployment Notes
- Deployed on Render using `Procfile`:
  ```text
  web: gunicorn vunoh_backend.wsgi
  ```
- Static files served with **WhiteNoise**
- Uses environment variables:
  - `GROQ_API_KEY`
  - `SECRET_KEY`
  - `DEBUG`

---

## Deliverables Checklist
- [x] Source code in GitHub
- [x] README with setup instructions + “Decisions I made and why”
- [x] SQL dump committed in repo (`schema.sql`)
- [x] Sample tasks in SQL dump (>= 5) with complete data
- [x] Hosted link (optional): https://ai-intern-practical-test.onrender.com/