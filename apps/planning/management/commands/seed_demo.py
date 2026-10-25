"""Idempotente lokale Demodaten; vorhandene Benutzerdaten werden nicht überschrieben."""
from datetime import date, time
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.planning.models import (Availability, Employee, Month, Need,
                                  Qualification, ShiftTemplate, Slot, Submission)
from apps.planning.services import ensure_slots


class Command(BaseCommand):
    help = 'Fiktive Nordlicht-Demodaten für November 2026 anlegen (nur DEBUG).'

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Demodaten dürfen nur mit DJANGO_DEBUG=1 angelegt werden.')
        if User.objects.exists():
            self.stdout.write('Bereits Benutzer vorhanden. Keine Daten geändert.')
            return
        group, _ = Group.objects.get_or_create(name='Planung')
        nora = User.objects.create_user('nora.krueger@example.com', 'nora.krueger@example.com', 'ShiftDemo2026!', first_name='Nora', last_name='Krüger')
        nora.groups.add(group)
        sale = Qualification.objects.create(name='Verkauf', description='Beratung und Verkauf auf der Fläche')
        cash = Qualification.objects.create(name='Kasse', description='Kasse selbstständig bedienen und abschließen')
        key = Qualification.objects.create(name='Schlüsselverantwortung', description='Öffnen und Schließen der Filiale')
        for name, start, end, desc in [
            ('Frühschicht', time(8), time(14), 'Für Öffnung und Warenannahme'),
            ('Tagschicht', time(10), time(16), 'Für das Tagesgeschäft'),
            ('Spätschicht', time(14), time(20), 'Für Verkauf und Abschluss'),
        ]:
            ShiftTemplate.objects.create(name=name, start=start, end=end, description=desc)
        month = Month.objects.create(date=date(2026, 11, 1), demand_saved=True)
        ensure_slots(month)
        slots = list(Slot.objects.filter(month=month).select_related('template'))
        for slot in slots:
            slot.total = 3
            slot.save(update_fields=['total'])
            Need.objects.create(slot=slot, qualification=sale, count=2)
            Need.objects.create(slot=slot, qualification=cash, count=1)
        names = [('Lea', 'Meyer', 'lea.meyer'), ('Ben', 'Fischer', 'ben.fischer'),
                 ('Mia', 'Hansen', 'mia.hansen'), ('Ali', 'Yilmaz', 'ali.yilmaz'),
                 ('Tom', 'Weber', 'tom.weber'), ('Eva', 'Koch', 'eva.koch'),
                 ('Finn', 'Peters', 'finn.peters'), ('Emma', 'Lange', 'emma.lange'),
                 ('Jonas', 'Wolf', 'jonas.wolf'), ('Lina', 'Schulz', 'lina.schulz'),
                 ('Paul', 'Becker', 'paul.becker'), ('Nele', 'Jansen', 'nele.jansen')]
        for index, (first, last, login) in enumerate(names):
            email = login + '@example.com'
            user = User.objects.create_user(email, email, 'ShiftDemo2026!', first_name=first, last_name=last)
            employee = Employee.objects.create(user=user)
            employee.qualifications.add(sale)
            if index < 8:
                employee.qualifications.add(cash)
            if index in (0, 3, 6):
                employee.qualifications.add(key)
            rows = []
            for slot in slots:
                shift = {'Frühschicht': 0, 'Tagschicht': 1, 'Spätschicht': 2}[slot.template.name]
                priority = (index + slot.date.day + shift) % 4
                # One visible, deliberately unfillable shift for explaining gaps.
                if slot.date == date(2026, 11, 6) and shift == 2:
                    priority = 0
                rows.append(Availability(employee=employee, slot=slot, priority=priority))
            Availability.objects.bulk_create(rows)
            Submission.objects.create(employee=employee, month=month, submitted=index not in (1, 5))
        self.stdout.write(self.style.SUCCESS('Demo angelegt: 12 Mitarbeitende, 3 Vorlagen, November 2026.'))
        self.stdout.write('Planung: nora.krueger@example.com | Mitarbeitende: lea.meyer@example.com')
        self.stdout.write('Demo-Passwort: ShiftDemo2026! | Ben und Eva haben noch nicht abgegeben.')
