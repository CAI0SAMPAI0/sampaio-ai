from rest_framework import serializers
from .models import KnowledgeChunk


class KnowledgeChunkSerializer(serializers.ModelSerializer):
    document_name = serializers.CharField(source="document.name", read_only=True)

    class Meta:
        model = KnowledgeChunk
        fields = [
            "id",
            "document",
            "document_name",
            "content",
            "page_number",
            "created_at",
        ]
