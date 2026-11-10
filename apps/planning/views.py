"""HTTP-Schicht von ShiftPlanner: Anmeldung, Rollenprüfung, Formulare und Seitenaufbau.

Die Views prüfen Zugriffsrechte, lesen Eingaben, rufen die Planungslogik in
``services.py`` auf und rendern die Templates. Fachliche Planungsregeln liegen
nicht hier, sondern in ``services.py`` (siehe docs/design/architektur.md).
"""

from collections import Counter, defaultdict
from datetime import date, timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from . import rules
from .autofill import fill_unassigned
from .corrections import correct_plan
from .forms import (
    CorrectionForm,
    DeadlineForm,
    EmployeeForm,
    OpeningForm,
    PlanVisibilityForm,
    QualificationForm,
    TemplateForm,
    VacationForm,
)
from .models import (
    Assignment,
    Availability,
    Employee,
    Month,
    Need,
    Plan,
    PlanningSettings,
    PublishedPlan,
    Qualification,
    ShiftTemplate,
    Submission,
    Vacation,
)
from .publications import publication_preview, publish_plan, published_timetable, team_plan_visible
from .rules import Shift
from .services import (
    ensure_slots,
    generate_plan,
    input_open,
    month_label,
    month_slots,
    open_days,
    period_status,
    readiness,
    save_employee,
    set_deadline,
    set_opening,
    touch,
)

PLANNER_GROUP = 'Planung'
WEEKDAY_SHORT = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']
MAX_PER_SLOT = 30


def is_planner(user):
    """Prüft, ob ein Konto zur Planungsrolle (Chef) gehört.

    Args:
        user: Angemeldetes Django-Benutzerkonto.

    Returns:
        True, wenn das Konto in der Gruppe „Planung“ ist.
    """
    return user.groups.filter(name=PLANNER_GROUP).exists()


def planner_only(view):
    """Decorator: lässt nur angemeldete Konten der Planungsrolle zu (QR-03).

    Args:
        view: View-Funktion, die geschützt werden soll.

    Returns:
        Gekapselte View; nicht angemeldete Konten werden zur Anmeldung umgeleitet,
        andere Rollen erhalten HTTP 403.
    """

    @wraps(view)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not is_planner(request.user):
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapped


def parse_month(raw):
    """Wandelt einen Monatsparameter ``JJJJ-MM`` in den ersten Tag des Monats um.

    Args:
        raw: Zeichenkette aus GET/POST, z. B. ``'2026-11'``.

    Returns:
        ``date`` des Monatsersten.

    Raises:
        ValueError: Wenn das Format ungültig ist oder das Jahr außerhalb 2020–2100 liegt.
    """
    try:
        day = date.fromisoformat(raw + '-01')
    except ValueError:
        day = None
    if day is None or not 2020 <= day.year <= 2100:
        raise ValueError('Bitte einen gültigen Monat zwischen 2020 und 2100 wählen.')
    return day


def selected_week(request, weeks):
    """Bestimmt die angezeigte Kalenderwoche; ungültige Angaben fallen auf die erste zurück.

    Args:
        request: Aktuelle Anfrage mit optionalem GET-Parameter ``week``.
        weeks: Sortierte Liste der Kalenderwochen des Monats.

    Returns:
        Gültige Kalenderwoche (int).
    """
    first = weeks[0] if weeks else 1
    try:
        week = int(request.GET.get('week', first))
    except ValueError:
        return first
    return week if not weeks or week in weeks else first


