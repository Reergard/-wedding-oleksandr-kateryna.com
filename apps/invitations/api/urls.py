from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it.
router = DefaultRouter()

app_name = 'invitations'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    # api/invitations/..
  
] + router.urls
