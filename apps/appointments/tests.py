from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Appointment, TimeSlot, TechnicianSchedule
from apps.accounts.models import User
from apps.services.models import Service

class AppointmentModelTest(TestCase):
    """Tests for the Appointment model"""
    
    def setUp(self):
        # Create test users
        self.customer = User.objects.create_user(
            username='customer', 
            email='customer@example.com',
            password='password123',
            role='customer'
        )
        
        self.technician = User.objects.create_user(
            username='technician', 
            email='technician@example.com',
            password='password123',
            role='technician'
        )
        
        # Create a service
        self.service = Service.objects.create(
            name='Test Service',
            description='Test Service Description',
            price=100.00
        )
        
        # Create a time slot
        self.time_slot = TimeSlot.objects.create(
            start_time='09:00',
            end_time='10:00'
        )
        
        # Create a technician schedule
        tomorrow = timezone.now().date() + timedelta(days=1)
        self.schedule = TechnicianSchedule.objects.create(
            technician=self.technician,
            date=tomorrow,
            is_available=True
        )
        self.schedule.available_slots.add(self.time_slot)
        
        # Create an appointment
        self.appointment = Appointment.objects.create(
            user=self.customer,
            service=self.service,
            technician=self.technician,
            date=tomorrow,
            time_slot='09:30',
            status='pending'
        )
    
    def test_appointment_creation(self):
        """Test appointment creation"""
        self.assertEqual(self.appointment.user, self.customer)
        self.assertEqual(self.appointment.service, self.service)
        self.assertEqual(self.appointment.technician, self.technician)
        self.assertEqual(self.appointment.status, 'pending')
    
    def test_string_representation(self):
        """Test string representation of appointment"""
        self.assertEqual(
            str(self.appointment), 
            f"{self.service.name} - {self.appointment.date} {self.appointment.time_slot}"
        ) 