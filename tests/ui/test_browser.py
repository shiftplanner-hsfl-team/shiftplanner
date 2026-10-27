"""Echte Chromium-Tests gegen Django + SQLite-Testdatenbank (QR-07)."""
import os
from pathlib import Path

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from django.test import override_settings
from playwright.sync_api import expect, sync_playwright

from apps.planning.models import Employee


@override_settings(DEBUG=True, PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BrowserTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.artifacts = Path(os.environ.get('UI_ARTIFACT_DIR', 'test-artifacts'))
        cls.artifacts.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        call_command('seed_demo', verbosity=0)
        self.ben_id = Employee.objects.get(user__first_name='Ben').pk
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch()
        self.browser_context = self.browser.new_context(viewport={'width': 1440, 'height': 1000})
        self.page = self.browser_context.new_page()
        self.js_errors = []
        self.page.on('pageerror', lambda e: self.js_errors.append(str(e)))

    def tearDown(self):
        self.page.screenshot(path=str(self.artifacts / f'{self._testMethodName}.png'), full_page=True)
        self.browser_context.close()
        self.browser.close()
        self.playwright.stop()
        self.assertEqual(self.js_errors, [])

    def login(self, name):
        self.page.goto(self.live_server_url + '/anmelden/')
        self.page.get_by_label('E-Mail-Adresse').fill(name + '@example.com')
        self.page.get_by_label('Passwort', exact=True).fill('ShiftDemo2026!')
        self.page.get_by_role('button', name='Anmelden', exact=True).click()
        self.page.wait_for_url(self.live_server_url + '/')

    def logout(self):
        # The desktop sidebar and mobile avatar both submit the same protected logout.
        self.page.locator('form[action="/abmelden/"]:visible button').first.click()
        self.page.wait_for_url('**/anmelden/')

    def assert_no_overflow(self):
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth <= innerWidth'))

    def test_planner_demand_template_and_qualification(self):
        self.login('nora.krueger')
        self.page.get_by_role('link', name='Personalbedarf', exact=True).click()
        total = self.page.locator('input[name^="total_"]').first
        field_id = total.get_attribute('id')
        total.fill('4')
        self.page.get_by_role('button', name='Bedarf speichern', exact=True).click()
        expect(self.page.locator('#' + field_id)).to_have_value('4')
        self.page.reload()
        expect(self.page.locator('#' + field_id)).to_have_value('4')
        self.page.get_by_role('link', name='Schichtvorlagen', exact=True).click()
        self.page.get_by_label('Name der Vorlage', exact=True).fill('Wochenendschicht')
        self.page.get_by_label('Beginn', exact=True).fill('09:00')
        self.page.get_by_label('Ende', exact=True).fill('15:00')
        self.page.get_by_role('button', name='Vorlage speichern').click()
        expect(self.page.get_by_role('heading', name='Wochenendschicht', exact=True)).to_be_visible()
        self.page.get_by_role('link', name='Qualifikationen', exact=True).click()
        self.page.get_by_label('Bezeichnung', exact=True).fill('Lager')
        self.page.get_by_label('Lea Meyer', exact=True).check()
        self.page.get_by_role('button', name='Änderungen speichern').click()
        expect(self.page.get_by_role('link', name='Lager', exact=True)).to_be_visible()
        self.assertEqual(self.page.locator('img').evaluate_all('(xs)=>xs.filter(i=>!i.complete||!i.naturalWidth).length'), 0)

    def test_mobile_save_submit_then_generate_month(self):
        self.page.set_viewport_size({'width': 360, 'height': 900})
        for name in ['ben.fischer', 'eva.koch']:
            self.login(name)
            self.page.goto(self.live_server_url + '/meine-verfuegbarkeiten/')
            field = self.page.locator('select[data-mirror]').first
            field.select_option('1')
            self.page.get_by_role('button', name='Entwurf speichern', exact=True).click()
            expect(self.page.get_by_role('status')).to_contain_text('Entwurf gespeichert')
            expect(self.page.locator('select[data-mirror]').first).to_have_value('1')
            self.page.get_by_role('button', name='Angaben abgeben', exact=True).click()
            expect(self.page.get_by_role('status')).to_contain_text('Alles abgegeben')
            self.assert_no_overflow()
            self.logout()
        self.page.set_viewport_size({'width': 1440, 'height': 1000})
        self.login('nora.krueger')
        self.page.goto(self.live_server_url + '/plan/erzeugen/')
        self.page.get_by_role('button', name='Schichtplan erzeugen', exact=True).click()
        self.page.wait_for_url('**/plan/?*')
        expect(self.page.get_by_text('Erzeugt · Nur lesen', exact=True)).to_be_visible()
        self.page.screenshot(path=str(self.artifacts / 'plan-desktop.png'), full_page=True)
        self.page.get_by_role('link', name='Unbesetzte Schichten ansehen', exact=True).click()
        expect(self.page.get_by_role('heading', name='Unbesetzte Schichten')).to_be_visible()
        expect(self.page.get_by_role('table')).to_contain_text('06.11.')

    def test_mobile_360_and_keyboard_login(self):
        self.page.set_viewport_size({'width': 360, 'height': 900})
        self.page.goto(self.live_server_url + '/anmelden/')
        self.page.get_by_label('E-Mail-Adresse').fill('lea.meyer@example.com')
        self.page.keyboard.press('Tab')
        self.page.keyboard.type('ShiftDemo2026!')
        self.page.keyboard.press('Enter')
        self.page.wait_for_url(self.live_server_url + '/')
        self.page.goto(self.live_server_url + '/meine-verfuegbarkeiten/')
        self.assert_no_overflow()
        expect(self.page.locator('.day-card:visible')).to_have_count(4)
        self.page.get_by_role('button', name='Weitere Tage').click()
        expect(self.page.locator('.day-card:visible')).to_have_count(6)
        self.assert_no_overflow()
        self.page.screenshot(path=str(self.artifacts / 'availability-mobile.png'), full_page=True)

    def test_employee_privacy_returns_403(self):
        self.login('lea.meyer')
        for path in ['/bedarf/', f'/verfuegbarkeiten/{self.ben_id}/']:
            response = self.page.goto(self.live_server_url + path)
            self.assertEqual(response.status, 403)
            expect(self.page.get_by_role('heading', name='Kein Zugriff')).to_be_visible()
            expect(self.page.get_by_text('Ben Fischer', exact=True)).to_have_count(0)
