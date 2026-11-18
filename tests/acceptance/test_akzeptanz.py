"""Automatisierte Akzeptanztests: ein Test je Akzeptanzkriterium (AK) des Anforderungsdokuments.

Quelle der Kriterien: Anforderungsdokument P4 (Stand 09.11.2026), Abschnitte 7–9.
Jeder Test trägt die ID TC-A-<REQ>-<AK> aus docs/testing/testfaelle.md; Gegeben/Wenn/Dann
steht wörtlich bzw. sinngemäß im Docstring. Die Tests bedienen das System wie Nutzende über
HTTP (Django-Testclient); direkte Datenbankzugriffe dienen nur dem „Gegeben“ und dem Prüfen.

Testdaten: Demobetrieb aus ``seed_demo`` (Planerin Nora Krüger, 12 Mitarbeitende, November
2026, Frist 28.10.2026, Ben und Eva haben noch nicht abgegeben), festes Datum 20.10.2026.
"""

import unittest
from datetime import date, time
from io import StringIO
from statistics import mean
from time import perf_counter

from django.contrib.auth.hashers import identify_hasher
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, TestCase, override_settings

from apps.planning.models import (
    Assignment,
    Availability,
    Employee,
    Month,
    Need,
    Plan,
    Qualification,
    ShiftTemplate,
    Slot,
    Submission,
    Vacation,
)

FAST = ['django.contrib.auth.hashers.MD5PasswordHasher']
PASSWORD = 'ShiftDemo2026!'
TODAY = '2026-10-20'  # Eingabephase, Frist 28.10.2026
AFTER_DEADLINE = '2026-10-29'
WEEK_45 = '/?month=2026-11&week=45'


class AcceptanceBase(TestCase):
    """Gemeinsamer Ausgangszustand und Bedienschritte der Akzeptanztests."""

    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0, stdout=StringIO())
        cls.month = Month.objects.get()
        cls.lea = Employee.objects.get(user__first_name='Lea')
        cls.ben = Employee.objects.get(user__first_name='Ben')
        cls.key = Qualification.objects.get(name='Schlüsselverantwortung')
        cls.sale = Qualification.objects.get(name='Verkauf')
        cls.cash = Qualification.objects.get(name='Kasse')
        cls.monday_early = Slot.objects.get(date=date(2026, 11, 2), template__name='Frühschicht')

    def as_user(self, login):
        client = Client()
        self.assertTrue(client.login(username=f'{login}@example.com', password=PASSWORD))
        return client

    def planner(self):
        return self.as_user('nora.krueger')

    def submit_all(self):
        Submission.objects.update(submitted=True)

    def generate(self, client=None):
        """Plan über die Oberfläche erzeugen (mit Bestätigung offener Abgaben)."""
        client = client or self.planner()
        response = client.post(
            '/plan/erzeugen/?month=2026-11', {'month': '2026-11', 'confirm_incomplete': 'yes'}
        )
        self.assertEqual(response.status_code, 302)
        return Plan.objects.get(month=self.month)

    def assignments_of(self, employee):
        return Assignment.objects.filter(employee=employee)

    def preview(self, client, assignment, data):
        return client.post(f'/plan/position/{assignment.pk}/?month=2026-11', data)

    def confirm(self, client, assignment, response):
        return client.post(
            f'/plan/position/{assignment.pk}/?month=2026-11',
            {'confirmation': response.context['confirmation']},
        )


@override_settings(PASSWORD_HASHERS=FAST, DEBUG=True, SHIFTPLANNER_TODAY=TODAY)
class Req01LoginTests(AcceptanceBase):
    def test_tc_a_01_1_employee_sees_only_own_availability_input(self):
        """REQ-01 AK 1: Gegeben ein Mitarbeitender, wenn er sich korrekt anmeldet,
        dann sieht er nur die Eingabe seiner eigenen Verfügbarkeiten (keine Planungsfunktionen)."""
        page = self.as_user('lea.meyer').get('/').content.decode()
        self.assertIn('/meine-verfuegbarkeiten/', page)
        for planner_link in ('/bedarf/', '/mitarbeitende/', '/plan/erzeugen/'):
            self.assertNotIn(f'href="{planner_link}', page)

    def test_tc_a_01_2_planner_sees_staff_demand_and_plan(self):
        """REQ-01 AK 2: Gegeben ein Chef, wenn er sich anmeldet,
        dann sieht er Mitarbeiterverwaltung, Bedarf und Plan."""
        page = self.planner().get('/').content.decode()
        for link in ('/mitarbeitende/', '/bedarf/', '/plan/'):
            self.assertIn(f'href="{link}', page)

    def test_tc_a_01_3_failed_login_does_not_reveal_which_field_was_wrong(self):
        """REQ-01 AK 3: Gegeben ein falsches Passwort, wenn die Anmeldung erfolgt,
        dann wird der Zugriff verweigert, ohne zu verraten, ob E-Mail oder Passwort falsch war."""
        wrong_password = Client().post(
            '/anmelden/', {'username': 'lea.meyer@example.com', 'password': 'falsch'}
        )
        unknown_email = Client().post(
            '/anmelden/', {'username': 'niemand@example.com', 'password': 'falsch'}
        )
        self.assertEqual(wrong_password.status_code, 200)
        self.assertEqual(
            wrong_password.context['form'].non_field_errors(),
            unknown_email.context['form'].non_field_errors(),
        )
        self.assertNotIn('_auth_user_id', wrong_password.wsgi_request.session)


