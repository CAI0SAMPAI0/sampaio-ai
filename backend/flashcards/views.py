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

    @action(detail=True, methods=['post'], url_path='verify-answer')
    def verify_answer(self, request, pk=None):
        import re
        import json
        from django.conf import settings
        from langchain_groq import ChatGroq
        from langchain_core.messages import HumanMessage
        
        flashcard = self.get_object()
        user_answer = request.data.get('user_answer', '').strip()
        
        if not user_answer:
            return Response({'error': 'A resposta do usuário é obrigatória.'}, status=status.HTTP_400_BAD_REQUEST)
            
        groq_key = getattr(settings, 'GROQ_API_KEY', None)
        
        if groq_key and groq_key != 'gsk_placeholder_for_development' and groq_key != "":
            try:
                llm = ChatGroq(
                    groq_api_key=groq_key,
                    model="llama-3.3-70b-versatile",
                    temperature=0.2
                )
                
                prompt = (
                    "Você é um tutor técnico avaliador. Compare a resposta enviada pelo usuário com a resposta esperada "
                    "do flashcard de programação. Determine se o raciocínio do usuário está correto ou se chega ao mesmo resultado prático, "
                    "mesmo se os termos ou a redação não forem idênticos.\n\n"
                    f"Frente do Flashcard (Pergunta): {flashcard.front}\n"
                    f"Verso do Flashcard (Resposta Correta): {flashcard.back}\n"
                    f"Resposta do Usuário: {user_answer}\n\n"
                    "Retorne APENAS um objeto JSON contendo:\n"
                    "- 'correct': true (se o raciocínio estiver correto/equivalente) ou false (caso contrário)\n"
                    "- 'score': um percentual de acerto (0 a 100) refletindo a proximidade lógica do raciocínio\n"
                    "- 'feedback': uma explicação objetiva e encorajadora do porquê está correto ou o que faltou.\n"
                    "Não adicione introduções ou explicações fora do JSON."
                )
                
                response = llm.invoke([HumanMessage(content=prompt)])
                match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    return Response(data)
            except Exception as e:
                print(f"Erro ao avaliar resposta do flashcard com IA: {e}")
                
        # Fallback/simulado caso a IA falhe
        import difflib
        ratio = difflib.SequenceMatcher(None, user_answer.lower(), flashcard.back.lower()).ratio()
        score = int(ratio * 100)
        correct = score >= 50
        
        return Response({
            'correct': correct,
            'score': score,
            'feedback': f"Feedback simulado: Sua resposta obteve {score}% de similaridade textual com a resposta esperada."
        })
