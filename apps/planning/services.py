"""Planungslogik von ShiftPlanner: Monatsaufbau, Vorbedingungen und deterministische Zuordnung.

Die Funktionen sind unabhängig von HTTP und werden von ``views.py`` aufgerufen.
Rahmenbedingungen (ArbZG, Feiertage) liegen im Regelmodul ``rules.py``.
Fairness-Regeln sind noch nicht enthalten (REQ-16, später).
"""

from calendar import monthrange
from collections import defaultdict
from datetime import date, timedelta
from time import perf_counter

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from . import rules
from .models import (
    Assignment,
    Availability,
    Employee,
    Month,
    Plan,
    ShiftTemplate,
    Slot,
    Submission,
    Vacation,
)
from .rules import Shift

MONTH_NAMES = [
    'Januar',
    'Februar',
    'März',
    'April',
    'Mai',
    'Juni',
    'Juli',
    'August',
    'September',
    'Oktober',
    'November',
    'Dezember',
]


def month_label(value):
    """Formatiert einen Monat für die Oberfläche, z. B. „November 2026“.

    Args:
        value: Beliebiges Datum im Monat.

    Returns:
        Monatsname und Jahr als Zeichenkette.
    """
    return f'{MONTH_NAMES[value.month - 1]} {value.year}'


def dates_for_month(value):
    """Liefert alle Kalendertage eines Monats.

    Args:
        value: Beliebiges Datum im Monat.

    Returns:
        Liste aller ``date``-Objekte des Monats.
    """
    return [
        date(value.year, value.month, n)
        for n in range(1, monthrange(value.year, value.month)[1] + 1)
    ]


def open_days(month):
    """Liefert die Öffnungstage eines Monats (REQ-22).

    Grundlage sind die geöffneten Wochentage des Monats (Standard Montag–Samstag);
    einzelne Tage können davon abweichend geöffnet oder geschlossen werden.

    Args:
        month: Planungsmonat.

    Returns:
        Sortierte Liste der geöffneten Tage.
    """
    exceptions = dict(month.day_exceptions.values_list('date', 'is_open'))
    return [
        day
        for day in dates_for_month(month.date)
        if exceptions.get(day, str(day.weekday()) in month.open_weekdays)
    ]


def month_slots(month):
    """Liefert die Slots der Öffnungstage eines Monats (Bedarf, Verfügbarkeit, Plan).

    Slots geschlossener Tage bleiben gespeichert, werden aber nicht angezeigt oder geplant.

    Args:
        month: Planungsmonat.

    Returns:
        QuerySet von ``Slot``.
    """
    return Slot.objects.filter(month=month, date__in=open_days(month))


def ensure_slots(month):
    """Legt fehlende Slots (Tag × Schichtvorlage) für alle Öffnungstage eines Monats an.

    Args:
        month: Planungsmonat.
    """
    existing = set(Slot.objects.filter(month=month).values_list('date', 'template_id'))
    templates = list(ShiftTemplate.objects.all())
    Slot.objects.bulk_create(
        [
            Slot(month=month, date=day, template=t)
            for day in open_days(month)
            for t in templates
            if (day, t.pk) not in existing
        ]
    )


@transaction.atomic
def set_opening(month, weekdays, day=None, is_open=None):
    """Ändert die Öffnungstage eines Monats und legt fehlende Slots an (REQ-22).

    Args:
        month: Planungsmonat.
        weekdays: Geöffnete Wochentage als Zahlen 0 (Montag) bis 6 (Sonntag).
        day: Optional ein einzelnes Datum im Monat, das abweichend gilt.
        is_open: Für ``day``: True = geöffnet, False = geschlossen.

    Raises:
        ValueError: Wenn kein Wochentag geöffnet ist oder ``day`` nicht im Monat liegt.
    """
    if not weekdays:
        raise ValueError('Mindestens ein Wochentag muss geöffnet sein.')
    month.open_weekdays = ''.join(str(d) for d in sorted(set(weekdays)))
    month.save(update_fields=['open_weekdays'])
    if day is not None:
        if (day.year, day.month) != (month.date.year, month.date.month):
            raise ValueError('Der Tag muss im gewählten Planungsmonat liegen.')
        month.day_exceptions.update_or_create(date=day, defaults={'is_open': is_open})
    ensure_slots(month)
    touch(month)


