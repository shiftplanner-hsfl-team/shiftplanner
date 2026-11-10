"""Regelmodul für Rahmenbedingungen RB-01 (Arbeitszeitgesetz) und RB-03 (Feiertage SH).

Das Modul ist bewusst unabhängig von Datenbank und HTTP: Es arbeitet nur mit Datum und
Uhrzeiten. Die Planerzeugung (``services.generate_plan``) und die manuelle Korrektur
(REQ-11) fragen hier lediglich „Ist diese Zuweisung zulässig?“. Grenzwerte stehen als
Konstanten an einer Stelle, weil eine Reform des ArbZG diskutiert wird (RB-01).

Vereinfachungen im MVP (dokumentiert in docs/design/architektur.md):
- Arbeitszeit = Schichtdauer abzüglich der gesetzlichen Mindestpause (§ 4).
- Der Durchschnitt von 8 Stunden über 6 Monate (§ 3 Satz 2) wird nicht nachgehalten;
  geprüft wird die Obergrenze von 10 Stunden je Tag.
- Wochenhöchstgrenze 48 Stunden je Kalenderwoche (6 Werktage × 8 Stunden, § 3).
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

# --- RB-01: Grenzwerte des Arbeitszeitgesetzes -------------------------------------
MAX_DAILY_HOURS = 10  # § 3 ArbZG: höchstens 10 Stunden werktäglich
MAX_WEEKLY_HOURS = 48  # § 3 ArbZG: 6 Werktage × 8 Stunden
MIN_REST_HOURS = 11  # § 5 ArbZG: ununterbrochene Ruhezeit nach Arbeitsende
BREAK_RULES = [(9 * 60, 45), (6 * 60, 30)]  # § 4 ArbZG: (ab Minuten Dauer, Pause Minuten)


@dataclass(frozen=True)
class Shift:
    """Eine geplante oder angefragte Schicht einer Person.

    Attributes:
        day: Datum der Schicht.
        start: Beginn (Uhrzeit).
        end: Ende (Uhrzeit, am selben Tag nach dem Beginn).
    """

    day: date
    start: time
    end: time

    @property
    def begins(self):
        """Beginn als ``datetime``."""
        return datetime.combine(self.day, self.start)

    @property
    def ends(self):
        """Ende als ``datetime``."""
        return datetime.combine(self.day, self.end)

    @property
    def minutes(self):
        """Dauer der Schicht in Minuten (inklusive Pause)."""
        return int((self.ends - self.begins).total_seconds() // 60)


def required_break_minutes(shift):
    """Liefert die gesetzliche Mindestpause einer Schicht (§ 4 ArbZG).

    Args:
        shift: ``Shift``.

    Returns:
        Pause in Minuten: 45 bei mehr als 9 Stunden, 30 bei mehr als 6 Stunden, sonst 0.
    """
    for threshold, minutes in BREAK_RULES:
        if shift.minutes > threshold:
            return minutes
    return 0


def working_hours(shift):
    """Berechnet die Arbeitszeit einer Schicht ohne Pause (§ 2 Abs. 1 ArbZG).

    Args:
        shift: ``Shift``.

    Returns:
        Arbeitszeit in Stunden (float).
    """
    return (shift.minutes - required_break_minutes(shift)) / 60


def fmt_hours(value):
    """Formatiert Stunden für Meldungen in deutscher Schreibweise.

    Args:
        value: Stunden als Zahl.

    Returns:
        Zeichenkette, z. B. ``'11,5'``.
    """
    return f'{value:g}'.replace('.', ',')


def _daily_violation(shifts, candidate):
    hours = sum(working_hours(s) for s in shifts if s.day == candidate.day)
    hours += working_hours(candidate)
    if hours > MAX_DAILY_HOURS:
        return (
            f'Mehr als {MAX_DAILY_HOURS} Stunden Arbeitszeit am {candidate.day:%d.%m.} '
            f'({fmt_hours(hours)} h, § 3 ArbZG).'
        )
    return None


def _weekly_violation(shifts, candidate):
    week = candidate.day.isocalendar()[:2]
    hours = sum(working_hours(s) for s in shifts if s.day.isocalendar()[:2] == week)
    hours += working_hours(candidate)
    if hours > MAX_WEEKLY_HOURS:
        return (
            f'Mehr als {MAX_WEEKLY_HOURS} Stunden in KW {week[1]} '
            f'({fmt_hours(hours)} h, § 3 ArbZG).'
        )
    return None


def _rest_violation(shifts, candidate):
    """Prüft die Ruhezeit zwischen dem Kandidaten und Schichten an anderen Tagen."""
    same_day = [s for s in shifts if s.day == candidate.day] + [candidate]
    day_start = min(s.begins for s in same_day)
    day_end = max(s.ends for s in same_day)
    minimum = timedelta(hours=MIN_REST_HOURS)
    for other in shifts:
        if other.day < candidate.day and day_start - other.ends < minimum:
            gap = day_start - other.ends
        elif other.day > candidate.day and other.begins - day_end < minimum:
            gap = other.begins - day_end
        else:
            continue
        return (
            f'Ruhezeit zwischen {other.day:%d.%m.} und {candidate.day:%d.%m.} nur '
            f'{fmt_hours(gap.total_seconds() / 3600)} h statt {MIN_REST_HOURS} h (§ 5 ArbZG).'
        )
    return None


def violations(shifts, candidate):
    """Prüft, ob eine weitere Schicht für eine Person gegen RB-01 verstößt.

    Zeitliche Überschneidungen prüft die Planerzeugung selbst (REQ-08); hier geht es
    nur um die gesetzlichen Grenzen.

    Args:
        shifts: Bereits zugewiesene Schichten derselben Person (``Shift``-Objekte).
        candidate: Zu prüfende zusätzliche Schicht.

    Returns:
        Liste verständlicher Meldungen; leer, wenn die Zuweisung zulässig ist.
    """
    checks = (_daily_violation, _weekly_violation, _rest_violation)
    return [message for check in checks if (message := check(shifts, candidate))]


def is_allowed(shifts, candidate):
    """Kurzform von ``violations``: True, wenn keine Grenze verletzt wird.

    Args:
        shifts: Bereits zugewiesene Schichten derselben Person.
        candidate: Zu prüfende zusätzliche Schicht.

    Returns:
        True bei zulässiger Zuweisung.
    """
    return not violations(shifts, candidate)


# --- RB-03: Gesetzliche Feiertage Schleswig-Holstein --------------------------------
def easter_sunday(year):
    """Berechnet den Ostersonntag (Gaußsche Osterformel, gregorianisch).

    Args:
        year: Jahr, z. B. 2026.

    Returns:
        Datum des Ostersonntags.
    """
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    m = (32 + 2 * e + 2 * i - h - k) % 7
    n = (a + 11 * h + 22 * m) // 451
    month = (h + m - 7 * n + 114) // 31
    day = (h + m - 7 * n + 114) % 31 + 1
    return date(year, month, day)


def holidays(year):
    """Liefert die gesetzlichen Feiertage in Schleswig-Holstein (RB-03).

    Args:
        year: Jahr.

    Returns:
        Dictionary Datum → Name des Feiertags.
    """
    easter = easter_sunday(year)
    return {
        date(year, 1, 1): 'Neujahr',
        easter - timedelta(days=2): 'Karfreitag',
        easter + timedelta(days=1): 'Ostermontag',
        date(year, 5, 1): 'Tag der Arbeit',
        easter + timedelta(days=39): 'Christi Himmelfahrt',
        easter + timedelta(days=50): 'Pfingstmontag',
        date(year, 10, 3): 'Tag der Deutschen Einheit',
        date(year, 10, 31): 'Reformationstag',
        date(year, 12, 25): '1. Weihnachtstag',
        date(year, 12, 26): '2. Weihnachtstag',
    }


def holiday_name(day):
    """Gibt den Namen des Feiertags zurück oder eine leere Zeichenkette.

    Args:
        day: Datum.

    Returns:
        Name des Feiertags in Schleswig-Holstein oder ``''``.
    """
    return holidays(day.year).get(day, '')
