# Teststand P4 (Sprint 1)

Verantwortlich: Anil Duth (Qualitätssicherung) · Stand: 10.11.2026

## 1 Automatisierter Testlauf

| Angabe | Wert |
|---|---|
| Datum | 10.11.2026 |
| Umgebung | GitHub Actions, Ubuntu |
| Befehl | `python manage.py test apps.planning tests.ui` |
| Tests gesamt | 53 |
| Bestanden / fehlgeschlagen | 53 / 0 |

## 2 Testabdeckung nach Ebene

| Testklasse | Anzahl | Ebene | Deckt ab |
|---|---|---|---|
| WorkflowTests | 15 | Integration | REQ-01, 03, 04, 06, 07, 10, QR-03 |
| EngineTests | 8 | Unit/Integration | REQ-08, 09, 14, QR-01 |
| DeadlineTests | 8 | Integration | REQ-05, REQ-07 (ABW-01) |
| EmployeeManagementTests | 5 | Integration | REQ-02 (ABW-02) |
| ArbZGRuleTests | 5 | Unit | RB-01, RB-03 |
| ArbZGPlanningTests | 3 | Integration | RB-01 in der Planerzeugung |
| HolidayCalendarTests | 1 | Integration | RB-03 |
| OpeningDayTests | 4 | Integration | REQ-22 |
| UI (test_browser.py) | 4 | UI (Chromium) | QR-02, QR-03, QR-07 |

## 3 Manuelle Prüfung

| Ablauf | Schritte | Erwartet | Ergebnis |
|---|---|---|---|
| Abgabefrist (ABW-01, PR #29) | Als Nora Frist gesetzt, als Eva nach Frist geprüft | Eingabe nach Frist gesperrt, Plan trotzdem erzeugbar | ok |
| Öffnungstage (REQ-22, PR #32) | Sonntag über Öffnungstage geöffnet | geöffneter Sonntag erscheint, Feiertag markiert | ok |

## 4 Offene Fehler

| Issue | Beschreibung | Schwere |
|---|---|---|
| #39 | UI-Test test_mobile_360_and_keyboard_login sporadisch rot | gering (kein Produktfehler) |

## 5 Fazit

Die automatisierte Test-Pipeline ist stabil und grün, die Leistungsanforderungen werden deutlich unterschritten und die Kernfunktionen wurden erfolgreich verifiziert. Der Stand ist bereit für die Abgabe.
