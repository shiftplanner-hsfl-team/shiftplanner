from datetime import date, time
from time import perf_counter

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, TestCase, override_settings

from . import rules
from .models import (
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
from .rules import Shift
from .services import assignment_violations, generate_plan, match_positions, readiness

FAST_PASSWORDS = ['django.contrib.auth.hashers.MD5PasswordHasher']


# Eingabephase der Demo: Frist 28.10.2026 liegt nach diesem Datum (REQ-05).
DEMO_TODAY = '2026-10-20'


@override_settings(PASSWORD_HASHERS=FAST_PASSWORDS, DEBUG=True, SHIFTPLANNER_TODAY=DEMO_TODAY)
class WorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)
        cls.month = Month.objects.get()
        cls.lea = Employee.objects.get(user__first_name='Lea')
        cls.ben = Employee.objects.get(user__first_name='Ben')
        cls.slot = Slot.objects.filter(month=cls.month).first()

    def login(self, name='nora.krueger'):
        self.client.login(username=name + '@example.com', password='ShiftDemo2026!')

    def complete(self):
        Submission.objects.update(submitted=True)

    def test_planner_screens_render_and_employee_home(self):
        self.login()
        for path in [
            '/',
            '/bedarf/',
            '/vorlagen/',
            '/qualifikationen/',
            '/verfuegbarkeiten/',
            '/plan/',
            '/plan/erzeugen/',
            '/plan/unbesetzt/',
        ]:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)
        self.login('lea.meyer')
        self.assertContains(self.client.get('/'), 'Hallo Lea.')
        self.assertEqual(self.client.get('/meine-verfuegbarkeiten/').status_code, 200)

    def test_login_required_and_logout_requires_post(self):
        self.assertEqual(self.client.get('/').status_code, 302)
        self.login()
        self.assertEqual(self.client.get('/abmelden/').status_code, 405)
        self.assertEqual(self.client.post('/abmelden/').status_code, 302)
        self.assertEqual(self.client.get('/').status_code, 302)

    def test_employee_cannot_read_or_write_planner_or_peer_data(self):
        self.login('lea.meyer')
        for path in [
            '/bedarf/',
            '/vorlagen/',
            '/qualifikationen/',
            '/verfuegbarkeiten/',
            '/plan/',
            '/plan/erzeugen/',
            '/plan/unbesetzt/',
            f'/verfuegbarkeiten/{self.ben.pk}/',
        ]:
            for method in (self.client.get, self.client.post):
                with self.subTest(path=path, method=method.__name__):
                    self.assertEqual(method(path).status_code, 403)
        response = self.client.get('/meine-verfuegbarkeiten/')
        self.assertNotContains(response, 'Ben Fischer')

    def test_planner_can_read_but_cannot_edit_peer_availability(self):
        self.login()
        path = f'/verfuegbarkeiten/{self.lea.pk}/'
        self.assertContains(self.client.get(path), 'Lea Meyer')
        self.assertEqual(
            self.client.post(path, {f'priority_{self.slot.pk}': '3'}).status_code, 403
        )

    def test_csrf_is_enforced(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(User.objects.get(first_name='Lea'))
        self.assertEqual(
            client.post('/meine-verfuegbarkeiten/', {'action': 'submit'}).status_code, 403
        )

    def test_draft_then_submit_preserves_other_weeks(self):
        self.login('lea.meyer')
        other = Slot.objects.filter(month=self.month, date=date(2026, 11, 30)).first()
        old = Availability.objects.get(employee=self.lea, slot=other).priority
        self.client.post(
            '/meine-verfuegbarkeiten/', {f'priority_{self.slot.pk}': '1', 'action': 'draft'}
        )
        self.assertFalse(Submission.objects.get(employee=self.lea, month=self.month).submitted)
        self.assertEqual(Availability.objects.get(employee=self.lea, slot=other).priority, old)
        self.client.post(
            '/meine-verfuegbarkeiten/', {f'priority_{self.slot.pk}': '2', 'action': 'submit'}
        )
        self.assertTrue(Submission.objects.get(employee=self.lea, month=self.month).submitted)
        self.assertEqual(Availability.objects.get(employee=self.lea, slot=self.slot).priority, 2)

    def test_invalid_priority_has_no_partial_write(self):
        self.login('lea.meyer')
        second = Slot.objects.exclude(pk=self.slot.pk).first()
        before = list(Availability.objects.filter(employee=self.lea).values_list('pk', 'priority'))
        response = self.client.post(
            '/meine-verfuegbarkeiten/',
            {f'priority_{self.slot.pk}': '1', f'priority_{second.pk}': '9'},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            before,
            list(Availability.objects.filter(employee=self.lea).values_list('pk', 'priority')),
        )

    def test_invalid_demand_does_not_change_database(self):
        self.login()
        q = Qualification.objects.first()
        self.client.post(
            '/bedarf/', {f'total_{self.slot.pk}': '1', f'need_{self.slot.pk}_{q.pk}': '2'}
        )
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.total, 3)

    def test_copy_week_applies_matching_weekdays(self):
        self.login()
        self.client.post('/bedarf/', {f'total_{self.slot.pk}': '2', 'action': 'copy_month'})
        totals = Slot.objects.filter(template=self.slot.template, date__week_day=2).values_list(
            'total', flat=True
        )
        self.assertEqual(set(totals), {2})

    def test_missing_submissions_block_generation(self):
        self.login()
        self.client.post('/plan/erzeugen/')
        self.assertFalse(Plan.objects.exists())

    def test_open_submissions_can_be_confirmed_before_deadline(self):
        self.login()
        response = self.client.get('/plan/erzeugen/?month=2026-11')
        self.assertContains(response, '2 Abgaben noch offen')
        self.assertContains(response, 'Ich habe die offenen Abgaben geprüft')
        self.assertEqual(
            self.client.post('/plan/erzeugen/', {'confirm_incomplete': 'yes'}).status_code, 302
        )
        self.assertTrue(Plan.objects.exists())
        self.assertFalse(
            Assignment.objects.filter(
                employee__in=[self.ben, Employee.objects.get(user__first_name='Eva')]
            ).exists()
        )

    def test_confirmation_never_bypasses_missing_demand(self):
        self.login()
        Month.objects.filter(pk=self.month.pk).update(demand_saved=False)
        self.client.post('/plan/erzeugen/', {'confirm_incomplete': 'yes'})
        self.assertFalse(Plan.objects.exists())

    def test_generating_without_confirmation_preserves_existing_plan(self):
        self.complete()
        plan = generate_plan(self.month)
        before = list(plan.assignments.values_list('pk', 'employee_id'))
        Submission.objects.filter(employee=self.ben, month=self.month).update(submitted=False)
        self.login()
        self.client.post('/plan/erzeugen/')
        self.assertEqual(before, list(plan.assignments.values_list('pk', 'employee_id')))

    def test_full_workflow_plan_is_persisted_deterministic_and_read_only(self):
        self.complete()
        self.login()
        response = self.client.post('/plan/erzeugen/')
        self.assertEqual(response.status_code, 302)
        first = list(
            Assignment.objects.values_list('slot_id', 'position', 'employee_id', 'priority')
        )
        self.assertEqual(len(first), sum(Slot.objects.values_list('total', flat=True)))
        self.assertTrue(Assignment.objects.filter(employee__isnull=True).exists())
        self.client.post('/plan/erzeugen/')
        self.assertEqual(
            first,
            list(Assignment.objects.values_list('slot_id', 'position', 'employee_id', 'priority')),
        )
        self.assertContains(self.client.get('/plan/'), 'Bearbeitbar')
        self.assertContains(self.client.get('/plan/unbesetzt/'), 'Unbesetzt')
        count = Assignment.objects.count()
        self.client.post('/plan/', {'employee_id': self.lea.pk})
        self.assertEqual(Assignment.objects.count(), count)

    def test_changed_inputs_mark_snapshot_stale(self):
        self.complete()
        generate_plan(self.month)
        self.login()
        self.client.post('/bedarf/', {f'total_{self.slot.pk}': '2'})
        self.assertContains(self.client.get('/plan/'), 'Eingaben wurden geändert')
        self.assertTrue(Assignment.objects.exists())

    def test_bad_month_and_week_are_handled(self):
        self.login()
        self.assertEqual(self.client.get('/?month=oops').status_code, 400)
        self.assertEqual(self.client.get('/bedarf/?week=oops').status_code, 200)

    def test_template_duration_validation(self):
        self.login()
        self.client.post('/vorlagen/', {'name': 'Ungültig', 'start': '20:00', 'end': '08:00'})
        self.assertFalse(ShiftTemplate.objects.filter(name='Ungültig').exists())

    def test_qualification_assignment_and_vacation(self):
        self.login()
        self.client.post(
            '/qualifikationen/', {'name': 'Lager', 'description': '', 'employees': [self.lea.pk]}
        )
        self.assertTrue(self.lea.qualifications.filter(name='Lager').exists())
        self.client.post(
            '/verfuegbarkeiten/',
            {'employee': self.lea.pk, 'start': '2026-11-02', 'end': '2026-11-07'},
        )
        self.complete()
        generate_plan(self.month)
        self.assertFalse(
            Assignment.objects.filter(
                employee=self.lea, date__range=[date(2026, 11, 2), date(2026, 11, 7)]
            ).exists()
        )


