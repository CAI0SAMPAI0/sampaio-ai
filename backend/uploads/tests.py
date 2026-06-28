import os
import tempfile
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import KnowledgeDocument
from knowledge_base.models import KnowledgeChunk

User = get_user_model()

@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class UploadsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@sampaio.ai',
            password='testpassword123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_single_upload_and_processing(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=True) as temp_file:
            temp_file.write(b"Introducao ao Python. Python e uma linguagem de programacao de alto nivel.")
            temp_file.seek(0)
            
            temp_file.name = "intro_python.txt"
            
            url = reverse('knowledge-document-list')
            response = self.client.post(url, {
                'file': temp_file,
                'tags': 'python,intro'
            }, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Verifica que o documento foi salvo
            self.assertEqual(KnowledgeDocument.objects.count(), 1)
            doc = KnowledgeDocument.objects.first()
            self.assertEqual(doc.name, "intro_python.txt")
            self.assertEqual(doc.file_type, 'txt')
            
            # Como CELERY_TASK_ALWAYS_EAGER=True, o processamento roda sincrono
            doc.refresh_from_db()
            self.assertEqual(doc.processing_status, 'completed')
            self.assertGreater(doc.chunks_count, 0)
            
            # Verifica que os chunks foram criados na base vetorial/relacional
            chunks = KnowledgeChunk.objects.filter(document=doc)
            self.assertEqual(chunks.count(), doc.chunks_count)
            first_chunk = chunks.first()
            self.assertIn("Python", first_chunk.content)
            self.assertEqual(len(first_chunk.embedding), 384) # 384 dimensoes

    def test_multiple_uploads_processing(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=True) as file1, \
             tempfile.NamedTemporaryFile(suffix=".md", delete=True) as file2:
            file1.write(b"TXT content notes about Django framework.")
            file1.seek(0)
            file1.name = "notes.txt"
            
            file2.write(b"Markdown content summary about DevOps.")
            file2.seek(0)
            file2.name = "summary.md"
            
            url = reverse('knowledge-document-list')
            response = self.client.post(url, {
                'files': [file1, file2],
                'tags': 'multi'
            }, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(KnowledgeDocument.objects.count(), 2)
            
            for doc in KnowledgeDocument.objects.all():
                doc.refresh_from_db()
                self.assertEqual(doc.processing_status, 'completed')
                self.assertGreater(doc.chunks_count, 0)
                self.assertTrue(KnowledgeChunk.objects.filter(document=doc).exists())

    def test_unsupported_format(self):
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=True) as temp_file:
            temp_file.write(b"Binary code")
            temp_file.seek(0)
            temp_file.name = "danger.exe"
            
            url = reverse('knowledge-document-list')
            response = self.client.post(url, {
                'file': temp_file
            }, format='multipart')
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