def context(request):
    """Baut den gemeinsamen Seitenkontext für Monat, Woche, Slots und Rolle.

    Args:
        request: Aktuelle Anfrage mit optionalen Parametern ``month`` und ``week``.

    Returns:
        Dictionary mit Monat, Slots, Tagen der Woche, Rolle, Abgabestand und Anzeigenamen.

    Raises:
        ValueError: Bei ungültigem Monatsparameter.
    """
    raw = request.GET.get('month') or request.POST.get('month') or '2026-11'
    day = parse_month(raw)
    month, _ = Month.objects.get_or_create(date=day)
    ensure_slots(month)
    slots = month_slots(month).select_related('template').prefetch_related('needs__qualification')
    dates = sorted({s.date for s in slots})
    weeks = sorted({d.isocalendar().week for d in dates})
    week = selected_week(request, weeks)
    user = request.user
    return dict(
        month=month,
        month_value=raw,
        month_label=month_label(day),
        month_name=month_label(day).rsplit(' ', 1)[0],
        slots=list(slots),
        days=[d for d in dates if d.isocalendar().week == week],
        week=week,
        weeks=weeks,
        planner=is_planner(user),
        readiness=readiness(month),
        display_name=user.get_full_name() or user.username,
        initials=''.join(n[0] for n in [user.first_name, user.last_name] if n) or 'SP',
    )


def with_context(view):
    """Decorator: übergibt der View den gemeinsamen Kontext als zweites Argument.

    Args:
        view: View-Funktion mit Signatur ``(request, ctx, ...)``.

    Returns:
        Gekapselte View; ungültige Monatsangaben ergeben HTTP 400.
    """

    @wraps(view)
    def wrapped(request, *args, **kwargs):
        try:
            return view(request, context(request), *args, **kwargs)
        except ValueError as error:
            return HttpResponseBadRequest(str(error))

    return wrapped


def go(name, ctx):
    """Leitet auf eine benannte Seite um und behält Monat und Woche bei.

    Args:
        name: URL-Name aus ``shiftplanner/urls.py``.
        ctx: Seitenkontext mit ``month_value`` und ``week``.

    Returns:
        HTTP-Redirect.
    """
    return redirect(f'{reverse(name)}?month={ctx["month_value"]}&week={ctx["week"]}')


def table_rows(ctx, values):
    """Erzeugt die Tabellenzeilen Vorlage × Tag für die gewählte Woche.

    Args:
        ctx: Seitenkontext mit ``slots`` und ``days``.
        values: Funktion, die für einen Slot zusätzliche Zellwerte liefert.

    Returns:
        Liste von Zeilen mit ``template`` und ``cells``.
    """
    return [
        dict(
            template=t,
            cells=[
                dict(slot=s, **values(s))
                for s in ctx['slots']
                if s.template_id == t.pk and s.date in ctx['days']
            ],
        )
        for t in ShiftTemplate.objects.all()
    ]


@login_required
@with_context
def dashboard(request, ctx):
    """Startseite: Planungsübersicht für den Chef, Abgabestatus für Mitarbeitende."""
    if ctx['planner']:
        ctx['plan'] = Plan.objects.filter(month=ctx['month']).first()
        ctx['template_count'] = ShiftTemplate.objects.count()
        ctx['slot_count'] = sum(s.total > 0 for s in ctx['slots'])
        ctx['deadline_form'] = DeadlineForm(initial={'deadline': ctx['month'].deadline})
        return render(request, 'planning/dashboard.html', ctx)
    employee = get_object_or_404(Employee, user=request.user)
    ctx['submission'] = Submission.objects.filter(employee=employee, month=ctx['month']).first()
    ctx['publication'] = PublishedPlan.objects.filter(month=ctx['month']).first()
    ctx['input_open'] = input_open(ctx['month'])
    ctx['available_count'] = Availability.objects.filter(
        employee=employee, slot__month=ctx['month'], priority__gt=0
    ).count()
    return render(request, 'planning/employee_home.html', ctx)


@planner_only
@with_context
def period(request, ctx):
    """Planungszeitraum mit Abgabefrist öffnen oder die Frist ändern (REQ-05 AK 1–2).

    Nur POST; danach Rückkehr zur Startseite mit Erfolgs- oder Fehlermeldung.
    """
    if request.method != 'POST':
        return go('dashboard', ctx)
    form = DeadlineForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Bitte ein gültiges Datum für die Abgabefrist eingeben.')
        return go('dashboard', ctx)
    try:
        set_deadline(ctx['month'], form.cleaned_data['deadline'])
    except ValueError as error:
        messages.error(request, str(error))
        return go('dashboard', ctx)
    messages.success(
        request,
        f'Abgabefrist für {ctx["month_label"]}: {ctx["month"].deadline:%d.%m.%Y} · '
        f'Zeitraum {period_status(ctx["month"])}.',
    )
    return go('dashboard', ctx)


