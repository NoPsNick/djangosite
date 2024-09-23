from django.apps import AppConfig


class LegaldocsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'legaldocs'
    verbose_name = "Documentos Legais"

    def ready(self):
        import legaldocs.signals
