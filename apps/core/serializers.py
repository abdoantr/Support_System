from rest_framework import serializers
from .models import Profile, FAQ, FAQInteraction
from apps.accounts.serializers import UserSerializer

class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profiles"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Profile
        fields = ['id', 'user', 'company', 'phone', 'preferred_contact_method', 'is_available']
        read_only_fields = ['id', 'user']

class FAQSerializer(serializers.ModelSerializer):
    """Serializer for FAQs"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = FAQ
        fields = [
            'id', 'category', 'category_display', 'question', 
            'answer', 'order', 'is_published', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class FAQInteractionSerializer(serializers.ModelSerializer):
    """Serializer for FAQ interactions"""
    faq = serializers.PrimaryKeyRelatedField(queryset=FAQ.objects.all())
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = FAQInteraction
        fields = ['id', 'faq', 'interaction_type', 'created_at', 'user', 'ip_address']
        read_only_fields = ['id', 'created_at', 'user']
        
    def create(self, validated_data):
        # Ensure ip_address is saved if user is anonymous
        request = self.context.get('request', None)
        if request and not validated_data.get('user') and not validated_data.get('ip_address'):
            validated_data['ip_address'] = self._get_client_ip(request)
        return super().create(validated_data)
        
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip 