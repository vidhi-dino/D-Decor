import json
import uuid
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from .models import FAQ, ChatSession, ChatMessage
from .services import ChatbotService

def populate_initial_faqs():
    """Populate FAQ database with initial data if empty"""
    if FAQ.objects.count() > 0:
        return  # FAQs already exist
    
    faqs_data = [
        {
            "question": "What is your return policy?",
            "answer": "Our return policy allows you to request a return within 7 days of your purchase. The product must be in its original condition. Please visit your Purchase History page to start a return request.",
            "keywords": "return,policy,refund,exchange"
        },
        {
            "question": "How long does shipping take?",
            "answer": "Standard shipping usually takes 3-5 business days. Express shipping takes 1-2 business days. You can use our Shipping Calculator on the website for a more precise estimate for your pincode.",
            "keywords": "shipping,delivery,how long,time,when arrive"
        },
        {
            "question": "How can I track my order?",
            "answer": "You can track your order using the 'Track Shipment' tool on our website. You will need the tracking number that was sent to your email after your purchase was confirmed.",
            "keywords": "track,order,status,where is my package"
        },
        {
            "question": "Can I request a custom product?",
            "answer": "Yes! We have a full customization service. You can submit a request through the 'Customization' section of our website, and our vendors will provide you with quotes.",
            "keywords": "custom,customization,bespoke,made to order,special"
        },
        {
            "question": "My product arrived damaged, what do I do?",
            "answer": "We're sorry to hear that! Please initiate a return request from your Purchase History page within 7 days of delivery. Select 'Damaged Item' as the reason and upload photos of the damage.",
            "keywords": "damaged,broken,defective,issue,wrong item"
        },
        {
            "question": "How do I contact customer support?",
            "answer": "For any issues not covered here, you can reach our human helpline at support@ddecor.com or call us at +91 22 1234 5678 during business hours.",
            "keywords": "help,support,contact,human,talk to someone,phone,email"
        }
    ]
    
    for faq_data in faqs_data:
        FAQ.objects.create(
            question=faq_data['question'],
            answer=faq_data['answer'],
            keywords=faq_data['keywords'],
            is_active=True
        )

def chatbot_home(request):
    """Render the main chatbot page"""
    # Populate initial FAQs if database is empty
    populate_initial_faqs()
    return render(request, 'chatbot/index.html')

@method_decorator(csrf_exempt, name='dispatch')
class ChatAPIView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            session_id = data.get('session_id', str(uuid.uuid4()))
            
            if not user_message:
                return JsonResponse({
                    'error': 'Message cannot be empty',
                    'session_id': session_id
                }, status=400)
            
            # Get or create chat session
            session, created = ChatSession.objects.get_or_create(
                session_id=session_id
            )
            
            # Process the message using chatbot service
            chatbot_service = ChatbotService()
            response_data = chatbot_service.get_response(user_message, session)
            
            return JsonResponse({
                'response': response_data['response'],
                'session_id': session_id,
                'matched_faq_id': response_data.get('matched_faq_id'),
                'confidence': response_data.get('confidence', 0)
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def populate_faqs_view(request):
    """Manual endpoint to populate FAQs"""
    try:
        # Clear existing FAQs first
        FAQ.objects.all().delete()
        populate_initial_faqs()
        return JsonResponse({
            'success': True, 
            'message': 'FAQs populated successfully',
            'count': FAQ.objects.count()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def chat_history(request, session_id):
    """Get chat history for a session"""
    try:
        session = ChatSession.objects.get(session_id=session_id)
        messages = ChatMessage.objects.filter(session=session).order_by('timestamp')
        
        history = []
        for message in messages:
            history.append({
                'user_message': message.user_message,
                'bot_response': message.bot_response,
                'timestamp': message.timestamp.isoformat(),
            })
        
        return JsonResponse({'history': history})
    except ChatSession.DoesNotExist:
        return JsonResponse({'error': 'Session not found'}, status=404)