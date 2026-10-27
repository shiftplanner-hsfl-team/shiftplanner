"""Deterministische MVP-Engine. Keine Fairness- oder Rechtsregeln enthalten."""
from calendar import monthrange
from collections import defaultdict
from datetime import date, timedelta
from time import perf_counter

from django.db import transaction
from django.db.models import F

from .models import (Assignment, Availability, Employee, Month, Plan, ShiftTemplate,
                     Slot, Submission, Vacation)

MONTH_NAMES = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
               'August', 'September', 'Oktober', 'November', 'Dezember']


def month_label(value):
    return f'{MONTH_NAMES[value.month - 1]} {value.year}'


def dates_for_month(value):
    return [date(value.year, value.month, n) for n in range(1, monthrange(value.year, value.month)[1] + 1)]


def ensure_slots(month):
    existing = set(Slot.objects.filter(month=month).values_list('date', 'template_id'))
    templates = list(ShiftTemplate.objects.all())
    Slot.objects.bulk_create([
        Slot(month=month, date=day, template=t)
        for day in dates_for_month(month.date) if day.weekday() != 6
        for t in templates if (day, t.pk) not in existing
    ])


def touch(month):
    Month.objects.filter(pk=month.pk).update(revision=F('revision') + 1)
    month.refresh_from_db()


def readiness(month):
    employees = Employee.objects.filter(user__is_active=True)
    submitted = Submission.objects.filter(month=month, submitted=True, employee__in=employees).count()
    total = employees.count()
    positions = sum(Slot.objects.filter(month=month).values_list('total', flat=True))
    return dict(submitted=submitted, employees=total, positions=positions,
                ready=bool(month.demand_saved and positions and total and submitted == total))


def match_positions(roles, candidates, priorities):
    """Minimum-cost maximum matching per slot, using a residual graph.

    Maximize filled positions, then lexicographically maximize priority 1 and 2.
    Stable employee/position order resolves equal-cost paths reproducibly.
    """
    graph = defaultdict(list)
    source, sink = ('source',), ('sink',)

    def edge(a, b, cap, cost):
        graph[a].append([b, cap, cost, len(graph[b])])
        graph[b].append([a, 0, -cost, len(graph[a]) - 1])

    for emp in sorted(priorities):
        edge(source, ('e', emp), 1, 0)
    for i, _ in enumerate(roles):
        edge(('p', i), sink, 1, 0)
        for emp in candidates[i]:
            # At most 30 positions: one lost P1 is dearer than all P2->P3 changes.
            cost = {1: 0, 2: 100, 3: 101}[priorities[emp]]
            edge(('e', emp), ('p', i), 1, cost)
    while True:
        distances = {source: 0}
        previous = {}
        for _ in range(len(graph)):
            changed = False
            for u in list(graph):
                if u not in distances:
                    continue
                for j, (v, cap, cost, _) in enumerate(graph[u]):
                    if cap and distances[u] + cost < distances.get(v, float('inf')):
                        distances[v] = distances[u] + cost
                        previous[v] = (u, j)
                        changed = True
            if not changed:
                break
        if sink not in previous:
            break
        node = sink
        while node != source:
            u, j = previous[node]
            item = graph[u][j]
            item[1] -= 1
            graph[node][item[3]][1] += 1
            node = u
    result = {}
    for emp in sorted(priorities):
        for v, cap, _, _ in graph[('e', emp)]:
            if v[0] == 'p' and cap == 0:
                result[v[1]] = emp
    return result


@transaction.atomic
def generate_plan(month):
    started = perf_counter()
    month = Month.objects.select_for_update().get(pk=month.pk)
    if not readiness(month)['ready']:
        raise ValueError('Bedarf speichern und alle Verfügbarkeiten abgeben, bevor du den Plan erzeugst.')
    slots = list(Slot.objects.filter(month=month, total__gt=0).select_related('template').prefetch_related('needs__qualification'))
    employees = {e.pk: e for e in Employee.objects.filter(user__is_active=True).select_related('user').prefetch_related('qualifications')}
    qualifications = {pk: {q.pk for q in e.qualifications.all()} for pk, e in employees.items()}
    available = defaultdict(dict)
    for a in Availability.objects.filter(slot__month=month, priority__gt=0, employee_id__in=employees):
        available[a.slot_id][a.employee_id] = a.priority
    vacations = list(Vacation.objects.filter(start__lte=month.date + timedelta(days=31), end__gte=month.date))
    busy = defaultdict(list)
    rows = []
    # Chronological slots, including overlapping templates. No random state, no history.
    for slot in slots:
        needs = sorted(slot.needs.all(), key=lambda n: n.qualification_id)
        if sum(n.count for n in needs) > slot.total:
            raise ValueError('Der Besetzungsmix übersteigt die Gesamtzahl eines Slots.')
        roles = [(n.qualification_id, n.qualification.name) for n in needs for _ in range(n.count)]
        roles += [(None, 'Ohne Vorgabe')] * (slot.total - len(roles))
        priorities = {
            pk: priority for pk, priority in available[slot.pk].items()
            if not any(v.employee_id == pk and v.start <= slot.date <= v.end for v in vacations)
            and not any(day == slot.date and start < slot.template.end and slot.template.start < end
                        for day, start, end in busy[pk])
        }
        candidates = [[pk for pk in sorted(priorities) if q is None or q in qualifications[pk]] for q, _ in roles]
        matches = match_positions(roles, candidates, priorities)
        for i, (_, role) in enumerate(roles):
            emp_id = matches.get(i)
            if emp_id:
                busy[emp_id].append((slot.date, slot.template.start, slot.template.end))
            rows.append(Assignment(slot=slot, employee_id=emp_id, position=i, role=role,
                                   priority=priorities.get(emp_id), date=slot.date,
                                   shift_name=slot.template.name, start=slot.template.start,
                                   end=slot.template.end, employee_name=str(employees[emp_id]) if emp_id else ''))
    plan, _ = Plan.objects.update_or_create(month=month, defaults={'revision': month.revision, 'duration_ms': 0})
    plan.assignments.all().delete()
    for row in rows:
        row.plan = plan
    Assignment.objects.bulk_create(rows)
    plan.duration_ms = round((perf_counter() - started) * 1000)
    plan.save(update_fields=['duration_ms', 'created_at'])
    return plan
