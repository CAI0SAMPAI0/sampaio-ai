from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Flashcard
from .serializers import FlashcardSerializer
from .services import generate_flashcards_for_document

class FlashcardViewSet(viewsets.ModelViewSet):
    serializer_class = FlashcardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Flashcard.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        document_id = request.data.get('document_id')
        if not document_id:
            return Response({'error': 'Parâmetro document_id é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
            
        flashcards = generate_flashcards_for_document(document_id, request.user)
        serializer = self.get_serializer(flashcards, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        flashcard = self.get_object()
        rating = request.data.get('rating')  # 'easy', 'medium', 'hard'
        
        if rating == 'easy':
            flashcard.box = min(5, flashcard.box + 1)
        elif rating == 'hard':
            flashcard.box = max(1, flashcard.box - 1)
            
        flashcard.reviewed_at = timezone.now()
        flashcard.save()
        
        serializer = self.get_serializer(flashcard)
        return Response(serializer.data)
