from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .services import search_similar_chunks
from .serializers import KnowledgeChunkSerializer

class SemanticSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.GET.get('q', '').strip()
        if not query:
            return Response({'error': 'Parâmetro de busca "q" é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            top_k = int(request.GET.get('k', 5))
        except ValueError:
            top_k = 5
            
        results = search_similar_chunks(request.user, query, top_k=top_k)
        
        data = []
        for score, chunk in results:
            serializer = KnowledgeChunkSerializer(chunk)
            chunk_data = serializer.data
            chunk_data['similarity_score'] = score
            data.append(chunk_data)
            
        return Response(data)
