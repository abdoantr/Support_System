from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TicketsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tickets'
    verbose_name = _('Tickets')
    
    def ready(self):
        """Import signal handlers when app is ready"""
        import apps.tickets.signals
