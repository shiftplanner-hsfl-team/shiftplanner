"""Unit-Tests für Überschneidung und Zuordnung (services.py) ohne Datenbank.

Testfälle TC-U-13 und TC-U-16 bis TC-U-19 aus docs/testing/testfaelle.md (REQ-08, REQ-09).
"""

from datetime import date, time

from django.test import SimpleTestCase

from apps.planning.rules import Shift
from apps.planning.services import match_positions, overlaps

FREE = (None, '')  # Position ohne Qualifikationsvorgabe


def shift(start, end):
    return Shift(date(2026, 11, 2), time(start), time(end))


class OverlapTests(SimpleTestCase):
    def test_tc_u_13_overlapping_adjacent_and_separate_shifts(self):
        """TC-U-13 (GW): 8–14 überschneidet 10–16, nicht aber 14–18 oder 15–20."""
        early = shift(8, 14)
        self.assertTrue(overlaps(early, shift(10, 16)))
        self.assertFalse(overlaps(early, shift(14, 18)))
        self.assertFalse(overlaps(early, shift(15, 20)))


class MatchingTests(SimpleTestCase):
    def test_tc_u_16_no_candidate_leaves_position_open(self):
        """TC-U-16 (ÄK): ohne Kandidaten bleibt die Position unbesetzt."""
        self.assertEqual(match_positions([FREE], [[]], {}), {})

    def test_tc_u_17_more_positions_than_candidates(self):
        """TC-U-17 (GW): 3 Positionen, 1 Person → genau eine Position besetzt."""
        result = match_positions([FREE] * 3, [[1], [1], [1]], {1: 1})
        self.assertEqual(len(result), 1)
        self.assertEqual(list(result.values()), [1])

    def test_tc_u_18_result_is_deterministic(self):
        """TC-U-18 (ÄK): gleiche Eingabe, gleiches Ergebnis – auch bei anderer Dict-Reihenfolge."""
        roles = [FREE] * 2
        candidates = [[1, 2, 3], [1, 2, 3]]
        first = match_positions(roles, candidates, {1: 2, 2: 2, 3: 2})
        second = match_positions(roles, candidates, {3: 2, 2: 2, 1: 2})
        self.assertEqual(first, second)
        self.assertEqual(first, match_positions(roles, candidates, {1: 2, 2: 2, 3: 2}))

    def test_tc_u_19_priority_1_wins_over_priority_3(self):
        """TC-U-19 (ET): eine Position, A mit Priorität 3, B mit Priorität 1 → B."""
        self.assertEqual(match_positions([FREE], [[1, 2]], {1: 3, 2: 1}), {0: 2})
