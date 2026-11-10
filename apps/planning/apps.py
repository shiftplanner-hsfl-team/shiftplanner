"""App-Konfiguration der Schichtplanung."""

from django.apps import AppConfig


class PlanningConfig(AppConfig):
    """Registriert die App ``apps.planning`` bei Django."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.planning'
    verbose_name = 'Schichtplanung'
