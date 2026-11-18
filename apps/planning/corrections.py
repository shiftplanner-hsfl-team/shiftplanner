"""Manuelle Änderungen an einem gespeicherten Plan prüfen und übernehmen (REQ-11)."""

import hashlib
import json

from django.db import transaction

from . import rules
from .models import Availability, Employee, Month, Need, Plan, Submission, Vacation
from .rules import Shift
from .services import overlaps


def correction_messages(assignment, employee, remaining):
    """Prüft eine Zuweisung gegen harte Regeln und weiche Hinweise.

    Args:
        assignment: Position mit den gespeicherten Schichtzeiten.
        employee: Neu zugewiesene Person oder None.
        remaining: Nach der geplanten Änderung vorhandene andere Zuweisungen.

    Returns:
        Paar aus blockierenden Meldungen und bestätigbaren Hinweisen.
    """
    if employee is None:
        return [], []
    label = f'{employee}: {assignment.date:%d.%m.%Y} {assignment.shift_name}'
    shift = Shift(assignment.date, assignment.start, assignment.end)
    shifts = [Shift(a.date, a.start, a.end) for a in remaining if a.employee_id == employee.pk]
    errors = (
        [f'{label}: Überschneidung mit einer anderen Schicht.']
        if any(overlaps(shift, other) for other in shifts)
        else []
    )
    errors.extend(f'{label}: {message}' for message in rules.violations(shifts, shift))
    warnings = []
    availability = Availability.objects.filter(employee=employee, slot=assignment.slot).first()
    submitted = Submission.objects.filter(
        employee=employee, month=assignment.plan.month, submitted=True
    ).exists()
    if not submitted or availability is None:
        warnings.append(f'{label}: Keine abgegebene Verfügbarkeit für diese Schicht.')
    elif availability.priority == 0:
        warnings.append(f'{label}: Für diese Schicht als nicht verfügbar angegeben.')
    elif availability.priority == 3:
        warnings.append(f'{label}: Nur wenn nötig verfügbar (Priorität 3).')
    if Vacation.objects.filter(
        employee=employee, start__lte=assignment.date, end__gte=assignment.date
    ).exists():
        warnings.append(f'{label}: Urlaub ist eingetragen.')
    required = Need.objects.filter(slot=assignment.slot, qualification__name=assignment.role)
    if (
        assignment.role != 'Ohne Vorgabe'
        and not required.filter(qualification__employee=employee).exists()
    ):
        warnings.append(f'{label}: Die erforderliche Qualifikation ist nicht zugeordnet.')
    return errors, warnings


def correction_state(plan):
    """Liefert den Stand des Plans für die Prüfung einer bestätigten Vorschau.

    Args:
        plan: Zu korrigierender Plan.

    Returns:
        Prüfsumme der Positionen und ihrer zugewiesenen Personen.
    """
    rows = list(plan.assignments.order_by('pk').values_list('pk', 'employee_id'))
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()


def correction_changes(by_id, assignment_id, employee_id, swap_id):
    """Ermittelt die Positionen und Personen für eine Korrektur.

    Args:
        by_id: Positionen des Plans nach ID.
        assignment_id: Zu bearbeitende Position.
        employee_id: Ausgewählte Person oder None.
        swap_id: Zweite Position oder None.

    Returns:
        Liste von Paaren aus Position und künftig zugewiesener Person.

    Raises:
        ValueError: Wenn eine ausgewählte Person nicht mehr aktiv ist.
    """
    first = by_id[assignment_id]
    if swap_id:
        second = by_id[swap_id]
        if (first.employee and not first.employee.user.is_active) or (
            second.employee and not second.employee.user.is_active
        ):
            raise ValueError('Ein Tausch mit einer inaktiven Person ist nicht möglich.')
        return [(first, second.employee), (second, first.employee)]
    if not employee_id:
        return [(first, None)]
    employee = (
        Employee.objects.select_related('user')
        .filter(pk=employee_id, user__is_active=True)
        .first()
    )
    if employee is None:
        raise ValueError('Die ausgewählte Person ist nicht mehr aktiv oder vorhanden.')
    return [(first, employee)]


@transaction.atomic
def correct_plan(plan_id, assignment_id, employee_id=None, swap_id=None, expected=None):
    """Prüft eine Zuweisung oder einen Tausch und speichert nach bestätigter Vorschau.

    Args:
        plan_id: ID des Plans.
        assignment_id: Zu ändernde Position.
        employee_id: Neue Person oder None zum Entfernen.
        swap_id: Zweite Position für einen Tausch oder None.
        expected: Signierter Vorschauzustand; None erstellt nur eine Vorschau.

    Returns:
        Dictionary mit Fehlern, Hinweisen und dem für die Bestätigung nötigen Zustand.

    Raises:
        ValueError: Wenn die Auswahl ungültig oder die Vorschau veraltet ist.
    """
    plan = Plan.objects.select_related('month').get(pk=plan_id)
    Month.objects.select_for_update().get(pk=plan.month_id)
    plan = Plan.objects.select_for_update().select_related('month').get(pk=plan_id)
    # Personen sind optional; PostgreSQL darf die äußeren Joins nicht mitsperren.
    rows = list(
        plan.assignments.select_for_update(of=('self',)).select_related('employee__user', 'slot')
    )
    by_id = {a.pk: a for a in rows}
    if assignment_id not in by_id or (
        swap_id and (swap_id not in by_id or swap_id == assignment_id)
    ):
        raise ValueError('Die ausgewählte Position ist nicht mehr im Plan vorhanden.')
    current = {
        'revision': plan.month.revision,
        'plan_revision': plan.revision,
        'assignments': correction_state(plan),
    }
    if expected is not None and expected != current:
        raise ValueError('Der Plan oder seine Eingaben wurden geändert. Bitte erneut prüfen.')
    changes = correction_changes(by_id, assignment_id, employee_id, swap_id)
    remaining = [a for a in rows if a.pk not in {item.pk for item, _ in changes}]
    errors, warnings = [], []
    for item, person in changes:
        hard, soft = correction_messages(item, person, remaining)
        errors.extend(hard)
        warnings.extend(soft)
        if person:
            item.employee = person
            remaining.append(item)
    if expected is not None and not errors:
        for item, person in changes:
            availability = (
                Availability.objects.filter(employee=person, slot=item.slot).first()
                if person
                else None
            )
            submitted = (
                person
                and Submission.objects.filter(
                    employee=person, month=plan.month, submitted=True
                ).exists()
            )
            item.employee = person
            item.employee_name = str(person) if person else ''
            item.priority = (
                availability.priority
                if availability and submitted and availability.priority
                else None
            )
            item.save(update_fields=['employee', 'employee_name', 'priority'])
    return {'errors': errors, 'warnings': warnings, 'state': current}
