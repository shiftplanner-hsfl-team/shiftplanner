"""Unit-Tests für das Regelmodul RB-01/RB-03 (rules.py) ohne Datenbank.

Testfälle TC-U-07 bis TC-U-12, TC-U-14, TC-U-15 und TC-U-20 aus docs/testing/testfaelle.md.
Verfahren: Grenzwertanalyse (GW) und Äquivalenzklassen (ÄK).
"""

from datetime import date, time

from django.test import SimpleTestCase

from apps.planning import rules
from apps.planning.rules import Shift


def shift(day, start, end):
    """Schicht im November 2026 (2.11. = Montag, KW 45)."""
    return Shift(date(2026, 11, day), time(*start), time(*end))


class BreakBoundaryTests(SimpleTestCase):
    def test_tc_u_07_break_boundaries_6_and_9_hours(self):
        """TC-U-07 (GW, § 4 ArbZG): genau 6 h ohne Pause, darüber 30 min, über 9 h 45 min."""
        cases = [
            (shift(2, (8, 0), (14, 0)), 0),
            (shift(2, (8, 0), (14, 1)), 30),
            (shift(2, (8, 0), (17, 0)), 30),
            (shift(2, (8, 0), (17, 1)), 45),
        ]
        for candidate, expected in cases:
            with self.subTest(minutes=candidate.minutes):
                self.assertEqual(rules.required_break_minutes(candidate), expected)


class DailyMaximumTests(SimpleTestCase):
    def test_tc_u_08_exactly_10_hours_allowed_more_is_violation(self):
        """TC-U-08 (GW, § 3 ArbZG): 6 h + 4 h = 10 h zulässig, 6 h + 4,25 h nicht."""
        early = shift(2, (6, 0), (12, 0))
        self.assertTrue(rules.is_allowed([early], shift(2, (13, 0), (17, 0))))
        messages = rules.violations([early], shift(2, (13, 0), (17, 15)))
        self.assertEqual(len(messages), 1)
        self.assertIn('§ 3', messages[0])
        self.assertIn('10,25 h', messages[0])


class RestPeriodTests(SimpleTestCase):
    def test_tc_u_09_exactly_11_hours_rest_allowed_one_minute_less_is_violation(self):
        """TC-U-09 (GW, § 5 ArbZG): Ende 22:00, Beginn 9:00 erlaubt, 8:59 nicht."""
        late = shift(2, (14, 0), (22, 0))
        self.assertTrue(rules.is_allowed([late], shift(3, (9, 0), (15, 0))))
        messages = rules.violations([late], shift(3, (8, 59), (14, 59)))
        self.assertEqual(len(messages), 1)
        self.assertIn('§ 5', messages[0])


class WeeklyMaximumTests(SimpleTestCase):
    def week(self):
        # Mo–Fr je 8:00–16:30 = 510 min − 30 min Pause = 8,0 h → 40 h.
        return [shift(day, (8, 0), (16, 30)) for day in range(2, 7)]

    def test_tc_u_10_exactly_48_hours_allowed_more_is_violation(self):
        """TC-U-10 (GW, § 3 ArbZG): 40 h + 8 h = 48 h zulässig, 40 h + 8,25 h nicht."""
        self.assertTrue(rules.is_allowed(self.week(), shift(7, (8, 0), (16, 30))))
        messages = rules.violations(self.week(), shift(7, (8, 0), (16, 45)))
        self.assertTrue(any('KW 45' in m and '48,25 h' in m for m in messages))

    def test_tc_u_11_hours_of_previous_week_do_not_count(self):
        """TC-U-11 (ÄK): 48 h in KW 45, Montag der KW 46 ist zulässig."""
        full_week = self.week() + [shift(7, (8, 0), (16, 30))]
        self.assertTrue(rules.is_allowed(full_week, shift(9, (8, 0), (16, 30))))


class EmptyScheduleTests(SimpleTestCase):
    def test_tc_u_12_no_existing_shifts(self):
        """TC-U-12 (ÄK): ohne bestehende Schichten ist eine normale Schicht zulässig."""
        candidate = shift(2, (8, 0), (14, 0))
        self.assertTrue(rules.is_allowed([], candidate))
        self.assertEqual(rules.violations([], candidate), [])


class HolidayTests(SimpleTestCase):
    def test_tc_u_14_easter_sunday_for_several_years(self):
        """TC-U-14 (ÄK, RB-03): Gaußsche Osterformel für drei weitere Jahre."""
        expected = {2025: date(2025, 4, 20), 2027: date(2027, 3, 28), 2028: date(2028, 4, 16)}
        for year, easter in expected.items():
            with self.subTest(year=year):
                self.assertEqual(rules.easter_sunday(year), easter)

    def test_tc_u_15_moveable_holidays_follow_easter(self):
        """TC-U-15 (ÄK, RB-03): bewegliche Feiertage 2027."""
        expected = {
            date(2027, 3, 26): 'Karfreitag',
            date(2027, 3, 29): 'Ostermontag',
            date(2027, 5, 6): 'Christi Himmelfahrt',
            date(2027, 5, 17): 'Pfingstmontag',
        }
        for day, name in expected.items():
            with self.subTest(day=day):
                self.assertEqual(rules.holiday_name(day), name)

    def test_tc_u_20_new_year_and_ordinary_day(self):
        """TC-U-20 (ÄK, RB-03): 1.1. ist Neujahr, 2.1. kein Feiertag."""
        self.assertEqual(rules.holiday_name(date(2027, 1, 1)), 'Neujahr')
        self.assertEqual(rules.holiday_name(date(2027, 1, 2)), '')
