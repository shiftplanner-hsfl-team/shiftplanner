"""Planungslogik von ShiftPlanner: Monatsaufbau, Vorbedingungen und deterministische Zuordnung.

Die Funktionen sind unabhängig von HTTP und werden von ``views.py`` aufgerufen.
Fairness-Regeln sind noch nicht enthalten (REQ-16, später).
"""

from calendar import monthrange
from collections import defaultdict
from datetime import date, timedelta
from time import perf_counter

from django.db import transaction
from django.db.models import F

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


def ensure_slots(month):
    """Legt fehlende Slots (Tag × Schichtvorlage) für einen Monat an; Sonntage bleiben frei.

    Args:
        month: Planungsmonat.
    """
    existing = set(Slot.objects.filter(month=month).values_list('date', 'template_id'))
    templates = list(ShiftTemplate.objects.all())
    Slot.objects.bulk_create(
        [
            Slot(month=month, date=day, template=t)
            for day in dates_for_month(month.date)
            if day.weekday() != 6
            for t in templates
            if (day, t.pk) not in existing
        ]
    )


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

    Returns:
        Dictionary mit Anzahl abgegebener und aktiver Mitarbeitender, Anzahl Positionen
        und ``ready`` (True, wenn Bedarf gespeichert ist und alle abgegeben haben).
    """
    employees = Employee.objects.filter(user__is_active=True)
    submitted = Submission.objects.filter(
        month=month, submitted=True, employee__in=employees
    ).count()
    total = employees.count()
    positions = sum(Slot.objects.filter(month=month).values_list('total', flat=True))
    return dict(
        submitted=submitted,
        employees=total,
        positions=positions,
        ready=bool(month.demand_saved and positions and total and submitted == total),
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


@transaction.atomic
def generate_plan(month):
    """Erzeugt den Schichtplan eines Monats und speichert ihn als Snapshot (REQ-08, REQ-09).

    Slots werden chronologisch bearbeitet. Personen im Urlaub oder mit zeitlich
    überlappender Schicht werden ausgeschlossen; nicht besetzbare Positionen bleiben
    als „unbesetzt“ (``employee=None``) im Plan.

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
            'Bedarf speichern und alle Verfügbarkeiten abgeben, bevor du den Plan erzeugst.'
        )
    slots = list(
        Slot.objects.filter(month=month, total__gt=0)
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
    available = defaultdict(dict)
    for a in Availability.objects.filter(
        slot__month=month, priority__gt=0, employee_id__in=employees
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
        priorities = {
            pk: priority
            for pk, priority in available[slot.pk].items()
            if not any(v.employee_id == pk and v.start <= slot.date <= v.end for v in vacations)
            and not any(
                day == slot.date and start < slot.template.end and slot.template.start < end
                for day, start, end in busy[pk]
            )
        }
        candidates = [
            [pk for pk in sorted(priorities) if q is None or q in qualifications[pk]]
            for q, _ in roles
        ]
        matches = match_positions(roles, candidates, priorities)
        for i, (_, role) in enumerate(roles):
            emp_id = matches.get(i)
            if emp_id:
                busy[emp_id].append((slot.date, slot.template.start, slot.template.end))
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
