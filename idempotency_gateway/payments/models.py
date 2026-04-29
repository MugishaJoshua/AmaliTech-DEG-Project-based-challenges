from django.db import models


class IdempotencyRecord(models.Model):
    idempotency_key = models.CharField(max_length=255, unique=True)
    request_body = models.JSONField()
    response_body = models.JSONField(null=True, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    is_processing = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__ (self):
        return self.idempotency_key