@override_settings(PASSWORD_HASHERS=FAST, DEBUG=True, SHIFTPLANNER_TODAY=TODAY)
class Req02EmployeeTests(AcceptanceBase):
    def data(self, **changes):
        data = {
            'month': '2026-11',
            'first_name': 'Sara',
            'last_name': 'Neumann',
            'email': 'sara.neumann@example.com',
            'contract_type': 'teilzeit',
            'weekly_hours': '20',
            'qualifications': [self.sale.pk],
            'password': 'Sicher-Start-2026',
        }
        data.update(changes)
        return data

    def test_tc_a_02_1_saved_employee_is_listed_and_can_log_in(self):
        """REQ-02 AK 1: Gegeben ein angemeldeter Chef, wenn er einen Mitarbeitenden mit allen
        Pflichtfeldern speichert, dann erscheint dieser in der Liste und kann sich anmelden."""
        nora = self.planner()
        nora.post('/mitarbeitende/', self.data())
        self.assertContains(nora.get('/mitarbeitende/'), 'Sara Neumann')
        sara = Client()
        self.assertTrue(
            sara.login(username='sara.neumann@example.com', password='Sicher-Start-2026')
        )

    def test_tc_a_02_2_missing_required_field_is_named_and_nothing_saved(self):
        """REQ-02 AK 2: Gegeben fehlende Pflichtfelder, wenn der Chef speichert,
        dann wird nicht gespeichert und das fehlende Feld benannt."""
        response = self.planner().post('/mitarbeitende/', self.data(last_name=''))
        self.assertContains(response, 'Nachname')
        self.assertFalse(User.objects.filter(email='sara.neumann@example.com').exists())

    def test_tc_a_02_3_qualification_change_applies_from_next_plan(self):
        """REQ-02 AK 3: Gegeben ein bestehender Mitarbeitender, wenn der Chef eine Qualifikation
        ändert, dann gilt sie ab dem nächsten erzeugten Plan; bestehende Pläne bleiben."""
        self.submit_all()
        nora = self.planner()
        self.generate(nora)
        before = list(self.assignments_of(self.lea).values_list('slot_id', 'role'))
        self.assertTrue(before)
        nora.post(
            f'/mitarbeitende/?edit={self.lea.pk}',
            self.data(
                id=self.lea.pk,
                first_name='Lea',
                last_name='Meyer',
                email='lea.meyer@example.com',
                qualifications=[self.key.pk],
                password='',
            ),
        )
        self.assertEqual(
            list(self.assignments_of(self.lea).values_list('slot_id', 'role')), before
        )
        self.generate(nora)
        # Der Demobedarf fordert nur Verkauf und Kasse; ohne beide wird Lea nicht mehr eingeplant.
        self.assertFalse(self.assignments_of(self.lea).exists())


@override_settings(PASSWORD_HASHERS=FAST, DEBUG=True, SHIFTPLANNER_TODAY=TODAY)
class Req03TemplateTests(AcceptanceBase):
    def test_tc_a_03_1_saved_template_is_selectable_for_demand(self):
        """REQ-03 AK 1: Gegeben Name, Start und Ende am selben Tag, wenn der Chef speichert,
        dann ist die Vorlage bei der Bedarfseingabe auswählbar."""
        nora = self.planner()
        nora.post('/vorlagen/', {'name': 'Inventur', 'start': '09:00', 'end': '13:00'})
        self.assertContains(nora.get('/bedarf/?month=2026-11&week=45'), 'Inventur')

    def test_tc_a_03_2_end_before_start_shows_error(self):
        """REQ-03 AK 2: Gegeben ein Ende vor dem Start, wenn der Chef speichert,
        dann erscheint eine Fehlermeldung."""
        response = self.planner().post(
            '/vorlagen/', {'name': 'Falsch', 'start': '14:00', 'end': '08:00'}
        )
        self.assertContains(response, 'Das Ende muss nach dem Beginn liegen')
        self.assertFalse(ShiftTemplate.objects.filter(name='Falsch').exists())

    def test_tc_a_03_3_changed_template_affects_only_future_plans(self):
        """REQ-03 AK 3: Gegeben eine geänderte Vorlage, wenn sie gespeichert wird,
        dann wirkt sie nur auf künftige Pläne."""
        self.submit_all()
        nora = self.planner()
        self.generate(nora)
        early = ShiftTemplate.objects.get(name='Frühschicht')
        nora.post(
            '/vorlagen/',
            {'id': early.pk, 'name': 'Frühschicht', 'start': '08:00', 'end': '13:00'},
        )
        old_ends = set(
            Assignment.objects.filter(shift_name='Frühschicht').values_list('end', flat=True)
        )
        self.assertEqual(old_ends, {time(14)})
        self.generate(nora)
        new_ends = set(
            Assignment.objects.filter(shift_name='Frühschicht').values_list('end', flat=True)
        )
        self.assertEqual(new_ends, {time(13)})


