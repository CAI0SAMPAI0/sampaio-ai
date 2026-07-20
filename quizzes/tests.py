from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from uploads.models import KnowledgeDocument
from .models import Quiz, QuizQuestion

User = get_user_model()

class QuizTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='quizstudent@sampaio.ai',
            password='password123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        self.doc = KnowledgeDocument.objects.create(
            user=self.user,
            name="book.txt",
            file_type="txt",
            file_size=100,
            processing_status="completed"
        )

    def test_generate_and_list_quiz(self):
        url = reverse('quiz-generate')
        response = self.client.post(url, {
            'document_id': self.doc.id
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('questions', response.data)
        
        # Test List
        list_url = reverse('quiz-list')
        list_response = self.client.get(list_url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)

    def test_submit_quiz(self):
        quiz = Quiz.objects.create(
            user=self.user,
            title="Django Test Quiz"
        )
        q1 = QuizQuestion.objects.create(
            quiz=quiz,
            question_text="O Django e um framework?",
            options=["Sim", "Nao"],
            correct_answer="Sim",
            explanation="Django e um framework web de alto nivel escrito em Python."
        )
        
        url = reverse('quiz-submit', args=[quiz.id])
        response = self.client.post(url, {
            'answers': {
                str(q1.id): "Sim"
            }
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['score'], 1)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(response.data['percentage'], 100)
