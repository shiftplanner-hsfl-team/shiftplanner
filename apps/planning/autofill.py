"""Unbesetzte Positionen ergänzen, ohne vorhandene Zuweisungen zu verändern."""

from collections import defaultdict

from django.db import transaction

from .models import Assignment, Availability, Employee, Month, Plan, Submission, Vacation
from .rules import Shift
from .services import is_eligible, match_positions


def fill_slot(rows, available, employees, qualifications, vacations, busy):
    """Ordnet geeignete Personen den freien Positionen einer Schicht zu.

    Args:
        rows: Freie Positionen derselben Schicht im gespeicherten Plan.
        available: Abgegebene Verfügbarkeiten je Person für diese Schicht.
        employees: Aktive Mitarbeitende nach ID.
        qualifications: Qualifikationsnamen je Person.
        vacations: Urlaubszeiträume je Person.
        busy: Bereits geplante Schichten je Person; wird ergänzt.

    Returns:
        Liste der geänderten Positionen.
    """
    shift = Shift(rows[0].date, rows[0].start, rows[0].end)
    priorities = {
        pk: priority
        for pk, priority in available.items()
        if pk in employees and is_eligible(shift, busy[pk], vacations[pk])
    }
    roles = [(None if row.role == 'Ohne Vorgabe' else row.role, row.role) for row in rows]
    candidates = [
        [pk for pk in sorted(priorities) if role is None or role in qualifications[pk]]
        for role, _ in roles
    ]
    changed = []
    for index, employee_id in match_positions(roles, candidates, priorities).items():
        row = rows[index]
        person = employees[employee_id]
        row.employee = person
        row.employee_name = str(person)
        row.priority = priorities[employee_id]
        busy[employee_id].append(shift)
        changed.append(row)
    return changed


@transaction.atomic
def fill_unassigned(month):
    """Füllt freie Positionen anhand abgegebener Angaben und bestehender Zuweisungen.

    Args:
        month: Planungsmonat mit einem vorhandenen Plan.

    Returns:
        Anzahl neu besetzter Positionen und Anzahl weiterhin offener Positionen.

    Raises:
        ValueError: Wenn noch kein Plan für den Monat existiert.
    """
    month = Month.objects.select_for_update().get(pk=month.pk)
    plan = Plan.objects.select_for_update().filter(month=month).first()
    if not plan:
        raise ValueError('Bitte zuerst einen Schichtplan erzeugen.')
    rows = list(
        plan.assignments.select_for_update().order_by('date', 'start', 'slot_id', 'position')
    )
    employees = {
        e.pk: e
        for e in Employee.objects.filter(user__is_active=True)
        .select_related('user')
        .prefetch_related('qualifications')
    }
    qualifications = {pk: {q.name for q in e.qualifications.all()} for pk, e in employees.items()}
    submitted = Submission.objects.filter(month=month, submitted=True).values_list(
        'employee_id', flat=True
    )
    available = defaultdict(dict)
    for value in Availability.objects.filter(
        slot__month=month, employee_id__in=submitted, priority__gt=0
    ):
        available[value.slot_id][value.employee_id] = value.priority
    vacations = defaultdict(list)
    for vacation in Vacation.objects.all():
        vacations[vacation.employee_id].append(vacation)
    busy = defaultdict(list)
    unfilled = defaultdict(list)
    for row in rows:
        if row.employee_id:
            busy[row.employee_id].append(Shift(row.date, row.start, row.end))
        else:
            unfilled[row.slot_id].append(row)
    changed = []
    for slot_id, open_rows in unfilled.items():
        changed.extend(
            fill_slot(open_rows, available[slot_id], employees, qualifications, vacations, busy)
        )
    Assignment.objects.bulk_update(changed, ['employee', 'employee_name', 'priority'])
    return len(changed), sum(len(group) for group in unfilled.values()) - len(changed)
