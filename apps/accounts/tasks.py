from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from .models import User

@shared_task
def send_password_reset_email(user_id, reset_url):
    """Send password reset email to user"""
    try:
        user = User.objects.get(id=user_id)
        subject = 'Password Reset Request'
        html_message = render_to_string('accounts/email/password_reset.html', {
            'user': user,
            'reset_url': reset_url
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False

@shared_task
def send_welcome_email(user_id):
    """Send welcome email to new users"""
    try:
        user = User.objects.get(id=user_id)
        subject = 'Welcome to Support System'
        html_message = render_to_string('users/email/welcome.html', {
            'user': user,
            'site_name': settings.SITE_NAME
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending welcome email: {e}")
        return False

@shared_task
def send_ticket_notification(user_id, ticket_id, notification_type):
    """Send ticket-related notifications"""
    try:
        user = User.objects.get(id=user_id)
        from apps.tickets.models import Ticket
        ticket = Ticket.objects.get(id=ticket_id)
        
        templates = {
            'assigned': 'tickets/email/ticket_assigned.html',
            'status_update': 'tickets/email/status_update.html',
            'comment': 'tickets/email/new_comment.html',
        }
        
        subjects = {
            'assigned': 'Ticket Assigned',
            'status_update': 'Ticket Status Updated',
            'comment': 'New Comment on Your Ticket',
        }
        
        template = templates.get(notification_type)
        subject = subjects.get(notification_type)
        
        if not template or not subject:
            return False
            
        html_message = render_to_string(template, {
            'user': user,
            'ticket': ticket
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending ticket notification: {e}")
        return False
