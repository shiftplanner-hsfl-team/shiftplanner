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
        self.assertContains(self.client.get('/plan/'), 'Nur lesen')
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
            self.assertTrue(state['ready'])
            self.assertEqual(state['missing'], 2)
            self.client.post('/plan/erzeugen/', {'month': '2026-11'})
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
