from rest_framework import serializers
from .models import KnowledgeDocument


class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeDocument
        fields = [
            "id",
            "user",
            "name",
            "file",
            "file_type",
            "file_size",
            "processing_status",
            "chunks_count",
            "tags",
            "uploaded_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "file_type",
            "file_size",
            "processing_status",
            "chunks_count",
            "uploaded_at",
            "updated_at",
        ]
