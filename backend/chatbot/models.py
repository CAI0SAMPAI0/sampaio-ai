from django.db import models
from django.contrib.auth.models import User

class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=255, default='Nova conversa')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} Conversation: {self.title}'

class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True, related_name='chats')
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username}: {self.message}'
    