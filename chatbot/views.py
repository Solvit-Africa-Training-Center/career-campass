from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import ChatSession, ChatMessage
from .serializers import ChatSessionSerializer, ChatMessageSerializer, SendMessageSerializer
from .services.gemini import GeminiService
from .services.anti_hallucination import AntiHallucinationService
from django.utils import timezone

class ChatSessionViewSet(viewsets.ModelViewSet):
	queryset = ChatSession.objects.all()
	serializer_class = ChatSessionSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		return ChatSession.objects.filter(user_id=self.request.user.id)

	def perform_create(self, serializer):
		serializer.save(user_id=self.request.user.id)

	@action(detail=True, methods=['get'])
	def history(self, request, pk=None):
		session = self.get_object()
		messages = session.messages.order_by('timestamp')
		serializer = ChatMessageSerializer(messages, many=True)
		return Response(serializer.data)

	@action(detail=True, methods=['post'])
	def end(self, request, pk=None):
		session = self.get_object()
		session.is_active = False
		session.save()
		return Response({'detail': 'Session ended.'}, status=status.HTTP_200_OK)

class ChatMessageViewSet(viewsets.ViewSet):
	permission_classes = [IsAuthenticated]

	def create(self, request):
		serializer = SendMessageSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		session_id = serializer.validated_data['session_id']
		message = serializer.validated_data['message']
		context = serializer.validated_data.get('context', {})

		session = get_object_or_404(ChatSession, pk=session_id, is_active=True)
		# Save user message
		user_msg = ChatMessage.objects.create(
			session=session,
			sender='user',
			content=message,
			timestamp=timezone.now()
		)
		
		try:
			# Call Gemini API with error handling
			# Create verified context (minimal for now)
			verified_context = f"User session ID: {session_id}"
			
			# Create anti-hallucination prompt
			safe_prompt = AntiHallucinationService.create_anti_hallucination_prompt(
				message, verified_context
			)
			
			gemini_response = GeminiService.send_message(safe_prompt)
			
			# Safely parse the response
			try:
				candidates = gemini_response.get('candidates', [])
				if candidates:
					content = candidates[0].get('content', {})
					parts = content.get('parts', [])
					if parts:
						raw_response = parts[0].get('text', 'I apologize, but I couldn\'t generate a response. Please try again.')
					else:
						raw_response = 'I apologize, but I couldn\'t generate a response. Please try again.'
				else:
					raw_response = 'I apologize, but I couldn\'t generate a response. Please try again.'
				
				# Validate response for hallucination
				is_valid, final_response, hallucination_patterns = AntiHallucinationService.validate_response(
					raw_response, {"session_id": session_id}
				)
				
				if not is_valid:
					print(f"🚨 BLOCKED HALLUCINATED RESPONSE: {hallucination_patterns}")
					bot_reply = final_response
				else:
					bot_reply = final_response
					
			except (AttributeError, TypeError):
				bot_reply = 'I apologize, but I couldn\'t process the response properly. Please try again.'
				
		except Exception as e:
			# Log the error and provide a user-friendly message
			print(f"Gemini API error: {str(e)}")
			bot_reply = 'I\'m currently experiencing technical difficulties. Please try again in a few moments.'
			gemini_response = {}

		# Save bot message
		bot_msg = ChatMessage.objects.create(
			session=session,
			sender='bot',
			content=bot_reply,
			timestamp=timezone.now(),
			gemini_response_id=gemini_response.get('id')
		)
		return Response({
			'reply': bot_reply,
			'actions': gemini_response.get('actions', []),
			'follow_up_questions': gemini_response.get('follow_up_questions', [])
		}, status=status.HTTP_200_OK)
