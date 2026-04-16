import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from .models import Task
from .utils import process_with_gemini

# 1. Frontend View 
def index(request):
    return render(request, 'index.html')

# 2. Refined Risk Calculation Logic
def calculate_risk_score(intent, entities):
    base_risks = {
        'verify_document': 35,
        'send_money': 15,
        'hire_service': 10,
        'get_airport_transfer': 5
    }
    score = base_risks.get(intent, 10)

    if intent == 'send_money':
        try:
            raw_val = entities.get('amount')
            if raw_val is None or raw_val == '':
                raw_val = '0'
            raw_amount = float(str(raw_val).replace(',', ''))
            currency = str(entities.get('currency', 'KES')).upper()

            exchange_rates = {
                'KES': 1, 'USD': 130, 'GBP': 165, 'EUR': 140, 'AED': 35
            }
            
            normalized_kes = raw_amount * exchange_rates.get(currency, 1)

            if normalized_kes < 2000:
                score = 5 
            elif normalized_kes > 1000000:
                score += 55 
            elif normalized_kes > 100000:
                score += 25
                
        except (ValueError, TypeError):
            score += 10

    if intent == 'verify_document':
        doc_type = str(entities.get('document_type', '')).lower()
        if any(kw in doc_type for kw in ['land', 'title', 'plot', 'shamba']):
            score += 40

    urgency = str(entities.get('urgency', '')).lower()
    if urgency in ['high', 'urgent', 'asap']:
        if score > 30:
            score += 20 
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

            # 1. AI Extraction (Now includes 'reasoning' from utils.py)
            ai_data = process_with_gemini(user_input)
            
            # 2. Dynamic Risk Calculation
            calculated_risk = calculate_risk_score(ai_data.get('intent'), ai_data.get('entities'))
            
            # 3. Create Task with Reasoning field
            task = Task.objects.create(
                intent=ai_data.get('intent', 'unknown'),
                entities=ai_data.get('entities', {}),
                risk_score=calculated_risk,
                reasoning=ai_data.get('reasoning', 'No specific analysis provided.'), # SAVING REASONING
                steps=ai_data.get('steps', []),
                assigned_team=ai_data.get('employee_assignment', 'General')
            )

            # 4. Replace placeholders with real Task Code
            raw_whatsapp = ai_data.get('messages', {}).get('whatsapp', '')
            raw_email = ai_data.get('messages', {}).get('email', '')
            raw_sms = ai_data.get('messages', {}).get('sms', '')

            task.whatsapp_message = raw_whatsapp.replace('[Task Code]', task.task_code).replace('VN1234', task.task_code)
            task.email_message = raw_email.replace('[Task Code]', task.task_code).replace('VN1234', task.task_code)
            task.sms_message = raw_sms.replace('[Task Code]', task.task_code).replace('VN1234', task.task_code)
            
            task.save() 
            
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
    # ADDED 'reasoning' to the values list so the frontend can display it
    tasks = Task.objects.all().order_by('-created_at').values(
        'id', 'task_code', 'intent', 'risk_score', 'assigned_team', 'status', 'created_at', 'steps', 'reasoning'
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