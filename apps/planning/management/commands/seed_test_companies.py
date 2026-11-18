"""Drei leere Demo-Unternehmen mit getrennten Planungskonten bereitstellen."""

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.planning.models import Company, CompanyAccount


class Command(BaseCommand):
    """Ergänzt die drei Testunternehmen, ohne vorhandene Betriebsdaten zu ändern."""

    help = 'Drei leere Testunternehmen und jeweils ein Planungskonto ergänzen (nur Demo).'

    @transaction.atomic
    def handle(self, *args, **options):
        """Legt fehlende Demo-Zugänge an und erhält bestehende Kennwörter und Inhalte.

        Raises:
            CommandError: Außerhalb der Demo oder bei einer kollidierenden Kontozuordnung.
        """
        if not (settings.DEBUG or getattr(settings, 'PUBLIC_DEMO', False)):
            raise CommandError('Testunternehmen dürfen nur im Debug- oder Demo-Modus entstehen.')
        group, _ = Group.objects.get_or_create(name='Planung')
        for number in range(1, 4):
            company, _ = Company.objects.get_or_create(
                slug=f'testunternehmen-{number}',
                defaults={'name': f'Testunternehmen {number}'},
            )
            email = f'planer{number}@example.com'
            user, created = User.objects.get_or_create(
                username=email,
                defaults={'email': email, 'first_name': f'Planung {number}'},
            )
            if created:
                user.set_password('ShiftDemo2026!')
                user.save(update_fields=['password'])
                CompanyAccount.objects.create(user=user, company=company)
            if not CompanyAccount.objects.filter(user=user, company=company).exists():
                raise CommandError(f'Der Anmeldename {email} ist bereits anderweitig vergeben.')
            user.groups.add(group)
        self.stdout.write(
            'Drei getrennte Testunternehmen bereit. Bestehende Daten bleiben erhalten.'
        )
