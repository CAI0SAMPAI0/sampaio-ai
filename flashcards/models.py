from django.db import models
from django.contrib.auth import get_user_model
from uploads.models import KnowledgeDocument

User = get_user_model()


class Flashcard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="flashcards")
    document = models.ForeignKey(
        KnowledgeDocument,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="flashcards",
    )
    front = models.TextField()
    back = models.TextField()
    box = models.IntegerField(
        default=1, help_text="Caixa para repetição espaçada (1-5)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Flashcard {self.id} - Frente: {self.front[:30]}..."
