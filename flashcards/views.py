from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Flashcard
from .serializers import FlashcardSerializer


class FlashcardViewSet(viewsets.ModelViewSet):
    serializer_class = FlashcardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Flashcard.objects.filter(
            user=self.request.user
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        document_id = request.data.get('document_id')
        if not document_id:
            return Response(
                {'error': 'Parâmetro document_id é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from core.tasks import generate_flashcards_task
        task = generate_flashcards_task.delay(
            document_id, request.user.id
        )
        return Response(
            {'task_id': task.id, 'status': 'processing'},
            status=status.HTTP_202_ACCEPTED
        )

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        flashcard = self.get_object()
        rating = request.data.get('rating')

        if rating == 'easy':
            flashcard.box = min(5, flashcard.box + 1)
        elif rating == 'hard':
            flashcard.box = max(1, flashcard.box - 1)

        flashcard.reviewed_at = timezone.now()
        flashcard.save()

        serializer = self.get_serializer(flashcard)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='verify-answer')
    def verify_answer(self, request, pk=None):
        flashcard = self.get_object()
        user_answer = request.data.get('user_answer', '').strip()

        if not user_answer:
            return Response(
                {'error': 'A resposta do usuário é obrigatória.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from core.tasks import verify_flashcard_answer_task
        task = verify_flashcard_answer_task.delay(
            flashcard.id, user_answer
        )
        return Response(
            {'task_id': task.id, 'status': 'processing'},
            status=status.HTTP_202_ACCEPTED
        )
