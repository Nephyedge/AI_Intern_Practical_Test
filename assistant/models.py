from django.db import models
from django.utils import timezone
import uuid

class Task(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]

    # Core Task Info
    task_code = models.CharField(max_length=20, unique=True, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    # LLM Extracted & Generated Data
    intent = models.CharField(max_length=100)
    entities = models.JSONField(default=dict, help_text="Stores extracted JSON data like amount, location, etc.")
    risk_score = models.IntegerField(default=0)
    steps = models.JSONField(default=list, help_text="Stores the array of logical execution steps")
    
    # Messages
    whatsapp_message = models.TextField(blank=True)
    email_message = models.TextField(blank=True)
    sms_message = models.CharField(max_length=160, blank=True)
    
    # Routing
    assigned_team = models.CharField(max_length=100)

    def save(self, *args, **kwargs):
        if not self.task_code:
            # Generate a unique task code like VN-A1B2C3
            self.task_code = f"VN-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.task_code} - {self.intent}"