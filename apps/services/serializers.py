from rest_framework import serializers
from .models import Service, ServiceFeature

class ServiceFeatureSerializer(serializers.ModelSerializer):
    """Serializer for the ServiceFeature model"""
    
    class Meta:
        model = ServiceFeature
        fields = ['id', 'name', 'description']

class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for the Service model"""
    
    features = ServiceFeatureSerializer(many=True, read_only=True)
    feature_ids = serializers.PrimaryKeyRelatedField(
        source='features',
        queryset=ServiceFeature.objects.all(),
        many=True,
        write_only=True,
        required=False
    )
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Service
        fields = [
            'id', 'name', 'description', 'category', 'category_display',
            'price', 'price_period', 'image', 'features', 'feature_ids',
            'is_featured', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
