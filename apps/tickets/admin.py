from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Ticket, TicketComment, TicketAttachment

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'priority', 'created_by', 'assigned_to', 'created_at', 'last_updated')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('title', 'description', 'created_by__email', 'assigned_to__email')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'last_updated', 'resolved_at')
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('title', 'description', 'status', 'priority')
        }),
        (_('Assignment'), {
            'fields': ('created_by', 'assigned_to')
        }),
        (_('Dates'), {
            'fields': ('due_date', 'created_at', 'updated_at', 'last_updated', 'resolved_at')
        }),
        (_('Device Information'), {
            'fields': ('category', 'device_type', 'device_model')
        }),
        (_('Notification Status'), {
            'fields': ('reminder_sent', 'overdue_notification_sent')
        }),
    )

@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'author', 'created_at', 'is_internal')
    list_filter = ('is_internal', 'created_at')
    search_fields = ('ticket__title', 'author__email', 'content')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'uploaded_by', 'uploaded_at', 'description')
    list_filter = ('uploaded_at',)
    search_fields = ('ticket__title', 'uploaded_by__email', 'description')
    date_hierarchy = 'uploaded_at'
    readonly_fields = ('uploaded_at',)
