from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse

from chatbot.services.anti_hallucination import AntiHallucinationService

from .models import ChatSession, ChatMessage
from .serializers import (
    BotReplySerializer,
    ChatSessionSerializer,
    ChatMessageSerializer,
    SendMessageSerializer,
)
from .services.gemini import GeminiService


class ChatSessionViewSet(viewsets.ModelViewSet):
    queryset = ChatSession.objects.all()
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        description="Get full chat history for a session",
        responses={200: ChatMessageSerializer(many=True)},
    )
    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        session = self.get_object()
        messages = session.messages.order_by("timestamp")
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)

    @extend_schema(
        description="End a chat session. Marks it inactive.",
        responses={200: OpenApiResponse(description="Session ended")},
    )
    @action(detail=True, methods=["post"])
    def end(self, request, pk=None):
        session = self.get_object()
        session.is_active = False
        session.save()
        return Response({"detail": "Session ended."}, status=status.HTTP_200_OK)




class ChatMessageViewSet(viewsets.ViewSet):
	permission_classes = [IsAuthenticated]

	@extend_schema(
        description="Send a message in a chat session and receive bot reply",
        request=SendMessageSerializer,
        responses={
            200: OpenApiResponse(
                response=BotReplySerializer,
                description="Bot response with optional actions and follow-up questions",
            ),
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Session not found or inactive"),
        },
    )

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
