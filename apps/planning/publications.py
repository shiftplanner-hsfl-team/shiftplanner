"""Explizite Freigabe eines Plans und getrennte Leseansicht (REQ-15)."""

import hashlib
import json

from django.db import transaction

from .models import Month, Plan, PlanningSettings, PublishedAssignment, PublishedPlan

SNAPSHOT_FIELDS = ('employee_id', 'employee_name', 'date', 'shift_name', 'start', 'end', 'role')


def team_plan_visible():
    """Liefert die gemeinsame Plansicht; ohne Einstellung gelten nur eigene Schichten."""
    return PlanningSettings.objects.filter(pk=1, show_team_plan=True).exists()


def publication_preview(month):
    """Bereitet die Freigabe des aktuellen Entwurfs vor.

    Args:
        month: Planungsmonat.

    Returns:
        Entwurf, Positionen, Kennzahlen und Zustand für eine signierte Bestätigung.

    Raises:
        ValueError: Wenn kein Plan mit Positionen vorhanden ist.
    """
    plan = Plan.objects.filter(month=month).first()
    if plan is None:
        raise ValueError('Bitte zuerst einen Schichtplan erzeugen.')
    rows = list(
        plan.assignments.order_by('date', 'start', 'slot_id', 'position').values(*SNAPSHOT_FIELDS)
    )
    if not rows:
        raise ValueError('Dieser Plan enthält noch keine Positionen.')
    payload = {'revision': plan.revision, 'rows': rows}
    fingerprint = hashlib.sha256(
        json.dumps(payload, default=str, sort_keys=True).encode()
    ).hexdigest()
    missing = sum(row['employee_id'] is None for row in rows)
    stale = plan.revision != month.revision
    return {
        'draft': plan,
        'rows': rows,
        'total': len(rows),
        'assigned': len(rows) - missing,
        'unfilled_count': missing,
        'stale': stale,
        'needs_acknowledgement': bool(missing or stale),
        'state': {'plan': plan.pk, 'fingerprint': fingerprint, 'month_revision': month.revision},
    }


@transaction.atomic
def publish_plan(month, user, expected, acknowledge=False):
    """Übernimmt genau den zuvor geprüften Planstand atomar als Veröffentlichung.

    Args:
        month: Planungsmonat.
        user: Veröffentlichendes Planungskonto; die View prüft die Rolle.
        expected: Zustand der signierten Prüfseite.
        acknowledge: Ausdrückliche Bestätigung der angezeigten Hinweise.

    Returns:
        Veröffentlichung mit unabhängig gespeicherten Positionen.

    Raises:
        ValueError: Wenn der Plan geändert wurde oder eine Bestätigung fehlt.
    """
    month = Month.objects.select_for_update().get(pk=month.pk)
    Plan.objects.select_for_update().filter(month=month).first()
    preview = publication_preview(month)
    if preview['state'] != expected:
        raise ValueError('Der Plan oder seine Eingaben wurden geändert. Bitte erneut prüfen.')
    if preview['needs_acknowledgement'] and not acknowledge:
        raise ValueError(
            'Bitte die Hinweise prüfen und die Veröffentlichung ausdrücklich bestätigen.'
        )
    publication, _ = PublishedPlan.objects.update_or_create(
        month=month,
        defaults={
            'published_by': user,
            'source_fingerprint': expected['fingerprint'],
            'source_input_revision': month.revision,
        },
    )
    publication.assignments.all().delete()
    PublishedAssignment.objects.bulk_create(
        [
            PublishedAssignment(publication=publication, position=index, **row)
            for index, row in enumerate(preview['rows'])
        ]
    )
    return publication


def published_timetable(month, rows, requested_week=None, employee_id=None):
    """Gruppiert freigegebene Positionen als Wochen-Stundenplan.

    Args:
        month: Ausgewählter Planungsmonat.
        rows: Bereits gemäß Sichtberechtigung gefilterte Veröffentlichungspositionen.
        requested_week: Montag der angefragten Woche als ISO-Datum.
        employee_id: Angemeldete Person zur Kennzeichnung eigener Positionen.

    Returns:
        Wochenwahl, Navigation, Tage und nach Schichtzeit gruppierte Tabellenzeilen.
    """
    from collections import defaultdict
    from datetime import timedelta

    from .services import dates_for_month, today

    positions = list(rows)
    mondays = sorted({day - timedelta(days=day.weekday()) for day in dates_for_month(month.date)})
    default_day = (
        today()
        if today().replace(day=1) == month.date
        else (positions[0].date if positions else month.date)
    )
    default_week = default_day - timedelta(days=default_day.weekday())
    options = {day.isoformat(): day for day in mondays}
    monday = options.get(requested_week, default_week)
    index = mondays.index(monday)
    days = [monday + timedelta(days=offset) for offset in range(7)]
    grouped = defaultdict(lambda: defaultdict(list))
    for row in positions:
        if row.date in days:
            grouped[(row.start, row.end, row.shift_name)][row.date].append(row)
    table = []
    for (start, end, name), cells in sorted(grouped.items()):
        table.append(
            {
                'name': name,
                'start': start,
                'end': end,
                'cells': [
                    {
                        'date': day,
                        'outside': day.month != month.date.month,
                        'positions': [
                            {'assignment': row, 'own': row.employee_id == employee_id}
                            for row in cells[day]
                        ],
                    }
                    for day in days
                ],
            }
        )
    return {
        'timetable_rows': table,
        'has_month_shifts': bool(positions),
        'timetable_days': [
            {'date': day, 'outside': day.month != month.date.month} for day in days
        ],
        'week_options': [
            {
                'value': day.isoformat(),
                'number': day.isocalendar().week,
                'start': day,
                'end': day + timedelta(days=6),
            }
            for day in mondays
        ],
        'selected_monday': monday.isoformat(),
        'week_number': monday.isocalendar().week,
        'week_start': monday,
        'week_end': days[-1],
        'previous_week': mondays[index - 1].isoformat() if index else None,
        'next_week': mondays[index + 1].isoformat() if index + 1 < len(mondays) else None,
    }
