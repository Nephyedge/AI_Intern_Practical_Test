from django.contrib import admin
from django.urls import path
from assistant import views 

urlpatterns = [
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