from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.payments'
    verbose_name = _('Payments')
    
    def ready(self):
        """Import signal handlers when app is ready"""
        import apps.payments.signals