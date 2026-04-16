from django.contrib import admin
from django.urls import path
from django.http import HttpResponse # Add this import
from assistant import views 

# A simple function to return 200 OK
def health_check(request):
    return HttpResponse("ok")

urlpatterns = [
    # Health Check for Render
    path('healthz', health_check), # Add this line
    
    # Default Admin Route
    path('admin/', admin.site.urls),
    
    # Frontend HTML View
    path('', views.index, name='index'),
    
    # AI Processing API
    path('api/process/', views.process_task, name='process_task'),
    
    # Dashboard APIs
    path('api/tasks/', views.get_tasks, name='get_tasks'),
    path('api/tasks/<int:task_id>/status/', views.update_task_status, name='update_task_status'),
]