@override_settings(PASSWORD_HASHERS=FAST_PASSWORDS)
class EngineTests(TestCase):
    def setUp(self):
        self.month = Month.objects.create(date=date(2026, 11, 1), demand_saved=True)
        self.sale = Qualification.objects.create(name='Verkauf')
        self.cash = Qualification.objects.create(name='Kasse')
        self.template = ShiftTemplate.objects.create(name='Früh', start=time(8), end=time(14))
        self.slot = Slot.objects.create(
            month=self.month, date=date(2026, 11, 2), template=self.template, total=1
        )

    def employee(self, name, priority=1, qualifications=None, slot=None):
        user = User.objects.create_user(name)
        employee = Employee.objects.create(user=user)
        employee.qualifications.set(qualifications or [])
        Submission.objects.create(employee=employee, month=self.month, submitted=True)
        Availability.objects.create(employee=employee, slot=slot or self.slot, priority=priority)
        return employee

    def test_priorities_1_before_2_before_3_and_zero_excluded(self):
        self.employee('zero', 0)
        self.employee('three', 3)
        self.employee('two', 2)
        best = self.employee('one', 1)
        self.assertEqual(generate_plan(self.month).assignments.get().employee, best)
        Availability.objects.filter(employee=best).update(priority=0)
        self.assertEqual(generate_plan(self.month).assignments.get().employee.user.username, 'two')

    def test_qualification_and_unfilled_positions(self):
        Need.objects.create(slot=self.slot, qualification=self.cash, count=1)
        self.employee('unqualified', 1, [self.sale])
        self.assertIsNone(generate_plan(self.month).assignments.get().employee_id)
        qualified = self.employee('qualified', 3, [self.cash])
        self.assertEqual(generate_plan(self.month).assignments.get().employee, qualified)

    def test_matching_preserves_rare_qualification(self):
        self.slot.total = 2
        self.slot.save()
        Need.objects.create(slot=self.slot, qualification=self.sale, count=1)
        Need.objects.create(slot=self.slot, qualification=self.cash, count=1)
        both = self.employee('both', 1, [self.sale, self.cash])
        self.employee('sales', 1, [self.sale])
        plan = generate_plan(self.month)
        self.assertEqual(plan.assignments.filter(employee__isnull=False).count(), 2)
        self.assertEqual(plan.assignments.get(role='Kasse').employee, both)

    def test_overlap_excluded_and_adjacent_allowed(self):
        emp = self.employee('one')
        # Spät 14–18 grenzt an Früh 8–14 an; zusammen 10 h, also auch nach RB-01 zulässig.
        for name, start, end in [('Tag', time(10), time(16)), ('Spät', time(14), time(18))]:
            template = ShiftTemplate.objects.create(name=name, start=start, end=end)
            slot = Slot.objects.create(
                month=self.month, date=self.slot.date, template=template, total=1
            )
            Availability.objects.create(employee=emp, slot=slot, priority=1)
        plan = generate_plan(self.month)
        self.assertIsNone(plan.assignments.get(shift_name='Tag').employee)
        self.assertEqual(plan.assignments.get(shift_name='Spät').employee, emp)

    def test_vacation_overrides_preferred_availability(self):
        emp = self.employee('one')
        Vacation.objects.create(employee=emp, start=self.slot.date, end=self.slot.date)
        self.assertIsNone(generate_plan(self.month).assignments.get().employee_id)

    def test_no_overlap_in_generated_month(self):
        self.employee('one')
        plan = generate_plan(self.month)
        rows = list(plan.assignments.filter(employee__isnull=False))
        for a in rows:
            for b in rows:
                if a.pk != b.pk and a.employee_id == b.employee_id and a.date == b.date:
                    self.assertFalse(a.start < b.end and b.start < a.end)

    def test_matching_prefers_more_priority_1_before_priority_2(self):
        matches = match_positions([(None, '')] * 2, [[1, 2, 3], [1, 2, 3]], {1: 1, 2: 2, 3: 3})
        self.assertEqual(set(matches.values()), {1, 2})

    def test_30_employees_3_templates_30_days_under_10_seconds(self):
        from .services import ensure_slots

        ShiftTemplate.objects.create(name='Tag', start=time(10), end=time(16))
        ShiftTemplate.objects.create(name='Spät', start=time(14), end=time(20))
        ensure_slots(self.month)
        slots = list(Slot.objects.all())
        Slot.objects.update(total=3)
        employees = [self.employee(f'e{i}') for i in range(30)]
        # Alle 30 Kalendertage für die QR-01-Referenzlast (REQ-22: Sonntage geöffnet).
        Month.objects.filter(pk=self.month.pk).update(open_weekdays='0123456')
        self.month.refresh_from_db()
        from .services import dates_for_month

        for day in dates_for_month(self.month.date):
            for template in ShiftTemplate.objects.all():
                Slot.objects.get_or_create(
                    date=day, template=template, defaults={'month': self.month, 'total': 3}
                )
        slots = list(Slot.objects.all())
        Availability.objects.bulk_create(
            [
                Availability(employee=e, slot=s, priority=1 + e.pk % 3)
                for e in employees
                for s in slots
                if s.pk != self.slot.pk
            ]
        )
        started = perf_counter()
        plan = generate_plan(self.month)
        elapsed = perf_counter() - started
        self.assertLess(elapsed, 10)
        self.assertEqual(plan.assignments.count(), 270)
        print(f'\nQR-01: 30 Mitarbeitende × 3 Vorlagen × 30 Tage: {elapsed:.3f} s')


