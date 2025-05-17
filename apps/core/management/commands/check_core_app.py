from django.core.management.base import BaseCommand
from django.apps import apps

class Command(BaseCommand):
    help = 'Checks the core app for issues'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Checking the core app configuration...'))
        
        # Check if CoreConfig is properly loaded
        try:
            core_app_config = apps.get_app_config('core')
            self.stdout.write(self.style.SUCCESS(f'Core app config found: {core_app_config}'))
        except LookupError:
            self.stdout.write(self.style.ERROR('Core app config not found!'))
            return
        
        # Check core models
        try:
            from apps.core.models import Profile, FAQ, FAQInteraction
            self.stdout.write(self.style.SUCCESS('Core models loaded successfully'))
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'Error loading core models: {e}'))
        
        # Check core API
        try:
            from apps.core.api import ProfileViewSet, FAQViewSet, FAQInteractionViewSet
            self.stdout.write(self.style.SUCCESS('Core API viewsets loaded successfully'))
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'Error loading core API: {e}'))
        
        # Check core serializers
        try:
            from apps.core.serializers import ProfileSerializer, FAQSerializer, FAQInteractionSerializer
            self.stdout.write(self.style.SUCCESS('Core serializers loaded successfully'))
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'Error loading core serializers: {e}'))
        
        # Check core forms
        try:
            from apps.core.forms import (
                ContactForm, RegistrationForm, ProfileForm,
                CustomPasswordChangeForm, ServiceRequestForm,
                TicketForm, FAQFeedbackForm
            )
            self.stdout.write(self.style.SUCCESS('Core forms loaded successfully'))
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'Error loading core forms: {e}'))
        
        # Check core URLs
        try:
            from apps.core.urls import urlpatterns as core_urlpatterns
            self.stdout.write(self.style.SUCCESS(f'Core URLs loaded successfully: {len(core_urlpatterns)} patterns'))
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'Error loading core URLs: {e}'))
        
        # Check core API URLs
        try:
            from apps.core.urls_api import urlpatterns as core_api_urlpatterns
            self.stdout.write(self.style.SUCCESS(f'Core API URLs loaded successfully: {len(core_api_urlpatterns)} patterns'))
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'Error loading core API URLs: {e}'))
        
        self.stdout.write(self.style.SUCCESS('Core app check complete.')) 