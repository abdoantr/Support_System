from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class AppointmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.appointments'
    verbose_name = _('Appointments')
    
    def ready(self):
        """Import signal handlers when app is ready"""
        import apps.appointments.signals