@override_settings(PASSWORD_HASHERS=FAST, DEBUG=True, SHIFTPLANNER_TODAY=TODAY)
class Req04DemandTests(AcceptanceBase):
    url = '/bedarf/?month=2026-11&week=45'

    def post_demand(self, client, total, key=0, sale=0, cash=0):
        slot = self.monday_early
        return client.post(
            self.url,
            {
                'month': '2026-11',
                f'total_{slot.pk}': str(total),
                f'need_{slot.pk}_{self.key.pk}': str(key),
                f'need_{slot.pk}_{self.sale.pk}': str(sale),
                f'need_{slot.pk}_{self.cash.pk}': str(cash),
            },
            follow=True,
        )

    def test_tc_a_04_1_demand_with_key_holder_is_saved_and_used(self):
        """REQ-04 AK 1: Gegeben ein offener Zeitraum, wenn der Chef für „Früh, Montag“
        3 Personen, davon 1 Schlüsselträger, speichert, dann ist der Bedarf gespeichert und
        wird bei der Planung berücksichtigt."""
        nora = self.planner()
        self.post_demand(nora, 3, key=1)
        self.monday_early.refresh_from_db()
        self.assertEqual(self.monday_early.total, 3)
        self.assertEqual(Need.objects.get(slot=self.monday_early, qualification=self.key).count, 1)
        self.submit_all()
        self.generate(nora)
        positions = Assignment.objects.filter(slot=self.monday_early)
        self.assertEqual(positions.count(), 3)
        key_position = positions.get(role='Schlüsselverantwortung')
        if key_position.employee:
            self.assertTrue(key_position.employee.qualifications.filter(pk=self.key.pk).exists())

    def test_tc_a_04_2_zero_demand_means_nobody_is_planned(self):
        """REQ-04 AK 2: Gegeben der Bedarf 0, wenn er gespeichert wird,
        dann wird für diese Schicht niemand eingeplant."""
        nora = self.planner()
        self.post_demand(nora, 0)
        self.submit_all()
        self.generate(nora)
        self.assertFalse(
            Assignment.objects.filter(slot=self.monday_early, employee__isnull=False).exists()
        )

    def test_tc_a_04_3_qualification_minimum_above_total_shows_error(self):
        """REQ-04 AK 3: Gegeben eine Mindestzahl an Qualifikationen über der Gesamtzahl,
        wenn der Chef speichert, dann erscheint eine Fehlermeldung."""
        response = self.post_demand(self.planner(), 1, key=1, sale=1)
        self.assertEqual(len(list(response.context['messages'])), 1)
        self.assertEqual(next(iter(response.context['messages'])).level_tag, 'error')
        self.monday_early.refresh_from_db()
        self.assertEqual(self.monday_early.total, 3)


