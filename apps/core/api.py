from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Profile, FAQ, FAQInteraction
from .serializers import ProfileSerializer, FAQSerializer, FAQInteractionSerializer


class ProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint for user profiles
    """
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Regular users can only see their own profile
        if self.request.user.is_staff or self.request.user.role in ['admin', 'manager']:
            return Profile.objects.all()
        return Profile.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # Ensure profile is associated with the current user
        serializer.save(user=self.request.user)


class FAQViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for FAQs (read-only)
    """
    queryset = FAQ.objects.filter(is_published=True).order_by('category', 'order')
    serializer_class = FAQSerializer
    permission_classes = [permissions.AllowAny]
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def interaction(self, request, pk=None):
        """
        Record an interaction with an FAQ
        """
        faq = self.get_object()
        
        # Set user if authenticated, otherwise None for anonymous users
        user = request.user if request.user.is_authenticated else None
        
        # Get client IP for anonymous users
        ip_address = self._get_client_ip(request) if not user else None
        
        # Create serializer with request data
        serializer = FAQInteractionSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(faq=faq, user=user, ip_address=ip_address)
            return Response({"status": "interaction recorded"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_client_ip(self, request):
        """Helper method to get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class FAQInteractionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for FAQ interactions
    """
    serializer_class = FAQInteractionSerializer
    
    def get_permissions(self):
        """
        Custom permissions:
        - List/retrieve: staff only
        - Create: anyone can create
        - Update/delete: staff only
        """
        if self.action in ['list', 'retrieve', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.AllowAny]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return FAQInteraction.objects.all()
        return FAQInteraction.objects.none() 