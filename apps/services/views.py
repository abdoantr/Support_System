from django.shortcuts import render
from rest_framework import viewsets, permissions, filters, status
from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Service, ServiceFeature
from .serializers import ServiceSerializer, ServiceFeatureSerializer

# Create your views here.

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to edit services.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Write permissions are only allowed to admin users
        return request.user and request.user.is_staff

class ServiceFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = filters.NumberFilter(field_name="price", lookup_expr='lte')
    
    class Meta:
        model = Service
        fields = {
            'name': ['exact', 'icontains'],
            'category': ['exact'],
            'is_featured': ['exact'],
            'is_active': ['exact'],
        }

class ServiceFeatureViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows service features to be viewed or edited.
    """
    queryset = ServiceFeature.objects.all()
    serializer_class = ServiceFeatureSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    ordering = ['name']

class ServiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows services to be viewed or edited.
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = ServiceFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'price']
    ordering = ['name']
    
    def get_queryset(self):
        """
        By default, filter out inactive services for non-staff users
        """
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        return queryset
    
    @extend_schema(
        description="Get featured services",
        responses={200: ServiceSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Return a list of featured services
        """
        featured_services = self.get_queryset().filter(is_featured=True, is_active=True)
        serializer = self.get_serializer(featured_services, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description="Get services by category",
        parameters=[
            OpenApiParameter(name="category", type=str, required=True)
        ],
        responses={200: ServiceSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """
        Return services filtered by category
        """
        category = request.query_params.get('category')
        if not category:
            return Response(
                {"error": "Category parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        services = self.get_queryset().filter(category=category, is_active=True)
        serializer = self.get_serializer(services, many=True)
        return Response(serializer.data)