def today():
    """Liefert das aktuelle Datum in der Zeitzone des Betriebs.

    Ist ``settings.SHIFTPLANNER_TODAY`` gesetzt (Demo, Tests), wird dieses Datum verwendet.

    Returns:
        Heutiges Datum als ``date``.
    """
    if settings.SHIFTPLANNER_TODAY:
        return date.fromisoformat(settings.SHIFTPLANNER_TODAY)
    return timezone.localdate()


PERIOD_CLOSED, PERIOD_OPEN, PERIOD_EXPIRED = 'nicht geöffnet', 'offen', 'geschlossen'


def period_status(month):
    """Bestimmt den Status des Planungszeitraums (REQ-05).

    Args:
        month: Planungsmonat.

    Returns:
        ``PERIOD_CLOSED`` ohne Frist, ``PERIOD_OPEN`` bis einschließlich zum Fristtag,
        danach ``PERIOD_EXPIRED``.
    """
    if month.deadline is None:
        return PERIOD_CLOSED
    return PERIOD_OPEN if today() <= month.deadline else PERIOD_EXPIRED


def input_open(month):
    """Prüft, ob Mitarbeitende Verfügbarkeiten eintragen dürfen (REQ-05 AK 3, REQ-07 AK 2).

    Args:
        month: Planungsmonat.

    Returns:
        True nur bei geöffnetem Zeitraum vor Ablauf der Frist.
    """
    return period_status(month) == PERIOD_OPEN


@transaction.atomic
def set_deadline(month, deadline):
    """Öffnet den Planungszeitraum bzw. ändert seine Abgabefrist (REQ-05 AK 1–2).

    Args:
        month: Planungsmonat.
        deadline: Neue Abgabefrist als ``date``.

    Raises:
        ValueError: Wenn die Frist nicht vor dem Beginn des Zeitraums liegt.
    """
    if deadline >= month.date:
        raise ValueError('Die Abgabefrist muss vor dem Beginn des Planungszeitraums liegen.')
    month.deadline = deadline
    month.save(update_fields=['deadline'])
    touch(month)


@transaction.atomic
def save_employee(data, employee=None):
    """Legt eine Person mit Konto an oder aktualisiert sie (REQ-02 AK 1, AK 3).

    Bestehende Pläne bleiben unverändert, weil sie Namen und Rollen als Snapshot
    speichern; alle Monate werden als geändert markiert, damit der nächste Plan
    die neuen Angaben verwendet.

    Args:
        data: Bereinigte Daten aus ``EmployeeForm``.
        employee: Bestehende Person oder ``None`` zum Anlegen.

    Returns:
        Gespeichertes ``Employee``-Objekt.
    """
    if employee is None:
        user = User.objects.create_user(data['email'], data['email'], data['password'])
        employee = Employee(user=user)
    else:
        user = employee.user
        user.username = user.email = data['email']
        if data['password']:
            user.set_password(data['password'])
    user.first_name, user.last_name = data['first_name'], data['last_name']
    user.save()
    employee.contract_type = data['contract_type']
    employee.weekly_hours = data['weekly_hours']
    employee.save()
    employee.qualifications.set(data['qualifications'])
    for month in Month.objects.select_for_update():
        touch(month)
    return employee


def touch(month):
    """Erhöht den Revisionszähler; ein vorhandener Plan gilt danach als veraltet.

    Args:
        month: Planungsmonat; wird aus der Datenbank neu geladen.
    """
    Month.objects.filter(pk=month.pk).update(revision=F('revision') + 1)
    month.refresh_from_db()


