from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class StudyPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_plans')
    title = models.CharField(max_length=255)
    objective = models.TextField()
    technology = models.CharField(max_length=100)
    available_hours_per_week = models.IntegerField(default=10)
    duration_weeks = models.IntegerField(default=4)
    plan_content = models.JSONField(help_text="Estrutura semanal do plano de estudos em JSON")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.technology}"
