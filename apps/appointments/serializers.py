from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Appointment, TimeSlot, TechnicianSchedule
from apps.accounts.serializers import UserSerializer
from apps.services.serializers import ServiceSerializer
from django.utils import timezone
from datetime import datetime
from apps.accounts.models import User
from apps.services.models import Service

class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ['id', 'start_time', 'end_time', 'is_active']

class TechnicianScheduleSerializer(serializers.ModelSerializer):
    technician = UserSerializer(read_only=True)
    technician_id = serializers.PrimaryKeyRelatedField(
        source='technician', 
        queryset=User.objects.filter(role='technician', is_active=True),
        write_only=True
    )
    available_slots = TimeSlotSerializer(many=True, read_only=True)
    available_slot_ids = serializers.PrimaryKeyRelatedField(
        source='available_slots',
        queryset=TimeSlot.objects.filter(is_active=True),
        write_only=True,
        many=True
    )
    
    class Meta:
        model = TechnicianSchedule
        fields = ['id', 'technician', 'technician_id', 'date', 
                 'available_slots', 'available_slot_ids', 'is_available', 'notes']
    
    def validate_date(self, value):
        """Validate that schedule date is not in the past"""
        if value < timezone.now().date():
            raise serializers.ValidationError(_("Schedule date cannot be in the past"))
        return value

class AppointmentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    technician = UserSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source='user', 
        queryset=User.objects.filter(is_active=True),
        write_only=True, 
        required=False,
        default=serializers.CurrentUserDefault()
    )
    technician_id = serializers.PrimaryKeyRelatedField(
        source='technician', 
        queryset=User.objects.filter(role='technician', is_active=True),
        write_only=True
    )
    service_id = serializers.PrimaryKeyRelatedField(
        source='service', 
        queryset=Service.objects.filter(is_active=True),
        write_only=True
    )
    time_slot_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = ['id', 'user', 'user_id', 'service', 'service_id',
                 'technician', 'technician_id', 'date', 'time_slot',
                 'time_slot_display', 'status', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_time_slot_display(self, obj):
        return obj.time_slot.strftime('%H:%M')
    
    def validate(self, data):
        """Validate appointment date, time and availability"""
        date = data.get('date')
        time_slot = data.get('time_slot')
        technician = data.get('technician')
        
        # Check if date is in the past
        if date < timezone.now().date():
            raise serializers.ValidationError({"date": _("Appointment date cannot be in the past")})
        
        # If the date is today, check if the time slot is in the past
        if date == timezone.now().date() and time_slot < timezone.now().time():
            raise serializers.ValidationError({"time_slot": _("Cannot book a time slot in the past")})
        
        # Check if technician is available at that time
        if technician:
            try:
                schedule = TechnicianSchedule.objects.get(
                    technician=technician,
                    date=date
                )
                
                if not schedule.is_available:
                    raise serializers.ValidationError(_("Technician is not available on this date"))
                
                # Check if the time slot is in the technician's available slots
                time_slot_exists = False
                for slot in schedule.available_slots.all():
                    if slot.start_time <= time_slot <= slot.end_time:
                        time_slot_exists = True
                        break
                
                if not time_slot_exists:
                    raise serializers.ValidationError(_("This time slot is not available for the selected technician"))
                
                # Check if the technician already has an appointment at this time
                existing_appointment = Appointment.objects.filter(
                    technician=technician,
                    date=date,
                    time_slot=time_slot,
                    status__in=['pending', 'confirmed']
                ).exists()
                
                if existing_appointment:
                    raise serializers.ValidationError(_("Technician already has an appointment at this time"))
                    
            except TechnicianSchedule.DoesNotExist:
                raise serializers.ValidationError(_("Technician has no schedule for this date"))
        
        return data 