import re
from django.db.models import Q
from .models import FAQ, ChatMessage

class ChatbotService:
    def __init__(self):
        self.default_response = "I'm sorry, I couldn't find an answer to your question. Please contact our support team at support@ddecor.com or call +91 22 1234 5678 for further assistance."
        self.greeting_responses = {
            'hello': "Hello! How can I help you today?",
            'hi': "Hi there! What can I do for you?",
            'hey': "Hey! How can I assist you?",
            'good morning': "Good morning! How may I help you?",
            'good afternoon': "Good afternoon! What can I do for you?",
            'good evening': "Good evening! How can I assist you today?"
        }
    
    def preprocess_message(self, message):
        """Clean and normalize the user message"""
        # Convert to lowercase and remove extra spaces
        message = message.lower().strip()
        # Remove special characters except basic punctuation
        message = re.sub(r'[^\w\s\?\!]', '', message)
        return message
    
    def check_greetings(self, message):
        """Check if message is a greeting"""
        message_lower = message.lower().strip()
        for greeting, response in self.greeting_responses.items():
            if greeting in message_lower:
                return response
        return None
    
    def find_best_match(self, user_message):
        """Find the best matching FAQ based on keywords and question similarity"""
        processed_message = self.preprocess_message(user_message)
        words_in_message = processed_message.split()
        
        best_match = None
        max_score = 0
        
        # Get all active FAQs
        faqs = FAQ.objects.filter(is_active=True)
        
        for faq in faqs:
            score = 0
            keywords = faq.get_keywords_list()
            question_words = faq.question.lower().split()
            
            # Score based on keyword matches
            for keyword in keywords:
                if keyword in processed_message:
                    score += 3  # High weight for exact keyword match
                else:
                    # Check for partial matches
                    for word in words_in_message:
                        if keyword in word or word in keyword:
                            score += 1
            
            # Score based on question word matches
            for word in question_words:
                if len(word) > 2 and word.lower() in processed_message:
                    score += 2
            
            # Bonus for multiple word matches
            common_words = set(words_in_message) & set(question_words + keywords)
            if len(common_words) > 1:
                score += len(common_words)
            
            if score > max_score and score > 0:
                max_score = score
                best_match = faq
        
        return best_match, max_score
    
    def get_response(self, user_message, session):
        """Get chatbot response for user message"""
        # Check for greetings first
        greeting_response = self.check_greetings(user_message)
        if greeting_response:
            # Save chat message
            ChatMessage.objects.create(
                session=session,
                user_message=user_message,
                bot_response=greeting_response
            )
            return {
                'response': greeting_response,
                'confidence': 100
            }
        
        # Find best matching FAQ
        best_match, confidence = self.find_best_match(user_message)
        
        if best_match and confidence >= 2:  # Minimum confidence threshold
            response = best_match.answer
            
            # Save chat message with matched FAQ
            ChatMessage.objects.create(
                session=session,
                user_message=user_message,
                bot_response=response,
                matched_faq=best_match
            )
            
            return {
                'response': response,
                'matched_faq_id': best_match.id,
                'confidence': min(confidence * 10, 100)  # Scale confidence to percentage
            }
        else:
            # No good match found, use default response
            ChatMessage.objects.create(
                session=session,
                user_message=user_message,
                bot_response=self.default_response
            )
            
            return {
                'response': self.default_response,
                'confidence': 0
            }