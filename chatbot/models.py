from django.db import models

class FAQ(models.Model):
    question = models.TextField(help_text="The question users might ask")
    answer = models.TextField(help_text="The response to give")
    keywords = models.TextField(help_text="Comma-separated keywords for matching")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.question[:50] + "..." if len(self.question) > 50 else self.question
    
    def get_keywords_list(self):
        """Return keywords as a list"""
        return [keyword.strip().lower() for keyword in self.keywords.split(',') if keyword.strip()]

class ChatSession(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Session {self.session_id}"

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    user_message = models.TextField()
    bot_response = models.TextField()
    matched_faq = models.ForeignKey(FAQ, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Chat at {self.timestamp}"