import os
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.base import ContentFile
from rest_framework.test import APIClient
from rest_framework import status
from uploads.models import KnowledgeDocument
from .models import KnowledgeChunk
from .services import process_document_into_chunks

User = get_user_model()


class SemanticSearchTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="student@sampaio.ai", password="password123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Cria o documento do usuario salvando o arquivo via ContentFile do Django
        self.doc = KnowledgeDocument.objects.create(
            user=self.user,
            name="python_study.txt",
            file_type="txt",
            file_size=100,
            processing_status="pending",
        )
        self.doc.file.save(
            "python_study.txt",
            ContentFile(
                b"Python e uma linguagem de programacao incrivel para Inteligencia Artificial."
            ),
        )
        self.doc.save()

        # Processa chunks e embeddings
        process_document_into_chunks(self.doc)

    def tearDown(self):
        # Remove o arquivo de teste criado
        if self.doc.file:
            try:
                self.doc.file.delete(save=False)
            except Exception:
                pass

    def test_semantic_search_api(self):
        url = reverse("semantic-search")
        response = self.client.get(
            url,
            {
                "q": "Python e uma linguagem de programacao incrivel para Inteligencia Artificial.",
                "k": 2,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

        first_result = response.data[0]
        self.assertEqual(first_result["document_name"], "python_study.txt")
        self.assertIn("Python", first_result["content"])
        self.assertIn("similarity_score", first_result)
        self.assertGreater(first_result["similarity_score"], 0.9)
