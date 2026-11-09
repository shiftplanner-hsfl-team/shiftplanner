# Umsetzungsstand und Rückverfolgbarkeit Anforderung → Code → Test

Stand: 09.11.2026 (Sprint 1, vor P4). Grundlage: Anforderungsdokument P3 (REQ-01 bis
REQ-23, QR-01 bis QR-07, RB-01 bis RB-04, UC-01 bis UC-05) und Feedback-Dokumentation
(`docs/feedback/feedback.md`). Tests in `apps/planning/tests.py` (Klasse genannt) und
`tests/ui/test_browser.py` (UI). Alle Tests laufen bei jedem Push in GitHub Actions.

Legende: ✅ umgesetzt und getestet · 🔄 in Arbeit · ⏳ geplant (Sprint) · ⚪ später

## Funktionale Anforderungen

| ID | Anforderung | Stand | Code (Funktion bzw. View) | Tests | PR |
|---|---|---|---|---|---|
| REQ-01 | Anmeldung mit Rollen | ✅ | `views.planner_only`, `is_planner`, Django-Login | `WorkflowTests` (Zugriff), UI `test_employee_privacy_returns_403` | #1 |
| REQ-02 | Mitarbeitende anlegen (ABW-02) | ✅ | `views.employees`, `forms.EmployeeForm`, `services.save_employee` | `EmployeeManagementTests` | #30 |
| REQ-03 | Schichtvorlagen anlegen | ✅ | `views.templates`, `forms.TemplateForm` | `WorkflowTests.test_template_duration_validation`, UI | #1 |
| REQ-04 | Bedarf pro Schicht, Besetzungsmix | ✅ | `views.demand`, `parse_demand`, `save_demand`, `expand_to_month` | `WorkflowTests` (Bedarf, Kopieren), UI | #1 |
| REQ-05 | Planungszeitraum mit Abgabefrist (ABW-01) | ✅ | `views.period`, `services.set_deadline`, `period_status`, `readiness` | `DeadlineTests` | #29 |
| REQ-06 | Verfügbarkeit mit Priorität 1–3 | ✅ | `views.availability`, `parse_priorities` | `WorkflowTests`, UI mobil | #1 |
| REQ-07 | Entwurf und Abgabe, Sperre nach Frist | ✅ | `views.availability`, `services.input_open` | `WorkflowTests.test_draft_then_submit…`, `DeadlineTests.test_ak3_input_locked…` | #1, #29 |
| REQ-08 | Plan automatisch erzeugen (P1 vor P2 vor P3, deterministisch) | ✅ | `services.generate_plan`, `match_positions`, `is_eligible` | `EngineTests` | #1, #31 |
| REQ-09 | Unbesetzte Schichten anzeigen | ✅ | `views.unfilled`, `plan_context` | `EngineTests.test_qualification_and_unfilled…`, UI | #1 |
| REQ-10 | Plan nur lesend ansehen | ✅ | `views.plan`, `plan_context` | `WorkflowTests.test_full_workflow…` | #1 |
| REQ-11 | Plan manuell korrigieren (inkl. Entscheidung E-01) | 🔄 | Schnittstelle `services.assignment_violations` vorhanden | `ArbZGPlanningTests.test_assignment_violations…` | Bennet, #2 |
| REQ-12 | → überführt in RB-01 | – | – | – | – |
| REQ-13 | Vertragsstunden und Minijob-Grenze | ⏳ Sprint 2 | Daten vorhanden (`Employee.weekly_hours`) | – | #4 |
| REQ-14 | Urlaub berücksichtigen | ✅ | `views.availability_overview`, `is_eligible` | `EngineTests.test_vacation_overrides…` | #1 |
| REQ-15 | Plan veröffentlichen | ⏳ Sprint 2 | – | – | #6 |
| REQ-16 | Fairness-Historie | ⚪ | – | – | #7 |
| REQ-17 | KI-Erklärung | ⏳ Sprint 3 | – | – | #8 |
| REQ-18 | Genehmigung | ⚪ | – | – | #9 |
| REQ-19 | Schichttausch | ⚪ | – | – | #10 |
| REQ-20 | Krankmeldung | ⚪ | – | – | #11 |
| REQ-21 | Vorschläge für unbesetzte Schichten | ⚪ | – | – | #14 |
| REQ-22 | Öffnungstage je Monat | ✅ | `views.opening`, `services.open_days`, `month_slots`, `set_opening` | `OpeningDayTests` | #32 |
| REQ-23 | Wochenmuster für Verfügbarkeiten | ⏳ Sprint 2 | – | – | #13 |
| REQ-24 | Erinnerung vor Abgabefrist (neu, FB-13/15) | ⏳ Sprint 3 | – | – | #33 |
| REQ-25 | Benachrichtigung bei Planänderungen (neu, FB-13/15) | ⚪ | – | – | #34 |

## Qualitätsanforderungen

| ID | Zielwert | Stand | Nachweis |
|---|---|---|---|
| QR-01 | Plan ≤ 10 s für 30 MA × 3 Vorlagen × 30 Tage | ✅ | `EngineTests.test_30_employees…` (lokal ca. 0,1 s) |
| QR-02 | Mobile Nutzung ab 360 px | ✅ | UI `test_mobile_360_and_keyboard_login`, `test_mobile_save_submit…` |
| QR-03 | Zugriffsschutz (HTTP 403) | ✅ | `WorkflowTests` (GET/POST), UI `test_employee_privacy_returns_403` |
| QR-04 | Keine Pflichtgründe für Sperrzeiten | ✅ | Datenmodell ohne Begründungsfeld |
| QR-05 | 10 Slots in ≤ 5 min | ⏳ | Messung im Nutzertest (P6) |
| QR-06 | Monatsplan in ≤ 30 min | ⏳ | Messung im Nutzertest (P6) |
| QR-07 | UI-Tests in GitHub Actions | ✅ | Workflow `tests.yml`, 4 Chromium-Tests |

## Rahmenbedingungen

| ID | Stand | Code | Tests | PR |
|---|---|---|---|---|
| RB-01 ArbZG | ✅ | `rules.py` (`violations`, `is_allowed`), `services.is_eligible` | `ArbZGRuleTests`, `ArbZGPlanningTests` | #31 |
| RB-02 DSGVO | ✅ | Zugriffsschutz, Datenminimierung | wie QR-03, QR-04 | #1 |
| RB-03 Feiertage SH | ✅ | `rules.holidays`, Template-Filter `holiday`, `expand_to_month` | `ArbZGRuleTests.test_holidays…`, `HolidayCalendarTests` | #31 |
| RB-04 Betriebsrat | Grundsatz | Produktgrundsätze, REQ-11, REQ-17 | – | – |

## Abweichungen (Anforderungsdokument P3, Abschnitt 11)

| ID | Stand |
|---|---|
| ABW-01 Abgabefrist | **geschlossen** mit PR #29, von beiden Planern bestätigt (FB-12, FB-14) |
| ABW-02 Mitarbeitende anlegen | **geschlossen** mit PR #30, von beiden Planern bestätigt (FB-12, FB-14) |
| ABW-03 Mehrere Betriebe | offen, bleibt Anforderung; relevant erst mit Mandantenfähigkeit |

## Bewusste Grenzen

Ein Betrieb je Installation; Nachtschichten über Mitternacht nicht enthalten (REQ-03);
der Ausgleichszeitraum nach § 3 Satz 2 ArbZG wird nicht nachgehalten (siehe
`docs/design/architektur.md`). Die Abnahme aller Akzeptanzkriterien durch reale
Nutzerinnen und Nutzer erfolgt in den Nutzertests (P6).
