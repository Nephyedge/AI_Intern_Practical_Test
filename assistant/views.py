import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import Task, TaskStatusHistory
from .utils import process_with_groq


# 1) Frontend view
def index(request):
    return render(request, "index.html")


# 2) Risk scoring (same logic you had, kept intact)
def calculate_risk_score(intent, entities):
    base_risks = {
        "verify_document": 35,
        "send_money": 15,
        "hire_service": 10,
        "get_airport_transfer": 5,
    }
    score = base_risks.get(intent, 10)

    if intent == "send_money":
        try:
            raw_val = entities.get("amount")
            if raw_val is None or raw_val == "":
                raw_val = "0"

            raw_amount = float(str(raw_val).replace(",", ""))
            currency = str(entities.get("currency", "KES")).upper()

            # Very rough normalization to KES for risk scoring purposes
            exchange_rates = {
                "KES": 1,
                "USD": 130,
                "GBP": 165,
                "EUR": 140,
                "AED": 35,
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

    if intent == "verify_document":
        doc_type = str(entities.get("document_type", "")).lower()
        if any(kw in doc_type for kw in ["land", "title", "plot", "shamba"]):
            score += 40

    urgency = str(entities.get("urgency", "")).lower()
    if urgency in ["high", "urgent", "asap"]:
        if score > 30:
            score += 20
        elif score > 10:
            score += 10

    return min(score, 100)


# 3) Core API endpoint: process a NEW task
@csrf_exempt
def process_task(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        data = json.loads(request.body or "{}")
        user_input = data.get("request_text")

        if not user_input or not str(user_input).strip():
            return JsonResponse({"error": "No input provided"}, status=400)

        # 1) AI extraction/generation
        ai_data = process_with_groq(user_input)

        intent = ai_data.get("intent", "unknown")
        entities = ai_data.get("entities", {}) or {}

        # 2) Risk score
        calculated_risk = calculate_risk_score(intent, entities)

        # 3) Create task record
        task = Task.objects.create(
            intent=ai_data.get('intent', 'unknown'),
            entities=ai_data.get('entities', {}),
            risk_score=calculated_risk,
            reasoning=ai_data.get('reasoning', ''),   # keep this
            assigned_team=ai_data.get('employee_assignment', 'General'),
            steps=ai_data.get('steps', []), 
        )

        # 4) Save messages (replace placeholders with real code)
        raw_whatsapp = (ai_data.get("messages") or {}).get("whatsapp", "") or ""
        raw_email = (ai_data.get("messages") or {}).get("email", "") or ""
        raw_sms = (ai_data.get("messages") or {}).get("sms", "") or ""

        task.whatsapp_message = (
            raw_whatsapp.replace("[Task Code]", task.task_code).replace("VN1234", task.task_code)
        )
        task.email_message = (
            raw_email.replace("[Task Code]", task.task_code).replace("VN1234", task.task_code)
        )
        task.sms_message = (
            raw_sms.replace("[Task Code]", task.task_code).replace("VN1234", task.task_code)
        )

        # Safety net: enforce SMS limit
        task.sms_message = (task.sms_message or "")[:160]

        task.save()

        # Optional: record initial status history (nice for audit trail)
        TaskStatusHistory.objects.create(
            task=task,
            from_status=None,
            to_status=task.status,
        )

        return JsonResponse(
            {
                "status": "success",
                "task_code": task.task_code,
                "risk_score": calculated_risk,
                "data": ai_data,
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# 4) Dashboard API: list tasks
def get_tasks(request):
    tasks = (
        Task.objects.all()
        .order_by("-created_at")
        .values(
            "id",
            "task_code",
            "intent",
            "risk_score",
            "assigned_team",
            "status",
            "created_at",
            "steps",
            "reasoning",
        )
    )
    return JsonResponse({"tasks": list(tasks)})


# 5) Dashboard API: update status + persist status history
@csrf_exempt
def update_task_status(request, task_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        data = json.loads(request.body or "{}")
        new_status = data.get("status")

        if new_status not in dict(Task.STATUS_CHOICES):
            return JsonResponse({"error": "Invalid status value"}, status=400)

        task = Task.objects.get(id=task_id)
        old_status = task.status

        if new_status != old_status:
            task.status = new_status
            task.save()

            TaskStatusHistory.objects.create(
                task=task,
                from_status=old_status,
                to_status=new_status,
            )

        return JsonResponse({"status": "success"})

    except Task.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# 6) Status history endpoint (optional but useful)
def get_task_history(request, task_id):
    history = (
        TaskStatusHistory.objects.filter(task_id=task_id)
        .order_by("-changed_at")
        .values("from_status", "to_status", "changed_at")
    )
    return JsonResponse({"history": list(history)})


# 7) Customer follow-up: check status by task code (implements "check_status" feature)
@csrf_exempt
def check_status(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    try:
        data = json.loads(request.body or "{}")
        task_code = (data.get("task_code") or "").strip().upper()

        if not task_code:
            return JsonResponse({"error": "task_code is required"}, status=400)

        task = Task.objects.get(task_code=task_code)

        return JsonResponse(
            {
                "status": "success",
                "task": {
                    "id": task.id,
                    "task_code": task.task_code,
                    "intent": task.intent,
                    "entities": task.entities,
                    "risk_score": task.risk_score,
                    "assigned_team": task.assigned_team,
                    "status": task.status,
                    "created_at": task.created_at,
                    "steps": task.steps,
                    "messages": {
                        "whatsapp": task.whatsapp_message,
                        "email": task.email_message,
                        "sms": task.sms_message,
                    },
                    "reasoning": task.reasoning,
                },
            }
        )

    except Task.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)