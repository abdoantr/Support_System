from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 
                 'phone', 'role', 'avatar', 'specialization', 'is_available')
        read_only_fields = ('id',)

class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password2', 
                 'first_name', 'last_name', 'phone', 'role')
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        if data['password'] != data.pop('password2'):
            raise serializers.ValidationError(_("Passwords don't match"))
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data.get('phone', ''),
            role=validated_data.get('role', User.Roles.CUSTOMER)
        )
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if user and user.is_active:
            return user
        raise serializers.ValidationError(_("Invalid email or password"))

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError(_("New passwords don't match"))
        
        # Password strength validation
        password = data['new_password']
        
        # Check minimum length
        if len(password) < 8:
            raise serializers.ValidationError(_("Password must be at least 8 characters long"))
        
        # Check for at least one digit
        if not any(char.isdigit() for char in password):
            raise serializers.ValidationError(_("Password must contain at least one number"))
        
        # Check for at least one letter
        if not any(char.isalpha() for char in password):
            raise serializers.ValidationError(_("Password must contain at least one letter"))
        
        return data