@override_settings(PASSWORD_HASHERS=FAST_PASSWORDS, DEBUG=True, SHIFTPLANNER_TODAY=DEMO_TODAY)
class DeadlineTests(TestCase):
    """ABW-01: Abgabefrist nach REQ-05 AK 1–4 und REQ-07 AK 2."""

    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)
        cls.month = Month.objects.get()
        cls.ben = Employee.objects.get(user__first_name='Ben')
        cls.eva = Employee.objects.get(user__first_name='Eva')
        cls.slot = Slot.objects.filter(month=cls.month).first()

    def login(self, name='nora.krueger'):
        self.client.login(username=name + '@example.com', password='ShiftDemo2026!')

    def test_ak1_open_period_with_deadline_visible_for_employees(self):
        Month.objects.filter(pk=self.month.pk).update(deadline=None)
        self.login('lea.meyer')
        self.assertContains(self.client.get('/'), 'noch nicht geöffnet')
        self.login()
        self.client.post('/zeitraum/', {'month': '2026-11', 'deadline': '2026-10-25'})
        self.month.refresh_from_db()
        self.assertEqual(self.month.deadline, date(2026, 10, 25))
        self.login('lea.meyer')
        self.assertContains(self.client.get('/'), 'bis zum 25.10.2026')

    def test_ak2_deadline_after_period_start_is_rejected(self):
        self.login()
        response = self.client.post(
            '/zeitraum/', {'month': '2026-11', 'deadline': '2026-11-02'}, follow=True
        )
        self.assertContains(response, 'vor dem Beginn des Planungszeitraums')
        self.month.refresh_from_db()
        self.assertEqual(self.month.deadline, date(2026, 10, 28))

    def test_employee_cannot_access_period_form(self):
        self.login('lea.meyer')
        response = self.client.post('/zeitraum/', {'month': '2026-11', 'deadline': '2026-10-25'})
        self.assertEqual(response.status_code, 403)

    def test_ak3_input_locked_after_deadline(self):
        self.login('ben.fischer')
        with override_settings(SHIFTPLANNER_TODAY='2026-10-29'):
            response = self.client.post(
                '/meine-verfuegbarkeiten/?month=2026-11',
                {'month': '2026-11', f'priority_{self.slot.pk}': '1', 'action': 'submit'},
                follow=True,
            )
            self.assertContains(response, 'Eingabe ist gesperrt')
            self.assertContains(self.client.get('/meine-verfuegbarkeiten/'), 'Eingabe gesperrt.')
        self.assertFalse(Submission.objects.get(employee=self.ben, month=self.month).submitted)

    def test_input_allowed_on_deadline_day(self):
        self.login('ben.fischer')
        with override_settings(SHIFTPLANNER_TODAY='2026-10-28'):
            self.client.post(
                '/meine-verfuegbarkeiten/?month=2026-11',
                {'month': '2026-11', f'priority_{self.slot.pk}': '1', 'action': 'submit'},
            )
        self.assertTrue(Submission.objects.get(employee=self.ben, month=self.month).submitted)

    def test_ak3_generation_after_deadline_with_missing_submissions(self):
        self.login()
        self.assertFalse(readiness(self.month)['ready'])
        with override_settings(SHIFTPLANNER_TODAY='2026-10-29'):
            state = readiness(self.month)
            self.assertTrue(state['can_generate'])
            self.assertFalse(state['ready'])
            self.assertEqual(state['missing'], 2)
            self.client.post('/plan/erzeugen/', {'month': '2026-11', 'confirm_incomplete': 'yes'})
        assigned = set(
            Assignment.objects.exclude(employee=None).values_list('employee_id', flat=True)
        )
        self.assertTrue(assigned)
        self.assertNotIn(self.ben.pk, assigned)
        self.assertNotIn(self.eva.pk, assigned)

    def test_ak4_generation_before_deadline_when_all_submitted(self):
        Submission.objects.update(submitted=True)
        self.assertTrue(readiness(self.month)['ready'])
        self.assertEqual(readiness(self.month)['status'], 'offen')

    def test_no_input_before_period_is_opened(self):
        Month.objects.filter(pk=self.month.pk).update(deadline=None)
        self.login('ben.fischer')
        self.client.post(
            '/meine-verfuegbarkeiten/?month=2026-11',
            {'month': '2026-11', f'priority_{self.slot.pk}': '1', 'action': 'submit'},
        )
        self.assertFalse(Submission.objects.get(employee=self.ben, month=self.month).submitted)


