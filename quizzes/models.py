from django.db import models
from django.contrib.auth import get_user_model
from uploads.models import KnowledgeDocument

User = get_user_model()

class Quiz(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quizzes')
    document = models.ForeignKey(KnowledgeDocument, on_delete=models.SET_NULL, null=True, blank=True, related_name='quizzes')
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    options = models.JSONField(help_text="Lista de alternativas")
    correct_answer = models.CharField(max_length=255, help_text="Texto exato da alternativa correta")
    explanation = models.TextField(blank=True, help_text="Explicação do porquê a resposta é correta")

    def __str__(self):
        return f"Questão {self.id} de {self.quiz.title}"
