from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response


def index(request):
    """Главная страница сайта (HTML)"""
    response = render(request, "main/home_pc.html")
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


@api_view(["GET"])
def home_data(request):
    """Данные для главной страницы (API)"""
    return Response({"message": "Home data endpoint"})
