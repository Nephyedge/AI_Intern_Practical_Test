# Vunoh Global — AI Internship Practical Test

An AI-powered assistant that helps Kenyan diaspora customers initiate and track services back home: money transfers, service hires, and document verification.

**Live Demo:** https://ai-intern-practical-test.onrender.com/

---

## What It Does

Customers type a plain-English request. The system uses Groq (LLaMA 3) to extract intent and entities, calculates a risk score, generates fulfilment steps, assigns the task to the right team, and produces three confirmation messages — WhatsApp, Email, and SMS — all saved to the database and visible on a live dashboard.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | Django 6.0 |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Database | SQLite  |
| AI | Groq API — LLaMA 3 |
| Hosting | Render (gunicorn + whitenoise) |

---

## Project Structure

```
AI_Intern_Practical_Test/
├── assistant/              # Django app — models, views, prompts, risk logic
├── vunoh_backend/          # Django project settings and URLs
├── manage.py
├── requirements.txt
├── Procfile                # gunicorn entry point for Render
├── schema.sql              # Full DB dump with 29 sample tasks
├── db.sqlite3              # Local SQLite database
└── README.md
```

---

## Local Setup

**Prerequisites:** Python 3.10+, pip

```bash
# 1. Clone the repository
git clone https://github.com/Nephyedge/AI_Intern_Practical_Test.git
cd AI_Intern_Practical_Test

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create a .env file in the project root
touch .env
```

Add the following to `.env`:

```
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=your_django_secret_key_here
DEBUG=True
```

Get a free Groq API key at https://console.groq.com

```bash
# 5. Run migrations
python manage.py migrate

# 6. (Optional) Load sample data from schema.sql
sqlite3 db.sqlite3 < schema.sql

# 7. Start the development server
python manage.py runserver
```

Open http://127.0.0.1:8000 in your browser.

---

## Features

### 1. Intent Extraction
The AI identifies one of five intents from the customer's natural language input:
- `send_money`
- `get_airport_transfer`
- `hire_service`
- `verify_document`
- `check_status`

Entities extracted include: amount, currency, recipient, location, document type, and urgency.

### 2. Risk Scoring
Each task is scored 0–100 using rules grounded in the Kenyan diaspora context. See the full logic in the **Risk Scoring** section below.

### 3. Task Creation
Every request generates a unique task code (`VN-XXXXXX`), stored with status, entities, steps, messages, risk score, team assignment, and timestamp.

### 4. Step Generation
The AI generates intent-specific fulfilment steps — e.g. a money transfer gets identity verification, recipient confirmation, transfer initiation, and confirmation. A title deed verification gets document submission, Ministry of Lands search, and ownership confirmation.

### 5. Three-Format Messages
| Format | Style |
|---|---|
| WhatsApp | Conversational, line breaks|
| Email | Formal, subject line, full task details |
| SMS | Under 160 characters, task code + key action only |

### 6. Employee Assignment
| Intent | Team |
|---|---|
| `send_money` | Finance |
| `hire_service` | Operations |
| `get_airport_transfer` | Operations |
| `verify_document` | Legal |

### 7. Task Dashboard
All tasks are displayed with task code, intent, status, risk score, team assignment, and creation time. Status can be updated between Pending, In Progress, and Completed — saved to the database immediately.

---

## Risk Scoring Logic

The risk score is calculated from a combination of factors that reflect real considerations for diaspora financial and service transactions in Kenya.

**Amount thresholds (send_money):**
- Above KES 1,000,000 or USD equivalent: +50
- Above KES 100,000: +30
- Above KES 50,000: +20
- Below KES 10,000: +5

**Urgency:**
- High / urgent: +20
- Medium: +10
- Low / none: +0

**Intent type:**
- `verify_document` (title deed): +25 — land fraud is a real risk in Kenya; title deed verification carries significant legal exposure
- `verify_document` (other): +15
- `send_money`: base from amount above
- `hire_service`: +10
- `get_airport_transfer`: +5