def parse_demand(post, slots, quals):
    """Liest Gesamtbedarf und Besetzungsmix je Slot aus dem Formular (REQ-04).

    Args:
        post: ``request.POST`` mit Feldern ``total_<slot>`` und ``need_<slot>_<qual>``.
        slots: Slots der aktuellen Ansicht.
        quals: Alle Qualifikationen in fester Reihenfolge.

    Returns:
        Tupel ``(rows, errors)``: ``rows`` ist eine Liste ``(slot, total, mix)``,
        ``errors`` eine Liste von Fehlermeldungen (leer bei gültiger Eingabe).
    """
    rows, errors = [], []
    for s in slots:
        if f'total_{s.pk}' not in post:
            continue
        try:
            total = int(post[f'total_{s.pk}'])
            mix = [(q, int(post.get(f'need_{s.pk}_{q.pk}', 0))) for q in quals]
        except (ValueError, TypeError):
            errors.append(f'Bitte ganze Zahlen zwischen 0 und {MAX_PER_SLOT} eingeben.')
            continue
        if not 0 <= total <= MAX_PER_SLOT or any(
            not 0 <= count <= MAX_PER_SLOT for _, count in mix
        ):
            errors.append(f'Bitte ganze Zahlen zwischen 0 und {MAX_PER_SLOT} eingeben.')
            continue
        if sum(count for _, count in mix) > total:
            errors.append(
                f'{s.date:%d.%m.} · {s.template}: Der Besetzungsmix übersteigt die Gesamtzahl.'
            )
        rows.append((s, total, mix))
    return rows, errors


def expand_to_month(rows, slots):
    """Überträgt die Eingaben einer Woche auf alle gleichen Wochentage des Monats.

    Feiertage (RB-03) bleiben ohne Bedarf, außer sie wurden in der Woche selbst bearbeitet.

    Args:
        rows: Liste ``(slot, total, mix)`` der bearbeiteten Woche.
        slots: Alle Slots des Monats.

    Returns:
        Liste ``(slot, total, mix)`` für alle passenden Slots des Monats.
    """
    by_weekday = {(s.date.weekday(), s.template_id): (total, mix) for s, total, mix in rows}
    edited = {s.pk for s, _, _ in rows}
    return [
        (s, *by_weekday[(s.date.weekday(), s.template_id)])
        for s in slots
        if (s.date.weekday(), s.template_id) in by_weekday
        and (s.pk in edited or not rules.holiday_name(s.date))
    ]


@transaction.atomic
def save_demand(month, rows):
    """Speichert Bedarf und Besetzungsmix und markiert den Monat als geändert.

    Args:
        month: Planungsmonat.
        rows: Liste ``(slot, total, mix)``.
    """
    Month.objects.select_for_update().get(pk=month.pk)
    for s, total, mix in rows:
        s.total = total
        s.save(update_fields=['total'])
        for q, count in mix:
            Need.objects.update_or_create(slot=s, qualification=q, defaults={'count': count})
    month.demand_saved = True
    month.save(update_fields=['demand_saved'])
    touch(month)


@planner_only
@with_context
def demand(request, ctx):
    """Bedarf je Tag und Schichtvorlage erfassen, optional auf den Monat kopieren (REQ-04)."""
    quals = list(Qualification.objects.all().order_by('pk'))
    if request.method == 'POST':
        rows, errors = parse_demand(request.POST, ctx['slots'], quals)
        if errors:
            for s in ctx['slots']:
                if f'total_{s.pk}' in request.POST:
                    s.total = request.POST[f'total_{s.pk}']
            for error in sorted(set(errors)):
                messages.error(request, error)
        elif rows:
            if request.POST.get('action') == 'copy_month':
                rows = expand_to_month(rows, ctx['slots'])
            save_demand(ctx['month'], rows)
            messages.success(
                request,
                'Personalbedarf gespeichert. '
                'Der Besetzungsmix wird bei der Planung berücksichtigt.',
            )
            return go('demand', ctx)

    def values(s):
        mix = {n.qualification_id: n.count for n in s.needs.all()}
        return {
            'mix': [(q, request.POST.get(f'need_{s.pk}_{q.pk}', mix.get(q.pk, 0))) for q in quals]
        }

    ctx['rows'] = table_rows(ctx, values)
    ctx['opening_form'] = OpeningForm(month=ctx['month'])
    ctx['opening_summary'] = opening_summary(ctx['month'])
    return render(request, 'planning/demand.html', ctx)


