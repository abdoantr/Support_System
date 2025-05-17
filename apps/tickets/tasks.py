from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Ticket
from apps.accounts.models import User

@shared_task
def send_ticket_notification(user_id, ticket_id, notification_type):
    """
    Send ticket-related notifications.
    """
    try:
        user = User.objects.get(id=user_id)
        ticket = Ticket.objects.get(id=ticket_id)
        
        templates = {
            'assigned': 'tickets/email/ticket_assigned.html',
            'status_update': 'tickets/email/status_update.html',
            'new_comment': 'tickets/email/new_comment.html',
            'overdue': 'tickets/email/ticket_overdue.html',
            'reminder': 'tickets/email/ticket_reminder.html'
        }
        
        subjects = {
            'assigned': 'New Ticket Assigned',
            'status_update': f'Ticket #{ticket.id} Status Update',
            'new_comment': f'New Comment on Ticket #{ticket.id}',
            'overdue': f'Ticket #{ticket.id} is Overdue',
            'reminder': f'Reminder: Ticket #{ticket.id} Needs Attention'
        }
        
        template = templates.get(notification_type)
        subject = subjects.get(notification_type)
        
        if not template or not subject:
            return f'Invalid notification type: {notification_type}'
            
        html_message = render_to_string(template, {
            'user': user,
            'ticket': ticket
        })
        
        send_mail(
            subject,
            '',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return f'Notification sent to {user.email}'
    except (User.DoesNotExist, Ticket.DoesNotExist) as e:
        return f'Error: {str(e)}'
    except Exception as e:
        return f'Failed to send notification: {str(e)}'

@shared_task
def check_overdue_tickets():
    """
    Check for overdue tickets and send notifications.
    This task runs daily.
    """
    overdue_tickets = Ticket.objects.filter(
        status__in=['open', 'in_progress'],
        due_date__lt=timezone.now(),
        overdue_notification_sent=False
    )
    
    for ticket in overdue_tickets:
        # Notify assigned technician
        if ticket.assigned_to:
            send_ticket_notification.delay(
                ticket.assigned_to.id,
                ticket.id,
                'overdue'
            )
        
        # Notify admin
        admins = User.objects.filter(role=User.Roles.ADMIN)
        for admin in admins:
            send_ticket_notification.delay(
                admin.id,
                ticket.id,
                'overdue'
            )
        
        ticket.overdue_notification_sent = True
        ticket.save()
    
    return f'Processed {len(overdue_tickets)} overdue tickets'

@shared_task
def send_ticket_reminders():
    """
    Send reminders for tickets that haven't been updated in 48 hours.
    This task runs daily.
    """
    two_days_ago = timezone.now() - timedelta(days=2)
    stale_tickets = Ticket.objects.filter(
        status__in=['open', 'in_progress'],
        last_updated__lt=two_days_ago,
        reminder_sent=False
    )
    
    for ticket in stale_tickets:
        # Notify assigned technician
        if ticket.assigned_to:
            send_ticket_notification.delay(
                ticket.assigned_to.id,
                ticket.id,
                'reminder'
            )
        
        ticket.reminder_sent = True
        ticket.save()
    
    return f'Sent reminders for {len(stale_tickets)} tickets'

@shared_task
def send_weekly_ticket_summary():
    """
    Send weekly ticket summary to admins.
    This task runs every Monday at 9:00 AM.
    """
    week_ago = timezone.now() - timedelta(days=7)
    new_tickets = Ticket.objects.filter(created_at__gte=week_ago).count()
    closed_tickets = Ticket.objects.filter(
        status='closed',
        updated_at__gte=week_ago
    ).count()
    overdue_tickets = Ticket.objects.filter(
        status__in=['open', 'in_progress'],
        due_date__lt=timezone.now()
    ).count()
    
    context = {
        'period': 'weekly',
        'new_tickets': new_tickets,
        'closed_tickets': closed_tickets,
        'overdue_tickets': overdue_tickets
    }
    
    html_message = render_to_string('tickets/email/ticket_summary.html', context)
    
    admins = User.objects.filter(role=User.Roles.ADMIN)
    for admin in admins:
        send_mail(
            'Weekly Ticket Summary',
            '',
            settings.DEFAULT_FROM_EMAIL,
            [admin.email],
            html_message=html_message,
            fail_silently=False,
        )
    
    return f'Sent weekly summary to {admins.count()} admins'
