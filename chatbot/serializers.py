from rest_framework import serializers
from .models import ChatSession, ChatMessage

class ChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ['id', 'user_id', 'role', 'created_at', 'last_active', 'is_active']
        read_only_fields = ['user_id', 'created_at', 'last_active', 'is_active']

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'session', 'sender', 'content', 'timestamp', 'gemini_response_id']

class SendMessageSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    message = serializers.CharField()
    context = serializers.JSONField(required=False)