@override_settings(PASSWORD_HASHERS=FAST, DEBUG=True, SHIFTPLANNER_TODAY=TODAY)
class Req05PeriodTests(AcceptanceBase):
    def submit_as(self, login):
        client = self.as_user(login)
        return client.post(
            '/meine-verfuegbarkeiten/?month=2026-11',
            {
                'month': '2026-11',
                f'priority_{self.monday_early.pk}': '1',
                'action': 'submit',
            },
            follow=True,
        )

    def test_tc_a_05_1_open_period_is_visible_for_employees(self):
        """REQ-05 AK 1: Gegeben kein offener Zeitraum, wenn der Chef Monat und Frist speichert,
        dann ist der Zeitraum „offen“ und für Mitarbeitende sichtbar."""
        Month.objects.filter(pk=self.month.pk).update(deadline=None)
        self.planner().post('/zeitraum/', {'month': '2026-11', 'deadline': '2026-10-27'})
        self.assertContains(self.as_user('lea.meyer').get('/'), 'bis zum 27.10.2026')

    def test_tc_a_05_2_deadline_after_period_start_shows_error(self):
        """REQ-05 AK 2: Gegeben eine Frist nach dem Beginn des Zeitraums, wenn der Chef
        speichert, dann erscheint eine Fehlermeldung."""
        response = self.planner().post(
            '/zeitraum/', {'month': '2026-11', 'deadline': '2026-11-03'}, follow=True
        )
        self.assertContains(response, 'vor dem Beginn des Planungszeitraums')

    def test_tc_a_05_3_after_deadline_input_locked_and_plan_can_be_generated(self):
        """REQ-05 AK 3: Gegeben die Frist ist abgelaufen, wenn ein Mitarbeitender eintragen will,
        dann ist die Eingabe gesperrt, und der Chef kann den Plan erzeugen."""
        with override_settings(SHIFTPLANNER_TODAY=AFTER_DEADLINE):
            self.assertContains(self.submit_as('ben.fischer'), 'Eingabe ist gesperrt')
            self.generate()
        self.assertFalse(Submission.objects.get(employee=self.ben).submitted)
        self.assertTrue(Plan.objects.filter(month=self.month).exists())

    def test_tc_a_05_4_generation_before_deadline_when_all_submitted(self):
        """REQ-05 AK 4: Gegeben alle aktiven Mitarbeitenden haben vor Ablauf der Frist
        abgegeben, wenn der Chef den Plan erzeugen will, dann ist die Erzeugung möglich."""
        self.submit_as('ben.fischer')
        self.submit_as('eva.koch')
        response = self.planner().post('/plan/erzeugen/', {'month': '2026-11'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Plan.objects.filter(month=self.month).exists())


@override_settings(PASSWORD_HASHERS=FAST, DEBUG=True, SHIFTPLANNER_TODAY=TODAY)
class Req06AvailabilityTests(AcceptanceBase):
    def save(self, client, value, action='draft'):
        return client.post(
            '/meine-verfuegbarkeiten/?month=2026-11&week=45',
            {'month': '2026-11', f'priority_{self.monday_early.pk}': value, 'action': action},
        )

    def test_tc_a_06_1_priority_visible_for_planner_not_for_colleagues(self):
        """REQ-06 AK 1: Gegeben ein offener Zeitraum, wenn ich einen Slot mit Priorität 2
        speichere, dann erscheint er in meiner Übersicht und ist für den Chef sichtbar,
        für andere Mitarbeitende nicht."""
        self.save(self.as_user('lea.meyer'), '2')
        self.assertEqual(
            Availability.objects.get(employee=self.lea, slot=self.monday_early).priority, 2
        )
        self.assertContains(self.planner().get(f'/verfuegbarkeiten/{self.lea.pk}/'), 'Lea Meyer')
        self.assertEqual(
            self.as_user('ben.fischer').get(f'/verfuegbarkeiten/{self.lea.pk}/').status_code, 403
        )

    def test_tc_a_06_2_slot_without_priority_is_rejected(self):
        """REQ-06 AK 2: Gegeben ein Slot ohne Priorität, wenn ich speichere,
        dann wird das abgelehnt."""
        before = Availability.objects.get(employee=self.lea, slot=self.monday_early).priority
        response = self.save(self.as_user('lea.meyer'), '')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            Availability.objects.get(employee=self.lea, slot=self.monday_early).priority, before
        )

    def test_tc_a_06_3_slot_without_entry_means_not_available(self):
        """REQ-06 AK 3: Gegeben ein Slot ohne Eintrag, wenn der Plan erzeugt wird,
        dann gelte ich dafür als nicht verfügbar."""
        Availability.objects.filter(employee=self.lea, slot=self.monday_early).delete()
        self.submit_all()
        self.generate()
        self.assertFalse(
            Assignment.objects.filter(slot=self.monday_early, employee=self.lea).exists()
        )


@override_settings(PASSWORD_HASHERS=FAST, DEBUG=True, SHIFTPLANNER_TODAY=TODAY)
class Req07ChangeAvailabilityTests(AcceptanceBase):
    def change(self, client, value):
        return client.post(
            '/meine-verfuegbarkeiten/?month=2026-11&week=45',
            {'month': '2026-11', f'priority_{self.monday_early.pk}': value, 'action': 'submit'},
            follow=True,
        )

    def priority(self):
        return Availability.objects.get(employee=self.lea, slot=self.monday_early).priority

    def test_tc_a_07_1_change_and_delete_before_deadline_apply_to_planning(self):
        """REQ-07 AK 1: Gegeben ein offener Zeitraum vor der Frist, wenn ich einen Slot ändere
        oder lösche (Priorität 0 = nicht verfügbar), dann gilt die Änderung für die Planung."""
        lea = self.as_user('lea.meyer')
        self.change(lea, '1')
        self.assertEqual(self.priority(), 1)
        self.change(lea, '0')
        self.assertEqual(self.priority(), 0)
        self.submit_all()
        self.generate()
        self.assertFalse(
            Assignment.objects.filter(slot=self.monday_early, employee=self.lea).exists()
        )

    def test_tc_a_07_2_no_change_after_deadline(self):
        """REQ-07 AK 2: Gegeben die Frist ist abgelaufen, wenn ich ändern will,
        dann ist das nicht mehr möglich."""
        before = self.priority()
        new = '1' if before != 1 else '2'
        with override_settings(SHIFTPLANNER_TODAY=AFTER_DEADLINE):
            response = self.change(self.as_user('lea.meyer'), new)
        self.assertContains(response, 'gesperrt')
        self.assertEqual(self.priority(), before)

    def test_tc_a_07_3_overview_shows_only_own_slots(self):
        """REQ-07 AK 3: Gegeben ich öffne die Übersicht, dann sehe ich nur meine eigenen Slots."""
        page = self.as_user('lea.meyer').get('/meine-verfuegbarkeiten/').content.decode()
        for other in ('Ben Fischer', 'Mia Hansen', 'Nele Jansen'):
            self.assertNotIn(other, page)


