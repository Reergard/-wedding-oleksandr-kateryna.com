from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from apps.main.utils import is_mobile_device

# Create your views here.

def index(request):
    """Главная страница сайта (HTML)"""
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    is_mobile = is_mobile_device(user_agent)
    
    template = 'main/home_mobile.html' if is_mobile else 'main/home_pc.html'
    
    response = render(request, template)
    
    # Настройка кэширования: Vary: User-Agent для правильного кэширования разных версий
    response['Vary'] = 'User-Agent'
    # Для HTML можно отключить кэш или установить короткий срок
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response

@api_view(['GET'])
def home_data(request):
    """Данные для главной страницы (API)"""
    return Response({'message': 'Home data endpoint'})
