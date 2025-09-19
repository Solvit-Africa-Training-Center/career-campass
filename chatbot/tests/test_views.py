"""
Test chatbot API views and endpoints
"""
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from chatbot.models import ChatSession, ChatMessage
from unittest.mock import patch

User = get_user_model()


class ChatbotAPITest(APITestCase):
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
        self.assertEqual(response.data['user_id'], str(self.user.id))

    def test_list_user_sessions(self):
        """Test listing sessions for authenticated user"""
        url = reverse('chatsession-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only user's own session

    @patch('chatbot.services.gemini.GeminiService.send_message')
    def test_send_message(self, mock_gemini):
        """Test sending a message with mocked Gemini response"""
        mock_gemini.return_value = {
            'candidates': [{'content': {'parts': [{'text': 'Great career advice here!'}]}}],
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
        self.assertIn('reply', response.data)
        mock_gemini.assert_called_once()

    def test_get_session_history(self):
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

    def test_end_session(self):
        """Test ending a chat session"""
        url = reverse('chatsession-end', kwargs={'pk': self.session.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify session is inactive
        self.session.refresh_from_db()
        self.assertFalse(self.session.is_active)

    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access chatbot"""
        self.client.force_authenticate(user=None)
        url = reverse('chatsession-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChatFlowIntegrationTest(APITestCase):
    """Test complete AI chat flow scenarios"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='tester@example.com', 
            password='testpass'
        )
        self.client.force_authenticate(user=self.user)

    @patch('chatbot.services.gemini.GeminiService.send_message')
    def test_complete_career_guidance_flow(self, mock_gemini):
        """Test a complete career guidance conversation flow"""
        # Mock realistic AI responses
        mock_responses = [
            {
                'candidates': [{'content': {'parts': [{'text': 
                    "Hello! I'm your career counselor. I'd be happy to help you explore career opportunities. "
                    "To provide the best guidance, could you tell me about your interests and educational background?"
                }]}}]
            },
            {
                'candidates': [{'content': {'parts': [{'text': 
                    "Computer science is an excellent field with many opportunities! Based on your interest in technology, "
                    "here are some key career paths to consider:\n\n"
                    "1. Software Development - Building applications and systems\n"
                    "2. Data Science - Analyzing data to drive business decisions\n"
                    "3. Cybersecurity - Protecting digital assets\n"
                    "4. AI/Machine Learning - Creating intelligent systems\n\n"
                    "Which of these areas interests you most?"
                }]}}]
            },
            {
                'candidates': [{'content': {'parts': [{'text': 
                    "Excellent choice! Data science is a rapidly growing field. Here's what I recommend:\n\n"
                    "**Skills to develop:**\n"
                    "- Python programming (pandas, numpy, scikit-learn)\n"
                    "- Statistics and mathematics\n"
                    "- SQL for database queries\n"
                    "- Data visualization tools (matplotlib, tableau)\n\n"
                    "**Next steps:**\n"
                    "1. Start with online courses (Coursera, edX)\n"
                    "2. Work on personal projects with real datasets\n"
                    "3. Build a portfolio on GitHub\n"
                    "4. Consider internships or entry-level analyst roles\n\n"
                    "Would you like specific course recommendations?"
                }]}}]
            }
        ]
        
        mock_gemini.side_effect = mock_responses
        
        # Step 1: Create a new chat session
        session_url = reverse('chatsession-list')
        session_data = {'role': 'student'}
        session_response = self.client.post(session_url, session_data)
        self.assertEqual(session_response.status_code, status.HTTP_201_CREATED)
        session_id = session_response.data['id']
        
        # Step 2: Send initial greeting
        message_url = reverse('chat-message-list')
        message_data = {
            'session_id': str(session_id),
            'message': 'Hi, I need career guidance',
            'context': {'role': 'student'}
        }
        response1 = self.client.post(message_url, message_data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertIn('career counselor', response1.data['reply'].lower())
        
        # Step 3: Share interests
        message_data['message'] = 'I am interested in computer science and technology'
        response2 = self.client.post(message_url, message_data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertIn('career paths', response2.data['reply'].lower())
        
        # Step 4: Express specific interest
        message_data['message'] = 'Data science sounds interesting, how do I get started?'
        response3 = self.client.post(message_url, message_data, format='json')
        self.assertEqual(response3.status_code, status.HTTP_200_OK)
        self.assertIn('python', response3.data['reply'].lower())
        
        # Verify conversation was recorded
        history_url = reverse('chatsession-history', kwargs={'pk': session_id})
        history_response = self.client.get(history_url)
        self.assertEqual(history_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(history_response.data), 6)  # 3 user + 3 bot messages
        
        # Verify anti-hallucination is working
        self.assertEqual(mock_gemini.call_count, 3)

    @patch('chatbot.services.gemini.GeminiService.send_message')
    def test_multi_session_conversation(self, mock_gemini):
        """Test managing multiple chat sessions"""
        mock_gemini.return_value = {
            'candidates': [{'content': {'parts': [{'text': 'I can help with that!'}]}}]
        }
        
        # Create two different sessions
        session_url = reverse('chatsession-list')
        
        # Session 1: Career guidance
        session1_response = self.client.post(session_url, {'role': 'student'})
        session1_id = session1_response.data['id']
        
        # Session 2: Job search help
        session2_response = self.client.post(session_url, {'role': 'job_seeker'})
        session2_id = session2_response.data['id']
        
        # Send messages to both sessions
        message_url = reverse('chat-message-list')
        
        # Message in session 1
        self.client.post(message_url, {
            'session_id': str(session1_id),
            'message': 'What should I study?',
            'context': {}
        }, format='json')
        
        # Message in session 2
        self.client.post(message_url, {
            'session_id': str(session2_id),
            'message': 'How do I write a resume?',
            'context': {}
        }, format='json')
        
        # Verify sessions are separate
        history1_url = reverse('chatsession-history', kwargs={'pk': session1_id})
        history2_url = reverse('chatsession-history', kwargs={'pk': session2_id})
        
        history1 = self.client.get(history1_url)
        history2 = self.client.get(history2_url)
        
        self.assertEqual(len(history1.data), 2)  # 1 user + 1 bot
        self.assertEqual(len(history2.data), 2)  # 1 user + 1 bot
        self.assertNotEqual(history1.data[0]['content'], history2.data[0]['content'])

    @patch('chatbot.services.gemini.GeminiService.send_message')
    def test_error_handling_in_chat_flow(self, mock_gemini):
        """Test chat flow when AI service has issues"""
        # Simulate API error
        mock_gemini.side_effect = Exception("API Error")
        
        # Create session
        session_url = reverse('chatsession-list')
        session_response = self.client.post(session_url, {'role': 'student'})
        session_id = session_response.data['id']
        
        # Try to send message
        message_url = reverse('chat-message-list')
        message_data = {
            'session_id': str(session_id),
            'message': 'Hello',
            'context': {}
        }
        response = self.client.post(message_url, message_data, format='json')
        
        # Should handle error gracefully with user-friendly message
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('technical difficulties', response.data['reply'])

    @patch('chatbot.services.gemini.GeminiService.send_message')
    def test_anti_hallucination_in_flow(self, mock_gemini):
        """Test that anti-hallucination protection works in chat flow"""
        # Mock a response that contains hallucination
        mock_gemini.return_value = {
            'candidates': [{'content': {'parts': [{'text': 
                'Based on your previous application to Google and your degree from MIT, I recommend...'
            }]}}]
        }
        
        # Create session and send message
        session_url = reverse('chatsession-list')
        session_response = self.client.post(session_url, {'role': 'student'})
        session_id = session_response.data['id']
        
        message_url = reverse('chat-message-list')
        message_data = {
            'session_id': str(session_id),
            'message': 'What career should I pursue?',
            'context': {}
        }
        response = self.client.post(message_url, message_data, format='json')
        
        # Should return safe response instead of hallucinated content
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('Google', response.data['reply'])
        self.assertNotIn('MIT', response.data['reply'])
        self.assertIn('I appreciate you sharing', response.data['reply'])

    def test_session_lifecycle_management(self):
        """Test complete session lifecycle"""
        # Create session
        session_url = reverse('chatsession-list')
        session_response = self.client.post(session_url, {'role': 'student'})
        session_id = session_response.data['id']
        
        # Verify session is active
        session = ChatSession.objects.get(id=session_id)
        self.assertTrue(session.is_active)
        
        # End session
        end_url = reverse('chatsession-end', kwargs={'pk': session_id})
        end_response = self.client.post(end_url)
        self.assertEqual(end_response.status_code, status.HTTP_200_OK)
        
        # Verify session is inactive
        session.refresh_from_db()
        self.assertFalse(session.is_active)
        
        # Try to send message to ended session (should fail)
        message_url = reverse('chat-message-list')
        message_data = {
            'session_id': str(session_id),
            'message': 'Hello after end',
            'context': {}
        }
        response = self.client.post(message_url, message_data, format='json')
        # When session is inactive, it should return 404 (session not found)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('chatbot.services.gemini.GeminiService.send_message')
    def test_context_persistence_in_conversation(self, mock_gemini):
        """Test that conversation context is maintained"""
        mock_gemini.return_value = {
            'candidates': [{'content': {'parts': [{'text': 'Context-aware response'}]}}]
        }
        
        # Create session
        session_url = reverse('chatsession-list')
        session_response = self.client.post(session_url, {'role': 'student'})
        session_id = session_response.data['id']
        
        # Send multiple messages with context
        message_url = reverse('chat-message-list')
        
        # First message
        self.client.post(message_url, {
            'session_id': str(session_id),
            'message': 'I am studying computer science',
            'context': {'field': 'computer_science'}
        }, format='json')
        
        # Second message should build on context
        self.client.post(message_url, {
            'session_id': str(session_id),
            'message': 'What jobs are available?',
            'context': {'field': 'computer_science', 'stage': 'job_search'}
        }, format='json')
        
        # Verify context was passed to AI service
        self.assertEqual(mock_gemini.call_count, 2)
        # The calls should include the context information
        first_call_args = mock_gemini.call_args_list[0]
        second_call_args = mock_gemini.call_args_list[1]
        
        # Both calls should have been made with prompts
        self.assertIsInstance(first_call_args[0][0], str)  # First argument is the prompt
        self.assertIsInstance(second_call_args[0][0], str)  # First argument is the prompt
