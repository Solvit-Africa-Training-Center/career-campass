from django.contrib import admin
from .models import ChatSession, ChatMessage

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'role', 'created_at', 'is_active')
    list_filter = ('is_active', 'role', 'created_at')
    search_fields = ('user_id',)
    readonly_fields = ('id', 'created_at')
    ordering = ('-created_at',)

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'sender', 'timestamp', 'content_preview')
    list_filter = ('sender', 'timestamp')
    search_fields = ('content', 'session__user_id')
    readonly_fields = ('id', 'timestamp')
    ordering = ('-timestamp',)
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'
