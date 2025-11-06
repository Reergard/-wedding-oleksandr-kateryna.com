from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Create your views here.

def index(request):
    """Главная страница сайта (HTML)"""
    return render(request, 'main/index.html')

@api_view(['GET'])
def home_data(request):
    """Данные для главной страницы (API)"""
    return Response({'message': 'Home data endpoint'})
