from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import ChatSession, ChatMessage
from .serializers import ChatSessionSerializer, ChatMessageSerializer, SendMessageSerializer
from .services.gemini import GeminiService
from django.utils import timezone

class ChatSessionViewSet(viewsets.ModelViewSet):
	queryset = ChatSession.objects.all()
	serializer_class = ChatSessionSerializer
	permission_classes = [IsAuthenticated]

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
		# Call Gemini API
		gemini_response = GeminiService.send_message(message, context)
		bot_reply = gemini_response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
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
