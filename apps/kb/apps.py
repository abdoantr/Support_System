from django.apps import AppConfig


class KnowledgeBaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.kb'
    verbose_name = 'Knowledge Base'

    def ready(self):
        import apps.kb.signals  # Import signals 