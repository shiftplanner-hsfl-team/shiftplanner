"""Datenmodell von ShiftPlanner (Persistenzschicht, SQLite über das Django-ORM).

Die Klassen entsprechen dem Klassen- und ER-Diagramm in docs/design/.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Qualification(models.Model):
    """Qualifikation bzw. Rolle, z. B. Kasse oder Schlüsselverantwortung (REQ-02, REQ-04)."""

    name = models.CharField('Bezeichnung', max_length=80, unique=True)
    description = models.CharField('Beschreibung', max_length=250, blank=True)

    def __str__(self):
        return self.name


class Employee(models.Model):
    """Mitarbeitendenprofil zu einem Django-Konto (REQ-02).

    Vertragsart und Wochenstunden werden im MVP nur gespeichert; die Prüfung der
    Vertragsstunden folgt mit REQ-13 (Sprint 2).
    """

    FULL_TIME, PART_TIME, STUDENT, MINIJOB = 'vollzeit', 'teilzeit', 'studierende', 'minijob'
    CONTRACT_TYPES = [
        (FULL_TIME, 'Vollzeit'),
        (PART_TIME, 'Teilzeit'),
        (STUDENT, 'Studierende'),
        (MINIJOB, 'Minijob'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    qualifications = models.ManyToManyField(Qualification, blank=True)
    contract_type = models.CharField('Vertragsart', max_length=20, choices=CONTRACT_TYPES)
    weekly_hours = models.DecimalField(
        'Wochenstunden',
        max_digits=4,
        decimal_places=1,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(48)],
    )

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class ShiftTemplate(models.Model):
    """Wiederverwendbare Schichtvorlage mit Name, Beginn und Ende am selben Tag (REQ-03)."""

    name = models.CharField('Name der Vorlage', max_length=80, unique=True)
    start = models.TimeField('Beginn')
    end = models.TimeField('Ende')
    description = models.CharField('Beschreibung', max_length=160, blank=True)

    class Meta:
        ordering = ['start', 'pk']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end__gt=models.F('start')), name='shift_positive_duration'
            )
        ]

    def __str__(self):
        return self.name


class Month(models.Model):
    """Planungszeitraum (Kalendermonat) mit Abgabefrist, Bedarfsstatus und Revision (REQ-05).

    Ohne Abgabefrist ist der Zeitraum noch nicht geöffnet; bis einschließlich zur Frist
    ist er offen, danach ist die Eingabe für Mitarbeitende gesperrt (ABW-01).
    """

    date = models.DateField(unique=True)
    revision = models.PositiveIntegerField(default=0)
    demand_saved = models.BooleanField(default=False)
    deadline = models.DateField('Abgabefrist', null=True, blank=True)

    def __str__(self):
        return f'{self.date:%m/%Y}'


class Slot(models.Model):
    """Planungseinheit aus Datum und Schichtvorlage mit Gesamtbedarf 0–30 (REQ-04)."""

    month = models.ForeignKey(Month, on_delete=models.CASCADE)
    date = models.DateField()
    template = models.ForeignKey(ShiftTemplate, on_delete=models.PROTECT)
    total = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(30)])

    class Meta:
        ordering = ['date', 'template__start', 'pk']
        constraints = [
            models.UniqueConstraint(fields=['date', 'template'], name='unique_day_template')
        ]

    def __str__(self):
        return f'{self.date:%d.%m.%Y} {self.template}'


class Need(models.Model):
    """Mindestanzahl einer Qualifikation in einem Slot (Besetzungsmix, REQ-04)."""

    slot = models.ForeignKey(Slot, on_delete=models.CASCADE, related_name='needs')
    qualification = models.ForeignKey(Qualification, on_delete=models.PROTECT)
    count = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(30)])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['slot', 'qualification'], name='unique_slot_qualification'
            )
        ]

    def __str__(self):
        return f'{self.slot}: {self.count} × {self.qualification}'


class Availability(models.Model):
    """Private Verfügbarkeit je Person und Slot: 0 = nicht verfügbar, 1–3 = Priorität (REQ-06)."""

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE)
    priority = models.PositiveSmallIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(3)]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['employee', 'slot'], name='unique_employee_slot'),
            models.CheckConstraint(condition=models.Q(priority__lte=3), name='valid_priority'),
        ]

    def __str__(self):
        return f'{self.employee} · {self.slot} · P{self.priority}'


class Submission(models.Model):
    """Abgabestatus einer Person für einen Monat: Entwurf oder abgegeben (REQ-07)."""

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.ForeignKey(Month, on_delete=models.CASCADE)
    submitted = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['employee', 'month'], name='unique_submission')
        ]

    def __str__(self):
        return f'{self.employee} · {self.month} · {"abgegeben" if self.submitted else "Entwurf"}'


class Vacation(models.Model):
    """Urlaubszeitraum ohne Begründungsfeld, von der Planung erfasst (REQ-14, QR-04)."""

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start = models.DateField('Von')
    end = models.DateField('Bis')

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end__gte=models.F('start')), name='vacation_positive_duration'
            )
        ]

    def __str__(self):
        return f'{self.employee}: {self.start:%d.%m.%Y}–{self.end:%d.%m.%Y}'


class Plan(models.Model):
    """Gespeicherter Schichtplan eines Monats mit Revision und Laufzeit (REQ-08, QR-01)."""

    month = models.OneToOneField(Month, on_delete=models.CASCADE)
    revision = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now=True)
    duration_ms = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'Plan {self.month} (Revision {self.revision})'


class Assignment(models.Model):
    """Eine Position im Plan; ``employee=None`` bedeutet „unbesetzt“ (REQ-09).

    Datum, Zeiten und Namen werden als Snapshot gespeichert, damit ein Plan
    nach späteren Änderungen der Eingaben lesbar bleibt.
    """

    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='assignments')
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, null=True)
    position = models.PositiveSmallIntegerField()
    role = models.CharField(max_length=80)
    priority = models.PositiveSmallIntegerField(null=True)
    # Snapshot: existing plans stay readable when inputs change.
    date = models.DateField()
    shift_name = models.CharField(max_length=80)
    start = models.TimeField()
    end = models.TimeField()
    employee_name = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ['date', 'start', 'slot_id', 'position']
        constraints = [
            models.UniqueConstraint(
                fields=['plan', 'slot', 'position'], name='unique_plan_position'
            )
        ]

    def __str__(self):
        person = self.employee_name or 'Unbesetzt'
        return f'{self.date:%d.%m.} {self.shift_name} · {self.role}: {person}'
