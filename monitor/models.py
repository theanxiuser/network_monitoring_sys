from django.db import models


class AnomalyLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    source_ip = models.GenericIPAddressField()
    destination_ip = models.GenericIPAddressField()
    protocol = models.CharField(max_length=10)
    length = models.IntegerField()
    latency = models.FloatField()
    jitter = models.FloatField()
    packet_loss = models.FloatField()
    bandwidth = models.FloatField()

    def __str__(self):
        return f'{self.source_ip} -> {self.destination_ip}'