from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Quiz, QuizQuestion
from .serializers import QuizListSerializer, QuizDetailSerializer
from .services import generate_quiz_for_document

class QuizViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return QuizDetailSerializer
        return QuizListSerializer

    @action(detail=False, methods=['post'])
    def generate(self, request):
        document_id = request.data.get('document_id')
        theme = request.data.get('theme') or None
        num_questions = int(request.data.get('num_questions') or 3)
        difficulty = request.data.get('difficulty') or "Médio"
        
        if not document_id:
            return Response({'error': 'Parâmetro document_id é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
            
        quiz = generate_quiz_for_document(
            document_id=document_id,
            user=request.user,
            theme=theme,
            num_questions=num_questions,
            difficulty=difficulty
        )
        if not quiz:
            return Response({'error': 'Erro ao gerar quiz.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        serializer = QuizDetailSerializer(quiz)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        quiz = self.get_object()
        answers = request.data.get('answers', {})  # Mapeia question_id (string) -> resposta (string)
        
        results = []
        correct_count = 0
        total_questions = quiz.questions.count()
        
        for q in quiz.questions.all():
            user_ans = answers.get(str(q.id))
            is_correct = (user_ans == q.correct_answer)
            if is_correct:
                correct_count += 1
                
            results.append({
                'question_id': q.id,
                'question_text': q.question_text,
                'user_answer': user_ans,
                'correct_answer': q.correct_answer,
                'is_correct': is_correct,
                'explanation': q.explanation
            })
            
        score_pct = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        return Response({
            'score': correct_count,
            'total': total_questions,
            'percentage': score_pct,
            'results': results
        })
