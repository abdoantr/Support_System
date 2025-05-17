from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Appointment, TimeSlot, TechnicianSchedule

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('service', 'user', 'technician', 'date', 'time_slot', 'status')
    list_filter = ('status', 'date', 'service')
    search_fields = ('user__email', 'technician__email', 'service__name')
    date_hierarchy = 'date'
    
@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time', 'is_active')
    list_filter = ('is_active',)
    ordering = ('start_time',)
    
@admin.register(TechnicianSchedule)
class TechnicianScheduleAdmin(admin.ModelAdmin):
    list_display = ('technician', 'date', 'is_available')
    list_filter = ('is_available', 'date')
    search_fields = ('technician__email', 'technician__first_name', 'technician__last_name')
    date_hierarchy = 'date'
    filter_horizontal = ('available_slots',) 