@override_settings(PASSWORD_HASHERS=FAST_PASSWORDS, DEBUG=True, SHIFTPLANNER_TODAY=DEMO_TODAY)
class EmployeeManagementTests(TestCase):
    """ABW-02: Mitarbeitende im System anlegen (REQ-02 AK 1–3)."""

    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)
        cls.month = Month.objects.get()
        cls.sale = Qualification.objects.get(name='Verkauf')
        cls.key = Qualification.objects.get(name='Schlüsselverantwortung')

    def setUp(self):
        self.client.login(username='nora.krueger@example.com', password='ShiftDemo2026!')

    def valid_data(self, **changes):
        data = {
            'month': '2026-11',
            'first_name': 'Sara',
            'last_name': 'Neumann',
            'email': 'sara.neumann@example.com',
            'contract_type': 'minijob',
            'weekly_hours': '10',
            'qualifications': [self.sale.pk],
            'password': 'Sicher-Start-2026',
        }
        data.update(changes)
        return data

    def test_ak1_created_employee_is_listed_and_can_log_in(self):
        response = self.client.post('/mitarbeitende/', self.valid_data(), follow=True)
        self.assertContains(response, 'Sara Neumann gespeichert')
        self.assertContains(response, 'Minijob')
        employee = Employee.objects.get(user__email='sara.neumann@example.com')
        self.assertEqual(employee.contract_type, Employee.MINIJOB)
        self.assertEqual(employee.weekly_hours, 10)
        self.assertEqual(list(employee.qualifications.all()), [self.sale])
        login = Client()
        self.assertTrue(
            login.login(username='sara.neumann@example.com', password='Sicher-Start-2026')
        )
        self.assertContains(login.get('/'), 'Hallo Sara.')

    def test_ak2_missing_required_fields_are_named_and_nothing_saved(self):
        before = Employee.objects.count()
        response = self.client.post(
            '/mitarbeitende/', self.valid_data(first_name='', contract_type='', password='')
        )
        self.assertContains(response, 'Bitte ausfüllen: Vorname, Vertragsart, Startpasswort.')
        self.assertEqual(Employee.objects.count(), before)
        self.assertFalse(User.objects.filter(email='sara.neumann@example.com').exists())

    def test_invalid_hours_and_duplicate_email_rejected(self):
        response = self.client.post('/mitarbeitende/', self.valid_data(weekly_hours='60'))
        self.assertContains(response, 'kleiner oder gleich 48')
        response = self.client.post(
            '/mitarbeitende/', self.valid_data(email='lea.meyer@example.com')
        )
        self.assertContains(response, 'bereits vergeben')

    def test_ak3_qualification_change_applies_to_next_plan_only(self):
        Submission.objects.update(submitted=True)
        generate_plan(self.month)
        lea = Employee.objects.get(user__first_name='Lea')
        roles_before = list(Assignment.objects.filter(employee=lea).values_list('role', flat=True))
        revision = Month.objects.get().revision
        response = self.client.post(
            f'/mitarbeitende/?edit={lea.pk}',
            self.valid_data(
                id=lea.pk,
                first_name='Lea',
                last_name='Meyer',
                email='lea.meyer@example.com',
                contract_type='teilzeit',
                weekly_hours='25',
                qualifications=[self.key.pk],
                password='',
            ),
        )
        self.assertEqual(response.status_code, 302)
        lea.refresh_from_db()
        self.assertEqual(list(lea.qualifications.all()), [self.key])
        self.assertEqual(
            list(Assignment.objects.filter(employee=lea).values_list('role', flat=True)),
            roles_before,
        )
        self.assertGreater(Month.objects.get().revision, revision)
        self.assertTrue(
            Client().login(username='lea.meyer@example.com', password='ShiftDemo2026!')
        )

    def test_employees_page_only_for_planner(self):
        self.assertEqual(self.client.get('/mitarbeitende/').status_code, 200)
        employee = Client()
        employee.login(username='lea.meyer@example.com', password='ShiftDemo2026!')
        self.assertEqual(employee.get('/mitarbeitende/').status_code, 403)
        self.assertEqual(employee.post('/mitarbeitende/', self.valid_data()).status_code, 403)


class ArbZGRuleTests(TestCase):
    """RB-01: Grenzen des Arbeitszeitgesetzes im Regelmodul (ohne Datenbank)."""

    def shift(self, day, start, end):
        return Shift(date(2026, 11, day), time(start), time(end))

    def test_break_and_working_hours_par_4(self):
        self.assertEqual(rules.required_break_minutes(self.shift(2, 8, 14)), 0)
        self.assertEqual(rules.required_break_minutes(self.shift(2, 8, 15)), 30)
        self.assertEqual(rules.required_break_minutes(self.shift(2, 8, 18)), 45)
        self.assertEqual(rules.working_hours(self.shift(2, 8, 18)), 9.25)

    def test_daily_maximum_10_hours_par_3(self):
        early = self.shift(2, 6, 12)
        self.assertTrue(rules.is_allowed([early], self.shift(2, 12, 16)))
        messages = rules.violations([early], self.shift(2, 12, 18))
        self.assertEqual(len(messages), 1)
        self.assertIn('§ 3', messages[0])

    def test_rest_period_11_hours_par_5(self):
        late = self.shift(2, 14, 22)
        self.assertIn('§ 5', rules.violations([late], self.shift(3, 8, 14))[0])
        self.assertTrue(rules.is_allowed([late], self.shift(3, 9, 15)))
        # Auch rückwärts: eine spätere Schicht am Folgetag ist bereits geplant.
        self.assertFalse(rules.is_allowed([self.shift(3, 6, 12)], self.shift(2, 14, 20)))

    def test_weekly_maximum_48_hours(self):
        week = [self.shift(day, 8, 16) for day in range(2, 8)]  # Mo–Sa je 7,5 h = 45 h
        self.assertTrue(rules.is_allowed(week[:5], week[5]))
        messages = rules.violations(week, self.shift(7, 17, 21))
        self.assertTrue(any('KW 45' in m for m in messages))
        self.assertIn('11,5 h', messages[0])

    def test_holidays_schleswig_holstein_rb_03(self):
        self.assertEqual(rules.easter_sunday(2026), date(2026, 4, 5))
        self.assertEqual(rules.holiday_name(date(2026, 4, 3)), 'Karfreitag')
        self.assertEqual(rules.holiday_name(date(2026, 5, 14)), 'Christi Himmelfahrt')
        self.assertEqual(rules.holiday_name(date(2026, 10, 31)), 'Reformationstag')
        self.assertEqual(rules.holiday_name(date(2026, 11, 18)), '')  # Buß- und Bettag: nur SN
        self.assertEqual(len(rules.holidays(2027)), 10)


class ArbZGPlanningTests(TestCase):
    """RB-01 in der Planerzeugung und für die manuelle Korrektur (REQ-11)."""

    def setUp(self):
        self.month = Month.objects.create(date=date(2026, 11, 1), demand_saved=True)
        self.user = User.objects.create_user('one')
        self.emp = Employee.objects.create(user=self.user)
        Submission.objects.create(employee=self.emp, month=self.month, submitted=True)

    def slot(self, day, start, end, name):
        template, _ = ShiftTemplate.objects.get_or_create(
            name=name, defaults={'start': time(start), 'end': time(end)}
        )
        slot = Slot.objects.create(
            month=self.month, date=date(2026, 11, day), template=template, total=1
        )
        Availability.objects.create(employee=self.emp, slot=slot, priority=1)
        return slot

    def test_plan_respects_daily_maximum(self):
        self.slot(2, 8, 14, 'Früh')
        self.slot(2, 14, 20, 'Spät')
        plan = generate_plan(self.month)
        self.assertEqual(plan.assignments.get(shift_name='Früh').employee, self.emp)
        self.assertIsNone(plan.assignments.get(shift_name='Spät').employee)

    def test_plan_respects_rest_period(self):
        self.slot(2, 14, 22, 'Spät lang')
        self.slot(3, 6, 12, 'Früh kurz')
        plan = generate_plan(self.month)
        self.assertEqual(plan.assignments.get(shift_name='Spät lang').employee, self.emp)
        self.assertIsNone(plan.assignments.get(shift_name='Früh kurz').employee)

    def test_assignment_violations_for_manual_correction(self):
        early = self.slot(2, 8, 14, 'Früh')
        late = self.slot(2, 14, 20, 'Spät')
        plan = generate_plan(self.month)
        self.assertEqual(assignment_violations(plan, self.emp, early), [])
        messages = assignment_violations(plan, self.emp, late)
        self.assertEqual(len(messages), 1)
        self.assertIn('Mehr als 10 Stunden', messages[0])


