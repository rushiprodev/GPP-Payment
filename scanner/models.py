from django.db import models
from django.utils import timezone

class QRCode(models.Model):
    data = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=10)
    created_at = models.DateTimeField(default=timezone.now)  # ✅ FIXED

    def __str__(self):
        return f"{self.data} - {self.mobile_number}"
