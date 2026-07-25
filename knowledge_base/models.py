from django.db import models
from uploads.models import KnowledgeDocument


class KnowledgeChunk(models.Model):
    document = models.ForeignKey(
        KnowledgeDocument, on_delete=models.CASCADE, related_name="chunks"
    )
    content = models.TextField()
    page_number = models.IntegerField(null=True, blank=True)
    embedding = models.JSONField(help_text="Vetor de embedding como lista de floats")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chunk {self.id} de {self.document.name} (Pág. {self.page_number or 'N/A'})"
