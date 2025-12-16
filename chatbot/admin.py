from django.contrib import admin
from .models import FAQ, ChatSession, ChatMessage

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question_preview', 'keywords_preview', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('question', 'keywords')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('question', 'answer', 'keywords', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def question_preview(self, obj):
        return obj.question[:50] + "..." if len(obj.question) > 50 else obj.question
    question_preview.short_description = 'Question'
    
    def keywords_preview(self, obj):
        return obj.keywords[:30] + "..." if len(obj.keywords) > 30 else obj.keywords
    keywords_preview.short_description = 'Keywords'

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'message_count', 'created_at', 'last_activity')
    list_filter = ('created_at', 'last_activity')
    search_fields = ('session_id',)
    readonly_fields = ('created_at', 'last_activity', 'message_count')
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'user_message_preview', 'matched_faq', 'timestamp')
    list_filter = ('timestamp', 'matched_faq')
    search_fields = ('user_message', 'bot_response')
    readonly_fields = ('timestamp',)
    
    def user_message_preview(self, obj):
        return obj.user_message[:50] + "..." if len(obj.user_message) > 50 else obj.user_message
    user_message_preview.short_description = 'User Message'