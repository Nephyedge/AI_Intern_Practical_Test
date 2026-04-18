from django.contrib import admin
from django.http import HttpResponse
from django.urls import path

from assistant import views


def health_check(request):
    return HttpResponse("ok")


urlpatterns = [
    # Health Check for Render
    path("healthz", health_check, name="healthz"),
    # Admin
    path("admin/", admin.site.urls),
    # Frontend
    path("", views.index, name="index"),
    # AI Processing API (create new task)
    path("api/process/", views.process_task, name="process_task"),
    # Customer follow-up (check existing task by code)
    path("api/check-status/", views.check_status, name="check_status"),
    # Dashboard APIs
    path("api/tasks/", views.get_tasks, name="get_tasks"),
    path("api/tasks/<int:task_id>/status/", views.update_task_status, name="update_task_status"),
    # Status history (audit trail)
    path("api/tasks/<int:task_id>/history/", views.get_task_history, name="get_task_history"),
]