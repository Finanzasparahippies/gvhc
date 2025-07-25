from django.db import models

class CallRecord(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    keyword = models.CharField(max_length=255)
    detected = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.keyword} - {self.timestamp}"
    