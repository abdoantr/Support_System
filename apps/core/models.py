from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.services.models import Service
from apps.tickets.models import Ticket

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True, null=True)#
    bio = models.TextField(blank=True, null=True)#
    notification_preferences = models.JSONField(default=dict, blank=True, null=True)#
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True, default='')
    preferred_contact_method = models.CharField(
        max_length=10,
        choices=[
            ('email', 'Email'),
            ('phone', 'Phone'),
            ('both', 'Both')
        ],
        default='email'
    )
    is_available = models.BooleanField(default=True, help_text='Whether the user is available to take new support tickets')
    
    def __str__(self):
        return f"{self.user.email}'s Profile"

class FAQ(models.Model):
    CATEGORY_CHOICES = [
        ('technical', 'Technical Support'),
        ('billing', 'Account & Billing'),
        ('services', 'Services')
    ]
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.IntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'order']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
    
    def __str__(self):
        return self.question

class FAQInteraction(models.Model):
    faq = models.ForeignKey(FAQ, on_delete=models.CASCADE)
    interaction_type = models.CharField(
        max_length=20,
        choices=[
            ('view', 'View'),
            ('helpful', 'Helpful'),
            ('not_helpful', 'Not Helpful')
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.faq.question[:30]} - {self.interaction_type}"

class UserSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='settings')
    notifications = models.JSONField(default=dict)
    preferences = models.JSONField(default=dict)
    appearance = models.JSONField(default=dict)
    privacy = models.JSONField(default=dict)
    system = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email}'s Settings"
    
    def get_default_notifications(self):
        return {
            'new_ticket': True,
            'ticket_update': True,
            'ticket_resolved': True,
            'browser_notifications': False,
            'sound_notifications': False,
        }
    
    def get_default_preferences(self):
        return {
            'default_view': 'tickets',
            'items_per_page': 25,
            'timezone': 'UTC',
        }
    
    def get_default_appearance(self):
        return {
            'accent_color': 'primary',
            'font_size': 'medium',
        }
    
    def get_default_privacy(self):
        return {
            'show_online_status': True,
            'show_activity': True,
            'show_email': False,
        }
    
    def get_default_system(self):
        return {
            'auto_assign': True,
            'default_due_date': 3,
            'email_enabled': True,
            'system_email': 'support@example.com',
        }
    
    def save(self, *args, **kwargs):
        # Ensure default values are set
        if not self.notifications:
            self.notifications = self.get_default_notifications()
        if not self.preferences:
            self.preferences = self.get_default_preferences()
        if not self.appearance:
            self.appearance = self.get_default_appearance()
        if not self.privacy:
            self.privacy = self.get_default_privacy()
        if not self.system and self.user.is_staff:
            self.system = self.get_default_system()
        super().save(*args, **kwargs)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_settings(sender, instance, created, **kwargs):
    """Create UserSettings when a user is created."""
    if created:
        UserSettings.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_settings(sender, instance, **kwargs):
    """Save UserSettings when user is saved."""
    try:
        instance.settings.save()
    except UserSettings.DoesNotExist:
        UserSettings.objects.create(user=instance)
