import uuid

from django.db import models

class Post(models.Model):
    post_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    media = models.JSONField(type=list, blank=True)
    caption = models.CharField(max_length=1000)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    username = models.CharField(max_length=100)
    user_id = models.CharField(max_length=100)

    def __str__(self):
        return self.id