def readiness(month):
    """Prüft die Vorbedingungen der Planerzeugung (UC-04).

    Args:
        month: Planungsmonat.

    Der Plan ist erzeugbar, wenn der Bedarf gespeichert ist und entweder alle aktiven
    Mitarbeitenden abgegeben haben (REQ-05 AK 4) oder die Abgabefrist abgelaufen ist
    (REQ-05 AK 3); fehlende Abgaben gelten dann als „nicht verfügbar“ (REQ-06 AK 3).

    Args:
        month: Planungsmonat.

    Returns:
        Dictionary mit Anzahl abgegebener, aktiver und fehlender Mitarbeitender, Anzahl
        Positionen, Zeitraumstatus, ``expired`` und ``ready``.
    """
    employees = Employee.objects.filter(user__is_active=True)
    submitted = Submission.objects.filter(
        month=month, submitted=True, employee__in=employees
    ).count()
    total = employees.count()
    positions = sum(month_slots(month).values_list('total', flat=True))
    status = period_status(month)
    expired = status == PERIOD_EXPIRED
    inputs_complete = submitted == total or expired
    return dict(
        submitted=submitted,
        employees=total,
        missing=total - submitted,
        positions=positions,
        status=status,
        expired=expired,
        ready=bool(month.demand_saved and positions and total and inputs_complete),
    )


PRIORITY_COST = {1: 0, 2: 100, 3: 101}
"""Kosten je Priorität: Bei höchstens 30 Positionen wiegt ein verlorenes P1 schwerer
als alle Wechsel von P2 zu P3 zusammen (P1 vor P2 vor P3, REQ-08)."""

SOURCE, SINK = ('source',), ('sink',)


def build_graph(roles, candidates, priorities):
    """Baut das Flussnetz Quelle → Person → Position → Senke für einen Slot.

    Args:
        roles: Positionen des Slots als Liste ``(qualification_id, name)``.
        candidates: Je Position die sortierten IDs zulässiger Personen.
        priorities: Zuordnung Personen-ID → Priorität 1–3 für diesen Slot.

    Returns:
        Restgraph als ``defaultdict(list)``; jede Kante ist ``[ziel, kapazität, kosten,
        index_der_rückkante]``.
    """
    graph = defaultdict(list)

    def edge(a, b, cap, cost):
        graph[a].append([b, cap, cost, len(graph[b])])
        graph[b].append([a, 0, -cost, len(graph[a]) - 1])

    for emp in sorted(priorities):
        edge(SOURCE, ('e', emp), 1, 0)
    for i, _ in enumerate(roles):
        edge(('p', i), SINK, 1, 0)
        for emp in candidates[i]:
            edge(('e', emp), ('p', i), 1, PRIORITY_COST[priorities[emp]])
    return graph


def relax_edges(graph, distances, previous):
    """Führt eine Bellman-Ford-Runde über alle Kanten mit Restkapazität aus.

    Args:
        graph: Restgraph aus ``build_graph``.
        distances: Bisher bekannte minimale Kosten je Knoten; wird verändert.
        previous: Vorgängerkante je Knoten ``(knoten, kantenindex)``; wird verändert.

    Returns:
        True, wenn sich mindestens eine Distanz verbessert hat.
    """
    changed = False
    for u in list(graph):
        if u not in distances:
            continue
        for j, (v, cap, cost, _) in enumerate(graph[u]):
            if cap and distances[u] + cost < distances.get(v, float('inf')):
                distances[v] = distances[u] + cost
                previous[v] = (u, j)
                changed = True
    return changed


def cheapest_path(graph):
    """Sucht den kostengünstigsten Pfad von der Quelle zur Senke (Bellman-Ford).

    Negative Kosten entstehen durch Rückkanten, daher kein Dijkstra.

    Args:
        graph: Restgraph aus ``build_graph``.

    Returns:
        Vorgängerkanten je Knoten oder ``None``, wenn die Senke nicht erreichbar ist.
    """
    distances, previous = {SOURCE: 0}, {}
    for _ in range(len(graph)):
        if not relax_edges(graph, distances, previous):
            break
    return previous if SINK in previous else None


