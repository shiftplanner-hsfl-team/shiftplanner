"""Betriebsgrenzen, leere Demo-Unternehmen und Erhalt bestehender Daten."""

# ruff: noqa: D101, D102

from datetime import date, time
from io import StringIO

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase, override_settings

from .corrections import correct_plan
from .models import (
    Assignment,
    Company,
    CompanyAccount,
    Employee,
    Month,
    Plan,
    PlanningSettings,
    Qualification,
    ShiftTemplate,
    Slot,
    Vacation,
)
from .publications import publication_preview, publish_plan, team_plan_visible
from .services import generate_plan, readiness


@override_settings(DEBUG=True, PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class CompanyIsolationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', stdout=StringIO())
        cls.original = Company.objects.get(slug='nordlicht')
        cls.company = Company.objects.get(slug='testunternehmen-1')
        cls.planner = User.objects.get(username='planer1@example.com')
        cls.month = Month.objects.create(company=cls.company, date=date(2026, 11, 1))
        cls.foreign_employee = Employee.objects.get(user__first_name='Lea')
        cls.foreign_template = ShiftTemplate.objects.filter(company=cls.original).first()
        cls.foreign_qualification = Qualification.objects.filter(company=cls.original).first()
        cls.old_month = Month.objects.get(company=cls.original)
        cls.old_plan = Plan.objects.create(month=cls.old_month, revision=0)
        cls.old_slot = Slot.objects.filter(month=cls.old_month).first()
        cls.assignment = Assignment.objects.create(
            plan=cls.old_plan,
            slot=cls.old_slot,
            position=0,
            date=cls.old_slot.date,
            shift_name='Frühschicht',
            start=time(8),
            end=time(14),
            role='Verkauf',
            employee=cls.foreign_employee,
            employee_name='Lea Meyer',
        )

    def setUp(self):
        self.client.force_login(self.planner)

    def test_three_companies_are_empty_and_seed_preserves_existing_data(self):
        self.assertEqual(Company.objects.count(), 4)
        self.assertEqual(Employee.objects.filter(company=self.original).count(), 12)
        before = list(self.old_plan.assignments.values())
        self.planner.set_password('ChangedPassword2026!')
        self.planner.save()
        call_command('seed_test_companies', stdout=StringIO())
        self.planner.refresh_from_db()
        self.assertTrue(self.planner.check_password('ChangedPassword2026!'))
        self.assertEqual(list(self.old_plan.assignments.values()), before)
        self.assertEqual(User.objects.count(), 16)
        for company in Company.objects.exclude(pk=self.original.pk):
            self.assertFalse(Employee.objects.filter(company=company).exists())
            self.assertFalse(ShiftTemplate.objects.filter(company=company).exists())
            self.assertFalse(Qualification.objects.filter(company=company).exists())
            self.assertFalse(Plan.objects.filter(month__company=company).exists())

    def test_views_only_show_own_company(self):
        for path in [
            '/',
            '/mitarbeitende/',
            '/vorlagen/',
            '/qualifikationen/',
            '/verfuegbarkeiten/',
            '/bedarf/',
            '/plan/',
            '/plan/erzeugen/',
        ]:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertContains(response, 'Testunternehmen 1')
                self.assertNotContains(response, 'Lea Meyer')
                self.assertNotContains(response, 'Filiale Flensburg')
        self.assertEqual(readiness(self.month)['employees'], 0)
        self.assertFalse(Slot.objects.filter(month=self.month).exists())
        with self.assertRaises(ValueError):
            generate_plan(self.month)

    def test_foreign_ids_are_rejected_for_get_and_post(self):
        routes = [
            f'/vorlagen/?edit={self.foreign_template.pk}',
            f'/qualifikationen/?edit={self.foreign_qualification.pk}',
            f'/mitarbeitende/?edit={self.foreign_employee.pk}',
            f'/verfuegbarkeiten/{self.foreign_employee.pk}/',
            f'/plan/position/{self.assignment.pk}/',
        ]
        for route in routes:
            for method in [self.client.get, self.client.post]:
                with self.subTest(route=route, method=method.__name__):
                    self.assertEqual(method(route).status_code, 404)

    def test_foreign_vacation_and_qualification_cannot_be_submitted(self):
        response = self.client.post(
            '/verfuegbarkeiten/',
            {
                'employee': self.foreign_employee.pk,
                'start': '2026-11-01',
                'end': '2026-11-02',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Vacation.objects.exists())
        response = self.client.post(
            '/mitarbeitende/',
            {
                'first_name': 'Test',
                'last_name': 'Person',
                'email': 'new@example.com',
                'contract_type': Employee.PART_TIME,
                'weekly_hours': '20',
                'password': 'NewDemoPassword2026!',
                'qualifications': [self.foreign_qualification.pk],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='new@example.com').exists())

    def test_same_names_are_allowed_between_companies_and_rejected_inside_one(self):
        data = {'name': self.foreign_template.name, 'start': '08:00', 'end': '14:00'}
        self.assertEqual(self.client.post('/vorlagen/', data).status_code, 302)
        self.assertEqual(self.client.post('/vorlagen/', data).status_code, 200)
        self.assertEqual(ShiftTemplate.objects.filter(company=self.company).count(), 1)
        self.old_month.refresh_from_db()
        self.assertEqual(self.old_month.revision, 0)
        data = {'name': self.foreign_qualification.name}
        self.assertEqual(self.client.post('/qualifikationen/', data).status_code, 302)
        self.assertEqual(self.client.post('/qualifikationen/', data).status_code, 200)
        self.assertEqual(Qualification.objects.filter(company=self.company).count(), 1)

    def test_new_employee_can_login_only_in_own_company(self):
        response = self.client.post(
            '/mitarbeitende/',
            {
                'first_name': 'Neue',
                'last_name': 'Person',
                'email': 'new@example.com',
                'contract_type': Employee.PART_TIME,
                'weekly_hours': '20',
                'password': 'NewDemoPassword2026!',
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='new@example.com')
        self.assertEqual(user.companyaccount.company_id, self.company.pk)
        self.assertEqual(user.employee.company_id, self.company.pk)
        self.client.force_login(user)
        self.assertContains(self.client.get('/'), 'Testunternehmen 1')
        self.assertEqual(self.client.get('/mitarbeitende/').status_code, 403)
        self.assertEqual(
            self.client.get(f'/verfuegbarkeiten/{self.foreign_employee.pk}/').status_code, 403
        )

    def test_visibility_is_per_company(self):
        self.client.post('/mitarbeitende/', {'action': 'visibility', 'visibility': 'team'})
        self.assertTrue(team_plan_visible(self.company))
        self.assertFalse(team_plan_visible(self.original))
        self.assertEqual(PlanningSettings.objects.count(), 1)

    def test_account_without_company_is_denied_even_with_planner_group(self):
        user = User.objects.create_user('unassigned')
        user.groups.add(Group.objects.get(name='Planung'))
        self.client.force_login(user)
        self.assertEqual(self.client.get('/').status_code, 403)
        self.assertEqual(self.client.post('/vorlagen/', {}).status_code, 403)

    def test_cross_company_assignment_is_rejected_in_service(self):
        self.assertEqual(CompanyAccount.objects.get(user=self.planner).company_id, self.company.pk)
        user = User.objects.create_user('own-worker')
        own = Employee.objects.create(user=user, company=self.company)
        with self.assertRaises(ValueError):
            correct_plan(self.old_plan.pk, self.assignment.pk, employee_id=own.pk)

    def test_employee_cannot_see_another_company_publication(self):
        publish_plan(
            self.old_month,
            User.objects.get(username='nora.krueger@example.com'),
            publication_preview(self.old_month)['state'],
        )
        user = User.objects.create_user('own-worker')
        Employee.objects.create(user=user, company=self.company)
        CompanyAccount.objects.create(user=user, company=self.company)
        self.client.force_login(user)
        response = self.client.get('/mein-schichtplan/')
        self.assertContains(response, 'noch kein Plan veröffentlicht')
        self.assertNotContains(response, 'Lea Meyer')

    def test_empty_company_does_not_consider_foreign_employees_for_generation(self):
        template = ShiftTemplate.objects.create(
            company=self.company, name='Eigene Schicht', start=time(8), end=time(14)
        )
        Slot.objects.create(month=self.month, template=template, date=date(2026, 11, 2), total=1)
        self.month.demand_saved = True
        self.month.save()
        self.assertFalse(readiness(self.month)['can_generate'])
        with self.assertRaises(ValueError):
            generate_plan(self.month, allow_incomplete=True)

    def test_preparation_only_changes_nordlicht_and_preserves_empty_companies(self):
        before = list(Month.objects.exclude(company=self.original).order_by('pk').values())
        call_command('prepare_usertests', stdout=StringIO())
        self.assertEqual(
            list(Month.objects.exclude(company=self.original).order_by('pk').values()), before
        )
        for company in Company.objects.exclude(pk=self.original.pk):
            self.assertFalse(Employee.objects.filter(company=company).exists())
            self.assertFalse(ShiftTemplate.objects.filter(company=company).exists())
        december = Month.objects.get(company=self.original, date=date(2026, 12, 1))
        self.assertEqual(december.deadline, date(2026, 11, 30))

    def test_preparation_excludes_foreign_employees(self):
        from .models import Submission

        worker = User.objects.create_user('foreign-test-worker')
        Employee.objects.create(user=worker, company=self.company)
        call_command('prepare_usertests', stdout=StringIO())
        december = Month.objects.get(company=self.original, date=date(2026, 12, 1))
        self.assertEqual(Submission.objects.filter(month=december, submitted=True).count(), 11)
        self.assertFalse(Submission.objects.filter(employee__company=self.company).exists())


class CompanyMigrationTests(TransactionTestCase):
    def test_existing_users_assignments_and_publications_are_preserved(self):
        before = [('planning', '0006_publication_input_revision')]
        after = [('planning', '0007_company_isolation')]
        executor = MigrationExecutor(connection)
        executor.migrate(before)
        old = executor.loader.project_state(before).apps
        try:
            user = old.get_model('auth', 'User').objects.create(username='old-planner')
            month = old.get_model('planning', 'Month').objects.create(date=date(2026, 11, 1))
            plan = old.get_model('planning', 'Plan').objects.create(month=month, revision=7)
            publication = old.get_model('planning', 'PublishedPlan').objects.create(
                month=month,
                published_by=user,
                source_fingerprint='unchanged',
                source_input_revision=7,
            )
            snapshot = old.get_model('planning', 'PublishedAssignment').objects.create(
                publication=publication,
                position=0,
                date=date(2026, 11, 2),
                shift_name='Bestehende Schicht',
                start=time(8),
                end=time(14),
                role='Verkauf',
                employee_name='Bestehender Name',
            )
            old.get_model('planning', 'PlanningSettings').objects.create(show_team_plan=True)
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(after)
        self.assertEqual(Month.objects.get(pk=month.pk).company.slug, 'nordlicht')
        self.assertEqual(CompanyAccount.objects.get(user_id=user.pk).company.slug, 'nordlicht')
        self.assertEqual(Plan.objects.get(pk=plan.pk).revision, 7)
        from .models import PublishedAssignment, PublishedPlan

        self.assertEqual(
            PublishedPlan.objects.get(pk=publication.pk).source_fingerprint, 'unchanged'
        )
        self.assertEqual(
            PublishedAssignment.objects.get(pk=snapshot.pk).employee_name, 'Bestehender Name'
        )
        self.assertTrue(team_plan_visible(Company.objects.get(slug='nordlicht')))