def opening_summary(month):
    """Beschreibt die Öffnungstage eines Monats in einem Satz für die Oberfläche.

    Args:
        month: Planungsmonat.

    Returns:
        Text, z. B. „Mo–Sa geöffnet · zusätzlich geöffnet: 06.12.“.
    """
    names = [WEEKDAY_SHORT[int(d)] for d in month.open_weekdays]
    text = ', '.join(names) + ' geöffnet'
    extra = [d for d in month.day_exceptions.all() if d.is_open]
    closed = [d for d in month.day_exceptions.all() if not d.is_open]
    if extra:
        text += ' · zusätzlich geöffnet: ' + ', '.join(f'{d.date:%d.%m.}' for d in extra)
    if closed:
        text += ' · geschlossen: ' + ', '.join(f'{d.date:%d.%m.}' for d in closed)
    return text


@planner_only
@with_context
def opening(request, ctx):
    """Öffnungstage des Planungsmonats festlegen, z. B. einen Sonntag öffnen (REQ-22).

    Nur POST; danach Rückkehr zur Bedarfsseite.
    """
    if request.method != 'POST':
        return go('demand', ctx)
    form = OpeningForm(request.POST, month=ctx['month'])
    if not form.is_valid():
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
        return go('demand', ctx)
    data = form.cleaned_data
    try:
        set_opening(
            ctx['month'],
            [int(d) for d in data['weekdays']],
            data['day'],
            data['day_state'] == 'open' if data['day'] else None,
        )
    except ValueError as error:
        messages.error(request, str(error))
        return go('demand', ctx)
    messages.success(
        request,
        f'Öffnungstage gespeichert: {len(open_days(ctx["month"]))} Tage im {ctx["month_label"]}.',
    )
    return go('demand', ctx)


