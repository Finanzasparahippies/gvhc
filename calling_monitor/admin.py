from django.contrib import admin
from .models import CallAnalysis

# Register your models here.
@admin.register(CallAnalysis)
class CallAnalysisAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at")
    readonly_fields = ("transcript", "motives", "agent_actions")