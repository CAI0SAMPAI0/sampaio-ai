from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from uploads.models import KnowledgeDocument
from .models import Flashcard

User = get_user_model()


class FlashcardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="cardstudent@sampaio.ai", password="password123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.doc = KnowledgeDocument.objects.create(
            user=self.user,
            name="notes.txt",
            file_type="txt",
            file_size=100,
            processing_status="completed",
        )

    def test_create_and_list_flashcard(self):
        url = reverse("flashcard-list")
        response = self.client.post(
            url,
            {
                "document": self.doc.id,
                "front": "O que e RAG?",
                "back": "Retrieval-Augmented Generation",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_generate_flashcards(self):
        url = reverse("flashcard-generate")
        response = self.client.post(url, {"document_id": self.doc.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreater(len(response.data), 0)

    def test_review_flashcard(self):
        card = Flashcard.objects.create(
            user=self.user, front="Frente", back="Verso", box=1
        )
        url = reverse("flashcard-review", args=[card.id])
        response = self.client.post(url, {"rating": "easy"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        card.refresh_from_db()
        self.assertEqual(card.box, 2)