@planner_only
@with_context
def templates(request, ctx):
    """Schichtvorlagen anlegen und bearbeiten (REQ-03)."""
    selected = request.GET.get('edit') or request.POST.get('id')
    instance = get_object_or_404(ShiftTemplate, pk=selected) if selected else None
    form = TemplateForm(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            form.save()
            # Geänderte Vorlagen machen bestehende Planeingaben aller Monate veraltet.
            for month in Month.objects.select_for_update():
                ensure_slots(month)
                touch(month)
        messages.success(request, 'Schichtvorlage gespeichert.')
        return go('templates', ctx)
    ctx.update(form=form, editing=instance, templates=ShiftTemplate.objects.all())
    return render(request, 'planning/templates.html', ctx)


@planner_only
@with_context
def employees(request, ctx):
    """Mitarbeitende mit Vertragsart, Wochenstunden und Qualifikationen verwalten (REQ-02).

    Ohne Parameter wird eine neue Person angelegt, mit ``edit`` eine bestehende bearbeitet.
    Fehlende Pflichtfelder werden benannt; dann wird nichts gespeichert (AK 2).
    """
    visibility_form = PlanVisibilityForm(
        request.POST
        if request.method == 'POST' and request.POST.get('action') == 'visibility'
        else None,
        initial={'visibility': 'team' if team_plan_visible() else 'own'},
    )
    if request.method == 'POST' and request.POST.get('action') == 'visibility':
        if visibility_form.is_valid():
            PlanningSettings.objects.update_or_create(
                pk=1,
                defaults={'show_team_plan': visibility_form.cleaned_data['visibility'] == 'team'},
            )
            messages.success(
                request, 'Plansicht für das gesamte Team gespeichert. Sie gilt ab sofort.'
            )
        else:
            messages.error(request, 'Bitte eine gültige Plansicht auswählen.')
        return go('employees', ctx)
    ctx['visibility_form'] = visibility_form
    selected = request.GET.get('edit') or request.POST.get('id')
    instance = (
        get_object_or_404(Employee.objects.select_related('user'), pk=selected)
        if selected
        else None
    )
    form = EmployeeForm(request.POST or None, employee=instance)
    if request.method == 'POST':
        if form.is_valid():
            saved = save_employee(form.cleaned_data, instance)
            messages.success(
                request,
                f'{saved} gespeichert. Die Angaben gelten ab dem nächsten erzeugten Plan.',
            )
            return go('employees', ctx)
        missing = form.missing_fields()
        if missing:
            messages.error(request, 'Bitte ausfüllen: ' + ', '.join(missing) + '.')
    ctx.update(
        form=form,
        editing=instance,
        employees=Employee.objects.select_related('user')
        .prefetch_related('qualifications')
        .order_by('user__last_name', 'user__first_name'),
    )
    return render(request, 'planning/employees.html', ctx)


@planner_only
@with_context
def qualifications(request, ctx):
    """Qualifikationen pflegen und Mitarbeitenden zuordnen (REQ-02 AK 3)."""
    selected = request.GET.get('edit') or request.POST.get('id')
    instance = get_object_or_404(Qualification, pk=selected) if selected else None
    form = QualificationForm(request.POST or None, instance=instance)
    employees = list(
        Employee.objects.select_related('user').prefetch_related('qualifications').order_by('pk')
    )
    selected_ids = (
        set(Employee.objects.filter(qualifications=instance).values_list('pk', flat=True))
        if instance
        else set()
    )
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
    ctx.update(
        form=form,
        editing=instance,
        qualifications=Qualification.objects.annotate(employee_count=Count('employee')).order_by(
            'pk'
        ),
        employee_choices=[(e, e.pk in selected_ids) for e in employees],
    )
    return render(request, 'planning/qualifications.html', ctx)


def next_month_start(day):
    """Liefert den ersten Tag des Folgemonats.

    Args:
        day: Beliebiges Datum.

    Returns:
        ``date`` des Ersten im Folgemonat.
    """
    return (day.replace(day=28) + timedelta(days=4)).replace(day=1)


@planner_only
@with_context
def availability_overview(request, ctx):
    """Abgabestand aller Mitarbeitenden ansehen und Urlaub erfassen (REQ-14)."""
    form = VacationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            vacation = form.save()
            for month in Month.objects.select_for_update():
                if month.date <= vacation.end and next_month_start(month.date) > vacation.start:
                    touch(month)
        messages.success(
            request, 'Urlaub gespeichert. Die Person wird in diesem Zeitraum nicht eingeplant.'
        )
        return go('availability_overview', ctx)
    submissions = {s.employee_id: s for s in Submission.objects.filter(month=ctx['month'])}
    ctx['people'] = [
        (e, submissions.get(e.pk))
        for e in Employee.objects.filter(user__is_active=True)
        .select_related('user')
        .order_by('pk')
    ]
    ctx['available_count'] = Availability.objects.filter(
        slot__month=ctx['month'], priority__gt=0
    ).count()
    ctx['vacations'] = Vacation.objects.filter(
        start__lt=ctx['month'].date + timedelta(days=31), end__gte=ctx['month'].date
    ).select_related('employee__user')
    ctx['vacation_form'] = form
    return render(request, 'planning/availability_overview.html', ctx)


def parse_priorities(post, slots):
    """Liest Prioritäten 0–3 je Slot aus dem Formular (REQ-06).

    Args:
        post: ``request.POST`` mit Feldern ``priority_<slot>``.
        slots: Slots der aktuellen Ansicht.

    Returns:
        Liste ``(slot, priority)``.

    Raises:
        ValueError: Wenn eine Priorität nicht 0, 1, 2 oder 3 ist.
    """
    parsed = []
    for slot in slots:
        key = f'priority_{slot.pk}'
        if key not in post:
            continue
        value = int(post[key])
        if value not in range(4):
            raise ValueError(value)
        parsed.append((slot, value))
    return parsed


def resolve_employee(request, ctx, employee_id):
    """Ermittelt, wessen Verfügbarkeiten angezeigt werden, und prüft den Zugriff (QR-03).

    Args:
        request: Aktuelle Anfrage.
        ctx: Seitenkontext mit ``planner``.
        employee_id: Angefragte Person oder ``None`` für die eigene.

    Returns:
        ``Employee``-Objekt.

    Raises:
        PermissionDenied: Wenn Mitarbeitende fremde Angaben aufrufen.
    """
    if employee_id is None:
        return get_object_or_404(Employee, user=request.user)
    own = Employee.objects.filter(pk=employee_id, user=request.user).exists()
    if not ctx['planner'] and not own:
        raise PermissionDenied
    return get_object_or_404(Employee.objects.select_related('user'), pk=employee_id)


@login_required
@with_context
def availability(request, ctx, employee_id=None):
    """Eigene Verfügbarkeiten mit Priorität eintragen und abgeben (REQ-06, REQ-07).

    Der Chef sieht fremde Angaben nur lesend; Mitarbeitende sehen nur ihre eigenen.
    Vor Öffnung des Zeitraums und nach Ablauf der Frist ist die Eingabe gesperrt (ABW-01).
    """
    employee = resolve_employee(request, ctx, employee_id)
    read_only = employee.user_id != request.user.pk
    locked = not input_open(ctx['month'])
    if request.method == 'POST':
        if read_only:
            raise PermissionDenied
        if locked:
            messages.error(
                request,
                'Die Eingabe ist gesperrt: Der Zeitraum ist nicht geöffnet '
                'oder die Abgabefrist ist abgelaufen.',
            )
            return go('availability', ctx)
        try:
            parsed = parse_priorities(request.POST, ctx['slots'])
        except ValueError:
            return HttpResponseBadRequest('Priorität muss 0, 1, 2 oder 3 sein.')
        with transaction.atomic():
            Month.objects.select_for_update().get(pk=ctx['month'].pk)
            for slot, value in parsed:
                Availability.objects.update_or_create(
                    employee=employee, slot=slot, defaults={'priority': value}
                )
            submit = request.POST.get('action') == 'submit'
            Submission.objects.update_or_create(
                employee=employee, month=ctx['month'], defaults={'submitted': submit}
            )
            touch(ctx['month'])
        messages.success(
            request,
            'Alles abgegeben. Deine Verfügbarkeiten sind bei der Planung angekommen.'
            if submit
            else 'Entwurf gespeichert. Zum Abschluss bitte deine Angaben abgeben.',
        )
        return go('availability', ctx)
    priorities = dict(
        Availability.objects.filter(employee=employee, slot__month=ctx['month']).values_list(
            'slot_id', 'priority'
        )
    )
    ctx['rows'] = table_rows(ctx, lambda s: {'priority': priorities.get(s.pk, 0)})
    ctx['mobile_days'] = [
        (
            day,
            [
                dict(slot=s, priority=priorities.get(s.pk, 0))
                for s in ctx['slots']
                if s.date == day
            ],
        )
        for day in ctx['days']
    ]
    ctx.update(
        employee=employee,
        read_only=read_only,
        locked=locked,
        submission=Submission.objects.filter(employee=employee, month=ctx['month']).first(),
        priority_choices=[
            (0, '× Nicht verfügbar'),
            (1, '1 Bevorzugt'),
            (2, '2 Möglich'),
            (3, '3 Nur wenn nötig'),
        ],
    )
    return render(request, 'planning/availability.html', ctx)


@planner_only
@with_context
def generate(request, ctx):
    """Schichtplan erzeugen (REQ-08); Vorbedingungen prüft ``services.generate_plan``."""
    if request.method == 'POST':
        try:
            result = generate_plan(
                ctx['month'], allow_incomplete=request.POST.get('confirm_incomplete') == 'yes'
            )
            messages.success(
                request,
                f'Schichtplan erzeugt · {result.duration_ms} ms. Positionen sind bearbeitbar.',
            )
            return go('plan', ctx)
        except ValueError as error:
            messages.error(request, str(error))
    return render(request, 'planning/generate.html', ctx)


def cell_summary(assignments):
    """Fasst die Besetzung einer Planzelle (Vorlage × Tag) für die Anzeige zusammen.

    Args:
        assignments: Positionen eines Slots aus dem Plan-Snapshot.

    Returns:
        Dictionary mit Kurznamen, Anzahl offener Positionen, Rollen und Tooltip-Text.
    """
    counts = Counter(a.role for a in assignments if a.employee_id)
    return dict(
        assignments=assignments,
        names=' · '.join(a.employee_name.split()[0] for a in assignments if a.employee_id),
        missing=sum(a.employee_id is None for a in assignments),
        roles=' · '.join(f'{count} {role}' for role, count in counts.items()),
        full_names='; '.join(f'{a.employee_name or "Unbesetzt"}: {a.role}' for a in assignments),
    )


def plan_context(ctx):
    """Ergänzt den Kontext um Plan, Kennzahlen und Wochentabelle (REQ-09, REQ-10).

    Args:
        ctx: Seitenkontext; wird direkt verändert.
    """
    result = Plan.objects.filter(month=ctx['month']).first()
    ctx['plan'] = result
    if not result:
        return
    ctx['publication'] = PublishedPlan.objects.filter(month=ctx['month']).first()
    if ctx['publication']:
        preview = publication_preview(ctx['month'])
        ctx['unpublished_changes'] = (
            ctx['publication'].source_fingerprint != preview['state']['fingerprint']
            or ctx['publication'].source_input_revision != ctx['month'].revision
        )
    rows = list(result.assignments.all())
    ctx.update(
        assigned=sum(a.employee_id is not None for a in rows),
        total=len(rows),
        unfilled_count=sum(a.employee_id is None for a in rows),
        preferred=sum(a.priority == 1 for a in rows),
        stale=result.revision != ctx['month'].revision,
    )
    days = ctx['days']
    grouped = {}
    for a in rows:
        if a.date in days:
            grouped.setdefault((a.shift_name, a.start, a.end), defaultdict(list))[a.date].append(a)
    ctx['plan_rows'] = [
        dict(
            name=key[0],
            start=key[1],
            end=key[2],
            break_minutes=rules.required_break_minutes(Shift(days[0], key[1], key[2])),
            cells=[cell_summary(group.get(day, [])) for day in days],
        )
        for key, group in grouped.items()
    ]
    ctx['unfilled_rows'] = [a for a in rows if a.employee_id is None]


@planner_only
@with_context
def plan(request, ctx):
    """Erzeugten Schichtplan mit Links zur Korrektur wochenweise anzeigen (REQ-10/11)."""
    plan_context(ctx)
    return render(request, 'planning/plan.html', ctx)


@planner_only
@with_context
def correct_assignment(request, ctx, assignment_id):
    """Zeigt die Vorschau und bestätigt eine manuelle Plankorrektur (REQ-11)."""
    assignment = get_object_or_404(
        Assignment.objects.select_related('plan', 'employee__user'),
        pk=assignment_id,
        plan__month=ctx['month'],
    )
    form = CorrectionForm(
        request.POST if request.method == 'POST' else None,
        plan=assignment.plan,
        assignment=assignment,
    )
    ctx.update(assignment=assignment, form=form)
    if request.method != 'POST':
        return render(request, 'planning/correction.html', ctx)
    try:
        if request.POST.get('confirmation'):
            data = signing.loads(
                request.POST['confirmation'], salt='plan-correction', max_age=3600
            )
            if data['assignment'] != assignment.pk or data['user'] != request.user.pk:
                raise ValueError('Diese Bestätigung gehört zu einer anderen Änderung.')
            result = correct_plan(
                assignment.plan_id, assignment.pk, data['employee'], data['swap'], data['state']
            )
            if not result['errors']:
                messages.success(request, 'Die Plankorrektur wurde gespeichert.')
                return go('plan', ctx)
        elif form.is_valid():
            person, swap = form.cleaned_data['employee'], form.cleaned_data['swap']
            person_id = person.pk if person else None
            swap_id = swap.pk if swap else None
            result = correct_plan(assignment.plan_id, assignment.pk, person_id, swap_id)
            if not result['errors']:
                ctx['confirmation'] = signing.dumps(
                    {
                        'assignment': assignment.pk,
                        'user': request.user.pk,
                        'employee': person_id,
                        'swap': swap_id,
                        'state': result['state'],
                    },
                    salt='plan-correction',
                )
                ctx['choice'] = str(swap) if swap else (str(person) if person else 'Unbesetzt')
                ctx['is_swap'] = bool(swap)
        else:
            return render(request, 'planning/correction.html', ctx)
        ctx.update(errors=result['errors'], warnings=result['warnings'])
    except (ValueError, signing.BadSignature, KeyError):
        ctx['errors'] = [
            'Die Änderung ist ungültig oder die Vorschau veraltet. Bitte erneut prüfen.'
        ]
    return render(request, 'planning/correction.html', ctx)


@planner_only
@with_context
def unfilled(request, ctx):
    """Liste der unbesetzten Positionen anzeigen (REQ-09)."""
    if request.method == 'POST':
        try:
            filled, remaining = fill_unassigned(ctx['month'])
            if filled:
                label = 'Position' if filled == 1 else 'Positionen'
                messages.success(
                    request,
                    f'{filled} {label} automatisch besetzt · {remaining} weiterhin unbesetzt.',
                )
            elif remaining:
                messages.warning(
                    request,
                    'Keine weitere passende Person gefunden. Prüfe offene Abgaben, '
                    'Qualifikationen, Urlaub und bereits geplante Schichten.',
                )
            else:
                messages.info(request, 'Alle Positionen sind bereits besetzt.')
        except ValueError as error:
            messages.error(request, str(error))
        return go('unfilled', ctx)
    plan_context(ctx)
    return render(request, 'planning/unfilled.html', ctx)


def forbidden(request, exception=None):
    """Eigene Fehlerseite für HTTP 403 (QR-03)."""
    return render(request, 'planning/403.html', status=403)


@planner_only
@with_context
def publish(request, ctx):
    """Prüft einen Plan vor der ausdrücklichen Veröffentlichung (REQ-15)."""
    if request.method == 'POST':
        try:
            data = signing.loads(
                request.POST.get('confirmation', ''), salt='publish-plan', max_age=3600
            )
            if data['month'] != ctx['month'].pk or data['user'] != request.user.pk:
                raise ValueError('Diese Bestätigung gehört zu einem anderen Plan.')
            publish_plan(
                ctx['month'],
                request.user,
                data['state'],
                acknowledge=request.POST.get('acknowledge') == 'yes',
            )
            messages.success(request, 'Der Plan wurde für Mitarbeitende veröffentlicht.')
            return go('plan', ctx)
        except (ValueError, signing.BadSignature, KeyError) as error:
            message = (
                str(error)
                if isinstance(error, ValueError)
                else 'Die Bestätigung ist ungültig oder abgelaufen. Bitte erneut prüfen.'
            )
            messages.error(request, message)
    try:
        preview = publication_preview(ctx['month'])
        ctx.update(preview)
        ctx['confirmation'] = signing.dumps(
            {'month': ctx['month'].pk, 'user': request.user.pk, 'state': preview['state']},
            salt='publish-plan',
        )
        ctx['publication'] = PublishedPlan.objects.filter(month=ctx['month']).first()
    except ValueError as error:
        ctx['preview_error'] = str(error)
    return render(request, 'planning/publish.html', ctx)


@login_required
@require_GET
@with_context
def employee_plan(request, ctx):
    """Zeigt ausschließlich veröffentlichte Positionen gemäß der gemeinsamen Plansicht."""
    employee = get_object_or_404(Employee, user=request.user)
    publication = PublishedPlan.objects.filter(month=ctx['month']).first()
    show_team = team_plan_visible()
    rows = publication.assignments.all() if publication else []
    if publication and not show_team:
        rows = rows.filter(employee=employee)
    ctx.update(publication=publication, published_rows=rows, show_team=show_team, weeks=[])
    if publication:
        ctx.update(published_timetable(ctx['month'], rows, request.GET.get('week'), employee.pk))
    return render(request, 'planning/employee_plan.html', ctx)