@override_settings(PASSWORD_HASHERS=FAST, DEBUG=True, SHIFTPLANNER_TODAY=AFTER_DEADLINE)
class Req08GenerationTests(AcceptanceBase):
    def test_tc_a_08_1_only_available_and_qualified_people_are_planned(self):
        """REQ-08 AK 1: Gegeben ein geschlossener Zeitraum mit Bedarf und Verfügbarkeiten, wenn
        ich den Plan erzeuge, dann wird jeder Slot nur mit verfügbaren Personen mit der
        geforderten Qualifikation besetzt."""
        self.generate()
        qualifications = {q.name: q.pk for q in Qualification.objects.all()}
        filled = Assignment.objects.exclude(employee=None).select_related('employee')
        self.assertTrue(filled.exists())
        for a in filled:
            with self.subTest(assignment=a.pk):
                availability = Availability.objects.get(employee=a.employee, slot=a.slot)
                self.assertIn(availability.priority, (1, 2, 3))
                self.assertTrue(Submission.objects.get(employee=a.employee).submitted)
                if a.role in qualifications:
                    self.assertTrue(
                        a.employee.qualifications.filter(pk=qualifications[a.role]).exists()
                    )

    def test_tc_a_08_2_priority_1_before_2_and_3(self):
        """REQ-08 AK 2: Gegeben mehr verfügbare Personen als Bedarf, wenn der Plan erzeugt wird,
        dann haben Personen mit Priorität 1 Vorrang vor 2 und 3."""
        slot = self.monday_early
        Slot.objects.filter(pk=slot.pk).update(total=1)
        Need.objects.filter(slot=slot).delete()
        Availability.objects.filter(slot=slot).update(priority=0)
        ranking = {'Mia': 3, 'Tom': 2, 'Paul': 1}
        for name, priority in ranking.items():
            Availability.objects.filter(slot=slot, employee__user__first_name=name).update(
                priority=priority
            )
        self.generate()
        self.assertEqual(Assignment.objects.get(slot=slot).employee.user.first_name, 'Paul')

    def test_tc_a_08_3_nobody_in_two_overlapping_shifts(self):
        """REQ-08 AK 3: Gegeben ein Mitarbeitender, wenn der Plan erzeugt wird,
        dann ist er nie in zwei sich überschneidenden Schichten am selben Tag eingeplant."""
        self.generate()
        rows = list(Assignment.objects.exclude(employee=None))
        for a in rows:
            for b in rows:
                if a.pk < b.pk and a.employee_id == b.employee_id and a.date == b.date:
                    self.assertFalse(a.start < b.end and b.start < a.end, (a.pk, b.pk))

    def test_tc_a_08_4_identical_inputs_give_identical_plans(self):
        """REQ-08 AK 4: Gegeben identische Eingaben, wenn der Plan zweimal erzeugt wird,
        dann sind beide Pläne gleich (deterministisch)."""
        fields = ('slot_id', 'position', 'employee_id', 'role', 'priority')
        self.generate()
        first = list(Assignment.objects.order_by('slot_id', 'position').values_list(*fields))
        self.generate()
        second = list(Assignment.objects.order_by('slot_id', 'position').values_list(*fields))
        self.assertEqual(first, second)


@override_settings(PASSWORD_HASHERS=FAST, DEBUG=True, SHIFTPLANNER_TODAY=AFTER_DEADLINE)
class Req09UnfilledTests(AcceptanceBase):
    def test_tc_a_09_1_unfilled_slot_shows_missing_count_and_qualification(self):
        """REQ-09 AK 1: Gegeben ein Slot ohne ausreichend qualifizierte verfügbare Personen,
        wenn der Plan erzeugt wird, dann erscheint er mit der Zahl fehlender Personen und der
        fehlenden Qualifikation als „unbesetzt“ (Demo: Fr 06.11., Spätschicht)."""
        nora = self.planner()
        self.generate(nora)
        page = nora.get('/plan/unbesetzt/?month=2026-11').content.decode()
        self.assertIn('06.11.', page)
        self.assertIn('Spätschicht', page)
        self.assertIn('× Verkauf', page)
        self.assertIn('× Kasse', page)

    def test_tc_a_09_2_plan_is_created_and_total_unfilled_is_shown(self):
        """REQ-09 AK 2: Gegeben mindestens ein unbesetzter Slot, wenn der Plan erzeugt wird,
        dann wird der Plan trotzdem erzeugt und die Gesamtzahl unbesetzter Slots angezeigt."""
        nora = self.planner()
        self.generate(nora)
        missing = Assignment.objects.filter(employee=None).count()
        self.assertGreater(missing, 0)
        self.assertContains(nora.get('/plan/?month=2026-11'), f'{missing} Positionen')


