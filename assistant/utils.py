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
    # 1. Initialize the Groq Client
    # Ensure 'GROQ_API_KEY' is in your .env file
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    # 2. Define the Model (Llama 3.3 70B is great for reasoning)
    model_id = "llama-3.3-70b-versatile" 

    # 3. Create the System Instruction
    system_prompt = """
    You are a Vunoh Global Assistant. You help the Kenyan diaspora manage tasks.
    Analyze the user's request and return ONLY a valid JSON object.
    
    The 'risk_score' field is NOT required here as it is calculated in views.py.
    
    Required JSON Schema:
    {
      "intent": "exactly one of: send_money, get_airport_transfer, hire_service, verify_document, check_status",
      "entities": {
        "amount": numeric or null,
        "currency": "string or null",
        "location": "string or null",
        "document_type": "string or null",
        "urgency": "high, medium, or low"
      },
      "steps": ["Step 1", "Step 2", "Step 3"],
      "messages": {
        "whatsapp": "Conversational, use emojis and line breaks.",
        "email": "Formal, structured professional email.",
        "sms": "Brief, under 160 characters."
      },
      "employee_assignment": "Finance, Operations, or Legal based on the intent."
    }
    """

    try:
        # 4. Request completion from Groq
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
            temperature=0.1, # Low temperature for consistent JSON
            response_format={"type": "json_object"} # Forces valid JSON
        )

        # 5. Parse and return the content
        raw_response = chat_completion.choices[0].message.content
        return json.loads(raw_response)

    except Exception as e:
        # If something goes wrong, we raise an error so views.py can catch it
        raise Exception(f"Groq API Error: {str(e)}")