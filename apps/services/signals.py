from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Service
from django.utils import timezone
import os

@receiver(pre_save, sender=Service)
def service_pre_save(sender, instance, **kwargs):
    """
    Signal to handle operations before saving a service
    """
    # If a new image is uploaded, delete the old one if it exists
    if instance.pk:
        try:
            old_instance = Service.objects.get(pk=instance.pk)
            if old_instance.image and instance.image != old_instance.image:
                if os.path.isfile(old_instance.image.path):
                    os.remove(old_instance.image.path)
        except Service.DoesNotExist:
            pass

@receiver(post_save, sender=Service)
def service_post_save(sender, instance, created, **kwargs):
    """
    Signal to handle operations after saving a service
    """
    # Add logging or additional functionality as needed
    pass 