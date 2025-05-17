from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Appointment, TechnicianSchedule, TimeSlot
from django.utils import timezone
from apps.accounts.models import User

class AppointmentForm(forms.ModelForm):
    """Form for creating and updating appointments"""
    
    class Meta:
        model = Appointment
        fields = ['service', 'technician', 'date', 'time_slot', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'min': timezone.now().date().isoformat()}),
            'time_slot': forms.TimeInput(attrs={'type': 'time'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Only show active technicians
        self.fields['technician'].queryset = User.objects.filter(
            role='technician',
            is_active=True,
            is_available=True
        )
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time_slot = cleaned_data.get('time_slot')
        technician = cleaned_data.get('technician')
        
        if not date or not time_slot or not technician:
            return cleaned_data
            
        # Check if date is in the past
        if date < timezone.now().date():
            self.add_error('date', _('Appointment date cannot be in the past'))
            
        # If the date is today, check if the time slot is in the past
        elif date == timezone.now().date() and time_slot < timezone.now().time():
            self.add_error('time_slot', _('Cannot book a time slot in the past'))
        
        # Check technician availability
        try:
            schedule = TechnicianSchedule.objects.get(
                technician=technician,
                date=date,
                is_available=True
            )
            
            # Check if the time slot exists in the technician's available slots
            time_slot_exists = False
            for slot in schedule.available_slots.all():
                if slot.start_time <= time_slot <= slot.end_time:
                    time_slot_exists = True
                    break
                    
            if not time_slot_exists:
                self.add_error('time_slot', 
                               _('This time slot is not available for the selected technician'))
                
            # Check if technician already has an appointment at this time
            existing_appointment = Appointment.objects.filter(
                technician=technician,
                date=date,
                time_slot=time_slot,
                status__in=['pending', 'confirmed']
            )
            
            # Exclude current instance if updating
            if self.instance and self.instance.pk:
                existing_appointment = existing_appointment.exclude(pk=self.instance.pk)
                
            if existing_appointment.exists():
                self.add_error('time_slot', 
                               _('Technician already has an appointment at this time'))
                
        except TechnicianSchedule.DoesNotExist:
            self.add_error('date', _('Technician has no availability for this date'))
            
        return cleaned_data

class TechnicianScheduleForm(forms.ModelForm):
    """Form for creating and updating technician schedules"""
    
    class Meta:
        model = TechnicianSchedule
        fields = ['technician', 'date', 'available_slots', 'is_available', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'min': timezone.now().date().isoformat()}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'available_slots': forms.CheckboxSelectMultiple(),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Only show active time slots
        self.fields['available_slots'].queryset = TimeSlot.objects.filter(is_active=True)
        
        # Only show technicians
        self.fields['technician'].queryset = User.objects.filter(role='technician', is_active=True)
    
    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date < timezone.now().date():
            raise forms.ValidationError(_('Schedule date cannot be in the past'))
        return date 