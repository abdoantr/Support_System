from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Appointment
from django.utils import timezone
from apps.accounts.tasks import send_ticket_notification

@receiver(post_save, sender=Appointment)
def appointment_notification(sender, instance, created, **kwargs):
    """
    Signal handler to send notifications when an appointment is created or updated
    """
    # Skip if this is a creation - handled separately
    if not created:
        # If status changed, notify user and technician
        if 'status' in kwargs.get('update_fields', []):
            # Notify user
            if instance.user:
                send_ticket_notification.delay(
                    user_id=instance.user.id,
                    ticket_id=instance.id,
                    notification_type='status_update'
                )
                
            # Notify technician
            if instance.technician:
                send_ticket_notification.delay(
                    user_id=instance.technician.id,
                    ticket_id=instance.id,
                    notification_type='status_update'
                )

@receiver(post_save, sender=Appointment)
def appointment_created(sender, instance, created, **kwargs):
    """
    Signal handler to send notifications when a new appointment is created
    """
    if created:
        # Notify technician about new assignment
        if instance.technician:
            send_ticket_notification.delay(
                user_id=instance.technician.id,
                ticket_id=instance.id,
                notification_type='assigned'
            )
            
        # Notify user about appointment confirmation
        if instance.user:
            send_ticket_notification.delay(
                user_id=instance.user.id,
                ticket_id=instance.id,
                notification_type='assigned'
            ) 