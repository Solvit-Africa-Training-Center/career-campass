"""
Chatbot application tests
"""
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.test import TestCase
from chatbot.models import ChatSession, ChatMessage
from chatbot.services.anti_hallucination import AntiHallucinationService
from unittest.mock import patch

User = get_user_model()


class ChatbotModelsTest(TestCase):
    """Test chatbot models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
    def test_chat_session_creation(self):
        """Test ChatSession model creation"""
        session = ChatSession.objects.create(
            user_id=self.user.id,
            role='student'
        )
        
        self.assertEqual(str(session), f"Session {session.id} for user {self.user.id}")
        self.assertTrue(session.is_active)
        
    def test_chat_message_creation(self):
        """Test ChatMessage model creation"""
        session = ChatSession.objects.create(
            user_id=self.user.id,
            role='student'
        )
        
        message = ChatMessage.objects.create(
            session=session,
            sender='user',
            content='Hello, I need career advice!'
        )
        
        self.assertEqual(message.session, session)
        self.assertEqual(message.sender, 'user')
        self.assertTrue('Hello, I need career advice!' in str(message))


class AntiHallucinationTest(TestCase):
    """Test anti-hallucination service"""
    
    def test_detect_false_education_claims(self):
        """Test detection of false educational claims"""
        test_response = "You mentioned having a degree from MIT with a 3.8 GPA."
        
        is_hallucination, patterns = AntiHallucinationService.detect_hallucination(test_response)
        
        self.assertTrue(is_hallucination)
        self.assertTrue(len(patterns) > 0)
        
    def test_detect_false_work_claims(self):
        """Test detection of false work experience claims"""
        test_response = "Based on your 5 years at Google as a software engineer..."
        
        is_hallucination, patterns = AntiHallucinationService.detect_hallucination(test_response)
        
        self.assertTrue(is_hallucination)
        self.assertTrue(len(patterns) > 0)
        
    def test_safe_response_passes(self):
        """Test that safe responses are not flagged"""
        test_response = "I don't have verified information about your background. Could you tell me more?"
        
        is_hallucination, patterns = AntiHallucinationService.detect_hallucination(test_response)
        
        self.assertFalse(is_hallucination)
        self.assertEqual(len(patterns), 0)


class ChatbotAPITests(APITestCase):
    """Test chatbot API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='student@example.com', 
            password='testpass'
        )
        self.client.force_authenticate(user=self.user)
        self.session = ChatSession.objects.create(
            user_id=self.user.id, 
            role='student'
        )

    def test_create_session(self):
        """Test creating a new chat session"""
        url = reverse('chatsession-list')
        data = {'role': 'student'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)

    @patch('chatbot.services.gemini.GeminiService.send_message')
    def test_send_message(self, mock_gemini):
        """Test sending a message with mocked Gemini response"""
        mock_gemini.return_value = {
            'candidates': [{'content': {'parts': [{'text': 'Recommended: Computer Science.'}]}}],
            'id': 'mock-id'
        }
        url = reverse('chat-message-list')
        data = {
            'session_id': str(self.session.id),
            'message': 'What career should I pursue?',
            'context': {}
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_gemini.assert_called_once()

    def test_get_history(self):
        """Test getting session history"""
        # Create some messages
        ChatMessage.objects.create(
            session=self.session,
            sender='user',
            content='Hello'
        )
        ChatMessage.objects.create(
            session=self.session,
            sender='bot',
            content='Hi there!'
        )
        
        url = reverse('chatsession-history', kwargs={'pk': self.session.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)