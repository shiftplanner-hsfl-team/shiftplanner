from datetime import date, timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render

from .forms import QualificationForm, TemplateForm, VacationForm
from .models import (Availability, Employee, Month, Need, Plan, Qualification,
                     ShiftTemplate, Slot, Submission, Vacation)
from .services import ensure_slots, generate_plan, month_label, readiness, touch


def planner_only(view):
    @wraps(view)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not request.user.groups.filter(name='Planung').exists():
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped


def is_planner(user):
    return user.groups.filter(name='Planung').exists()


def context(request):
    raw = request.GET.get('month') or request.POST.get('month') or '2026-11'
    try:
        day = date.fromisoformat(raw + '-01')
        if day.year < 2020 or day.year > 2100:
            raise ValueError
    except ValueError:
        raise ValueError('Bitte einen gültigen Monat zwischen 2020 und 2100 wählen.')
    month, _ = Month.objects.get_or_create(date=day)
    ensure_slots(month)
    slots = Slot.objects.filter(month=month).select_related('template').prefetch_related('needs__qualification')
    dates = sorted({s.date for s in slots})
    weeks = sorted({d.isocalendar().week for d in dates})
    try:
        week = int(request.GET.get('week', weeks[0] if weeks else 1))
    except ValueError:
        week = weeks[0] if weeks else 1
    if weeks and week not in weeks:
        week = weeks[0]
    days = [d for d in dates if d.isocalendar().week == week]
    planner = is_planner(request.user)
    return dict(month=month, month_value=raw, month_label=month_label(day),
                month_name=month_label(day).rsplit(' ', 1)[0], slots=list(slots),
                days=days, week=week, weeks=weeks, planner=planner,
                readiness=readiness(month), display_name=request.user.get_full_name() or request.user.username,
                initials=''.join(n[0] for n in [request.user.first_name, request.user.last_name] if n) or 'SP')