@override_settings(PASSWORD_HASHERS=FAST_PASSWORDS, DEBUG=True, SHIFTPLANNER_TODAY=DEMO_TODAY)
class HolidayCalendarTests(TestCase):
    """RB-03: Feiertage gekennzeichnet und standardmäßig ohne Bedarf."""

    def setUp(self):
        call_command('seed_demo', verbosity=0)
        self.client.login(username='nora.krueger@example.com', password='ShiftDemo2026!')

    def test_holidays_marked_and_skipped_when_copying_week(self):
        response = self.client.get('/bedarf/?month=2026-12&week=52')
        self.assertContains(response, '1. Weihnachtstag')
        december = Month.objects.get(date=date(2026, 12, 1))
        week = Slot.objects.filter(
            month=december, date__range=[date(2026, 12, 14), date(2026, 12, 19)]
        )
        data = {'month': '2026-12', 'action': 'copy_month'}
        data.update({f'total_{s.pk}': '2' for s in week})
        self.client.post('/bedarf/?month=2026-12&week=51', data)
        self.assertEqual(
            Slot.objects.get(date=date(2026, 12, 21), template__name='Frühschicht').total, 2
        )
        self.assertEqual(
            Slot.objects.get(date=date(2026, 12, 25), template__name='Frühschicht').total, 0
        )
        self.assertEqual(
            Slot.objects.get(date=date(2026, 12, 26), template__name='Frühschicht').total, 0
        )


@override_settings(PASSWORD_HASHERS=FAST_PASSWORDS, DEBUG=True, SHIFTPLANNER_TODAY=DEMO_TODAY)
class OpeningDayTests(TestCase):
    """REQ-22: Öffnungstage je Planungsmonat (Sonntag optional)."""

    def setUp(self):
        call_command('seed_demo', verbosity=0)
        self.month = Month.objects.get()
        self.client.login(username='nora.krueger@example.com', password='ShiftDemo2026!')

    def post(self, **data):
        payload = {'month': '2026-11', 'weekdays': ['0', '1', '2', '3', '4', '5']}
        payload.update(data)
        return self.client.post('/oeffnungstage/', payload, follow=True)

    def test_sunday_closed_by_default(self):
        response = self.client.get('/bedarf/?month=2026-11&week=45')
        self.assertContains(response, 'Mo, Di, Mi, Do, Fr, Sa geöffnet')
        self.assertNotContains(response, 'So 08')

    def test_ak_open_single_sunday_shows_slots_in_demand_availability_plan(self):
        sunday = date(2026, 11, 8)
        revision = self.month.revision
        self.post(day='2026-11-08', day_state='open')
        self.month.refresh_from_db()
        self.assertGreater(self.month.revision, revision)
        self.assertContains(self.client.get('/bedarf/?month=2026-11&week=45'), 'So 08')
        slot = Slot.objects.get(date=sunday, template__name='Frühschicht')
        self.client.post(
            '/bedarf/?month=2026-11&week=45',
            {'month': '2026-11', f'total_{slot.pk}': '1', f'need_{slot.pk}_1': '0'},
        )
        lea = Client()
        lea.login(username='lea.meyer@example.com', password='ShiftDemo2026!')
        self.assertContains(lea.get('/meine-verfuegbarkeiten/?month=2026-11&week=45'), 'So 08')
        lea.post(
            '/meine-verfuegbarkeiten/?month=2026-11&week=45',
            {'month': '2026-11', f'priority_{slot.pk}': '1', 'action': 'submit'},
        )
        Submission.objects.update(submitted=True)
        plan = generate_plan(self.month)
        self.assertTrue(plan.assignments.filter(date=sunday).exists())
        self.assertEqual(
            Slot.objects.filter(date__week_day=1, month=self.month)
            .values('date')
            .distinct()
            .count(),
            1,
        )

    def test_closed_weekday_and_single_day_are_not_planned(self):
        self.post(weekdays=['0', '1', '2', '3', '4'], day='2026-11-02', day_state='closed')
        Submission.objects.update(submitted=True)
        plan = generate_plan(self.month)
        dates = set(plan.assignments.values_list('date', flat=True))
        self.assertNotIn(date(2026, 11, 7), dates)  # Samstag geschlossen
        self.assertNotIn(date(2026, 11, 2), dates)  # einzelner Tag geschlossen
        self.assertIn(date(2026, 11, 3), dates)

    def test_invalid_opening_input(self):
        self.assertContains(self.post(weekdays=[]), 'Mindestens ein Wochentag')
        self.assertContains(
            self.post(day='2026-12-06', day_state='open'), 'im gewählten Planungsmonat'
        )
        employee = Client()
        employee.login(username='lea.meyer@example.com', password='ShiftDemo2026!')
        self.assertEqual(employee.post('/oeffnungstage/', {'month': '2026-11'}).status_code, 403)


