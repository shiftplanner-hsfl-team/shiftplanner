from datetime import date, time
from time import perf_counter

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import Client, TestCase, override_settings

from .models import (Assignment, Availability, Employee, Month, Need, Plan,
                     Qualification, ShiftTemplate, Slot, Submission, Vacation)
from .services import generate_plan, match_positions, touch

FAST_PASSWORDS = ['django.contrib.auth.hashers.MD5PasswordHasher']


@override_settings(PASSWORD_HASHERS=FAST_PASSWORDS, DEBUG=True)
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
        for path in ['/', '/bedarf/', '/vorlagen/', '/qualifikationen/', '/verfuegbarkeiten/', '/plan/', '/plan/erzeugen/', '/plan/unbesetzt/']:
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
        for path in ['/bedarf/', '/vorlagen/', '/qualifikationen/', '/verfuegbarkeiten/', '/plan/', '/plan/erzeugen/', '/plan/unbesetzt/', f'/verfuegbarkeiten/{self.ben.pk}/']:
            for method in (self.client.get, self.client.post):
                with self.subTest(path=path, method=method.__name__):
                    self.assertEqual(method(path).status_code, 403)
        response = self.client.get('/meine-verfuegbarkeiten/')
        self.assertNotContains(response, 'Ben Fischer')

    def test_planner_can_read_but_cannot_edit_peer_availability(self):
        self.login()
        path = f'/verfuegbarkeiten/{self.lea.pk}/'
        self.assertContains(self.client.get(path), 'Lea Meyer')
        self.assertEqual(self.client.post(path, {f'priority_{self.slot.pk}': '3'}).status_code, 403)

    def test_csrf_is_enforced(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(User.objects.get(first_name='Lea'))
        self.assertEqual(client.post('/meine-verfuegbarkeiten/', {'action': 'submit'}).status_code, 403)

    def test_draft_then_submit_preserves_other_weeks(self):
        self.login('lea.meyer')
        other = Slot.objects.filter(month=self.month, date=date(2026, 11, 30)).first()
        old = Availability.objects.get(employee=self.lea, slot=other).priority
        self.client.post('/meine-verfuegbarkeiten/', {f'priority_{self.slot.pk}': '1', 'action': 'draft'})
        self.assertFalse(Submission.objects.get(employee=self.lea, month=self.month).submitted)
        self.assertEqual(Availability.objects.get(employee=self.lea, slot=other).priority, old)
        self.client.post('/meine-verfuegbarkeiten/', {f'priority_{self.slot.pk}': '2', 'action': 'submit'})
        self.assertTrue(Submission.objects.get(employee=self.lea, month=self.month).submitted)
        self.assertEqual(Availability.objects.get(employee=self.lea, slot=self.slot).priority, 2)

    def test_invalid_priority_has_no_partial_write(self):
        self.login('lea.meyer')
        second = Slot.objects.exclude(pk=self.slot.pk).first()
        before = list(Availability.objects.filter(employee=self.lea).values_list('pk', 'priority'))
        response = self.client.post('/meine-verfuegbarkeiten/', {f'priority_{self.slot.pk}': '1', f'priority_{second.pk}': '9'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(before, list(Availability.objects.filter(employee=self.lea).values_list('pk', 'priority')))

    def test_invalid_demand_does_not_change_database(self):
        self.login()
        q = Qualification.objects.first()
        self.client.post('/bedarf/', {f'total_{self.slot.pk}': '1', f'need_{self.slot.pk}_{q.pk}': '2'})
        self.slot.refresh_from_db()
        self.assertEqual(self.slot.total, 3)

    def test_copy_week_applies_matching_weekdays(self):
        self.login()
        self.client.post('/bedarf/', {f'total_{self.slot.pk}': '2', 'action': 'copy_month'})
        totals = Slot.objects.filter(template=self.slot.template, date__week_day=2).values_list('total', flat=True)
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
        first = list(Assignment.objects.values_list('slot_id', 'position', 'employee_id', 'priority'))
        self.assertEqual(len(first), sum(Slot.objects.values_list('total', flat=True)))
        self.assertTrue(Assignment.objects.filter(employee__isnull=True).exists())
        self.client.post('/plan/erzeugen/')
        self.assertEqual(first, list(Assignment.objects.values_list('slot_id', 'position', 'employee_id', 'priority')))
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
        self.client.post('/qualifikationen/', {'name': 'Lager', 'description': '', 'employees': [self.lea.pk]})
        self.assertTrue(self.lea.qualifications.filter(name='Lager').exists())
        self.client.post('/verfuegbarkeiten/', {'employee': self.lea.pk, 'start': '2026-11-02', 'end': '2026-11-07'})
        self.complete()
        generate_plan(self.month)
        self.assertFalse(Assignment.objects.filter(employee=self.lea, date__range=[date(2026, 11, 2), date(2026, 11, 7)]).exists())


@override_settings(PASSWORD_HASHERS=FAST_PASSWORDS)
class EngineTests(TestCase):
    def setUp(self):
        self.month = Month.objects.create(date=date(2026, 11, 1), demand_saved=True)
        self.sale = Qualification.objects.create(name='Verkauf')
        self.cash = Qualification.objects.create(name='Kasse')
        self.template = ShiftTemplate.objects.create(name='Früh', start=time(8), end=time(14))
        self.slot = Slot.objects.create(month=self.month, date=date(2026, 11, 2), template=self.template, total=1)

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
        for name, start, end in [('Tag', time(10), time(16)), ('Spät', time(14), time(20))]:
            template = ShiftTemplate.objects.create(name=name, start=start, end=end)
            slot = Slot.objects.create(month=self.month, date=self.slot.date, template=template, total=1)
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
        matches = match_positions([(None, '')]*2, [[1, 2, 3], [1, 2, 3]], {1: 1, 2: 2, 3: 3})
        self.assertEqual(set(matches.values()), {1, 2})

    def test_30_employees_3_templates_30_days_under_10_seconds(self):
        from .services import ensure_slots
        ShiftTemplate.objects.create(name='Tag', start=time(10), end=time(16))
        ShiftTemplate.objects.create(name='Spät', start=time(14), end=time(20))
        ensure_slots(self.month)
        slots = list(Slot.objects.all())
        Slot.objects.update(total=3)
        employees = [self.employee(f'e{i}') for i in range(30)]
        # Include all 30 calendar days for the QR-01 reference workload.
        from .services import dates_for_month
        for day in dates_for_month(self.month.date):
            for template in ShiftTemplate.objects.all():
                Slot.objects.get_or_create(date=day, template=template, defaults={'month': self.month, 'total': 3})
        slots = list(Slot.objects.all())
        Availability.objects.bulk_create([Availability(employee=e, slot=s, priority=1 + e.pk % 3) for e in employees for s in slots if s.pk != self.slot.pk])
        started = perf_counter()
        plan = generate_plan(self.month)
        elapsed = perf_counter() - started
        self.assertLess(elapsed, 10)
        self.assertEqual(plan.assignments.count(), 270)
        print(f'\nQR-01: 30 Mitarbeitende × 3 Vorlagen × 30 Tage: {elapsed:.3f} s')
