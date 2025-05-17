from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView
from django.contrib.auth import login
from .serializers import (
    UserSerializer, RegisterSerializer, 
    LoginSerializer, ChangePasswordSerializer
)
from .models import User
from rest_framework.views import APIView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .tasks import send_password_reset_email, send_welcome_email
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Allow admin users
        if request.user.is_staff:
            return True
        # Check if the object has a user field and if the requesting user is the owner
        return obj == request.user

class RegisterView(generics.CreateAPIView):
    """
    Register a new user in the system.
    
    This endpoint allows anyone to register a new user account.
    The user will receive a welcome email upon successful registration.
    """
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        description='Register a new user',
        responses={201: UserSerializer},
        examples=[
            OpenApiExample(
                'Valid Registration',
                value={
                    'email': 'user@example.com',
                    'username': 'newuser',
                    'password': 'securepass123',
                    'password2': 'securepass123',
                    'first_name': 'John',
                    'last_name': 'Doe'
                }
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send welcome email asynchronously
        send_welcome_email.delay(user.id)
        
        return Response({
            "user": UserSerializer(user).data,
            "token": AuthToken.objects.create(user)[1]
        })

class LoginView(KnoxLoginView):
    """
    Log in to the system.
    
    This endpoint allows users to log in using their email and password.
    Returns an authentication token upon successful login.
    """
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        description='Login to the system',
        request=LoginSerializer,
        responses={200: {'type': 'object', 'properties': {'token': {'type': 'string'}}}},
        examples=[
            OpenApiExample(
                'Valid Login',
                value={
                    'email': 'user@example.com',
                    'password': 'yourpassword'
                }
            )
        ]
    )
    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        login(request, user)
        return super().post(request, format=None)

class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the user's profile.
    
    This endpoint allows users to view or update their own profile information.
    """
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(
        description='Retrieve or update the user\'s profile',
        responses={200: UserSerializer},
        examples=[
            OpenApiExample(
                'Valid Profile Update',
                value={
                    'email': 'user@example.com',
                    'username': 'newuser',
                    'first_name': 'John',
                    'last_name': 'Doe'
                }
            )
        ]
    )
    def get_object(self):
        return self.request.user

class ChangePasswordView(generics.UpdateAPIView):
    """
    Change the user's password.
    
    This endpoint allows users to change their own password.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(
        description='Change the user\'s password',
        request=ChangePasswordSerializer,
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}},
        examples=[
            OpenApiExample(
                'Valid Password Change',
                value={
                    'old_password': 'oldpassword',
                    'new_password': 'newpassword',
                    'new_password2': 'newpassword'
                }
            )
        ]
    )
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        if not user.check_password(serializer.data.get('old_password')):
            return Response(
                {'old_password': ['Wrong password.']}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        user.set_password(serializer.data.get('new_password'))
        user.save()
        return Response(
            {'message': 'Password updated successfully'}, 
            status=status.HTTP_200_OK
        )

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def get_technicians(request):
    """
    Retrieve a list of technicians.
    
    This endpoint allows admin users to view a list of all technicians in the system.
    """
    technicians = User.objects.filter(role=User.Roles.TECHNICIAN)
    serializer = UserSerializer(technicians, many=True)
    return Response(serializer.data)

class UpdateProfileView(generics.UpdateAPIView):
    """
    Update the user's profile.
    
    This endpoint allows users to update their own profile information.
    """
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated, IsOwnerOrAdmin)

    @extend_schema(
        description='Update the user\'s profile',
        responses={200: UserSerializer},
        examples=[
            OpenApiExample(
                'Valid Profile Update',
                value={
                    'email': 'user@example.com',
                    'username': 'newuser',
                    'first_name': 'John',
                    'last_name': 'Doe'
                }
            )
        ]
    )
    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        if 'avatar' in self.request.FILES:
            # حذف الصورة القديمة إذا وجدت
            if self.get_object().avatar:
                self.get_object().avatar.delete()
        serializer.save()

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_availability(request):
    """
    Toggle the user's availability.
    
    This endpoint allows technicians to toggle their own availability.
    """
    user = request.user
    if user.role != User.Roles.TECHNICIAN:
        return Response(
            {'error': 'Only technicians can toggle availability'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    user.is_available = not user.is_available
    user.save()
    return Response({
        'message': 'Availability updated successfully',
        'is_available': user.is_available
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_available_technicians(request):
    """
    Retrieve a list of available technicians.
    
    This endpoint allows users to view a list of all available technicians in the system.
    """
    technicians = User.objects.filter(
        role=User.Roles.TECHNICIAN,
        is_available=True,
        is_active=True
    )
    serializer = UserSerializer(technicians, many=True)
    return Response(serializer.data)

class PasswordResetRequestView(APIView):
    """
    Request a password reset.
    
    This endpoint allows users to request a password reset.
    """
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        description='Request a password reset',
        request={'type': 'object', 'properties': {'email': {'type': 'string'}}},
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}},
        examples=[
            OpenApiExample(
                'Valid Password Reset Request',
                value={
                    'email': 'user@example.com'
                }
            )
        ]
    )
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            
            reset_url = f"{request.scheme}://{request.get_host()}/reset-password/{uid}/{token}/"
            
            # Send password reset email asynchronously
            send_password_reset_email.delay(user.id, reset_url)
            
            return Response({
                'message': 'Password reset email has been sent.'
            })
            
        except User.DoesNotExist:
            return Response({
                'message': 'If a user with this email exists, a password reset link will be sent.'
            })

class PasswordResetConfirmView(APIView):
    """
    Confirm a password reset.
    
    This endpoint allows users to confirm a password reset.
    """
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        description='Confirm a password reset',
        request={'type': 'object', 'properties': {'new_password': {'type': 'string'}}},
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}},
        examples=[
            OpenApiExample(
                'Valid Password Reset Confirmation',
                value={
                    'new_password': 'newpassword'
                }
            )
        ]
    )
    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            
            if not default_token_generator.check_token(user, token):
                return Response(
                    {'error': 'Invalid token'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            new_password = request.data.get('new_password')
            if not new_password:
                return Response(
                    {'error': 'New password is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Password strength validation    
            if len(new_password) < 8:
                return Response(
                    {'error': 'Password must be at least 8 characters long'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not any(char.isdigit() for char in new_password):
                return Response(
                    {'error': 'Password must contain at least one number'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not any(char.isalpha() for char in new_password):
                return Response(
                    {'error': 'Password must contain at least one letter'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            user.set_password(new_password)
            user.save()
            
            return Response({
                'message': 'Password has been reset successfully.'
            })
            
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'error': 'Invalid reset link'},
                status=status.HTTP_400_BAD_REQUEST
            )