@override_settings(PASSWORD_HASHERS=FAST_PASSWORDS)
class ManualCorrectionTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import Group

        self.planner = User.objects.create_user('planner', password='password')
        self.planner.groups.add(Group.objects.create(name='Planung'))
        self.a = Employee.objects.create(user=User.objects.create_user('a', first_name='Anna'))
        self.b = Employee.objects.create(user=User.objects.create_user('b', first_name='Ben'))
        self.month = Month.objects.create(date=date(2026, 11, 1))
        self.plan = Plan.objects.create(month=self.month, revision=0)
        self.q = Qualification.objects.create(name='Kasse')
        self.template = ShiftTemplate.objects.create(name='Früh', start=time(8), end=time(14))
        self.slot = Slot.objects.create(
            month=self.month, date=date(2026, 11, 2), template=self.template, total=2
        )
        Need.objects.create(slot=self.slot, qualification=self.q, count=1)
        self.first = self.assignment(self.slot, 0, self.a, 'Kasse')
        self.second = self.assignment(self.slot, 1, None, 'Ohne Vorgabe')
        self.client.force_login(self.planner)

    def assignment(self, slot, position, employee, role):
        return Assignment.objects.create(
            plan=self.plan,
            slot=slot,
            employee=employee,
            position=position,
            role=role,
            date=slot.date,
            shift_name=slot.template.name,
            start=slot.template.start,
            end=slot.template.end,
            employee_name=str(employee) if employee else '',
        )

    def url(self, assignment=None):
        return f'/plan/position/{(assignment or self.first).pk}/?month=2026-11'

    def preview(self, data, assignment=None):
        return self.client.post(self.url(assignment), data)

    def confirm(self, response, assignment=None):
        return self.client.post(
            self.url(assignment), {'confirmation': response.context['confirmation']}
        )

    def test_replace_warns_and_only_saves_after_confirmation(self):
        response = self.preview({'employee': self.b.pk})
        self.assertContains(response, 'Keine abgegebene Verfügbarkeit')
        self.assertContains(response, 'erforderliche Qualifikation')
        self.first.refresh_from_db()
        self.assertEqual(self.first.employee, self.a)
        self.assertEqual(self.confirm(response).status_code, 302)
        self.first.refresh_from_db()
        self.assertEqual(self.first.employee, self.b)
        self.assertEqual(self.first.employee_name, 'Ben')
        self.assertIsNone(self.first.priority)

    def test_remove_and_reassign_open_position(self):
        self.assertEqual(self.confirm(self.preview({})).status_code, 302)
        self.first.refresh_from_db()
        self.assertIsNone(self.first.employee)
        self.assertEqual(self.first.employee_name, '')
        self.assertEqual(self.confirm(self.preview({'employee': self.b.pk})).status_code, 302)
        self.first.refresh_from_db()
        self.assertEqual(self.first.employee, self.b)

    def test_same_shift_duplicate_is_blocked(self):
        response = self.preview({'employee': self.a.pk}, self.second)
        self.assertContains(response, 'Überschneidung')
        self.assertNotIn('confirmation', response.context)
        self.second.refresh_from_db()
        self.assertIsNone(self.second.employee)

    def test_working_hours_violation_is_blocked(self):
        late = ShiftTemplate.objects.create(name='Spät', start=time(14), end=time(20))
        slot = Slot.objects.create(month=self.month, date=self.slot.date, template=late)
        position = self.assignment(slot, 0, None, 'Ohne Vorgabe')
        response = self.preview({'employee': self.a.pk}, position)
        self.assertContains(response, 'Mehr als 10 Stunden')
        self.assertNotIn('confirmation', response.context)

    def test_swap_works_atomically_and_keeps_snapshot_correct(self):
        later = ShiftTemplate.objects.create(name='Spät', start=time(14), end=time(18))
        slot = Slot.objects.create(month=self.month, date=date(2026, 11, 3), template=later)
        other = self.assignment(slot, 0, self.b, 'Ohne Vorgabe')
        response = self.preview({'swap': other.pk})
        self.assertContains(response, 'Tausch mit')
        self.assertEqual(self.confirm(response).status_code, 302)
        self.first.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual((self.first.employee, other.employee), (self.b, self.a))
        self.assertEqual((self.first.employee_name, other.employee_name), ('Ben', 'Anna'))

    def test_stale_preview_is_rejected(self):
        response = self.preview({'employee': self.b.pk})
        self.month.revision += 1
        self.month.save()
        self.assertContains(self.confirm(response), 'Vorschau veraltet')
        self.first.refresh_from_db()
        self.assertEqual(self.first.employee, self.a)

    def test_correction_is_planner_only_and_foreign_position_is_rejected(self):
        self.client.force_login(self.a.user)
        self.assertEqual(self.client.get(self.url()).status_code, 403)
        self.assertEqual(self.client.post(self.url(), {}).status_code, 403)
        self.client.force_login(self.planner)
        self.assertEqual(
            self.client.get(f'/plan/position/{self.first.pk}/?month=2026-12').status_code, 404
        )

    def test_invalid_confirmation_does_not_save(self):
        self.assertContains(self.client.post(self.url(), {'confirmation': 'invalid'}), 'ungültig')
        self.first.refresh_from_db()
        self.assertEqual(self.first.employee, self.a)

    def test_priority_and_vacation_warnings_can_be_confirmed(self):
        self.b.qualifications.add(self.q)
        Submission.objects.create(employee=self.b, month=self.month, submitted=True)
        Availability.objects.create(employee=self.b, slot=self.slot, priority=3)
        Vacation.objects.create(employee=self.b, start=self.slot.date, end=self.slot.date)
        response = self.preview({'employee': self.b.pk})
        self.assertContains(response, 'Priorität 3')
        self.assertContains(response, 'Urlaub ist eingetragen')
        self.assertEqual(self.confirm(response).status_code, 302)
        self.first.refresh_from_db()
        self.assertEqual(self.first.priority, 3)

    def test_swap_rejects_conflict_without_changing_either_position(self):
        template = ShiftTemplate.objects.create(name='Spät', start=time(14), end=time(22))
        slot = Slot.objects.create(month=self.month, date=self.slot.date, template=template)
        other = self.assignment(slot, 0, self.b, 'Ohne Vorgabe')
        extra_slot = Slot.objects.create(
            month=self.month, date=date(2026, 11, 3), template=self.template
        )
        self.assignment(extra_slot, 0, self.a, 'Ohne Vorgabe')
        response = self.preview({'swap': other.pk})
        self.assertContains(response, '§ 5')
        self.assertNotIn('confirmation', response.context)
        self.first.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual((self.first.employee, other.employee), (self.a, self.b))

    def test_autofill_keeps_existing_assignments_and_fills_open_position(self):
        Submission.objects.create(employee=self.b, month=self.month, submitted=True)
        Availability.objects.create(employee=self.b, slot=self.slot, priority=2)
        before = (self.first.pk, self.first.employee_id, self.first.employee_name)
        response = self.client.post('/plan/unbesetzt/?month=2026-11', follow=True)
        self.assertContains(response, '1 Position automatisch besetzt')
        self.first.refresh_from_db()
        self.second.refresh_from_db()
        self.assertEqual((self.first.pk, self.first.employee_id, self.first.employee_name), before)
        self.assertEqual((self.second.employee, self.second.priority), (self.b, 2))

    def test_autofill_requires_submitted_availability_and_qualification(self):
        self.first.employee = None
        self.first.employee_name = ''
        self.first.save()
        Submission.objects.create(employee=self.b, month=self.month, submitted=False)
        Availability.objects.create(employee=self.b, slot=self.slot, priority=1)
        self.client.post('/plan/unbesetzt/?month=2026-11')
        self.assertEqual(self.plan.assignments.filter(employee__isnull=True).count(), 2)
        Submission.objects.filter(employee=self.b).update(submitted=True)
        self.client.post('/plan/unbesetzt/?month=2026-11')
        self.first.refresh_from_db()
        self.second.refresh_from_db()
        self.assertIsNone(self.first.employee)
        self.assertEqual(self.second.employee, self.b)

    def test_autofill_respects_other_shifts_even_when_later_in_plan(self):
        Submission.objects.create(employee=self.b, month=self.month, submitted=True)
        Availability.objects.create(employee=self.b, slot=self.slot, priority=1)
        late = ShiftTemplate.objects.create(name='Andere Schicht', start=time(12), end=time(18))
        slot = Slot.objects.create(month=self.month, date=self.slot.date, template=late)
        self.assignment(slot, 0, self.b, 'Ohne Vorgabe')
        self.client.post('/plan/unbesetzt/?month=2026-11')
        self.second.refresh_from_db()
        self.assertIsNone(self.second.employee)

    def test_autofill_uses_new_submissions_on_outdated_plan(self):
        self.month.revision = 1
        self.month.save()
        Submission.objects.create(employee=self.b, month=self.month, submitted=True)
        Availability.objects.create(employee=self.b, slot=self.slot, priority=1)
        self.client.post('/plan/unbesetzt/?month=2026-11')
        self.second.refresh_from_db()
        self.plan.refresh_from_db()
        self.assertEqual(self.second.employee, self.b)
        self.assertNotEqual(self.plan.revision, self.month.revision)

    def test_autofill_is_restricted_to_planner(self):
        self.client.force_login(self.b.user)
        self.assertEqual(self.client.post('/plan/unbesetzt/?month=2026-11').status_code, 403)

    def test_autofill_explains_when_no_person_is_eligible(self):
        response = self.client.post('/plan/unbesetzt/?month=2026-11', follow=True)
        self.assertContains(response, 'Keine weitere passende Person gefunden')
        self.assertContains(response, 'Abgaben prüfen')


