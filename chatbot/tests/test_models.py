"""
Test chatbot models functionality
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from chatbot.models import ChatSession, ChatMessage

User = get_user_model()


class ChatSessionModelTest(TestCase):
    """Test ChatSession model"""
    
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
        self.assertEqual(session.role, 'student')
        
    def test_chat_session_defaults(self):
        """Test ChatSession default values"""
        session = ChatSession.objects.create(
            user_id=self.user.id,
            role='student'
        )
        
        self.assertTrue(session.is_active)
        self.assertIsNotNone(session.created_at)
        self.assertIsNotNone(session.last_active)


class ChatMessageModelTest(TestCase):
    """Test ChatMessage model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.session = ChatSession.objects.create(
            user_id=self.user.id,
            role='student'
        )
        
    def test_chat_message_creation(self):
        """Test ChatMessage model creation"""
        message = ChatMessage.objects.create(
            session=self.session,
            sender='user',
            content='Hello, I need career advice!'
        )
        
        self.assertEqual(message.session, self.session)
        self.assertEqual(message.sender, 'user')
        self.assertEqual(message.content, 'Hello, I need career advice!')
        self.assertTrue('Hello, I need career advice!' in str(message))
        
    def test_message_sender_choices(self):
        """Test that message sender accepts valid choices"""
        # Test user message
        user_message = ChatMessage.objects.create(
            session=self.session,
            sender='user',
            content='User message'
        )
        self.assertEqual(user_message.sender, 'user')
        
        # Test bot message
        bot_message = ChatMessage.objects.create(
            session=self.session,
            sender='bot',
            content='Bot response'
        )
        self.assertEqual(bot_message.sender, 'bot')
        
    def test_message_ordering(self):
        """Test that messages are ordered by timestamp"""
        message1 = ChatMessage.objects.create(
            session=self.session,
            sender='user',
            content='First message'
        )
        message2 = ChatMessage.objects.create(
            session=self.session,
            sender='bot',
            content='Second message'
        )
        
        messages = self.session.messages.all()
        self.assertEqual(list(messages), [message1, message2])
