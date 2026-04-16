import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def process_with_gemini(user_input):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    model_id = "llama-3.3-70b-versatile" 

    # We update the REASONING constraint to be more analytical
    system_prompt = """
    You are the Vunoh Global Assistant. You help the Kenyan diaspora manage tasks back home accurately and professionally.
    
    Analyze the user's request and return ONLY a valid JSON object.
    
    CRITICAL CONSTRAINTS:
    1. NO EMOJIS: Do not use emojis anywhere.
    2. TONE: Formal and corporate.
    3. DYNAMIC REASONING: In the 'reasoning' field, provide a step-by-step breakdown of how you arrived at the conclusion. 
       - Mention specific keywords from the user's input that triggered the 'intent'.
       - Explain why the chosen 'employee_assignment' is the most appropriate for this specific context.
       - Briefly justify why the generated 'steps' are necessary for the Kenyan legal or operational environment.

    Required JSON Schema:
    {
      "intent": "exactly one of: send_money, get_airport_transfer, hire_service, verify_document, check_status",
      "entities": {
        "amount": float or null,
        "currency": "string or null",
        "location": "string or null",
        "recipient": "string or null",
        "document_type": "string or null",
        "urgency": "high, medium, or low"
      },
      "reasoning": "Step-by-step logical breakdown of intent identification and operational choices.",
      "steps": ["Step 1", "Step 2", "Step 3", "Step 4"],
      "messages": {
        "whatsapp": "Professional summary. No emojis.",
        "email": "Formal email with Subject line: 'Task Confirmation: [Task Code]'",
        "sms": "Brief notification starting with 'Vunoh Global: [Task Code]'"
      },
      "employee_assignment": "Finance, Operations, or Legal"
    }
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            model=model_id,
            temperature=0.1, 
            response_format={"type": "json_object"} 
        )

        raw_response = chat_completion.choices[0].message.content
        return json.loads(raw_response)

    except Exception as e:
        raise Exception(f"Groq API Error: {str(e)}")