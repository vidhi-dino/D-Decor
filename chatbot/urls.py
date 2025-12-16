from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('', views.chatbot_home, name='home'),
    path('api/chat/', views.ChatAPIView.as_view(), name='chat_api'),
    path('api/history/<str:session_id>/', views.chat_history, name='chat_history'),
    path('api/populate-faqs/', views.populate_faqs_view, name='populate_faqs'),
]