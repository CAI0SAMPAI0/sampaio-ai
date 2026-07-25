from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class StudyPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="study_plans")
    title = models.CharField(max_length=255)
    objective = models.TextField()
    technology = models.CharField(max_length=100)
    available_hours_per_week = models.IntegerField(default=10)
    duration_weeks = models.IntegerField(default=4)
    plan_content = models.JSONField(
        help_text="Estrutura semanal do plano de estudos in JSON"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.technology}"


class DailyChallenge(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(
        help_text="Descrição detalhada do desafio e requisitos"
    )
    difficulty = models.CharField(
        max_length=20,
        choices=[
            ("iniciante", "Iniciante"),
            ("intermediario", "Intermediário"),
            ("avancado", "Avançado"),
        ],
    )
    initial_code = models.TextField(
        blank=True, help_text="Código inicial de modelo/esqueleto"
    )
    test_code = models.TextField(
        blank=True,
        help_text="Código de testes unitários ou assertivas para validar o funcionamento",
    )
    date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.difficulty.upper()}] {self.title} - {self.date}"


class ChallengeSubmission(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="challenge_submissions"
    )
    challenge = models.ForeignKey(
        DailyChallenge, on_delete=models.CASCADE, related_name="submissions"
    )
    code = models.TextField()
    status = models.CharField(
        max_length=20,
        default="pending",
        choices=[("pending", "Pendente"), ("passed", "Aprovado"), ("failed", "Falhou")],
    )
    execution_output = models.TextField(
        blank=True, null=True, help_text="Saída do console de execução de testes"
    )
    feedback = models.TextField(
        blank=True,
        null=True,
        help_text="Feedback da IA analisando o código, PEP8 e sugestões",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Submissão de {self.user.email} para {self.challenge.title} ({self.status})"
