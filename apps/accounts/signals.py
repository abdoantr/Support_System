from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from .tasks import send_welcome_email as send_welcome_email_task

@receiver(post_save, sender=User)
def user_created_handler(sender, instance, created, **kwargs):
    """Handler for user creation that calls the Celery task for sending welcome email"""
    if created:
        # Trigger the Celery task for sending welcome email
        send_welcome_email_task.delay(instance.id)