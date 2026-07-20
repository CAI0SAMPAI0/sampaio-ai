from rest_framework import serializers
from .models import Quiz, QuizQuestion

class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = ['id', 'question_text', 'options', 'explanation']  # Oculta correct_answer na consulta padrão

class QuizDetailSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)
    document_name = serializers.CharField(source='document.name', read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'document', 'document_name', 'title', 'questions', 'created_at']

class QuizListSerializer(serializers.ModelSerializer):
    document_name = serializers.CharField(source='document.name', read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'document', 'document_name', 'title', 'created_at']