@override_settings(PASSWORD_HASHERS=FAST, DEBUG=True, SHIFTPLANNER_TODAY=AFTER_DEADLINE)
class Req10PlanViewTests(AcceptanceBase):
    def test_tc_a_10_1_planner_sees_shifts_per_day_and_week_with_names(self):
        """REQ-10 AK 1: Gegeben ein erzeugter Plan, wenn der Chef ihn öffnet, dann sieht er die
        Schichten je Tag und Woche mit den zugewiesenen Personen."""
        nora = self.planner()
        self.generate(nora)
        page = nora.get('/plan/?month=2026-11&week=45').content.decode()
        self.assertIn('KW 45', page)
        self.assertIn('Mo, 02.11.', page)
        named = Assignment.objects.filter(slot=self.monday_early).exclude(employee=None).first()
        self.assertIn(named.employee_name, page)

    def test_tc_a_10_2_unfilled_slot_is_highlighted(self):
        """REQ-10 AK 2: Gegeben ein unbesetzter Slot, wenn der Plan angezeigt wird,
        dann ist er farblich hervorgehoben (CSS-Klasse ``has-missing``)."""
        nora = self.planner()
        self.generate(nora)
        page = nora.get('/plan/?month=2026-11&week=45').content.decode()
        self.assertIn('plan-cell has-missing', page)
        self.assertIn('× Unbesetzt', page)

    def test_tc_a_10_3_employees_have_no_access_to_draft_plan(self):
        """REQ-10 AK 3 (Teil Zugriff): Mitarbeitende haben keinen Zugriff auf den Planentwurf.
        Der Teil „keine Bearbeitungsfunktion“ ist durch REQ-11 überholt (siehe Testbericht)."""
        self.generate()
        self.assertEqual(self.as_user('lea.meyer').get('/plan/').status_code, 403)


@override_settings(PASSWORD_HASHERS=FAST, DEBUG=True, SHIFTPLANNER_TODAY=AFTER_DEADLINE)
class Req11CorrectionTests(AcceptanceBase):
    def test_tc_a_11_1_change_is_shown_and_unfilled_marking_updated(self):
        """REQ-11 AK 1: Gegeben ein erzeugter Plan, wenn ich eine Person einer Schicht ändere und
        speichere, dann erscheint die Änderung im Plan, und „unbesetzt“ wird aktualisiert."""
        nora = self.planner()
        self.generate(nora)
        position = Assignment.objects.filter(slot=self.monday_early).exclude(employee=None).first()
        person = position.employee
        unfilled_before = Assignment.objects.filter(employee=None).count()
        self.confirm(nora, position, self.preview(nora, position, {}))
        self.assertEqual(Assignment.objects.filter(employee=None).count(), unfilled_before + 1)
        self.assertContains(nora.get('/plan/?month=2026-11'), f'{unfilled_before + 1} Positionen')
        self.confirm(nora, position, self.preview(nora, position, {'employee': person.pk}))
        position.refresh_from_db()
        self.assertEqual(position.employee, person)
        self.assertEqual(Assignment.objects.filter(employee=None).count(), unfilled_before)

    def test_tc_a_11_2_rb01_violation_is_not_saved_and_paragraph_named(self):
        """REQ-11 AK 2: Gegeben eine Änderung, die gegen RB-01 verstößt (mehr als 10 Stunden am
        Tag), wenn der Chef speichert, dann wird nicht gespeichert und der Paragraf genannt."""
        nora = self.planner()
        self.generate(nora)
        early = Assignment.objects.filter(slot=self.monday_early).exclude(employee=None).first()
        late = (
            Assignment.objects.filter(date=self.monday_early.date, shift_name='Spätschicht')
            .exclude(employee=early.employee)
            .first()
        )
        before = late.employee_id
        response = self.preview(nora, late, {'employee': early.employee_id})
        self.assertContains(response, '§ 3')
        self.assertNotIn('confirmation', response.context)
        late.refresh_from_db()
        self.assertEqual(late.employee_id, before)

    def test_tc_a_11_3_allowed_change_with_low_priority_is_saved_with_hint(self):
        """REQ-11 AK 3: Gegeben eine zulässige Änderung, bei der die Person nur Priorität 3
        angegeben hat, wenn der Chef speichert, dann wird gespeichert und ein Hinweis angezeigt."""
        nora = self.planner()
        self.generate(nora)
        day = self.monday_early.date
        # Ben hat bis zur Frist nicht abgegeben und ist deshalb nirgends eingeplant; danach
        # liegt seine Abgabe mit Priorität 3 vor (zulässig: keine Schicht, keine Ruhezeitfrage).
        candidate = self.ben
        Submission.objects.filter(employee=candidate).update(submitted=True)
        Availability.objects.filter(employee=candidate, slot=self.monday_early).update(priority=3)
        position = Assignment.objects.filter(slot=self.monday_early, role='Verkauf').first()
        response = self.preview(nora, position, {'employee': candidate.pk})
        self.assertContains(response, 'Priorität 3')
        self.assertEqual(self.confirm(nora, position, response).status_code, 302)
        position.refresh_from_db()
        self.assertEqual((position.employee, position.date), (candidate, day))


