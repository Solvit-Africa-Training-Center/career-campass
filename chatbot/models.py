from django.db import models
import uuid

class ChatSession(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user_id = models.UUIDField(db_index=True)
	role = models.CharField(max_length=20)
	created_at = models.DateTimeField(auto_now_add=True)
	last_active = models.DateTimeField(auto_now=True)
	is_active = models.BooleanField(default=True)

	def __str__(self):
		return f"Session {self.id} for user {self.user_id}"

class ChatMessage(models.Model):
	SENDER_CHOICES = [
		("user", "User"),
		("bot", "Bot"),
	]
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
	sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
	content = models.TextField()
	timestamp = models.DateTimeField(auto_now_add=True)
	gemini_response_id = models.CharField(max_length=100, blank=True, null=True)

	def __str__(self):
		return f"{self.sender} at {self.timestamp}: {self.content[:30]}..."
