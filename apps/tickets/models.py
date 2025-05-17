from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import User
from apps.services.models import Service
from django.utils import timezone

class Ticket(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', _('New')
        ASSIGNED = 'assigned', _('Assigned')
        IN_PROGRESS = 'in_progress', _('In Progress')
        PENDING = 'pending', _('Pending')
        RESOLVED = 'resolved', _('Resolved')
        CLOSED = 'closed', _('Closed')

    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        URGENT = 'urgent', _('Urgent')

    title = models.CharField(_('title'), max_length=200)
    description = models.TextField(_('description'))
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_tickets'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tickets'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_updated = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    overdue_notification_sent = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)
    category = models.CharField(max_length=100, blank=True)
    device_type = models.CharField(max_length=100, blank=True)
    device_model = models.CharField(max_length=100, blank=True)
    contact_method = models.CharField(max_length=20, blank=True, null=True)
    preferred_contact_time = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.pk:
            self.last_updated = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Ticket #{self.id} - {self.title}"

class TicketComment(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ticket_comments'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_internal = models.BooleanField(default=False)  # للملاحظات الداخلية للفنيين

    class Meta:
        ordering = ['created_at']

class TicketAttachment(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='ticket_attachments/%Y/%m/')
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ticket_attachments'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Attachment for {self.ticket.title}"