import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .models import Task
from .utils import process_with_gemini

# 1. Frontend View 
def index(request):
    return render(request, 'index.html')

# 2. Refined Risk Calculation Logic (Kenyan Corporate & Legal Context)
def calculate_risk_score(intent, entities):
    # 1. Base Intent Risk
    base_risks = {
        'verify_document': 35,
        'send_money': 15,
        'hire_service': 10,
        'get_airport_transfer': 5
    }
    score = base_risks.get(intent, 10)

    # 2. Currency Normalization Logic
    if intent == 'send_money':
        try:
            # Extract raw values
            raw_amount = float(str(entities.get('amount', '0')).replace(',', ''))
            currency = str(entities.get('currency', 'KES')).upper()

            # 2026 Internal Exchange Rates (Approximate for risk logic)
            exchange_rates = {
                'KES': 1,
                'USD': 130,
                'GBP': 165,
                'EUR': 140,
                'AED': 35
            }
            
            # Normalize amount to KES
            normalized_kes = raw_amount * exchange_rates.get(currency, 1)

            # 3. Dynamic Scaling based on Normalized KES
            if normalized_kes < 2000:
                score = 5 # Very low risk (e.g., $15 USD or 600 KES)
            elif normalized_kes > 1000000:
                score += 55 # High-value AML trigger
            elif normalized_kes > 100000:
                score += 25
                
        except (ValueError, TypeError):
            score += 10

    # 4. Contextual Modifiers (Land/Title Deeds)
    if intent == 'verify_document':
        doc_type = str(entities.get('document_type', '')).lower()
        if any(kw in doc_type for kw in ['land', 'title', 'plot', 'shamba']):
            score += 40

    # 5. The Urgency Multiplier (Conditional)
    urgency = str(entities.get('urgency', '')).lower()
    if urgency in ['high', 'urgent', 'asap']:
        if score > 30:
            score += 20 # Sensitive task + Urgency = Critical Risk
        elif score > 10:
            score += 10
            
    return min(score, 100)

# 3. Core API Endpoint
@csrf_exempt
def process_task(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_input = data.get('request_text')
            
            if not user_input:
                return JsonResponse({'error': 'No input provided'}, status=400)

            # 1. AI Extraction
            ai_data = process_with_gemini(user_input)
            
            # 2. Dynamic Risk Calculation (Normalizes Currency to KES)
            calculated_risk = calculate_risk_score(ai_data.get('intent'), ai_data.get('entities'))
            
            # 3. Create the Task first to get the real Task Code
            task = Task.objects.create(
                intent=ai_data.get('intent', 'unknown'),
                entities=ai_data.get('entities', {}),
                risk_score=calculated_risk,
                steps=ai_data.get('steps', []),
                assigned_team=ai_data.get('employee_assignment', 'General')
            )

            # 4. FIX: Replace AI placeholders with the real Database Task Code
            # This ensures the messages match the VN-XXXXXX code in the dashboard
            raw_whatsapp = ai_data.get('messages', {}).get('whatsapp', '')
            raw_email = ai_data.get('messages', {}).get('email', '')
            raw_sms = ai_data.get('messages', {}).get('sms', '')

            # Mapping the real code back to the model fields
            task.whatsapp_message = raw_whatsapp.replace('[Task Code]', task.task_code).replace('VN1234', task.task_code)
            task.email_message = raw_email.replace('[Task Code]', task.task_code).replace('VN1234', task.task_code)
            task.sms_message = raw_sms.replace('[Task Code]', task.task_code).replace('VN1234', task.task_code)
            
            task.save() # Final save with correct messages
            
            return JsonResponse({
                'status': 'success',
                'task_code': task.task_code,
                'risk_score': calculated_risk,
                'data': ai_data
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

# 4. Dashboard API endpoints
def get_tasks(request):
    tasks = Task.objects.all().order_by('-created_at').values(
        'id', 'task_code', 'intent', 'risk_score', 'assigned_team', 'status', 'created_at'
    )
    return JsonResponse({'tasks': list(tasks)})

@csrf_exempt
def update_task_status(request, task_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            task = Task.objects.get(id=task_id)
            task.status = data.get('status')
            task.save()
            return JsonResponse({'status': 'success'})
        except Task.DoesNotExist:
            return JsonResponse({'error': 'Task not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid method'}, status=405)