from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import StudyPlan
from .serializers import StudyPlanSerializer
from .services import generate_study_plan

class StudyPlanViewSet(viewsets.ModelViewSet):
    serializer_class = StudyPlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StudyPlan.objects.filter(user=self.request.user).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        objective = request.data.get('objective', '').strip()
        technology = request.data.get('technology', '').strip()
        
        if not objective or not technology:
            return Response(
                {'error': 'Parâmetros objective e technology são obrigatórios.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            available_hours = int(request.data.get('available_hours_per_week', 10))
            duration_weeks = int(request.data.get('duration_weeks', 4))
        except ValueError:
            available_hours = 10
            duration_weeks = 4
            
        plan = generate_study_plan(request.user, objective, technology, available_hours, duration_weeks)
        serializer = self.get_serializer(plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
