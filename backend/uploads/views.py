import os
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse
from .models import KnowledgeDocument
from .serializers import KnowledgeDocumentSerializer
from .tasks import process_document_task

class KnowledgeDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = KnowledgeDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return KnowledgeDocument.objects.filter(user=self.request.user).order_by('-uploaded_at')

    def create(self, request, *args, **kwargs):
        files = request.FILES.getlist('files')
        
        # Se houver múltiplos arquivos (upload múltiplo)
        if files:
            created_docs = []
            for file_obj in files:
                ext = os.path.splitext(file_obj.name)[1].lower().replace('.', '')
                allowed_exts = ['pdf', 'docx', 'txt', 'md', 'markdown', 'csv', 'xlsx', 'pptx', 'png', 'jpg', 'jpeg']
                if ext not in allowed_exts:
                    return Response(
                        {'error': f"Formato de arquivo .{ext} não suportado."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                doc = KnowledgeDocument.objects.create(
                    user=request.user,
                    name=file_obj.name,
                    file=file_obj,
                    file_type=ext,
                    file_size=file_obj.size,
                    processing_status='pending',
                    tags=request.data.get('tags', '')
                )
                
                # Dispara processamento assíncrono via Celery
                process_document_task.delay(doc.id)
                created_docs.append(doc)
            
            serializer = self.get_serializer(created_docs, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        # Caso contrário, trata como upload único padrão
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response(
                {'error': 'Nenhum arquivo enviado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        ext = os.path.splitext(file_obj.name)[1].lower().replace('.', '')
        allowed_exts = ['pdf', 'docx', 'txt', 'md', 'markdown', 'csv', 'xlsx', 'pptx', 'png', 'jpg', 'jpeg']
        if ext not in allowed_exts:
            return Response(
                {'error': f"Formato de arquivo .{ext} não suportado."},
                status=status.HTTP_400_BAD_REQUEST
            )

        doc = KnowledgeDocument.objects.create(
            user=request.user,
            name=file_obj.name,
            file=file_obj,
            file_type=ext,
            file_size=file_obj.size,
            processing_status='pending',
            tags=request.data.get('tags', '')
        )
        
        # Dispara processamento assíncrono via Celery
        process_document_task.delay(doc.id)
        
        serializer = self.get_serializer(doc)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        if instance.file:
            try:
                if os.path.isfile(instance.file.path):
                    os.remove(instance.file.path)
            except Exception:
                pass
        instance.delete()

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        doc = self.get_object()
        response = FileResponse(doc.file.open(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{doc.name}"'
        return response