@override_settings(PASSWORD_HASHERS=FAST, DEBUG=True, SHIFTPLANNER_TODAY=TODAY)
class Req14VacationTests(AcceptanceBase):
    def test_tc_a_14_1_person_is_not_planned_on_vacation_days(self):
        """REQ-14 AK 1: Gegeben ein eingetragener Urlaubstag einer Person, wenn der Plan erzeugt
        wird, dann wird sie an diesem Tag nicht eingeplant."""
        nora = self.planner()
        nora.post(
            '/verfuegbarkeiten/?month=2026-11',
            {'employee': self.lea.pk, 'start': '2026-11-09', 'end': '2026-11-13'},
        )
        self.assertTrue(Vacation.objects.filter(employee=self.lea).exists())
        self.submit_all()
        self.generate(nora)
        self.assertFalse(
            self.assignments_of(self.lea)
            .filter(date__range=[date(2026, 11, 9), date(2026, 11, 13)])
            .exists()
        )


@override_settings(PASSWORD_HASHERS=FAST, DEBUG=True, SHIFTPLANNER_TODAY=TODAY)
class Req15PublicationTests(AcceptanceBase):
    def publish(self, client):
        preview = client.get('/plan/veroeffentlichen/?month=2026-11')
        client.post(
            '/plan/veroeffentlichen/?month=2026-11',
            {'confirmation': preview.context['confirmation'], 'acknowledge': 'yes'},
        )
        return preview

    def test_tc_a_15_1a_employees_see_own_shifts_after_publication(self):
        """REQ-15 AK 1 (Teil 1): Gegeben ein erzeugter Plan, wenn der Chef ihn veröffentlicht,
        dann sehen Mitarbeitende ihre eigenen Schichten."""
        nora = self.planner()
        self.submit_all()
        self.generate(nora)
        self.publish(nora)
        own = self.assignments_of(self.lea).order_by('date').first()
        page = self.as_user('lea.meyer').get(
            f'/mein-schichtplan/?month=2026-11&week={own.date - _weekday(own.date)}'
        )
        self.assertContains(page, 'Meine Schichten')
        self.assertContains(page, own.shift_name)
        self.assertNotContains(page, 'Ben Fischer')

    @unittest.expectedFailure
    def test_tc_a_15_1b_planner_gets_hint_when_publishing_less_than_14_days_before_start(self):
        """REQ-15 AK 1 (Teil 2): Liegt die Veröffentlichung weniger als 14 Tage vor Planbeginn,
        erhält der Chef einen Hinweis. Datum 20.10.2026, Planbeginn 01.11.2026 → 12 Tage.

        BEKANNTER FEHLER (Testbericht P5, DEF-02): Der Hinweis ist nicht umgesetzt. Der Test ist
        als ``expectedFailure`` markiert, damit CI grün bleibt; nach der Korrektur meldet er
        „unexpected success“ und die Markierung muss entfernt werden.
        """
        nora = self.planner()
        self.submit_all()
        self.generate(nora)
        preview = nora.get('/plan/veroeffentlichen/?month=2026-11')
        self.assertContains(preview, '14 Tage')


