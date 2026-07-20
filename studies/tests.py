from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import StudyPlan

User = get_user_model()

class StudyPlanTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='planstudent@sampaio.ai',
            password='password123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_generate_and_list_study_plan(self):
        url = reverse('studyplan-list')
        response = self.client.post(url, {
            'objective': 'Dominar o framework Django',
            'technology': 'Django',
            'available_hours_per_week': 12,
            'duration_weeks': 6
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('plan_content', response.data)
        
        # Test List
        list_response = self.client.get(url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
