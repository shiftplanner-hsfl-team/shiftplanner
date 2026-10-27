from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Qualification(models.Model):
    name = models.CharField('Bezeichnung', max_length=80, unique=True)
    description = models.CharField('Beschreibung', max_length=250, blank=True)

    def __str__(self):
        return self.name


class Employee(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    qualifications = models.ManyToManyField(Qualification, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class ShiftTemplate(models.Model):
    name = models.CharField('Name der Vorlage', max_length=80, unique=True)
    start = models.TimeField('Beginn')
    end = models.TimeField('Ende')
    description = models.CharField('Beschreibung', max_length=160, blank=True)

    class Meta:
        ordering = ['start', 'pk']
        constraints = [models.CheckConstraint(condition=models.Q(end__gt=models.F('start')), name='shift_positive_duration')]

    def __str__(self):
        return self.name


class Month(models.Model):
    date = models.DateField(unique=True)
    revision = models.PositiveIntegerField(default=0)
    demand_saved = models.BooleanField(default=False)


class Slot(models.Model):
    month = models.ForeignKey(Month, on_delete=models.CASCADE)
    date = models.DateField()
    template = models.ForeignKey(ShiftTemplate, on_delete=models.PROTECT)
    total = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(30)])

    class Meta:
        ordering = ['date', 'template__start', 'pk']
        constraints = [models.UniqueConstraint(fields=['date', 'template'], name='unique_day_template')]


class Need(models.Model):
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE, related_name='needs')
    qualification = models.ForeignKey(Qualification, on_delete=models.PROTECT)
    count = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(30)])

    class Meta:
        constraints = [models.UniqueConstraint(fields=['slot', 'qualification'], name='unique_slot_qualification')]


class Availability(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    slot = models.ForeignKey(Slot, on_delete=models.CASCADE)
    priority = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(3)])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['employee', 'slot'], name='unique_employee_slot'),
            models.CheckConstraint(condition=models.Q(priority__lte=3), name='valid_priority'),
        ]


class Submission(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.ForeignKey(Month, on_delete=models.CASCADE)
    submitted = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['employee', 'month'], name='unique_submission')]


class Vacation(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start = models.DateField('Von')
    end = models.DateField('Bis')

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(end__gte=models.F('start')), name='vacation_positive_duration')]


class Plan(models.Model):
    month = models.OneToOneField(Month, on_delete=models.CASCADE)
    revision = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now=True)
    duration_ms = models.PositiveIntegerField(default=0)


class Assignment(models.Model):
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
        constraints = [models.UniqueConstraint(fields=['plan', 'slot', 'position'], name='unique_plan_position')]
