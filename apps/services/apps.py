from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ServicesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.services'
    verbose_name = _('Services')
    
    def ready(self):
        """Import signal handlers when app is ready"""
        import apps.services.signals
