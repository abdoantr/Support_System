from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import ProfileViewSet, FAQViewSet, FAQInteractionViewSet

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'faqs', FAQViewSet, basename='faq')
router.register(r'faq-interactions', FAQInteractionViewSet, basename='faq-interaction')

# The API URLs are determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]

app_name = 'core_api'  # Add this line to register the 'core_api' namespace 