def with_context(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try:
            return view(request, context(request), *args, **kwargs)
        except ValueError as error:
            return HttpResponseBadRequest(str(error))
    return wrapped


def go(name, ctx):
    from django.urls import reverse
    return redirect(f'{reverse(name)}?month={ctx["month_value"]}&week={ctx["week"]}')


def table_rows(ctx, values):
    return [dict(template=t, cells=[dict(slot=s, **values(s)) for s in ctx['slots']
                                  if s.template_id == t.pk and s.date in ctx['days']])
            for t in ShiftTemplate.objects.all()]


@login_required
@with_context
def dashboard(request, ctx):
    if ctx['planner']:
        ctx['plan'] = Plan.objects.filter(month=ctx['month']).first()
        ctx['template_count'] = ShiftTemplate.objects.count()
        ctx['slot_count'] = sum(s.total > 0 for s in ctx['slots'])
        return render(request, 'planning/dashboard.html', ctx)
    employee = get_object_or_404(Employee, user=request.user)
    ctx['submission'] = Submission.objects.filter(employee=employee, month=ctx['month']).first()
    ctx['available_count'] = Availability.objects.filter(employee=employee, slot__month=ctx['month'], priority__gt=0).count()
    return render(request, 'planning/employee_home.html', ctx)


@planner_only
@with_context
def demand(request, ctx):
    quals = list(Qualification.objects.all().order_by('pk'))
    if request.method == 'POST':
        rows = []
        errors = []
        for s in ctx['slots']:
            if f'total_{s.pk}' not in request.POST:
                continue
            try:
                total = int(request.POST[f'total_{s.pk}'])
                mix = [(q, int(request.POST.get(f'need_{s.pk}_{q.pk}', 0))) for q in quals]
                if not 0 <= total <= 30 or any(not 0 <= count <= 30 for _, count in mix):
                    raise ValueError
                if sum(count for _, count in mix) > total:
                    errors.append(f'{s.date:%d.%m.} · {s.template}: Der Besetzungsmix übersteigt die Gesamtzahl.')
                rows.append((s, total, mix))
            except (ValueError, TypeError):
                errors.append('Bitte ganze Zahlen zwischen 0 und 30 eingeben.')
        if errors:
            for s in ctx['slots']:
                if f'total_{s.pk}' in request.POST:
                    s.total = request.POST[f'total_{s.pk}']
            for error in sorted(set(errors)):
                messages.error(request, error)
        elif rows:
            with transaction.atomic():
                Month.objects.select_for_update().get(pk=ctx['month'].pk)
                if request.POST.get('action') == 'copy_month':
                    by_weekday = {(s.date.weekday(), s.template_id): (total, mix) for s, total, mix in rows}
                    rows = [(s, *by_weekday[(s.date.weekday(), s.template_id)]) for s in ctx['slots'] if (s.date.weekday(), s.template_id) in by_weekday]
                for s, total, mix in rows:
                    s.total = total
                    s.save(update_fields=['total'])
                    for q, count in mix:
                        Need.objects.update_or_create(slot=s, qualification=q, defaults={'count': count})
                ctx['month'].demand_saved = True
                ctx['month'].save(update_fields=['demand_saved'])
                touch(ctx['month'])
            messages.success(request, 'Personalbedarf gespeichert. Der Besetzungsmix wird bei der Planung berücksichtigt.')
            return go('demand', ctx)
    def values(s):
        mix = {n.qualification_id: n.count for n in s.needs.all()}
        return {'mix': [(q, request.POST.get(f'need_{s.pk}_{q.pk}', mix.get(q.pk, 0))) for q in quals]}
    ctx['rows'] = table_rows(ctx, values)
    return render(request, 'planning/demand.html', ctx)


@planner_only
@with_context
def templates(request, ctx):
    selected = request.GET.get('edit') or request.POST.get('id')
    instance = get_object_or_404(ShiftTemplate, pk=selected) if selected else None
    form = TemplateForm(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            form.save()
            # Changing shared templates invalidates all existing plan inputs.
            for month in Month.objects.select_for_update():
                ensure_slots(month)
                touch(month)
        messages.success(request, 'Schichtvorlage gespeichert.')
        return go('templates', ctx)
    ctx.update(form=form, editing=instance, templates=ShiftTemplate.objects.all())
    return render(request, 'planning/templates.html', ctx)


@planner_only
@with_context
def qualifications(request, ctx):
    selected = request.GET.get('edit') or request.POST.get('id')
    instance = get_object_or_404(Qualification, pk=selected) if selected else None
    form = QualificationForm(request.POST or None, instance=instance)
    employees = list(Employee.objects.select_related('user').prefetch_related('qualifications').order_by('pk'))
    selected_ids = set(Employee.objects.filter(qualifications=instance).values_list('pk', flat=True)) if instance else set()
    if request.method == 'POST' and form.is_valid():
        try:
            submitted = {int(pk) for pk in request.POST.getlist('employees')}
        except ValueError:
            return HttpResponseBadRequest('Ungültige Mitarbeitenden-Auswahl.')
        if not submitted <= {e.pk for e in employees}:
            return HttpResponseBadRequest('Unbekannte Mitarbeitende.')
        with transaction.atomic():
            q = form.save()
            q.employee_set.set([e for e in employees if e.pk in submitted])
            for month in Month.objects.select_for_update():
                touch(month)
        messages.success(request, 'Qualifikation und Zuordnungen gespeichert.')
        return go('qualifications', ctx)
    ctx.update(form=form, editing=instance, qualifications=Qualification.objects.annotate(employee_count=Count('employee')).order_by('pk'),
               employee_choices=[(e, e.pk in selected_ids) for e in employees])
    return render(request, 'planning/qualifications.html', ctx)


@planner_only
@with_context
def availability_overview(request, ctx):
    form = VacationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            vacation = form.save()
            for month in Month.objects.select_for_update():
                if month.date <= vacation.end and (month.date.replace(day=28) + timedelta(days=4)).replace(day=1) > vacation.start:
                    touch(month)
        messages.success(request, 'Urlaub gespeichert. Die Person wird in diesem Zeitraum nicht eingeplant.')
        return go('availability_overview', ctx)
    submissions = {s.employee_id: s for s in Submission.objects.filter(month=ctx['month'])}
    ctx['people'] = [(e, submissions.get(e.pk)) for e in Employee.objects.filter(user__is_active=True).select_related('user').order_by('pk')]
    ctx['available_count'] = Availability.objects.filter(slot__month=ctx['month'], priority__gt=0).count()
    ctx['vacations'] = Vacation.objects.filter(start__lt=ctx['month'].date + timedelta(days=31), end__gte=ctx['month'].date).select_related('employee__user')
    ctx['vacation_form'] = form
    return render(request, 'planning/availability_overview.html', ctx)


@login_required
@with_context
def availability(request, ctx, employee_id=None):
    if employee_id is None:
        employee = get_object_or_404(Employee, user=request.user)
    else:
        if not ctx['planner'] and not Employee.objects.filter(pk=employee_id, user=request.user).exists():
            raise PermissionDenied
        employee = get_object_or_404(Employee.objects.select_related('user'), pk=employee_id)
    read_only = employee.user_id != request.user.pk
    if request.method == 'POST':
        if read_only:
            raise PermissionDenied
        parsed = []
        for slot in ctx['slots']:
            key = f'priority_{slot.pk}'
            if key not in request.POST:
                continue
            try:
                value = int(request.POST[key])
                if value not in range(4):
                    raise ValueError
                parsed.append((slot, value))
            except ValueError:
                return HttpResponseBadRequest('Priorität muss 0, 1, 2 oder 3 sein.')
        with transaction.atomic():
            Month.objects.select_for_update().get(pk=ctx['month'].pk)
            for slot, value in parsed:
                Availability.objects.update_or_create(employee=employee, slot=slot, defaults={'priority': value})
            submit = request.POST.get('action') == 'submit'
            Submission.objects.update_or_create(employee=employee, month=ctx['month'], defaults={'submitted': submit})
            touch(ctx['month'])
        messages.success(request, 'Alles abgegeben. Deine Verfügbarkeiten sind bei der Planung angekommen.' if submit else 'Entwurf gespeichert. Zum Abschluss bitte deine Angaben abgeben.')
        return go('availability', ctx)
    priorities = dict(Availability.objects.filter(employee=employee, slot__month=ctx['month']).values_list('slot_id', 'priority'))
    ctx['rows'] = table_rows(ctx, lambda s: {'priority': priorities.get(s.pk, 0)})
    ctx['mobile_days'] = [(day, [dict(slot=s, priority=priorities.get(s.pk, 0)) for s in ctx['slots'] if s.date == day]) for day in ctx['days']]
    ctx.update(employee=employee, read_only=read_only, submission=Submission.objects.filter(employee=employee, month=ctx['month']).first(),
               priority_choices=[(0, '× Nicht verfügbar'), (1, '1 Bevorzugt'), (2, '2 Möglich'), (3, '3 Nur wenn nötig')])
    return render(request, 'planning/availability.html', ctx)


@planner_only
@with_context
def generate(request, ctx):
    if request.method == 'POST':
        try:
            result = generate_plan(ctx['month'])
            messages.success(request, f'Schichtplan erzeugt · {result.duration_ms} ms. Das Ergebnis ist nur lesbar.')
            return go('plan', ctx)
        except ValueError as error:
            messages.error(request, str(error))
    return render(request, 'planning/generate.html', ctx)


def plan_context(ctx):
    result = Plan.objects.filter(month=ctx['month']).first()
    ctx['plan'] = result
    if not result:
        return
    rows = list(result.assignments.all())
    ctx.update(assigned=sum(a.employee_id is not None for a in rows), total=len(rows),
               unfilled_count=sum(a.employee_id is None for a in rows),
               preferred=sum(a.priority == 1 for a in rows), stale=result.revision != ctx['month'].revision)
    days = ctx['days']
    grouped = {}
    for a in rows:
        if a.date not in days:
            continue
        key = (a.shift_name, a.start, a.end)
        grouped.setdefault(key, defaultdict_list())
        grouped[key][a.date].append(a)
    from collections import Counter
    def cell_summary(assignments):
        counts = Counter(a.role for a in assignments if a.employee_id)
        return dict(assignments=assignments,
                    names=' · '.join(a.employee_name.split()[0] for a in assignments if a.employee_id),
                    missing=sum(a.employee_id is None for a in assignments),
                    roles=' · '.join(f'{count} {role}' for role, count in counts.items()),
                    full_names='; '.join(f'{a.employee_name or "Unbesetzt"}: {a.role}' for a in assignments))
    ctx['plan_rows'] = [dict(name=key[0], start=key[1], end=key[2], cells=[cell_summary(group.get(day, [])) for day in days]) for key, group in grouped.items()]
    ctx['unfilled_rows'] = [a for a in rows if a.employee_id is None]


def defaultdict_list():
    from collections import defaultdict
    return defaultdict(list)


@planner_only
@with_context
def plan(request, ctx):
    plan_context(ctx)
    return render(request, 'planning/plan.html', ctx)


@planner_only
@with_context
def unfilled(request, ctx):
    plan_context(ctx)
    return render(request, 'planning/unfilled.html', ctx)


def forbidden(request, exception=None):
    return render(request, 'planning/403.html', status=403)