def augment(graph, previous):
    """Schickt eine Flusseinheit entlang des gefundenen Pfads (eine Person → eine Position).

    Args:
        graph: Restgraph; Kapazitäten werden verändert.
        previous: Vorgängerkanten aus ``cheapest_path``.
    """
    node = SINK
    while node != SOURCE:
        u, j = previous[node]
        item = graph[u][j]
        item[1] -= 1
        graph[node][item[3]][1] += 1
        node = u


def match_positions(roles, candidates, priorities):
    """Ordnet Personen den Positionen eines Slots zu (Minimum-Cost-Maximum-Matching, REQ-08).

    Zuerst werden möglichst viele Positionen besetzt, danach möglichst viele mit
    Priorität 1, dann 2. Die feste Reihenfolge der IDs macht das Ergebnis bei
    gleichen Kosten reproduzierbar (deterministisch).

    Args:
        roles: Positionen des Slots als Liste ``(qualification_id, name)``.
        candidates: Je Position die sortierten IDs zulässiger Personen.
        priorities: Zuordnung Personen-ID → Priorität 1–3 für diesen Slot.

    Returns:
        Dictionary Positionsindex → Personen-ID; nicht besetzte Positionen fehlen.
    """
    graph = build_graph(roles, candidates, priorities)
    while (previous := cheapest_path(graph)) is not None:
        augment(graph, previous)
    result = {}
    for emp in sorted(priorities):
        for v, cap, _, _ in graph[('e', emp)]:
            if v[0] == 'p' and cap == 0:
                result[v[1]] = emp
    return result


def overlaps(shift, other):
    """Prüft, ob sich zwei Schichten zeitlich überschneiden (angrenzend ist erlaubt).

    Args:
        shift: Erste ``Shift``.
        other: Zweite ``Shift``.

    Returns:
        True bei Überschneidung.
    """
    return shift.begins < other.ends and other.begins < shift.ends


def is_eligible(shift, assigned, vacations):
    """Filtert Kandidaten einer Schicht: Urlaub, Überschneidung und RB-01 (Erweiterungspunkt).

    Args:
        shift: Zu besetzende ``Shift``.
        assigned: Bereits zugewiesene Schichten der Person im Monat.
        vacations: Urlaube der Person.

    Returns:
        True, wenn die Person die Schicht übernehmen darf.
    """
    if any(v.start <= shift.day <= v.end for v in vacations):
        return False
    if any(overlaps(shift, other) for other in assigned):
        return False
    return rules.is_allowed(assigned, shift)


def assignment_violations(plan, employee, slot):
    """Prüft eine manuelle Zuweisung gegen RB-01 (für REQ-11, manuelle Korrektur).

    Berücksichtigt alle übrigen Zuweisungen der Person im selben Plan.

    Args:
        plan: Gespeicherter ``Plan``.
        employee: ``Employee``, die zugewiesen werden soll.
        slot: ``Slot`` der Position.

    Returns:
        Liste verständlicher Meldungen (leer = zulässig); Überschneidungen zuerst.
    """
    shift = Shift(slot.date, slot.template.start, slot.template.end)
    assigned = [
        Shift(a.date, a.start, a.end)
        for a in plan.assignments.filter(employee=employee).exclude(slot=slot)
    ]
    messages = [
        f'Überschneidung mit einer anderen Schicht am {other.day:%d.%m.}.'
        for other in assigned
        if overlaps(shift, other)
    ]
    return messages + rules.violations(assigned, shift)


