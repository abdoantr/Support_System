from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import User
from apps.services.models import Service

class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        CONFIRMED = 'confirmed', _('Confirmed')
        CANCELLED = 'cancelled', _('Cancelled')
        COMPLETED = 'completed', _('Completed')

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    technician = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_appointments',
        limit_choices_to={'role': 'technician'}
    )
    date = models.DateField(_('Date'))
    time_slot = models.TimeField(_('Time Slot'))
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'time_slot']
        unique_together = ['technician', 'date', 'time_slot']

    def __str__(self):
        return f"{self.service.name} - {self.date} {self.time_slot}"

class TimeSlot(models.Model):
    start_time = models.TimeField(_('Start Time'))
    end_time = models.TimeField(_('End Time'))
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['start_time']
        unique_together = ['start_time', 'end_time']

    def __str__(self):
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"

class TechnicianSchedule(models.Model):
    technician = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='schedules',
        limit_choices_to={'role': 'technician'}
    )
    date = models.DateField(_('Date'))
    available_slots = models.ManyToManyField(
        TimeSlot,
        related_name='technician_schedules'
    )
    is_available = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['date']
        unique_together = ['technician', 'date']

    def __str__(self):
        return f"{self.technician.get_full_name()} - {self.date}"
