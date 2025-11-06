from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it.
router = DefaultRouter()
# router.register(r'status', StatusViewSet, basename='status')
# router.register(r'product', ProductViewSet, basename='product')

app_name = 'main'

# The API URLs are now determined automatically by the router.
urlpatterns = [
    # API endpoints
    path('home/', views.home_data, name='home_data'),
] + router.urls
