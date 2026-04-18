import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def process_with_groq(user_input: str):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    model_id = "llama-3.3-70b-versatile"

    system_prompt = """
You are the Vunoh Global Assistant. You help Kenyan diaspora customers initiate and track tasks back home.

Return ONLY valid JSON. No markdown. No code fences. No extra keys.

INTENTS (choose exactly one):
- send_money
- get_airport_transfer
- hire_service
- verify_document
- check_status

EMPLOYEE ASSIGNMENT (choose exactly one):
- Finance
- Operations
- Legal

EMPLOYEE ASSIGNMENT RULES:
- If intent is send_money, employee_assignment MUST be Finance
- If intent is verify_document, employee_assignment MUST be Legal
- If intent is hire_service or get_airport_transfer, employee_assignment MUST be Operations
- If intent is check_status, employee_assignment MUST be Operations

URGENCY (choose exactly one):
- high
- medium
- low

REASONING REQUIREMENT (must follow exactly):
- reasoning MUST be 5–8 bullet points (as a single string with \\n line breaks).
- Each bullet must start with "- ".
- Must explicitly mention:
  1) Which exact words/phrases from the user's message triggered the intent
  2) Why the chosen intent is correct vs at least one alternative intent
  3) Which entities were extracted and why they matter operationally
  4) Why the employee_assignment is the correct team for Kenya context
  5) Any risk signals noticed (urgency, large amount, land/title, unknown recipient, etc.)
- At least 2 bullets must mention Kenyan context (fraud risk, local verification, service coordination realities).

MESSAGES REQUIREMENT (must be clearly different):
- whatsapp: conversational, concise, uses line breaks naturally, may include 1–2 relevant emojis
- email: formal, structured, includes: "Subject: Task Confirmation: [Task Code]" and full details
- sms: MUST be <= 160 characters, includes [Task Code] and key action only (no long explanation)

Rules:
- DO NOT invent a real task code. Always use the placeholder [Task Code].
- SMS must be <= 160 characters (hard limit).

OUTPUT JSON SCHEMA (exact keys):
{
  "intent": "send_money | get_airport_transfer | hire_service | verify_document | check_status",
  "entities": {
    "amount": 0.0,
    "currency": "KES|USD|GBP|EUR|AED" or null,
    "location": "string or null",
    "recipient": "string or null",
    "document_type": "string or null",
    "urgency": "high|medium|low"
  },
  "reasoning": "string (5–8 bullets, newline separated)",
  "steps": ["string", "string", "string", "string"],
  "messages": {
    "whatsapp": "string",
    "email": "string",
    "sms": "string"
  },
  "employee_assignment": "Finance|Operations|Legal"
}

SANITY CHECKS:
- Do not assume illegal or suspicious transactions.
- If the recipient looks like a restaurant/retail purchase (e.g., KFC, Amazon) and the intent is send_money, treat it as send_money only if the user explicitly says they are transferring money to that entity in Kenya.
- If the request is ambiguous, choose the closest intent and put clarification needs in entities.notes.
"""

    def call_llm():
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": user_input},
            ],
            model=model_id,
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return chat_completion.choices[0].message.content

    raw_response = call_llm()
    data = json.loads(raw_response)

    # ---- Optional enforcement: if reasoning is too short, retry once with a stronger nudge ----
    reasoning = (data.get("reasoning") or "").strip()
    bullet_count = sum(1 for line in reasoning.splitlines() if line.strip().startswith("- "))

    if bullet_count < 5:
        # One retry with explicit correction instruction
        retry_user = (
            user_input
            + "\n\nIMPORTANT: Your previous reasoning was not detailed enough. "
              "Return the same JSON schema, but ensure reasoning is 5–8 bullet points as required."
        )
        raw_response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt.strip()},
                {"role": "user", "content": retry_user},
            ],
            model=model_id,
            temperature=0.1,
            response_format={"type": "json_object"},
        ).choices[0].message.content

        data = json.loads(raw_response)

    return data