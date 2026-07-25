from rest_framework import serializers
from .models import Flashcard


class FlashcardSerializer(serializers.ModelSerializer):
    document_name = serializers.CharField(source="document.name", read_only=True)

    class Meta:
        model = Flashcard
        fields = [
            "id",
            "document",
            "document_name",
            "front",
            "back",
            "box",
            "created_at",
            "reviewed_at",
        ]
        read_only_fields = ["id", "box", "created_at", "reviewed_at"]