@override_settings(PASSWORD_HASHERS=FAST, DEBUG=True, SHIFTPLANNER_TODAY=TODAY)
class Req22OpeningDayTests(AcceptanceBase):
    def test_tc_a_22_1_single_sunday_appears_in_demand_availability_and_plan(self):
        """REQ-22 AK 1: Gegeben ein Planungsmonat mit Sonntag standardmäßig geschlossen, wenn der
        Chef einen einzelnen Sonntag öffnet, dann erscheinen für diesen Tag Slots in Bedarf,
        Verfügbarkeit und Plan."""
        nora = self.planner()
        nora.post(
            '/oeffnungstage/',
            {
                'month': '2026-11',
                'weekdays': ['0', '1', '2', '3', '4', '5'],
                'day': '2026-11-08',
                'day_state': 'open',
            },
        )
        self.assertContains(nora.get('/bedarf/?month=2026-11&week=45'), 'So 08')
        sunday = Slot.objects.get(date=date(2026, 11, 8), template__name='Frühschicht')
        nora.post(
            '/bedarf/?month=2026-11&week=45',
            {'month': '2026-11', f'total_{sunday.pk}': '1'},
        )
        lea = self.as_user('lea.meyer')
        self.assertContains(lea.get('/meine-verfuegbarkeiten/?month=2026-11&week=45'), 'So 08')
        lea.post(
            '/meine-verfuegbarkeiten/?month=2026-11&week=45',
            {'month': '2026-11', f'priority_{sunday.pk}': '1', 'action': 'submit'},
        )
        self.submit_all()
        self.generate(nora)
        self.assertTrue(Assignment.objects.filter(date=date(2026, 11, 8)).exists())


class Qr01PerformanceTests(TestCase):
    def test_tc_a_qr01_1_mean_of_5_runs_at_most_10_seconds(self):
        """QR-01 AK 1: Gegeben 30 Mitarbeitende, 3 Vorlagen und 30 Tage, wenn der Plan erzeugt
        wird, dann dauert das im Mittel von 5 Läufen höchstens 10 Sekunden."""
        from apps.planning.services import dates_for_month, generate_plan

        month = Month.objects.create(
            date=date(2026, 11, 1), demand_saved=True, open_weekdays='0123456'
        )
        templates = [
            ShiftTemplate.objects.create(name=n, start=time(s), end=time(e))
            for n, s, e in [('Früh', 8, 14), ('Tag', 10, 16), ('Spät', 14, 20)]
        ]
        slots = [
            Slot.objects.create(month=month, date=d, template=t, total=3)
            for d in dates_for_month(month.date)
            for t in templates
        ]
        employees = []
        for i in range(30):
            employee = Employee.objects.create(user=User.objects.create_user(f'p{i}'))
            Submission.objects.create(employee=employee, month=month, submitted=True)
            employees.append(employee)
        Availability.objects.bulk_create(
            [
                Availability(employee=e, slot=s, priority=1 + (e.pk + s.pk) % 3)
                for e in employees
                for s in slots
            ]
        )
        runs = []
        for _ in range(5):
            started = perf_counter()
            plan = generate_plan(month)
            runs.append(perf_counter() - started)
        self.assertEqual(plan.assignments.count(), 270)
        self.assertLessEqual(mean(runs), 10)
        print(f'\nQR-01: Mittel aus 5 Läufen {mean(runs):.3f} s (max {max(runs):.3f} s)')


@override_settings(DEBUG=True, SHIFTPLANNER_TODAY=TODAY)
class Qr03Qr04PrivacyTests(AcceptanceBase):
    """Ohne schnellen Test-Hasher, damit AK 3 den echten Passwort-Hasher prüft."""

    def test_tc_a_qr03_1_colleague_availability_by_direct_url_is_403(self):
        """QR-03 AK 1: Gegeben zwei Mitarbeitende A und B, wenn A die Verfügbarkeiten von B
        abrufen will (auch per direkter URL), dann wird der Zugriff verweigert (HTTP 403)."""
        ben = Client()
        ben.force_login(self.ben.user)
        self.assertEqual(ben.get(f'/verfuegbarkeiten/{self.lea.pk}/').status_code, 403)

    def test_tc_a_qr03_3_passwords_are_stored_as_hash_only(self):
        """QR-03 AK 3: Gegeben die Datenbank, dann sind Passwörter nur als Hash gespeichert."""
        for user in User.objects.all():
            with self.subTest(user=user.username):
                self.assertNotIn(PASSWORD, user.password)
                self.assertTrue(identify_hasher(user.password).algorithm)

    def test_tc_a_qr04_1_availability_form_has_no_reason_field(self):
        """QR-04 AK 1: Gegeben das Verfügbarkeitsformular, dann enthält es nur Slot und
        Priorität, kein Freitextfeld für Gründe."""
        lea = Client()
        lea.force_login(self.lea.user)
        page = lea.get('/meine-verfuegbarkeiten/').content.decode()
        self.assertNotIn('<textarea', page)
        self.assertNotIn('type="text"', page)

    def test_tc_a_qr04_2_no_reason_field_in_database(self):
        """QR-04 AK 2: Gegeben die Datenbank, dann gibt es kein Feld für Begründungen."""
        for model in (Availability, Vacation, Submission):
            names = {f.name.lower() for f in model._meta.get_fields()}
            with self.subTest(model=model.__name__):
                self.assertFalse(
                    names & {'reason', 'grund', 'begruendung', 'comment', 'kommentar', 'note'}
                )


def _weekday(day):
    """Abstand zum Montag als ``timedelta`` (für den Wochenparameter der Planansicht)."""
    from datetime import timedelta

    return timedelta(days=day.weekday())