@transaction.atomic
def generate_plan(month):
    """Erzeugt den Schichtplan eines Monats und speichert ihn als Snapshot (REQ-08, REQ-09).

    Slots werden chronologisch bearbeitet. Berücksichtigt werden nur abgegebene
    Verfügbarkeiten (REQ-07). Personen im Urlaub, mit zeitlich überlappender Schicht
    oder bei einem Verstoß gegen das Arbeitszeitgesetz (RB-01) werden ausgeschlossen;
    nicht besetzbare Positionen bleiben als „unbesetzt“ (``employee=None``) im Plan.

    Args:
        month: Planungsmonat.

    Returns:
        Gespeicherter ``Plan`` mit Laufzeit in ``duration_ms``.

    Raises:
        ValueError: Wenn Vorbedingungen fehlen oder der Besetzungsmix die Gesamtzahl übersteigt.
    """
    started = perf_counter()
    month = Month.objects.select_for_update().get(pk=month.pk)
    if not readiness(month)['ready']:
        raise ValueError(
            'Bedarf speichern und alle Verfügbarkeiten abwarten (oder Fristablauf), '
            'bevor du den Plan erzeugst.'
        )
    slots = list(
        month_slots(month)
        .filter(total__gt=0)
        .select_related('template')
        .prefetch_related('needs__qualification')
    )
    employees = {
        e.pk: e
        for e in Employee.objects.filter(user__is_active=True)
        .select_related('user')
        .prefetch_related('qualifications')
    }
    qualifications = {pk: {q.pk for q in e.qualifications.all()} for pk, e in employees.items()}
    # Nur abgegebene Angaben zählen; ohne Abgabe gilt eine Person als nicht verfügbar.
    submitted = Submission.objects.filter(
        month=month, submitted=True, employee_id__in=employees
    ).values_list('employee_id', flat=True)
    available = defaultdict(dict)
    for a in Availability.objects.filter(
        slot__month=month, priority__gt=0, employee_id__in=list(submitted)
    ):
        available[a.slot_id][a.employee_id] = a.priority
    vacations = list(
        Vacation.objects.filter(start__lte=month.date + timedelta(days=31), end__gte=month.date)
    )
    busy = defaultdict(list)
    rows = []
    # Chronologisch, inkl. überlappender Vorlagen. Kein Zufall, kein Planverlauf.
    for slot in slots:
        needs = sorted(slot.needs.all(), key=lambda n: n.qualification_id)
        if sum(n.count for n in needs) > slot.total:
            raise ValueError('Der Besetzungsmix übersteigt die Gesamtzahl eines Slots.')
        roles = [(n.qualification_id, n.qualification.name) for n in needs for _ in range(n.count)]
        roles += [(None, 'Ohne Vorgabe')] * (slot.total - len(roles))
        shift = Shift(slot.date, slot.template.start, slot.template.end)
        priorities = {
            pk: priority
            for pk, priority in available[slot.pk].items()
            if is_eligible(shift, busy[pk], [v for v in vacations if v.employee_id == pk])
        }
        candidates = [
            [pk for pk in sorted(priorities) if q is None or q in qualifications[pk]]
            for q, _ in roles
        ]
        matches = match_positions(roles, candidates, priorities)
        for i, (_, role) in enumerate(roles):
            emp_id = matches.get(i)
            if emp_id:
                busy[emp_id].append(shift)
            rows.append(
                Assignment(
                    slot=slot,
                    employee_id=emp_id,
                    position=i,
                    role=role,
                    priority=priorities.get(emp_id),
                    date=slot.date,
                    shift_name=slot.template.name,
                    start=slot.template.start,
                    end=slot.template.end,
                    employee_name=str(employees[emp_id]) if emp_id else '',
                )
            )
    plan, _ = Plan.objects.update_or_create(
        month=month, defaults={'revision': month.revision, 'duration_ms': 0}
    )
    plan.assignments.all().delete()
    for row in rows:
        row.plan = plan
    Assignment.objects.bulk_create(rows)
    plan.duration_ms = round((perf_counter() - started) * 1000)
    plan.save(update_fields=['duration_ms', 'created_at'])
    return plan
