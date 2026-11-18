"""Bereitet die Demo für die Akzeptanztests mit Nutzenden vor (TC-M, Testplan Abschnitt 3)."""

from datetime import date

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.planning.models import (
    Availability,
    Employee,
    Month,
    PublishedPlan,
    Slot,
    Submission,
)
from apps.planning.publications import publication_preview, publish_plan
from apps.planning.services import ensure_slots, generate_plan, set_deadline

# Planungsmonat → (Abgabefrist, Login der Testperson, die selbst abgibt)
TEST_MONTHS = {
    date(2026, 12, 1): (date(2026, 11, 30), 'mia.hansen'),
    date(2027, 1, 1): (date(2026, 12, 15), 'tom.weber'),
}
# Je Monat eine bewusst unbesetzbare Spätschicht (außerhalb der Aufgabenwoche von M1),
# damit Aufgabe P2 eine Lücke zum manuellen Schließen findet (wie 06.11. in seed_demo).
GAP_DAYS = {date(2026, 12, 1): date(2026, 12, 18), date(2027, 1, 1): date(2027, 1, 15)}
SHIFT_INDEX = {'Frühschicht': 0, 'Tagschicht': 1, 'Spätschicht': 2}


class Command(BaseCommand):
    """Management-Befehl ``prepare_usertests``: Demo für die Tests mit Nutzenden vorbereiten.

    Idempotent: Bereits vorhandene Testmonate werden nicht verändert, damit ein Neustart
    der Demo (z. B. auf Render) laufende Tests nicht überschreibt.
    """

    help = 'Novemberplan veröffentlichen und Testmonate Dezember/Januar anlegen (Demo-Modus).'

    @transaction.atomic
    def handle(self, *args, **options):
        """Veröffentlicht den Novemberplan und legt die Testmonate an.

        Raises:
            CommandError: Wenn weder Debug- noch Demo-Modus aktiv ist oder die Demodaten fehlen.
        """
        if not (settings.DEBUG or getattr(settings, 'PUBLIC_DEMO', False)):
            raise CommandError('Nur im Debug- oder Demo-Modus erlaubt.')
        planner = User.objects.filter(username='nora.krueger@example.com').first()
        november = Month.objects.filter(date=date(2026, 11, 1)).first()
        if planner is None or november is None:
            raise CommandError('Bitte zuerst seed_demo ausführen.')
        self.publish_november(november, planner)
        for month_date, (deadline, tester) in TEST_MONTHS.items():
            self.prepare_month(month_date, deadline, tester)

    def publish_november(self, november, planner):
        """Erzeugt und veröffentlicht den Novemberplan, falls noch nicht veröffentlicht."""
        if PublishedPlan.objects.filter(month=november).exists():
            self.stdout.write('November: bereits veröffentlicht, unverändert.')
            return
        Submission.objects.filter(month=november).update(submitted=True)
        generate_plan(november, allow_incomplete=True)
        preview = publication_preview(november)
        publish_plan(november, planner, preview['state'], acknowledge=True)
        self.stdout.write('November: Plan erzeugt und veröffentlicht.')

    def prepare_month(self, month_date, deadline, tester):
        """Legt einen Testmonat mit Frist und Abgaben aller außer der Testperson an."""
        if Month.objects.filter(date=month_date).exists():
            self.stdout.write(f'{month_date:%m/%Y}: existiert bereits, unverändert.')
            return
        month = Month.objects.create(date=month_date)
        ensure_slots(month)
        set_deadline(month, deadline)
        slots = list(Slot.objects.filter(month=month).select_related('template'))
        employees = list(Employee.objects.select_related('user').order_by('pk'))
        for index, employee in enumerate(employees):
            is_tester = employee.user.username == f'{tester}@example.com'
            Submission.objects.create(employee=employee, month=month, submitted=not is_tester)
            if is_tester:
                continue
            Availability.objects.bulk_create(
                Availability(employee=employee, slot=slot, priority=self.priority(index, slot))
                for slot in slots
            )
        self.stdout.write(f'{month_date:%m/%Y}: Frist {deadline:%d.%m.%Y}, ohne Bedarf angelegt.')

    @staticmethod
    def priority(index, slot):
        """Deterministische Demo-Priorität; die Lückenschicht erhält überall 0."""
        shift = SHIFT_INDEX.get(slot.template.name, 0)
        if slot.date == GAP_DAYS.get(slot.month.date) and shift == 2:
            return 0
        return (index + slot.date.day + shift) % 4
