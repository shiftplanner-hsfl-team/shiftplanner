"""Template-Filter für die Anzeige von Feiertagen (RB-03)."""

from django import template

from ..rules import holiday_name

register = template.Library()


@register.filter
def holiday(day):
    """Gibt den Namen des Feiertags in Schleswig-Holstein zurück oder ``''``.

    Args:
        day: Datum aus dem Template.

    Returns:
        Feiertagsname oder leere Zeichenkette.
    """
    return holiday_name(day) if day else ''
