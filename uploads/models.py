from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class KnowledgeDocument(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pendente"),
        ("processing", "Processando"),
        ("completed", "Concluído"),
        ("failed", "Falhou"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="documents")
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/")
    file_type = models.CharField(max_length=50)
    file_size = models.IntegerField(help_text="Tamanho em bytes")
    processing_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    chunks_count = models.IntegerField(default=0)
    tags = models.CharField(
        max_length=255, blank=True, help_text="Tags separadas por vírgula"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.file_type}) - {self.processing_status}"