**Document type modifier:**
- Title deed specifically: additional +20 — Karen, Kiambu, Nanyuki plots are high-value and frequently disputed

**Recipient status:**
- Unknown or unverified recipient: +10
- Named recipient with context (e.g. family member with reason): −5

**Score is capped at 100.**

This produces results like: a KES 600 low-urgency birthday transfer scores 5, a title deed verification with high urgency scores 95, and a KES 50,000,000 urgent transfer scores 100. The scoring is intentionally conservative — it errs toward flagging rather than missing a genuine risk.

---

## Decisions I Made and Why

### AI tools used
I use Groq’s Llama 3.3 70B model as my primary reasoning engine for intent extraction and task generation because it combines strong reasoning with sub-second inference speeds. This allows me to quickly interpret user inputs and generate actionable tasks while maintaining a smooth, responsive user experience.

### System prompt design
The core of the system prompt instructs the model to return only valid JSON with a fixed schema — no preamble, no explanation, no markdown fences. The schema specifies every field: `intent`, `entities` (with typed sub-fields), `risk_score`, `steps` (as an array), `whatsapp_message`, `email_message`, `sms_message`, `assigned_team`, and `reasoning`.

I included `reasoning` as an explicit field because I wanted the model to commit to an explanation of its intent classification before generating the downstream fields. This reduced hallucination on edge cases — when the model had to justify its intent choice first, the step generation and team assignment were more consistent with it.

I excluded any instruction about tone or length for the main JSON fields, because I found that adding those instructions caused the model to treat them as competing objectives and produce poorly structured output. The tone instructions are only applied inside the message generation fields where they are directly relevant.

**What I excluded deliberately:** I did not include few-shot examples in the system prompt. I tested with examples and found that Groq LLaMA 3 actually performed better without them on varied input — the examples appeared to anchor the model too rigidly to the example structure and it would misclassify requests that didn't pattern-match.

### One decision where I overrode the AI
When I first built the risk scoring, I asked Claude to suggest a scoring rubric. It suggested a simple three-tier system: low/medium/high mapped to 25/50/75. I overrode this because it produced identical scores for very different scenarios — a KES 600 birthday transfer and a KES 500,000 unknown-recipient transfer both landed at 50.

I replaced it with a component-based additive model where amount, urgency, intent type, and recipient status each contribute independently. This produces a much wider distribution (5 to 100 in practice) and gives the Finance and Legal teams genuinely useful signal. The data in `schema.sql` shows this range — task scores vary from 5 to 100 across the 29 sample records.

### One thing that didn't work as expected
The initial Groq API calls were returning responses with markdown code fences (` ```json ... ``` `) around the JSON, which caused `json.loads()` to fail silently in some cases and raise exceptions in others. I expected the model to respect the "return only valid JSON, no formatting" instruction consistently.

The fix was to add a post-processing strip in the view before parsing: `.strip().removeprefix("```json").removesuffix("```").strip()`. I also added a fallback that catches `JSONDecodeError` and returns a structured error response to the frontend rather than a 500, so the user sees a clear message instead of a crash. After adding this, I also tightened the system prompt to say "Your response must begin with `{` and end with `}` — no other characters before or after."

---

## Database

The `schema.sql` file in the repository root contains:
- Full table schema for `assistant_task` and all Django system tables
- 29 sample tasks covering all intent types with complete data: extracted entities, generated steps, all three messages, risk scores, team assignments, and AI reasoning

To inspect the schema directly:
```bash
sqlite3 db.sqlite3 ".schema assistant_task"
```

---

## Deployment

The application is deployed on Render using the `Procfile`:
```
web: gunicorn vunoh_backend.wsgi
```

Static files are served via whitenoise. The production database uses PostgreSQL (psycopg2-binary is included in requirements.txt). Environment variables `GROQ_API_KEY`, `SECRET_KEY`, and `DATABASE_URL` are set in the Render dashboard.

---

## Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your Groq API key (free at console.groq.com) |
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Set to `False` in production |
| `DATABASE_URL` | PostgreSQL URL (Render sets this automatically) |