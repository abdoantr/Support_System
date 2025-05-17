from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Ticket, TicketComment, TicketAttachment
from .tasks import send_ticket_notification
import os

@receiver(post_save, sender=Ticket)
def ticket_post_save(sender, instance, created, **kwargs):
    """
    Handle post-save operations for tickets
    """
    # When a ticket is created, notify admins and technicians
    if created:
        # Ticket creation logic
        pass
    else:
        # Check if status has changed
        update_fields = kwargs.get('update_fields')
        if update_fields is not None and 'status' in update_fields:
            old_status = kwargs.get('old_status')
            if old_status != instance.status:
                # Status changed, send notifications
                if instance.assigned_to:
                    # Notify the assigned technician
                    try:
                        send_ticket_notification.delay(
                            user_id=instance.assigned_to.id,
                            ticket_id=instance.id,
                            notification_type='status_update'
                        )
                    except:
                        # Task may fail if Celery is not running
                        pass
                
                # Notify the ticket creator
                try:
                    send_ticket_notification.delay(
                        user_id=instance.created_by.id,
                        ticket_id=instance.id,
                        notification_type='status_update'
                    )
                except:
                    # Task may fail if Celery is not running
                    pass
                
                # If resolved, set resolved_at timestamp
                if instance.status == Ticket.Status.RESOLVED and not instance.resolved_at:
                    instance.resolved_at = timezone.now()
                    instance.save(update_fields=['resolved_at'])

@receiver(pre_save, sender=Ticket)
def ticket_pre_save(sender, instance, **kwargs):
    """
    Handle pre-save operations for tickets
    """
    # Store the old status if this is an existing ticket
    if instance.pk:
        try:
            old_instance = Ticket.objects.get(pk=instance.pk)
            kwargs['old_status'] = old_instance.status
        except Ticket.DoesNotExist:
            pass

@receiver(post_save, sender=TicketComment)
def ticket_comment_post_save(sender, instance, created, **kwargs):
    """
    Handle post-save operations for ticket comments
    """
    if created:
        # New comment created, send notifications
        
        # Skip notification for internal comments if the author is the one who created the ticket
        if instance.is_internal and instance.author == instance.ticket.created_by:
            return
            
        # Notify the assigned technician if the comment is from the ticket creator
        if instance.author == instance.ticket.created_by and instance.ticket.assigned_to:
            try:
                send_ticket_notification.delay(
                    user_id=instance.ticket.assigned_to.id,
                    ticket_id=instance.ticket.id,
                    notification_type='new_comment'
                )
            except:
                # Task may fail if Celery is not running
                pass
        
        # Notify the ticket creator if the comment is from someone else
        if instance.author != instance.ticket.created_by and not instance.is_internal:
            try:
                send_ticket_notification.delay(
                    user_id=instance.ticket.created_by.id,
                    ticket_id=instance.ticket.id,
                    notification_type='new_comment'
                )
            except:
                # Task may fail if Celery is not running
                pass

@receiver(pre_save, sender=TicketAttachment)
def attachment_pre_save(sender, instance, **kwargs):
    """
    Handle pre-save operations for ticket attachments
    """
    # If replacing an existing attachment, delete the old file
    if instance.pk:
        try:
            old_instance = TicketAttachment.objects.get(pk=instance.pk)
            if old_instance.file and instance.file != old_instance.file:
                if os.path.isfile(old_instance.file.path):
                    os.remove(old_instance.file.path)
        except TicketAttachment.DoesNotExist:
            pass 