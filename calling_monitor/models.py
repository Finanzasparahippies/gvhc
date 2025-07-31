#calling_monitor
from django.db import models

class CallRecord(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    keyword = models.CharField(max_length=255)
    detected = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.keyword} - {self.timestamp}"
    
class CallAnalysis(models.Model):
    audio_file = models.FileField(upload_to="call_audios/")
    transcript = models.TextField(blank=True)
    motives = models.JSONField(blank=True, null=True)
    unique_id = models.CharField(max_length=255, unique=True, blank=True, null=True) # Nuevo campo
    language_used = models.CharField(max_length=10, default='es', blank=True, null=True) # NEW FIELD
    agent_actions = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Llamada {self.id} - {self.created_at.strftime('%Y-%m-%d')}"