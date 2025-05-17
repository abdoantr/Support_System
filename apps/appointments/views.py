from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils.translation import gettext_lazy as _
from .models import Appointment, TimeSlot, TechnicianSchedule
from .serializers import AppointmentSerializer, TimeSlotSerializer, TechnicianScheduleSerializer
from apps.accounts.models import User
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

class IsOwnerOrStaff(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or staff to view or edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Staff can do anything
        if request.user.is_staff:
            return True
        
        # Technicians can view appointments assigned to them
        if request.user.role == 'technician' and hasattr(obj, 'technician') and obj.technician == request.user:
            return True
            
        # Otherwise, users can only see their own appointments
        return obj.user == request.user

class TimeSlotViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows time slots to be viewed or edited.
    """
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer
    permission_classes = [permissions.IsAdminUser]

class TechnicianScheduleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows technician schedules to be viewed or edited.
    """
    queryset = TechnicianSchedule.objects.all()
    serializer_class = TechnicianScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter schedules based on user role
        """
        user = self.request.user
        if user.is_staff:
            return TechnicianSchedule.objects.all()
        elif user.role == 'technician':
            return TechnicianSchedule.objects.filter(technician=user)
        else:
            # Only return schedules with available slots
            return TechnicianSchedule.objects.filter(is_available=True)
    
    @extend_schema(
        description="Get available schedules for a specific date",
        parameters=[
            OpenApiParameter(name='date', description='Date in YYYY-MM-DD format')
        ]
    )
    @action(detail=False, methods=['get'])
    def available(self, request):
        """
        Get available schedules for a specific date
        """
        date_str = request.query_params.get('date')
        
        if not date_str:
            return Response(
                {"error": _("Date parameter is required")}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            from datetime import datetime
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": _("Invalid date format. Use YYYY-MM-DD")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if date < timezone.now().date():
            return Response(
                {"error": _("Cannot get schedules for past dates")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        schedules = TechnicianSchedule.objects.filter(
            date=date,
            is_available=True
        )
        
        serializer = self.get_serializer(schedules, many=True)
        return Response(serializer.data)

class AppointmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows appointments to be viewed or edited.
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrStaff]
    
    def get_queryset(self):
        """
        Filter appointments based on user role
        """
        user = self.request.user
        if user.is_staff:
            return Appointment.objects.all()
        elif user.role == 'technician':
            return Appointment.objects.filter(technician=user)
        else:
            return Appointment.objects.filter(user=user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @extend_schema(
        description="Cancel an appointment",
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel an appointment
        """
        appointment = self.get_object()
        
        # Check if appointment can be cancelled
        if appointment.status not in ['pending', 'confirmed']:
            return Response(
                {"error": _("Cannot cancel an appointment that is not pending or confirmed")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check if appointment is in the future
        if appointment.date < timezone.now().date():
            return Response(
                {"error": _("Cannot cancel a past appointment")},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Cancel the appointment
        appointment.status = Appointment.Status.CANCELLED
        appointment.save()
        
        return Response({"message": _("Appointment cancelled successfully")})
    
    @extend_schema(
        description="Get appointments for the upcoming week",
        responses={200: AppointmentSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Get appointments for the upcoming week
        """
        today = timezone.now().date()
        next_week = today + timedelta(days=7)
        
        # Filter based on user role
        user = request.user
        if user.is_staff:
            appointments = Appointment.objects.filter(
                date__gte=today,
                date__lte=next_week
            )
        elif user.role == 'technician':
            appointments = Appointment.objects.filter(
                technician=user,
                date__gte=today,
                date__lte=next_week
            )
        else:
            appointments = Appointment.objects.filter(
                user=user,
                date__gte=today,
                date__lte=next_week
            )
            
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data) 