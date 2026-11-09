"""Django-Administration für Stammdaten (technischer Zugang, nicht für die Planung)."""

from django.contrib import admin

from .models import Employee, Qualification, ShiftTemplate, Vacation


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Verwaltung der Mitarbeitendenprofile mit Qualifikationsauswahl."""

    list_display = ['user']
    filter_horizontal = ['qualifications']


admin.site.register([Qualification, ShiftTemplate, Vacation])
