from django.db import models

# Create your models here.
class CandleJson(models.Model):
    symbol = models.CharField(max_length=20)
    timestamp = models.DateField()
    data = models.JSONField()

    class Meta:
        unique_together = ['symbol', 'timestamp']

    def __str__(self):
        return f"{self.symbol} - {self.timestamp}"