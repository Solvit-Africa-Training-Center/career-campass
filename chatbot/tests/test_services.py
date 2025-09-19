"""
Test Gemini service integration
"""
from django.test import TestCase
from unittest.mock import patch, Mock
import requests
from chatbot.services.gemini import GeminiService


class GeminiServiceTest(TestCase):
    """Test Gemini AI service integration"""
    
    def setUp(self):
        self.service = GeminiService()

    @patch('chatbot.services.gemini.requests.post')
    def test_successful_message(self, mock_post):
        """Test successful message sending to Gemini"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'candidates': [
                {'content': {'parts': [{'text': 'Great career advice!'}]}}
            ]
        }
        mock_post.return_value = mock_response
        
        result = self.service.send_message("What career should I pursue?")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['candidates'][0]['content']['parts'][0]['text'], 'Great career advice!')
        mock_post.assert_called_once()

    @patch('chatbot.services.gemini.requests.post')
    def test_api_error_handling(self, mock_post):
        """Test handling of API errors"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_post.return_value = mock_response
        
        with self.assertRaises(Exception) as context:
            self.service.send_message("Test message")
        
        self.assertIn("Invalid Gemini API key", str(context.exception))
        
    @patch('chatbot.services.gemini.requests.post')
    def test_timeout_handling(self, mock_post):
        """Test handling of request timeouts"""
        mock_post.side_effect = requests.exceptions.Timeout()
        
        with self.assertRaises(Exception) as context:
            self.service.send_message("Test message")
        
        self.assertIn("timed out", str(context.exception))

    @patch('chatbot.services.gemini.requests.post')
    def test_rate_limit_handling(self, mock_post):
        """Test handling of rate limit errors"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_post.return_value = mock_response
        
        with self.assertRaises(Exception) as context:
            self.service.send_message("Test message")
        
        self.assertIn("rate limit exceeded", str(context.exception))

    @patch('chatbot.services.gemini.requests.post')
    def test_invalid_json_response(self, mock_post):
        """Test handling of invalid JSON responses"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response
        
        with self.assertRaises(ValueError):
            self.service.send_message("Test message")

    def test_build_prompt_with_context(self):
        """Test building prompts with context"""
        message = "What should I study?"
        context = {"role": "student", "interests": ["technology"]}
        
        # This would test internal prompt building if the method was public
        # For now, we test through send_message integration
        with patch('chatbot.services.gemini.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                'candidates': [{'content': {'parts': [{'text': 'Study computer science!'}]}}]
            }
            mock_post.return_value = mock_response
            
            result = self.service.send_message(message, context)
            
            # Verify the API was called
            self.assertIsNotNone(result)
            mock_post.assert_called_once()
            
            # Verify the request body contains our message
            call_args = mock_post.call_args
            request_data = call_args[1]['json']
            self.assertIn('contents', request_data)
