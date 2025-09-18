from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from chatbot.models import ChatSession, ChatMessage
from unittest.mock import patch

User = get_user_model()

class ChatbotAPITests(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(email='student@example.com', password='testpass')
		self.client.force_authenticate(user=self.user)
		self.session = ChatSession.objects.create(user_id=self.user.id, role='student')

	def test_create_session(self):
		url = reverse('chatsession-list')
		data = {'user_id': str(self.user.id), 'role': 'student'}
		response = self.client.post(url, data)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertIn('id', response.data)

	@patch('chatbot.services.gemini.GeminiService.send_message')
	def test_send_message(self, mock_gemini):
		mock_gemini.return_value = {
			'candidates': [{'content': {'parts': [{'text': 'Recommended: Computer Science.'}]}}],
			'id': 'mock-id'
		}
		url = reverse('chat-message-list')
		data = {
			'session_id': str(self.session.id),
			'message': 'What programs fit my interests?',
			'context': {}
		}
		response = self.client.post(url, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('reply', response.data)
		self.assertEqual(response.data['reply'], 'Recommended: Computer Science.')

	def test_get_history(self):
		ChatMessage.objects.create(session=self.session, sender='user', content='Hi', timestamp='2025-09-18T10:00:00Z')
		ChatMessage.objects.create(session=self.session, sender='bot', content='Hello!', timestamp='2025-09-18T10:00:01Z')
		url = reverse('chatsession-history', args=[str(self.session.id)])
		response = self.client.get(url)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 2)
		self.assertEqual(response.data[0]['content'], 'Hi')
		self.assertEqual(response.data[1]['content'], 'Hello!')