@override_settings(PASSWORD_HASHERS=FAST_PASSWORDS, SHIFTPLANNER_TODAY='2026-10-20')
class PublicationTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import Group

        self.planner = User.objects.create_user('planner')
        self.planner.groups.add(Group.objects.create(name='Planung'))
        self.anna = Employee.objects.create(
            user=User.objects.create_user('anna', first_name='Anna')
        )
        self.ben = Employee.objects.create(user=User.objects.create_user('ben', first_name='Ben'))
        self.month = Month.objects.create(date=date(2026, 11, 1), demand_saved=True)
        self.plan = Plan.objects.create(month=self.month, revision=0)
        self.template = ShiftTemplate.objects.create(name='Früh', start=time(8), end=time(14))
        self.slot = Slot.objects.create(
            month=self.month, date=date(2026, 11, 2), template=self.template, total=2
        )
        self.first = self.position(0, self.anna)
        self.second = self.position(1, self.ben)
        self.client.force_login(self.planner)
        self.publish_url = '/plan/veroeffentlichen/?month=2026-11'
        self.employee_url = '/mein-schichtplan/?month=2026-11'

    def position(self, index, employee):
        return Assignment.objects.create(
            plan=self.plan,
            slot=self.slot,
            position=index,
            employee=employee,
            employee_name=str(employee) if employee else '',
            date=self.slot.date,
            shift_name=self.template.name,
            start=self.template.start,
            end=self.template.end,
            role='Ohne Vorgabe',
            priority=1 if employee else None,
        )

    def publish(self, acknowledge='yes'):
        response = self.client.get(self.publish_url)
        return self.client.post(
            self.publish_url,
            {'confirmation': response.context['confirmation'], 'acknowledge': acknowledge},
        )

    def publication(self):
        from .models import PublishedPlan

        return PublishedPlan.objects.get(month=self.month)

    def test_unpublished_plan_is_never_exposed_and_preview_does_not_publish(self):
        from .models import PublishedPlan

        self.client.get(self.publish_url)
        self.assertFalse(PublishedPlan.objects.exists())
        self.client.force_login(self.anna.user)
        response = self.client.get(self.employee_url)
        self.assertContains(response, 'Für diesen Monat wurde noch kein Plan veröffentlicht')
        self.assertNotContains(response, 'Ben')

    def test_default_view_only_shows_own_snapshot_and_ignores_foreign_employee_parameter(self):
        self.assertEqual(self.publish().status_code, 302)
        self.client.force_login(self.anna.user)
        response = self.client.get(self.employee_url + f'&employee={self.ben.pk}')
        self.assertContains(response, 'Meine Schichten')
        self.assertEqual(
            list(response.context['published_rows'].values_list('employee_id', flat=True)),
            [self.anna.pk],
        )
        self.assertNotContains(response, 'Ben')
        self.assertNotContains(response, 'Priorität')
        self.assertContains(
            self.client.get('/?month=2026-11'), 'Dein Schichtplan ist veröffentlicht'
        )

    def test_team_setting_applies_immediately_without_invalidating_draft(self):
        self.publish()
        self.client.post(
            '/mitarbeitende/?month=2026-11', {'action': 'visibility', 'visibility': 'team'}
        )
        self.month.refresh_from_db()
        self.assertEqual(self.month.revision, 0)
        self.client.force_login(self.anna.user)
        self.assertContains(self.client.get(self.employee_url), 'Ben')
        self.client.force_login(self.planner)
        self.client.post(
            '/mitarbeitende/?month=2026-11', {'action': 'visibility', 'visibility': 'own'}
        )
        self.client.force_login(self.anna.user)
        self.assertNotContains(self.client.get(self.employee_url), 'Ben')

    def test_employee_cannot_publish_or_change_visibility_or_read_draft(self):
        self.client.force_login(self.anna.user)
        for method in (self.client.get, self.client.post):
            self.assertEqual(method(self.publish_url).status_code, 403)
        self.assertEqual(
            self.client.post(
                '/mitarbeitende/', {'action': 'visibility', 'visibility': 'team'}
            ).status_code,
            403,
        )
        self.assertEqual(self.client.get('/plan/').status_code, 403)
        self.assertEqual(self.client.post(self.employee_url).status_code, 405)
        self.client.logout()
        self.assertEqual(self.client.get(self.employee_url).status_code, 302)

    def test_publication_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.planner)
        self.assertEqual(client.post(self.publish_url).status_code, 403)

    def test_missing_positions_need_acknowledgement_and_own_empty_state(self):
        from .models import PublishedPlan

        self.first.employee = None
        self.first.employee_name = ''
        self.first.save()
        self.assertEqual(self.publish(acknowledge='').status_code, 200)
        self.assertFalse(PublishedPlan.objects.exists())
        self.assertEqual(self.publish().status_code, 302)
        self.client.force_login(self.anna.user)
        self.assertContains(
            self.client.get(self.employee_url),
            'Du hast in diesem Monat keine zugewiesenen Schichten',
        )
        self.client.force_login(self.planner)
        self.client.post('/mitarbeitende/', {'action': 'visibility', 'visibility': 'team'})
        self.client.force_login(self.anna.user)
        self.assertContains(self.client.get(self.employee_url), 'Unbesetzt')

    def test_stale_inputs_warn_and_require_confirmation(self):
        from .models import PublishedPlan

        self.month.revision = 1
        self.month.save()
        response = self.client.get(self.publish_url)
        self.assertContains(response, 'bisherigen Planstand')
        self.publish(acknowledge='')
        self.assertFalse(PublishedPlan.objects.exists())
        self.publish()
        response = self.client.get('/plan/?month=2026-11')
        self.assertFalse(response.context['unpublished_changes'])

    def test_complete_plan_can_be_published_without_warning_acknowledgement(self):
        self.assertEqual(self.publish(acknowledge='').status_code, 302)
        self.assertEqual(self.publication().published_by, self.planner)
        self.assertEqual(self.publication().assignments.count(), 2)

    def test_concurrent_change_or_tampered_confirmation_is_rejected(self):
        from .models import PublishedPlan

        response = self.client.get(self.publish_url)
        self.first.employee_name = 'Anderer Stand'
        self.first.save()
        result = self.client.post(
            self.publish_url, {'confirmation': response.context['confirmation']}
        )
        self.assertContains(result, 'Bitte erneut prüfen')
        self.assertFalse(PublishedPlan.objects.exists())
        self.client.post(self.publish_url, {'confirmation': 'invalid', 'acknowledge': 'yes'})
        self.assertFalse(PublishedPlan.objects.exists())

    def test_confirmation_cannot_publish_a_different_month(self):
        from .models import PublishedPlan

        response = self.client.get(self.publish_url)
        self.client.post(
            '/plan/veroeffentlichen/?month=2026-12',
            {'confirmation': response.context['confirmation']},
        )
        self.assertFalse(PublishedPlan.objects.exists())

    def test_missing_plan_has_no_publish_action(self):
        response = self.client.get('/plan/veroeffentlichen/?month=2026-12')
        self.assertContains(response, 'Bitte zuerst einen Schichtplan erzeugen')
        self.assertNotContains(response, 'name="confirmation"')

    def test_corrections_and_autofill_do_not_change_published_snapshot(self):
        from .autofill import fill_unassigned
        from .corrections import correct_plan

        self.publish()
        before = list(self.publication().assignments.values_list('employee_id', 'employee_name'))
        preview = correct_plan(self.plan.pk, self.first.pk)
        correct_plan(self.plan.pk, self.first.pk, expected=preview['state'])
        self.assertEqual(
            list(self.publication().assignments.values_list('employee_id', 'employee_name')),
            before,
        )
        Submission.objects.create(employee=self.anna, month=self.month, submitted=True)
        Availability.objects.create(employee=self.anna, slot=self.slot, priority=1)
        self.assertEqual(fill_unassigned(self.month), (1, 0))
        self.assertEqual(
            list(self.publication().assignments.values_list('employee_id', 'employee_name')),
            before,
        )

    def test_regeneration_keeps_publication_until_republished(self):
        self.publish()
        publication_id = self.publication().pk
        for employee in (self.anna, self.ben):
            Submission.objects.create(employee=employee, month=self.month, submitted=True)
            Availability.objects.create(employee=employee, slot=self.slot, priority=0)
        generate_plan(self.month)
        self.assertEqual(self.publication().assignments.filter(employee__isnull=False).count(), 2)
        self.assertContains(
            self.client.get('/plan/?month=2026-11'), 'Unveröffentlichte Änderungen'
        )
        self.publish()
        self.assertEqual(self.publication().pk, publication_id)
        self.assertEqual(self.publication().assignments.filter(employee__isnull=True).count(), 2)

    def test_failure_rolls_back_previous_publication(self):
        from unittest.mock import patch

        from .publications import publication_preview, publish_plan

        self.publish()
        previous = list(self.publication().assignments.values_list('pk', 'employee_id'))
        with (
            patch(
                'apps.planning.publications.PublishedAssignment.objects.bulk_create',
                side_effect=RuntimeError('test'),
            ),
            self.assertRaises(RuntimeError),
        ):
            publish_plan(self.month, self.planner, publication_preview(self.month)['state'])
        self.assertEqual(
            list(self.publication().assignments.values_list('pk', 'employee_id')), previous
        )

    def test_timetable_groups_team_positions_by_shift_and_day(self):
        self.publish()
        self.client.post('/mitarbeitende/', {'action': 'visibility', 'visibility': 'team'})
        self.client.force_login(self.anna.user)
        response = self.client.get(self.employee_url)
        self.assertEqual(response.context['selected_monday'], '2026-11-02')
        table = response.context['timetable_rows']
        self.assertEqual(len(table), 1)
        self.assertEqual(len(table[0]['cells']), 7)
        monday = table[0]['cells'][0]['positions']
        self.assertEqual(
            [item['assignment'].employee_id for item in monday], [self.anna.pk, self.ben.pk]
        )
        self.assertEqual([item['own'] for item in monday], [True, False])
        self.assertContains(response, 'Schichtplan der Woche')

    def test_timetable_filters_weeks_and_handles_invalid_selection(self):
        self.publish()
        self.client.force_login(self.anna.user)
        response = self.client.get(self.employee_url + '&week=2026-11-09')
        self.assertEqual(response.context['selected_monday'], '2026-11-09')
        self.assertEqual(response.context['timetable_rows'], [])
        self.assertContains(response, 'Du hast in dieser Woche keine zugewiesenen Schichten')
        self.assertEqual(response.context['previous_week'], '2026-11-02')
        self.assertEqual(response.context['next_week'], '2026-11-16')
        response = self.client.get(self.employee_url + '&week=invalid')
        self.assertEqual(response.context['selected_monday'], '2026-11-02')
        self.assertEqual(len(response.context['timetable_rows']), 1)

    def test_timetable_uses_publication_and_handles_year_boundary(self):
        from .publications import published_timetable

        self.publish()
        self.first.shift_name = 'Interner Entwurf'
        self.first.save()
        self.client.force_login(self.anna.user)
        response = self.client.get(self.employee_url)
        self.assertNotContains(response, 'Interner Entwurf')
        self.assertNotContains(response, 'Ben')
        context = published_timetable(Month(date=date(2027, 1, 1)), [], '2026-12-28')
        self.assertEqual(context['week_number'], 53)
        self.assertEqual(context['next_week'], '2027-01-04')
        self.assertTrue(context['timetable_days'][0]['outside'])
        self.assertFalse(context['timetable_days'][4]['outside'])
