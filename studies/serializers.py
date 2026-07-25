from rest_framework import serializers
from .models import StudyPlan


class StudyPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyPlan
        fields = [
            "id",
            "title",
            "objective",
            "technology",
            "available_hours_per_week",
            "duration_weeks",
            "plan_content",
            "created_at",
        ]
        read_only_fields = ["id", "title", "plan_content", "created_at"]
