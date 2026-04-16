import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

def process_with_gemini(user_input):
    """
    Using Groq for sub-second inference speed. 
    Function name kept as 'process_with_gemini' to avoid breaking views.py.
    """
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    model_id = "llama-3.3-70b-versatile" 

    # 3. Create the System Instruction (Updated for Professional Tone)
    system_prompt = """
    You are a Vunoh Global Assistant. You help the Kenyan diaspora manage tasks back home.
    Analyze the user's request and return ONLY a valid JSON object.
    
    CRITICAL MESSAGE RULES:
    1. STERNLY FORBIDDEN: Do not use any emojis or informal greetings (e.g., 'Hey', '🤑').
    2. TONE: Highly professional, corporate, and reliable.
    3. WHATSAPP FORMAT: Must include the Amount and Currency clearly. 
       Example: 'Your request to send [Amount] [Currency] to [Recipient] has been received. Task Code: [Task Code].'
    4. EMAIL: Subject line must be 'Task Confirmation: [Task Code]'. Use a formal letter structure: 'Dear [Customer Name],' then a body paragraph, then 'Regards, Vunoh Global Support'.
    5. SMS: Maximum 160 characters. Format must be: "Vunoh Global: [Task Code]. Request to send [Amount] [Currency] to [Recipient Name] is [Status]. Details: [Link/Action]."

    Required JSON Schema:
    {
      "intent": "send_money, get_airport_transfer, hire_service, verify_document, check_status",
      "entities": {"amount": float, "currency": "string", "location": "string", "document_type": "string", "urgency": "string"},
      "steps": ["Step 1", "Step 2", "Step 3"],
      "messages": {
        "whatsapp": "Professional status update regarding the specific request. No emojis.",
        "email": "Full formal email with Subject, Salutation, Body, and Sign-off.",
        "sms": "Concise notification under 160 chars starting with 'Vunoh Global:'"
      },
      "employee_assignment": "Finance, Operations, or Legal"
    }
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_input,
                }
            ],
            model=model_id,
            temperature=0.1, 
            response_format={"type": "json_object"}
        )

        raw_response = chat_completion.choices[0].message.content
        return json.loads(raw_response)

    except Exception as e:
        raise Exception(f"Groq API Error: {str(e)}")