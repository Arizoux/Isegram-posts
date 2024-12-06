import uuid

from django.db import models

class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    media = models.JSONField(default=dict)
    caption = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    username = models.CharField(max_length=100)

    def __str__(self):
        return self.id