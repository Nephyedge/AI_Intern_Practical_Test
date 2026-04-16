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
    risk_score = 0  # Starting at 0 for cleaner math
    
    # Intent-based Base Risk
    intent_base_weights = {
        'verify_document': 30,  # High risk due to title deed fraud in Kenya
        'send_money': 20,       # Financial compliance risk
        'get_airport_transfer': 5,
        'hire_service': 10,
        'check_status': 0
    }
    risk_score += intent_base_weights.get(intent, 10)

    # Land/Title Specific Scrutiny
    if intent == 'verify_document':
        doc_type = str(entities.get('document_type', '')).lower()
        # Specific keywords that trigger high alert in Kenya
        if any(kw in doc_type for kw in ['land', 'title', 'plot', 'title deed', 'shamba']):
            risk_score += 45  # Total ~75 for land
        else:
            risk_score += 15
            
    # Financial Thresholds (Adjusted for Diaspora Remittance)
    if intent == 'send_money':
        try:
            # Cleaning the amount string (removing commas if present)
            raw_amount = str(entities.get('amount', '0')).replace(',', '')
            amount = float(raw_amount)
            
            if amount >= 1000000:   # 1M+ KES is a major AML trigger
                risk_score += 60
            elif amount >= 150000: # Standard CBK reporting threshold is ~10k USD
                risk_score += 30
            elif amount > 50000:
                risk_score += 15
        except (ValueError, TypeError):
            risk_score += 10 # Penalize for unclear financial data
            
    # Urgency & Emotional Context
    urgency = str(entities.get('urgency', '')).lower()
    if urgency in ['high', 'urgent', 'asap', 'immediately']:
        risk_score += 20  # High urgency often correlates with social engineering scams
        
    return min(risk_score, 100)

# 3. Core API Endpoint
@csrf_exempt
def process_task(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_input = data.get('request_text')
            
            if not user_input:
                return JsonResponse({'error': 'No input provided'}, status=400)

            # AI Processing
            ai_data = process_with_gemini(user_input)
            
            # Calculate Accurate Risk
            calculated_risk = calculate_risk_score(ai_data.get('intent'), ai_data.get('entities'))
            
            # Save to Database
            task = Task.objects.create(
                intent=ai_data.get('intent', 'unknown'),
                entities=ai_data.get('entities', {}),
                risk_score=calculated_risk, # Using the calculated variable
                steps=ai_data.get('steps', []),
                whatsapp_message=ai_data.get('messages', {}).get('whatsapp', ''),
                email_message=ai_data.get('messages', {}).get('email', ''),
                sms_message=ai_data.get('messages', {}).get('sms', ''),
                assigned_team=ai_data.get('employee_assignment', 'General')
            )
            
            return JsonResponse({
                'status': 'success',
                'task_code': task.task_code,
                'risk_score': calculated_risk, # Returning to UI for the color gauge
                'data': ai_data
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

# 4. Dashboard API endpoints
def get_tasks(request):
    # Fetch all tasks, ordered by newest first
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

# (Dashboard endpoints remain the same)