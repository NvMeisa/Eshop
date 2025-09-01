from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = 'API'

    def ready(self):
        """Инициализация приложения при запуске"""
        try:
            import api.signals  # noqa
        except ImportError:
            pass
