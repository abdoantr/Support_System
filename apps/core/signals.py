from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile, FAQInteraction

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a profile for new users
    """
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Ensure profile is saved when user is saved
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=FAQInteraction)
def process_faq_interaction(sender, instance, created, **kwargs):
    """
    Process FAQ interaction (e.g., for analytics)
    """
    if created:
        # For future analytics or notification systems
        pass 