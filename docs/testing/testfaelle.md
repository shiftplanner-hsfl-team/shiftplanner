# Testfallkatalog ShiftPlanner

Verantwortlich: Anil Duth (Qualitätssicherung); ab 23.11.2026 vertretungsweise Muhammed Asif Shahul Hameed · Stand: 23.11.2026 · Version 1.2 (ergänzt um PR #45, #46 und #66) · Grundlage: `testkonzept.md`

Dieser Katalog beschreibt jeden Testfall so, dass Außenstehende ihn ohne Blick in den Code verstehen und wiederholen können: geprüfte Anforderung, Eingabe, erwartetes Ergebnis (Testorakel) und das Verfahren, mit dem er abgeleitet wurde. Die Vorbedingungen und Testdaten sind je Gruppe einmal angegeben, weil alle Testfälle einer Gruppe denselben Ausgangszustand verwenden. Die Ergebnisse der einzelnen Läufe (bestanden/fehlgeschlagen, Datum, CI-Lauf) stehen nicht hier, sondern im jeweiligen Testbericht (`teststand_*.md`), der über die Testfall-ID auf diesen Katalog verweist.

**Aufbau der IDs:** `TC-U` Unit-Test · `TC-K` Komponententest · `TC-A` automatisierter Akzeptanztest · `TC-UI` Oberflächentest im Browser · `TC-M` manueller Akzeptanztest mit Nutzenden. Die Testfälle TC-U-07 bis TC-U-20 und alle TC-A wurden für P5 ergänzt; die Tests mit Nutzenden (TC-M) laufen ab P5 und vollständig zu P6.

**Abkürzungen der Verfahren:** ÄK = Äquivalenzklassen · GW = Grenzwertanalyse · ET = Entscheidungstabelle · ZB = zustandsbasiert · AB = Ablauf/Anwendungsfall · NF = nichtfunktionale Messung · SI = Sicherheit/Zugriffsschutz

**Ausführung:** Alle automatisierten Testfälle laufen bei jedem Push in GitHub Actions (Backend zusätzlich gegen PostgreSQL 18, Abdeckungsbericht als Artefakt `coverage-report`). Lokal: `coverage run manage.py test apps.planning tests.unit tests.acceptance` und `coverage report` (Backend) und `python manage.py test tests.ui` (Browser, vorher einmalig `python -m playwright install chromium`).

## Übersicht

| Stufe | Automatisiert | Geplant bis P6 | Ort |
|---|---|---|---|
| Unit (TC-U) | 20 | – | `apps/planning/tests.py` (6), `tests/unit/` (14) |
| Komponente (TC-K) | 113 | – | `apps/planning/tests.py` (99), `apps/planning/test_companies.py` (14) |
| Akzeptanz automatisiert (TC-A) | 43 | – | `tests/acceptance/test_akzeptanz.py` (alle bestanden) |
| Oberfläche (TC-UI) | 10 | – | `tests/ui/test_browser.py` |
| Akzeptanz mit Nutzenden (TC-M) | – | 5 Aufgaben × 4 Personen | `docs/testing/nutzertests/` |
| **Summe automatisiert** | **186** | | |

## Rückverfolgbarkeit Anforderung → Testfälle

| Anforderung | Testfälle |
|---|---|
| REQ-01 Anmeldung mit Rollen | TC-K-01, TC-K-02, TC-UI-07, TC-A-01-1 bis -3 |
| REQ-02 Mitarbeitende anlegen (ABW-02), Betriebstrennung (ABW-03) | TC-K-27 bis TC-K-31, TC-K-87 bis TC-K-100, TC-UI-09, TC-A-02-1 bis -3 |
| REQ-03 Schichtvorlagen | TC-K-17, TC-UI-01, TC-A-03-1 bis -3 |
| REQ-04 Bedarf, Besetzungsmix | TC-K-08, TC-K-09, TC-UI-01, TC-A-04-1 bis -3 |
| REQ-05 Planungszeitraum mit Frist (ABW-01) | TC-K-19 bis TC-K-26, TC-A-05-1 bis -4 |
| REQ-06 Verfügbarkeit mit Priorität | TC-K-06, TC-K-07, TC-UI-02, TC-A-06-1 bis -3 |
| REQ-07 Entwurf, Abgabe, Sperre | TC-K-06, TC-K-22, TC-K-23, TC-K-26, TC-UI-02, TC-A-07-1 bis -3 |
| REQ-08 Plan automatisch erzeugen | TC-U-06, TC-U-13, TC-U-16 bis TC-U-19, TC-K-10 bis TC-K-15, TC-K-32 bis TC-K-37, TC-UI-02, TC-UI-04, TC-A-08-1 bis -4 |
| REQ-09 Unbesetzte Schichten | TC-K-14, TC-K-33, TC-UI-02, TC-A-09-1, -2 |
| REQ-10 Plan nur lesend | TC-K-14, TC-A-10-1 bis -3 |
| REQ-11 Plan manuell korrigieren | TC-K-47 bis TC-K-62, TC-UI-03, TC-UI-05, TC-A-11-1 bis -3 |
| REQ-14 Urlaub | TC-K-18, TC-K-36, TC-A-14-1 |
| REQ-15 Plan veröffentlichen | TC-K-101 bis TC-K-103, TC-K-63 bis TC-K-79, TC-UI-06, TC-A-15-1a, -1b |
| REQ-22 Öffnungstage | TC-K-43 bis TC-K-46, TC-A-22-1 |
| QR-01 Laufzeit ≤ 10 s | TC-K-38, TC-A-QR01-1 |
| QR-02 Mobil ab 360 px | TC-UI-02, TC-UI-06, TC-UI-07 |
| QR-03 Zugriffsschutz 403 (inkl. AK 2 fremder Betrieb) | TC-K-88 bis TC-K-91, TC-K-94, TC-K-96, TC-UI-09, TC-K-03, TC-K-04, TC-K-05, TC-K-21, TC-K-31, TC-K-46, TC-K-53, TC-K-61, TC-K-66, TC-K-67, TC-UI-08, TC-A-QR03-1, -3 |
| QR-04 Keine Pflichtgründe | TC-A-QR04-1, -2; Inspektion Datenmodell |
| QR-05, QR-06 Bearbeitungszeiten | TC-M-01 bis TC-M-05, TC-UI-10 (10 Eingaben möglich) |
| QR-07 UI-Tests in CI | TC-UI-01 bis TC-UI-08 |
| RB-01 ArbZG | TC-U-01 bis TC-U-04, TC-U-07 bis TC-U-12, TC-K-39 bis TC-K-41, TC-K-50, TC-K-56 |
| RB-03 Feiertage SH | TC-U-05, TC-U-14, TC-U-15, TC-U-20, TC-K-42 |

---

## 1 Unit-Tests (TC-U)

**Vorbedingung:** keine Datenbankdaten; geprüft werden reine Funktionen aus `rules.py` und `services.py`. Schichten werden als `Shift(Datum, Beginn, Ende)` im November 2026 übergeben (2.11. = Montag, KW 45).

### 1.1 Vorhanden (`apps/planning/tests.py`, Klassen `ArbZGRuleTests`, `EngineTests`)

| ID | Testfall | Anf. | Eingabe | Erwartetes Ergebnis (Orakel) | Verf. | Umsetzung |
|---|---|---|---|---|---|---|
| TC-U-01 | Pausen und Arbeitszeit nach § 4 ArbZG | RB-01 | Schichten 8–14, 8–15, 8–18 Uhr | Pause 0 / 30 / 45 min; Arbeitszeit 8–18 Uhr = 9,25 h | GW | `ArbZGRuleTests.test_break_and_working_hours_par_4` |
| TC-U-02 | Tageshöchstarbeitszeit 10 h (§ 3) | RB-01 | Bestehend 6–12; Kandidat 12–16 bzw. 12–18 | 12–16 erlaubt; 12–18 liefert genau einen Verstoß mit „§ 3“ | GW | `…test_daily_maximum_10_hours_par_3` |
| TC-U-03 | Ruhezeit 11 h (§ 5), vorwärts und rückwärts | RB-01 | Spät 14–22 am 2.11.; Kandidat 3.11. 8–14 bzw. 9–15; rückwärts: 3.11. 6–12 vorhanden, Kandidat 2.11. 14–20 | 8–14 Verstoß „§ 5“; 9–15 erlaubt (genau 11 h); rückwärts nicht erlaubt | GW | `…test_rest_period_11_hours_par_5` |
| TC-U-04 | Wochenhöchstarbeitszeit 48 h | RB-01 | Mo–Sa je 8–16 (7,5 h); Kandidat Sa 17–21 | Sechs Schichten (45 h) erlaubt; zusätzlicher Kandidat liefert Verstoß mit „KW 45“ und „11,5 h“ | GW | `…test_weekly_maximum_48_hours` |
| TC-U-05 | Feiertage Schleswig-Holstein | RB-03 | Jahre 2026/2027, einzelne Daten | Ostersonntag 2026 = 5.4.; 3.4. Karfreitag; 14.5. Christi Himmelfahrt; 31.10. Reformationstag; 18.11. kein Feiertag (Buß- und Bettag nur Sachsen); 2027 genau 10 Feiertage | ÄK | `…test_holidays_schleswig_holstein_rb_03` |
| TC-U-06 | Zuordnung maximiert Priorität-1-Besetzungen | REQ-08 | 2 Positionen, Kandidaten {1,2,3} je Position, Prioritäten {1:1, 2:2, 3:3} | Zugewiesen sind Personen 1 und 2 | ET | `EngineTests.test_matching_prefers_more_priority_1_before_priority_2` |

### 1.2 Ergänzt für P5 (`tests/unit/test_rules.py`, `tests/unit/test_matching.py`; Methodenname `test_tc_u_<NN>_…`)

| ID | Testfall | Anf. | Eingabe | Erwartetes Ergebnis (Orakel) | Verf. |
|---|---|---|---|---|---|
| TC-U-07 | Pausengrenze genau 6 h und genau 9 h | RB-01 | Schichten 8–14 (6 h), 8–14:01, 8–17 (9 h), 8–17:01 | 0 / 30 / 30 / 45 min | GW |
| TC-U-08 | Tageshöchstarbeitszeit genau 10 h | RB-01 | Bestehend 6–12; Kandidat so, dass Summe genau 10,0 h bzw. 10,25 h | genau 10 h erlaubt, darüber Verstoß § 3 | GW |
| TC-U-09 | Ruhezeit genau 11 h und 10:59 h | RB-01 | Spät endet 22:00; Kandidat Folgetag 9:00 bzw. 8:59 | 9:00 erlaubt; 8:59 Verstoß § 5 | GW |
| TC-U-10 | Wochenhöchstarbeitszeit genau 48 h | RB-01 | Schichten mit Summe 48,0 h bzw. 48,25 h in einer KW | 48 h erlaubt; darüber Verstoß | GW |
| TC-U-11 | Wochengrenze: Schichten in verschiedenen KW | RB-01 | 45 h in KW 45, Kandidat am Montag KW 46 | erlaubt (getrennte Wochen) | ÄK |
| TC-U-12 | Leere Ausgangslage | RB-01 | keine bestehenden Schichten, Kandidat 8–14 | `is_allowed` = wahr, `violations` = leere Liste | ÄK |
| TC-U-13 | Überschneidung: echte, angrenzende, getrennte Schichten | REQ-08 | 8–14 vs. 10–16 / 14–18 / 15–20 | überschneidend / nicht / nicht | GW |
| TC-U-14 | Ostersonntag für mehrere Jahre | RB-03 | 2025, 2027, 2028 | 20.4.2025, 28.3.2027, 16.4.2028 | ÄK |
| TC-U-15 | Bewegliche Feiertage folgen Ostern | RB-03 | 2027 | Karfreitag 26.3., Ostermontag 29.3., Christi Himmelfahrt 6.5., Pfingstmontag 17.5. | ÄK |
| TC-U-16 | Zuordnung: kein Kandidat | REQ-08, REQ-09 | 1 Position, leere Kandidatenliste | Ergebnis ohne Zuordnung (Position bleibt unbesetzt) | ÄK |
| TC-U-17 | Zuordnung: mehr Positionen als Kandidaten | REQ-08, REQ-09 | 3 Positionen, 1 Kandidat | genau eine Position besetzt, Person nur einmal | GW |
| TC-U-18 | Zuordnung ist deterministisch | REQ-08 | gleiche Eingabe zweimal; Prioritäten in anderer Dict-Reihenfolge | identisches Ergebnis | ÄK |
| TC-U-19 | Zuordnung: Priorität 1 vor 3 bei Konkurrenz | REQ-08 | 1 Position, Kandidat A Prio 3, B Prio 1 | B wird zugeordnet | ET |
| TC-U-20 | Feiertagsname für Nicht-Feiertag und 1. Januar | RB-03 | 1.1.2027, 2.1.2027 | „Neujahr“ bzw. leer | ÄK |

---

## 2 Komponententests (TC-K)

### 2.1 Arbeitsablauf und Zugriffsschutz (`WorkflowTests`)

**Vorbedingung:** Demobetrieb aus `seed_demo` (Planerin Nora Krüger; Mitarbeitende u. a. Lea Meyer, Ben Fischer, Eva Koch; Planungsmonat November 2026, Frist 28.10.2026, Abgaben von Ben und Eva offen); festes Datum 20.10.2026; Passwort aller Demokonten `ShiftDemo2026!`.

| ID | Testfall | Anf. | Eingabe / Schritte | Erwartetes Ergebnis (Orakel) | Verf. | Umsetzung |
|---|---|---|---|---|---|---|
| TC-K-01 | Alle Seiten der Planung und Startseite der Mitarbeitenden erreichbar | REQ-01 | Als Planerin 8 Planungsseiten aufrufen; als Lea Startseite und „Meine Verfügbarkeiten“ | alle HTTP 200; Startseite zeigt „Hallo Lea.“ | AB | `test_planner_screens_render_and_employee_home` |
| TC-K-02 | Anmeldung erforderlich, Abmelden nur per POST | REQ-01 | Ohne Anmeldung `/`; angemeldet GET und POST auf `/abmelden/` | ohne Anmeldung 302 zur Anmeldung; GET 405; POST 302; danach wieder 302 | SI | `test_login_required_and_logout_requires_post` |
| TC-K-03 | Mitarbeitende können Planungsdaten und fremde Daten weder lesen noch schreiben | QR-03, RB-02 | Als Lea GET und POST auf 8 Planungs-URLs inkl. Bens Verfügbarkeiten | jeweils 403; eigene Seite enthält „Ben Fischer“ nicht | SI | `test_employee_cannot_read_or_write_planner_or_peer_data` |
| TC-K-04 | Planerin liest, ändert aber keine fremde Verfügbarkeit | QR-03, REQ-06 | Als Planerin Leas Verfügbarkeit öffnen und Priorität 3 senden | GET zeigt „Lea Meyer“; POST 403 | SI | `test_planner_can_read_but_cannot_edit_peer_availability` |
| TC-K-05 | CSRF-Schutz | QR-03 | POST „Abgeben“ ohne CSRF-Token | 403 | SI | `test_csrf_is_enforced` |
| TC-K-06 | Entwurf speichern, dann abgeben, andere Wochen bleiben unverändert | REQ-06, REQ-07 | Lea: Slot 1 = Prio 1 als Entwurf; dann Prio 2 abgeben | nach Entwurf: nicht abgegeben, Slot am 30.11. unverändert; nach Abgabe: abgegeben, Slot 1 = 2 | ZB | `test_draft_then_submit_preserves_other_weeks` |
| TC-K-07 | Ungültige Priorität verhindert jede Teiländerung | REQ-06 | Slot 1 = „1“, Slot 2 = „9“ | HTTP 400; alle Verfügbarkeiten unverändert | ÄK | `test_invalid_priority_has_no_partial_write` |
| TC-K-08 | Ungültiger Besetzungsmix ändert nichts | REQ-04 | Gesamt 1, davon Qualifikation 2 | Slot behält Gesamtbedarf 3 | ÄK | `test_invalid_demand_does_not_change_database` |
| TC-K-09 | Bedarf auf gleiche Wochentage des Monats kopieren | REQ-04 | Bedarf 2 setzen, Aktion „copy_month“ | alle Slots derselben Vorlage am gleichen Wochentag haben Bedarf 2 | AB | `test_copy_week_applies_matching_weekdays` |
| TC-K-10 | Fehlende Abgaben blockieren Planerzeugung ohne Bestätigung | REQ-05, REQ-08 | Planerin sendet „Erzeugen“ ohne Bestätigung | kein Plan angelegt | ZB | `test_missing_submissions_block_generation` |
| TC-K-11 | Offene Abgaben bestätigen und vor Frist erzeugen | REQ-05 AK 4, REQ-08 | Seite zeigt „2 Abgaben noch offen“; Bestätigung senden | 302; Plan existiert; Ben und Eva sind nirgends eingeteilt | ZB | `test_open_submissions_can_be_confirmed_before_deadline` |
| TC-K-12 | Bestätigung umgeht fehlenden Bedarf nicht | REQ-04, REQ-08 | Bedarf nicht gespeichert, Bestätigung senden | kein Plan angelegt | ET | `test_confirmation_never_bypasses_missing_demand` |
| TC-K-13 | Erneutes Erzeugen ohne Bestätigung lässt bestehenden Plan unverändert | REQ-08 | Plan erzeugen, Bens Abgabe zurücknehmen, erneut senden | Zuordnungen identisch | ZB | `test_generating_without_confirmation_preserves_existing_plan` |
| TC-K-14 | Vollständiger Ablauf: Plan gespeichert, deterministisch, nur lesend | REQ-08, REQ-09, REQ-10 | Alle abgegeben, zweimal erzeugen; POST auf `/plan/` | Anzahl Positionen = Summe Bedarf; mindestens eine unbesetzt; zweiter Lauf identisch; Seiten zeigen „Bearbeitbar“/„Unbesetzt“; POST ändert nichts | AB | `test_full_workflow_plan_is_persisted_deterministic_and_read_only` |
| TC-K-15 | Geänderte Eingaben markieren Plan als veraltet | REQ-08 | Plan erzeugen, danach Bedarf ändern | Planseite zeigt „Eingaben wurden geändert“; Plan bleibt erhalten | ZB | `test_changed_inputs_mark_snapshot_stale` |
| TC-K-16 | Ungültiger Monat bzw. ungültige Woche | REQ-04 | `/?month=oops`, `/bedarf/?week=oops` | 400 bzw. 200 mit Standardwoche | ÄK | `test_bad_month_and_week_are_handled` |
| TC-K-17 | Schichtvorlage mit Ende vor Beginn wird abgelehnt | REQ-03 | Vorlage 20:00–08:00 | Vorlage wird nicht gespeichert | ÄK | `test_template_duration_validation` |
| TC-K-18 | Qualifikation zuweisen und Urlaub berücksichtigen | REQ-14 | Qualifikation „Lager“ an Lea; Urlaub 2.–7.11.; Plan erzeugen | Lea hat „Lager“; keine Schicht für Lea vom 2. bis 7.11. | AB | `test_qualification_assignment_and_vacation` |

### 2.2 Abgabefrist (`DeadlineTests`)

**Vorbedingung:** wie 2.1. Datum 20.10.2026, sofern nicht anders angegeben.

| ID | Testfall | Anf. | Eingabe / Schritte | Erwartetes Ergebnis (Orakel) | Verf. | Umsetzung |
|---|---|---|---|---|---|---|
| TC-K-19 | Zeitraum mit Frist öffnen, Frist für Mitarbeitende sichtbar | REQ-05 AK 1 | Ohne Frist: Lea sieht „noch nicht geöffnet“; Planerin setzt Frist 25.10. | Frist gespeichert; Lea sieht „bis zum 25.10.2026“ | ZB | `test_ak1_open_period_with_deadline_visible_for_employees` |
| TC-K-20 | Frist nach Beginn des Zeitraums wird abgelehnt | REQ-05 AK 2 | Frist 2.11.2026 | Meldung „vor dem Beginn des Planungszeitraums“; Frist bleibt 28.10. | GW | `test_ak2_deadline_after_period_start_is_rejected` |
| TC-K-21 | Mitarbeitende dürfen keine Frist setzen | QR-03 | Lea sendet Frist | 403 | SI | `test_employee_cannot_access_period_form` |
| TC-K-22 | Eingabe nach Fristablauf gesperrt | REQ-05 AK 3, REQ-07 | Datum 29.10.; Ben gibt ab | Meldung „Eingabe ist gesperrt“; Ben bleibt „nicht abgegeben“ | GW | `test_ak3_input_locked_after_deadline` |
| TC-K-23 | Eingabe am Fristtag noch möglich | REQ-05, REQ-07 | Datum 28.10.; Ben gibt ab | Ben „abgegeben“ | GW | `test_input_allowed_on_deadline_day` |
| TC-K-24 | Nach Frist mit fehlenden Abgaben erzeugen | REQ-05 AK 3 | Datum 29.10.; Bestätigung senden | `can_generate` wahr, `ready` falsch, 2 fehlend; Plan ohne Ben und Eva | ZB | `test_ak3_generation_after_deadline_with_missing_submissions` |
| TC-K-25 | Vor Frist erzeugbar, wenn alle abgegeben | REQ-05 AK 4 (ABW-01) | alle Abgaben gesetzt | `ready` wahr, Status „offen“ | ZB | `test_ak4_generation_before_deadline_when_all_submitted` |
| TC-K-26 | Keine Eingabe vor Öffnung des Zeitraums | REQ-05, REQ-07 | Frist entfernt; Ben gibt ab | Ben bleibt „nicht abgegeben“ | ZB | `test_no_input_before_period_is_opened` |

### 2.3 Mitarbeitende anlegen (`EmployeeManagementTests`)

**Vorbedingung:** wie 2.1; Planerin angemeldet. Gültige Testdaten: Sara Neumann, sara.neumann@example.com, Minijob, 10 h/Woche, Qualifikation „Verkauf“, Startpasswort `Sicher-Start-2026`.

| ID | Testfall | Anf. | Eingabe / Schritte | Erwartetes Ergebnis (Orakel) | Verf. | Umsetzung |
|---|---|---|---|---|---|---|
| TC-K-27 | Angelegte Person erscheint in der Liste und kann sich anmelden | REQ-02 AK 1 | gültige Testdaten senden; mit neuem Konto anmelden | Meldung „Sara Neumann gespeichert“, „Minijob“; Vertragsart, Stunden, Qualifikation korrekt; Startseite „Hallo Sara.“ | AB | `test_ak1_created_employee_is_listed_and_can_log_in` |
| TC-K-28 | Fehlende Pflichtfelder werden benannt, nichts gespeichert | REQ-02 AK 2 | Vorname, Vertragsart, Passwort leer | Meldung „Bitte ausfüllen: Vorname, Vertragsart, Startpasswort.“; Anzahl Mitarbeitende unverändert | ÄK | `test_ak2_missing_required_fields_are_named_and_nothing_saved` |
| TC-K-29 | Ungültige Wochenstunden und doppelte E-Mail | REQ-02 | 60 h; E-Mail von Lea | „kleiner oder gleich 48“; „bereits vergeben“ | GW | `test_invalid_hours_and_duplicate_email_rejected` |
| TC-K-30 | Qualifikationsänderung wirkt erst im nächsten Plan | REQ-02 AK 3 | Plan erzeugen; Lea auf „Schlüsselverantwortung“ ändern | Lea hat neue Qualifikation; Rollen im bestehenden Plan unverändert; Revision erhöht; Anmeldung mit altem Passwort möglich | ZB | `test_ak3_qualification_change_applies_to_next_plan_only` |
| TC-K-31 | Verwaltung nur für Planung | QR-03 | Lea GET/POST `/mitarbeitende/` | Planerin 200; Lea 403/403 | SI | `test_employees_page_only_for_planner` |

### 2.4 Planerzeugung (`EngineTests`)

**Vorbedingung:** leere Datenbank; Monat November 2026 mit gespeichertem Bedarf; Vorlage „Früh“ 8–14 Uhr; ein Slot am 2.11. mit Bedarf 1; Qualifikationen „Verkauf“ und „Kasse“. Testpersonen werden je Testfall mit abgegebener Verfügbarkeit angelegt.

| ID | Testfall | Anf. | Eingabe / Schritte | Erwartetes Ergebnis (Orakel) | Verf. | Umsetzung |
|---|---|---|---|---|---|---|
| TC-K-32 | Priorität 1 vor 2 vor 3, Priorität 0 ausgeschlossen | REQ-08 | Personen mit Prio 0, 3, 2, 1; danach Prio 1 auf 0 setzen | zuerst Person mit Prio 1; danach Person mit Prio 2 | ET | `test_priorities_1_before_2_before_3_and_zero_excluded` |
| TC-K-33 | Fehlende Qualifikation führt zu unbesetzter Position | REQ-08, REQ-09 | Bedarf „Kasse“; nur Person mit „Verkauf“ (Prio 1); dann Person mit „Kasse“ (Prio 3) | zuerst unbesetzt; danach die qualifizierte Person trotz Prio 3 | ET | `test_qualification_and_unfilled_positions` |
| TC-K-34 | Seltene Qualifikation wird geschont | REQ-08 | Bedarf 2 (1× Verkauf, 1× Kasse); Person „beide“ und Person „nur Verkauf“ | beide Positionen besetzt; „beide“ auf Kasse | ET | `test_matching_preserves_rare_qualification` |
| TC-K-35 | Überschneidende Schicht ausgeschlossen, angrenzende erlaubt | REQ-08 | Person verfügbar für Früh 8–14, Tag 10–16, Spät 14–18 | Tag unbesetzt; Spät der Person zugeordnet | GW | `test_overlap_excluded_and_adjacent_allowed` |
| TC-K-36 | Urlaub hat Vorrang vor Verfügbarkeit | REQ-14 | Person Prio 1, Urlaub am Slot-Tag | Position unbesetzt | ET | `test_vacation_overrides_preferred_availability` |
| TC-K-37 | Keine Überschneidung im erzeugten Monat | REQ-08 | Plan erzeugen | keine Person hat zwei sich überschneidende Schichten am selben Tag | AB | `test_no_overlap_in_generated_month` |
| TC-K-38 | Laufzeit bei Referenzlast | QR-01 | 30 Personen × 3 Vorlagen × 30 Tage, Bedarf 3 je Slot | Erzeugung < 10 s; 270 Positionen | NF | `test_30_employees_3_templates_30_days_under_10_seconds` |

### 2.5 ArbZG in der Planerzeugung (`ArbZGPlanningTests`)

**Vorbedingung:** leere Datenbank; Monat November 2026; eine Person mit abgegebener Verfügbarkeit Prio 1 für alle angelegten Slots.

| ID | Testfall | Anf. | Eingabe / Schritte | Erwartetes Ergebnis (Orakel) | Verf. | Umsetzung |
|---|---|---|---|---|---|---|
| TC-K-39 | Plan hält Tageshöchstarbeitszeit ein | RB-01 | Früh 8–14 und Spät 14–20 am 2.11. | Früh zugeordnet; Spät unbesetzt | GW | `test_plan_respects_daily_maximum` |
| TC-K-40 | Plan hält Ruhezeit ein | RB-01 | Spät 14–22 am 2.11.; Früh 6–12 am 3.11. | Spät zugeordnet; Früh unbesetzt | GW | `test_plan_respects_rest_period` |
| TC-K-41 | Verstoßprüfung für die manuelle Korrektur | RB-01, REQ-11 | Plan wie TC-K-39; Prüfung für Früh und Spät | Früh: keine Meldung; Spät: genau eine Meldung „Mehr als 10 Stunden“ | GW | `test_assignment_violations_for_manual_correction` |

### 2.6 Feiertage und Öffnungstage (`HolidayCalendarTests`, `OpeningDayTests`)

**Vorbedingung:** wie 2.1; Planerin angemeldet. Standard: Mo–Sa geöffnet, Sonntag geschlossen.

| ID | Testfall | Anf. | Eingabe / Schritte | Erwartetes Ergebnis (Orakel) | Verf. | Umsetzung |
|---|---|---|---|---|---|---|
| TC-K-42 | Feiertage markiert und beim Kopieren übersprungen | RB-03 | Bedarf Dezember KW 52 aufrufen; Woche 14.–19.12. mit Bedarf 2 auf den Monat kopieren | „1. Weihnachtstag“ angezeigt; 21.12. Bedarf 2; 25. und 26.12. Bedarf 0 | ÄK | `HolidayCalendarTests.test_holidays_marked_and_skipped_when_copying_week` |
| TC-K-43 | Sonntag standardmäßig geschlossen | REQ-22 | Bedarf KW 45 aufrufen | „Mo, Di, Mi, Do, Fr, Sa geöffnet“; kein Sonntag „So 08“ | ÄK | `OpeningDayTests.test_sunday_closed_by_default` |
| TC-K-44 | Einzelnen Sonntag öffnen: erscheint in Bedarf, Verfügbarkeit und Plan | REQ-22 | Sonntag 8.11. öffnen; Bedarf 1; Lea gibt Prio 1 ab; Plan erzeugen | Revision erhöht; „So 08“ bei Bedarf und Lea; Plan enthält 8.11.; genau ein Sonntag im Monat | AB | `…test_ak_open_single_sunday_shows_slots_in_demand_availability_plan` |
| TC-K-45 | Geschlossener Wochentag und einzelner Tag werden nicht geplant | REQ-22 | Samstag schließen, 2.11. schließen; Plan erzeugen | 7.11. und 2.11. nicht im Plan; 3.11. im Plan | ÄK | `…test_closed_weekday_and_single_day_are_not_planned` |
| TC-K-46 | Ungültige Öffnungseingaben und Zugriffsschutz | REQ-22, QR-03 | keine Wochentage; Tag im Dezember; Lea sendet Formular | „Mindestens ein Wochentag“; „im gewählten Planungsmonat“; Lea 403 | ÄK | `…test_invalid_opening_input` |

### 2.7 Manuelle Korrektur und automatisches Auffüllen (`ManualCorrectionTests`)

**Vorbedingung:** Planer-Konto (Gruppe „Planung“); Anna und Ben; Plan November 2026 mit Slot 2.11. Früh 8–14, Bedarf 2 (1× Kasse); Position 1 = Anna (Kasse), Position 2 = unbesetzt. Planer angemeldet. Jede Änderung erfolgt zweistufig: Vorschau, dann Bestätigung mit signiertem Token.

| ID | Testfall | Anf. | Eingabe / Schritte | Erwartetes Ergebnis (Orakel) | Verf. | Umsetzung |
|---|---|---|---|---|---|---|
| TC-K-47 | Ersetzen warnt und speichert erst nach Bestätigung | REQ-11 | Vorschau: Ben statt Anna; dann bestätigen | Warnungen „Keine abgegebene Verfügbarkeit“ und „erforderliche Qualifikation“; vor Bestätigung Anna; danach Ben, Priorität leer | ZB | `test_replace_warns_and_only_saves_after_confirmation` |
| TC-K-48 | Position leeren und neu besetzen | REQ-11 | Vorschau ohne Person, bestätigen; dann Ben, bestätigen | erst unbesetzt mit leerem Namen; dann Ben | ZB | `test_remove_and_reassign_open_position` |
| TC-K-49 | Doppelbesetzung in derselben Schicht blockiert | REQ-11 | Anna auf Position 2 | Meldung „Überschneidung“; keine Bestätigung angeboten; Position 2 bleibt leer | ET | `test_same_shift_duplicate_is_blocked` |
| TC-K-50 | ArbZG-Verstoß blockiert | REQ-11, RB-01 | Anna zusätzlich Spät 14–20 am selben Tag | Meldung „Mehr als 10 Stunden“; keine Bestätigung angeboten | GW | `test_working_hours_violation_is_blocked` |
| TC-K-51 | Tausch erfolgt atomar | REQ-11 | Anna (2.11.) mit Ben (3.11. Spät) tauschen | Vorschau „Tausch mit“; danach Positionen und Namen vertauscht | ZB | `test_swap_works_atomically_and_keeps_snapshot_correct` |
| TC-K-52 | Veraltete Vorschau wird abgelehnt | REQ-11 | Vorschau erstellen, Monat zwischendurch ändern, bestätigen | „Vorschau veraltet“; Anna bleibt | ZB | `test_stale_preview_is_rejected` |
| TC-K-53 | Korrektur nur für Planung; fremder Monat abgelehnt | QR-03, REQ-11 | Anna ruft Korrektur auf; Planer mit falschem Monat | 403/403; 404 | SI | `test_correction_is_planner_only_and_foreign_position_is_rejected` |
| TC-K-54 | Ungültige Bestätigung speichert nicht | REQ-11 | Token „invalid“ | Meldung „ungültig“; Anna bleibt | ÄK | `test_invalid_confirmation_does_not_save` |
| TC-K-55 | Weiche Hinweise (Prio 3, Urlaub) bestätigbar | REQ-11 (E-01) | Ben qualifiziert, Prio 3, Urlaub am Tag | Hinweise „Priorität 3“, „Urlaub ist eingetragen“; nach Bestätigung Ben mit Prio 3 | ET | `test_priority_and_vacation_warnings_can_be_confirmed` |
| TC-K-56 | Tausch mit Ruhezeitkonflikt wird abgelehnt | REQ-11, RB-01 | Ben Spät 14–22; Anna hat am 3.11. Früh; Tausch | Meldung „§ 5“; keine Bestätigung; beide Positionen unverändert | GW | `test_swap_rejects_conflict_without_changing_either_position` |
| TC-K-57 | Auffüllen besetzt nur offene Positionen | REQ-09, REQ-11 | Ben Prio 2 abgegeben; „automatisch füllen“ | „1 Position automatisch besetzt“; Position 1 unverändert; Position 2 = Ben, Prio 2 | ZB | `test_autofill_keeps_existing_assignments_and_fills_open_position` |
| TC-K-58 | Auffüllen nur mit abgegebener Verfügbarkeit und passender Qualifikation | REQ-09 | Ben nicht abgegeben; dann abgegeben, ohne „Kasse“ | erst beide Positionen leer; danach Kasse-Position leer, Position 2 = Ben | ET | `test_autofill_requires_submitted_availability_and_qualification` |
| TC-K-59 | Auffüllen berücksichtigt andere Schichten | REQ-09, REQ-08 | Ben bereits 12–18 am selben Tag | Position 2 bleibt leer | ET | `test_autofill_respects_other_shifts_even_when_later_in_plan` |
| TC-K-60 | Auffüllen nutzt neue Abgaben bei veraltetem Plan | REQ-09 | Monatsrevision erhöht, Ben neu abgegeben | Position 2 = Ben; Planrevision bleibt ungleich Monatsrevision | ZB | `test_autofill_uses_new_submissions_on_outdated_plan` |
| TC-K-61 | Auffüllen nur für Planung | QR-03 | Ben sendet Auffüllen | 403 | SI | `test_autofill_is_restricted_to_planner` |
| TC-K-62 | Auffüllen erklärt, wenn niemand passt | REQ-09 | keine geeignete Person | „Keine weitere passende Person gefunden“, Hinweis „Abgaben prüfen“ | ÄK | `test_autofill_explains_when_no_person_is_eligible` |

### 2.8 Veröffentlichung (`PublicationTests`)

**Vorbedingung:** Planer-Konto; Anna und Ben; Plan November 2026, Slot 2.11. Früh 8–14 mit Anna und Ben besetzt; Datum 20.10.2026. Planer angemeldet.

| ID | Testfall | Anf. | Eingabe / Schritte | Erwartetes Ergebnis (Orakel) | Verf. | Umsetzung |
|---|---|---|---|---|---|---|
| TC-K-63 | Unveröffentlichter Plan bleibt verborgen; Vorschau veröffentlicht nicht | REQ-15, RB-02 | Vorschau öffnen; Anna ruft ihren Plan auf | keine Veröffentlichung; Anna sieht „noch kein Plan veröffentlicht“, nicht „Ben“ | ZB | `test_unpublished_plan_is_never_exposed_and_preview_does_not_publish` |
| TC-K-64 | Standardansicht zeigt nur eigene Schichten | REQ-15, RB-02 | veröffentlichen; Anna ruft Plan mit fremdem Parameter `employee=Ben` auf | „Meine Schichten“; nur Annas Zeilen; weder „Ben“ noch „Priorität“; Startseite „Dein Schichtplan ist veröffentlicht“ | SI | `test_default_view_only_shows_own_snapshot_and_ignores_foreign_employee_parameter` |
| TC-K-65 | Teamansicht sofort wirksam, ohne Entwurf zu verändern | REQ-15 | Sichtbarkeit „team“, dann „own“ | Revision bleibt 0; Anna sieht „Ben“, danach nicht mehr | ZB | `test_team_setting_applies_immediately_without_invalidating_draft` |
| TC-K-66 | Mitarbeitende können nicht veröffentlichen, Sichtbarkeit ändern oder Entwurf lesen | QR-03 | Anna: GET/POST Veröffentlichung, POST Sichtbarkeit, GET `/plan/`, POST eigener Plan; abgemeldet aufrufen | 403, 403, 403, 403; 405; abgemeldet 302 | SI | `test_employee_cannot_publish_or_change_visibility_or_read_draft` |
| TC-K-67 | Veröffentlichung erfordert CSRF-Token | QR-03 | POST ohne Token | 403 | SI | `test_publication_requires_csrf` |
| TC-K-68 | Unbesetzte Positionen erfordern Bestätigung | REQ-15, REQ-09 | Position 1 leeren; ohne/mit Bestätigung veröffentlichen | ohne: 200, nichts veröffentlicht; mit: 302; Anna „keine zugewiesenen Schichten“; in Teamansicht „Unbesetzt“ | ET | `test_missing_positions_need_acknowledgement_and_own_empty_state` |
| TC-K-69 | Veraltete Eingaben erfordern Bestätigung | REQ-15 | Monatsrevision 1; ohne/mit Bestätigung | Hinweis „bisherigen Planstand“; ohne: nichts veröffentlicht; mit: veröffentlicht, keine offenen Änderungen | ZB | `test_stale_inputs_warn_and_require_confirmation` |
| TC-K-70 | Vollständiger Plan ohne Zusatzbestätigung veröffentlichbar | REQ-15 | veröffentlichen ohne Bestätigung | 302; veröffentlicht von Planer; 2 Positionen | ÄK | `test_complete_plan_can_be_published_without_warning_acknowledgement` |
| TC-K-71 | Zwischenzeitliche Änderung oder manipulierter Token abgelehnt | REQ-15 | Vorschau, dann Position ändern, senden; Token „invalid“ | „Bitte erneut prüfen“; jeweils nichts veröffentlicht | SI | `test_concurrent_change_or_tampered_confirmation_is_rejected` |
| TC-K-72 | Token gilt nicht für anderen Monat | REQ-15 | Token November an Dezember senden | nichts veröffentlicht | SI | `test_confirmation_cannot_publish_a_different_month` |
| TC-K-73 | Ohne Plan keine Veröffentlichungsaktion | REQ-15 | Dezember aufrufen | „Bitte zuerst einen Schichtplan erzeugen“; kein Bestätigungsfeld | ÄK | `test_missing_plan_has_no_publish_action` |
| TC-K-74 | Korrektur und Auffüllen ändern veröffentlichten Stand nicht | REQ-15, REQ-11 | veröffentlichen; Position 1 leeren; auffüllen | veröffentlichte Zuordnungen unverändert; Auffüllen meldet (1, 0) | ZB | `test_corrections_and_autofill_do_not_change_published_snapshot` |
| TC-K-75 | Neuerzeugung bleibt unveröffentlicht bis zur erneuten Veröffentlichung | REQ-15 | veröffentlichen; alle Prio 0; neu erzeugen; erneut veröffentlichen | vorher 2 besetzt, Hinweis „Unveröffentlichte Änderungen“; danach gleiche Veröffentlichung mit 2 unbesetzten | ZB | `test_regeneration_keeps_publication_until_republished` |
| TC-K-76 | Fehler beim Veröffentlichen rollt vollständig zurück | REQ-15 | Speichern der neuen Zeilen schlägt fehl (simuliert) | Ausnahme; bisherige Veröffentlichung unverändert | ZB | `test_failure_rolls_back_previous_publication` |
| TC-K-77 | Teamplan nach Schicht und Tag gruppiert | REQ-15 | Teamansicht, Anna ruft Plan auf | Woche ab 2.11.; 1 Zeile, 7 Tage; Montag Anna (eigene) vor Ben | AB | `test_timetable_groups_team_positions_by_shift_and_day` |
| TC-K-78 | Wochenfilter und ungültige Woche | REQ-15 | Woche 9.11.; Woche „invalid“ | 9.11. leer mit Hinweis, vorherige 2.11., nächste 16.11.; „invalid“ fällt auf 2.11. zurück | GW | `test_timetable_filters_weeks_and_handles_invalid_selection` |
| TC-K-79 | Ansicht nutzt Veröffentlichung, Jahreswechsel korrekt | REQ-15 | Entwurf nach Veröffentlichung ändern; Woche 28.12.2026 im Januar 2027 | Entwurfsänderung nicht sichtbar; KW 53; nächste Woche 4.1.2027; Tage außerhalb des Monats markiert | GW | `test_timetable_uses_publication_and_handles_year_boundary` |


### 2.9 Vorbereitung der Tests mit Nutzenden (`UserTestSetupTests`, PR #45)

**Vorbedingung:** Demobetrieb aus `seed_demo`, danach `prepare_usertests`; Datum 20.11.2026, Debug-Modus.

| ID | Testfall | Anf. | Eingabe / Schritte | Erwartetes Ergebnis (Orakel) | Verf. | Umsetzung |
|---|---|---|---|---|---|---|
| TC-K-80 | November veröffentlicht, Testmonate offen und ohne Bedarf | Testplan TC-M | Kommando ausführen | Novemberplan veröffentlicht; Dezember Frist 30.11., Januar Frist 15.12.; alle Slots Bedarf 0; Mia bzw. Tom nicht abgegeben; je 11 Abgaben | AB | `test_november_published_and_test_months_open_without_demand` |
| TC-K-81 | Erneuter Lauf verändert laufende Tests nicht | Testplan TC-M | Dezember-Bedarf auf 2 setzen, Kommando erneut | Bedarf bleibt 2 | ZB | `test_rerun_does_not_change_running_tests` |
| TC-K-82 | Lückenschicht bleibt unbesetzt | REQ-09 | Bedarf 1 je Slot, Plan erzeugen | Spätschicht 18.12. ohne Person | ÄK | `test_gap_shift_stays_unfilled` |
| TC-K-83 | Bereits angelegter, unbenutzter Dezember wird geöffnet | Testplan TC-M | Dezember leer neu anlegen, Kommando | Frist 30.11.; 11 Abgaben | ZB | `test_existing_untouched_december_is_opened` |
| TC-K-84 | Bestehende Eingaben werden nie überschrieben oder neu geöffnet | Testplan TC-M | Dezember ohne Frist mit Verfügbarkeiten, Kommando | Frist bleibt leer; Verfügbarkeiten unverändert | ZB | `test_existing_input_is_never_overwritten_or_reopened` |
| TC-K-85 | Vorhandener Novemberentwurf wird ohne Neuerzeugung veröffentlicht | REQ-15 | Veröffentlichung löschen, Entwurf ändern, Kommando | veröffentlichte Positionen = geänderter Entwurf; Abgaben unverändert | ZB | `test_existing_november_draft_is_published_without_regeneration` |
| TC-K-86 | Kommando außerhalb des Demo-Modus gesperrt | RB-02 | Debug und Demo aus | `CommandError` | SI | `test_preparation_is_blocked_outside_demo_mode` |

### 2.10 Betriebstrennung (`CompanyIsolationTests`, `CompanyMigrationTests`, PR #46)

**Vorbedingung:** `seed_demo` mit Demobetrieb „Nordlicht“ und drei leeren Testunternehmen; angemeldet als `planer1@example.com` (Testunternehmen 1); ein Plan mit Position von Lea Meyer im Betrieb Nordlicht.

| ID | Testfall | Anf. | Eingabe / Schritte | Erwartetes Ergebnis (Orakel) | Verf. | Umsetzung |
|---|---|---|---|---|---|---|
| TC-K-87 | Drei leere Testunternehmen; erneutes Seeding erhält Daten | REQ-02 (ABW-03) | `seed_test_companies` nach Passwortänderung erneut | 4 Betriebe, 12 Personen in Nordlicht, 16 Konten; geändertes Passwort und Plan unverändert; neue Betriebe ohne Stammdaten | ÄK | `test_three_companies_are_empty_and_seed_preserves_existing_data` |
| TC-K-88 | Alle Seiten zeigen nur den eigenen Betrieb | QR-03 AK 2 | 8 Planungsseiten aufrufen | „Testunternehmen 1“ sichtbar, weder „Lea Meyer“ noch „Filiale Flensburg“; Erzeugen ohne Personen nicht möglich | SI | `test_views_only_show_own_company` |
| TC-K-89 | Fremde Objekt-IDs per GET und POST abgelehnt | QR-03 AK 2 | Vorlage, Qualifikation, Person, Verfügbarkeit, Planposition des anderen Betriebs | jeweils HTTP 404 | SI | `test_foreign_ids_are_rejected_for_get_and_post` |
| TC-K-90 | Fremde Person/Qualifikation in Formularen abgelehnt | QR-03 AK 2 | Urlaub für Lea; neue Person mit fremder Qualifikation | Formular mit Fehler (200); nichts gespeichert | SI | `test_foreign_vacation_and_qualification_cannot_be_submitted` |
| TC-K-91 | Gleiche Namen zwischen Betrieben erlaubt, im Betrieb eindeutig | REQ-03, REQ-02 | Vorlage/Qualifikation mit Namen aus Nordlicht zweimal anlegen | erstes Mal 302, zweites Mal 200; je 1 Eintrag; Nordlicht unverändert | GW | `test_same_names_are_allowed_between_companies_and_rejected_inside_one` |
| TC-K-92 | Neue Person gehört zum Betrieb der Planung | REQ-02 | Person anlegen und mit ihr anmelden | Betrieb = Testunternehmen 1; Verwaltung und fremde Verfügbarkeit 403 | SI | `test_new_employee_can_login_only_in_own_company` |
| TC-K-93 | Plansicht je Betrieb | REQ-15 | Sichtbarkeit „team“ setzen | gilt nur für Testunternehmen 1 | ÄK | `test_visibility_is_per_company` |
| TC-K-94 | Konto ohne Betrieb hat keinen Zugriff | QR-03 | Konto in Gruppe „Planung“ ohne Zuordnung | GET und POST 403 | SI | `test_account_without_company_is_denied_even_with_planner_group` |
| TC-K-95 | Korrektur mit Person eines anderen Betriebs abgelehnt | REQ-11, QR-03 | `correct_plan` mit fremder Person | `ValueError` | SI | `test_cross_company_assignment_is_rejected_in_service` |
| TC-K-96 | Fremde Veröffentlichung unsichtbar | QR-03 AK 2, REQ-15 | Nordlicht veröffentlicht; Person aus Testunternehmen 1 ruft eigenen Plan auf | „noch kein Plan veröffentlicht“, kein „Lea Meyer“ | SI | `test_employee_cannot_see_another_company_publication` |
| TC-K-97 | Planerzeugung berücksichtigt keine fremden Personen | REQ-08 | leerer Betrieb mit Slot und Bedarf | nicht erzeugbar; `ValueError` | ET | `test_empty_company_does_not_consider_foreign_employees_for_generation` |
| TC-K-98 | Vorbereitung ändert nur Nordlicht | Testplan TC-M | `prepare_usertests` | andere Betriebe unverändert und leer; Dezember Nordlicht Frist 30.11. | SI | `test_preparation_only_changes_nordlicht_and_preserves_empty_companies` |
| TC-K-99 | Vorbereitung schließt fremde Personen aus | Testplan TC-M | Person in Testunternehmen 1, dann `prepare_usertests` | 11 Abgaben in Nordlicht; keine Abgabe für fremde Person | SI | `test_preparation_excludes_foreign_employees` |
| TC-K-100 | Migration erhält bestehende Daten | REQ-02 (ABW-03) | Daten im Schema vor `0007`, dann Migration | Monat und Konto Nordlicht zugeordnet; Plan-Revision, Veröffentlichung und Snapshot-Namen unverändert; Teamansicht erhalten | ZB | `CompanyMigrationTests.test_existing_users_assignments_and_publications_are_preserved` |

### 2.11 Vorlauf vor Veröffentlichung und Fehlerpfade (`PublicationLeadTimeTests`, `ErrorPathTests`, PR #66)

**Vorbedingung:** für TC-K-101 bis -103 wie 2.8 (Plan November 2026), Datum je Test gesetzt; für TC-K-104 bis -113 Demobetrieb aus `seed_demo`, Datum 20.10.2026, Planerin angemeldet.

| ID | Testfall | Anf. | Eingabe / Schritte | Erwartetes Ergebnis (Orakel) | Verf. | Umsetzung |
|---|---|---|---|---|---|---|
| TC-K-101 | Genau 14 Tage Vorlauf: kein Hinweis | REQ-15 AK 1 (DEF-02) | Datum 18.10.2026, Veröffentlichungsseite | `lead_days` = 14; kein Hinweis | GW | `PublicationLeadTimeTests.test_exactly_14_days_before_start_shows_no_hint` |
| TC-K-102 | 13 Tage Vorlauf: Hinweis, Veröffentlichen möglich | REQ-15 AK 1 (DEF-02) | Datum 19.10.2026; veröffentlichen ohne Bestätigung | „nur 13 Tage und damit weniger als 14 Tage vor Beginn“; keine Bestätigungspflicht; Veröffentlichung gespeichert | GW | `…test_13_days_before_start_shows_hint_and_publishing_stays_possible` |
| TC-K-103 | 1 Tag bzw. nach Beginn: passende Formulierung | REQ-15 AK 1 (DEF-02) | Datum 31.10. bzw. 03.11.2026 | „nur 1 Tag und damit“ bzw. „erst nach Beginn des Planungsmonats“ | GW | `…test_one_day_and_after_start_use_matching_wording` |
| TC-K-104 | Zeitraum: GET leitet um, ungültige Frist abgelehnt | REQ-05 | GET `/zeitraum/`; POST Frist „kein-datum“ | 302; Meldung „gültiges Datum“; Frist bleibt 28.10. | ÄK | `ErrorPathTests.test_period_get_redirects_and_invalid_deadline_is_rejected` |
| TC-K-105 | Bedarf: Text und Werte außerhalb 0–30 abgelehnt | REQ-04 | Gesamtzahl „drei“, „31“, „-1“ | Meldung „ganze Zahlen“; Gesamtzahl bleibt 3 | GW | `…test_demand_rejects_text_and_out_of_range_values` |
| TC-K-106 | Öffnungstage: GET leitet zur Bedarfsseite | REQ-22 | GET `/oeffnungstage/` | 302 auf `/bedarf/` | ÄK | `…test_opening_get_redirects_to_demand` |
| TC-K-107 | Ungültige Plansicht abgelehnt | REQ-15 | Sichtbarkeit „alle“ | Meldung „gültige Plansicht“ | ÄK | `…test_invalid_visibility_is_rejected` |
| TC-K-108 | Urlaub mit Ende vor Beginn abgelehnt | REQ-14 | Lea, 10.11. bis 09.11. | Formularfehler; kein Urlaub gespeichert | GW | `…test_vacation_end_before_start_is_rejected` |
| TC-K-109 | Korrektur mit Person und Tausch zugleich abgelehnt | REQ-11 | Position mit `employee` und `swap` senden | Meldung „Person auswählen oder zwei Positionen tauschen“; keine Bestätigung | ET | `…test_correction_with_person_and_swap_at_once_is_rejected` |
| TC-K-110 | Auffüllen ohne offene Positionen | REQ-09 | Plan ohne Lücken, „automatisch füllen“ | Meldung „Alle Positionen sind bereits besetzt.“ | ÄK | `…test_autofill_reports_when_everything_is_filled` |
| TC-K-111 | Öffnungstage: kein Wochentag bzw. Tag außerhalb des Monats | REQ-22 | `set_opening` mit [] bzw. 06.12.2026 | `ValueError` „Mindestens ein Wochentag“ bzw. „im gewählten Planungsmonat“ | ÄK | `…test_set_opening_requires_weekday_and_day_in_month` |
| TC-K-112 | Mitarbeitende: fremder Betrieb in `save_employee` | REQ-02, QR-03 | fremdes Unternehmen bzw. fremde Qualifikation | `ValueError` „Person/Qualifikation gehört zu einem anderen …“ | SI | `…test_save_employee_rejects_foreign_company_data` |
| TC-K-113 | Besetzungsmix über Gesamtzahl bei Erzeugung | REQ-04, REQ-08 | Slot Gesamtzahl 1, Mindestzahl 2 | `ValueError` „Besetzungsmix übersteigt“ | GW | `…test_generation_rejects_mix_above_total` |

---

## 3 Automatisierte Akzeptanztests (TC-A, `tests/acceptance/test_akzeptanz.py`)

**Vorbedingung:** Demobetrieb aus `seed_demo` (wie 2.1); festes Datum 20.10.2026 (Eingabephase) bzw. 29.10.2026 (nach der Frist) je Testklasse. Jeder Test bildet genau ein Akzeptanzkriterium aus dem Anforderungsdokument (Stand P4, 09.11.2026) ab; Gegeben/Wenn/Dann steht im Docstring, der Name lautet `test_tc_a_<REQ>_<AK>_…`. Die Tests bedienen das System über HTTP wie Nutzende; Datenbankzugriffe dienen nur dem Herstellen des Ausgangszustands und dem Prüfen. Das Orakel ist jeweils der „Dann“-Teil des Akzeptanzkriteriums.

Abgedeckt sind alle 37 Akzeptanzkriterien der umgesetzten Anforderungen REQ-01 bis REQ-11, REQ-14, REQ-15 und REQ-22 sowie die automatisiert prüfbaren Kriterien QR-01 AK 1, QR-03 AK 1 und 3 und QR-04 AK 1 und 2. Nicht automatisiert sind QR-02 (Oberflächentests TC-UI), QR-05/QR-06 (Tests mit Nutzenden TC-M) und QR-07 (durch die CI-Pipeline selbst nachgewiesen). QR-03 AK 2 (keine Daten fremder Betriebe) ist seit PR #46 auf Komponentenebene geprüft (TC-K-87 bis TC-K-100).

| ID | Kriterium | Gegeben | Wenn | Dann (Orakel) | Umsetzung |
|---|---|---|---|---|---|
| TC-A-01-1 | REQ-01 AK 1 | ein Mitarbeitender | er sich korrekt anmeldet | sieht er nur die Eingabe seiner eigenen Verfügbarkeiten (keine Planungsfunktionen) | `Req01LoginTests.test_tc_a_01_1_employee_sees_only_own_availability_input` |
| TC-A-01-2 | REQ-01 AK 2 | ein Chef | er sich anmeldet | sieht er Mitarbeiterverwaltung, Bedarf und Plan | `Req01LoginTests.test_tc_a_01_2_planner_sees_staff_demand_and_plan` |
| TC-A-01-3 | REQ-01 AK 3 | ein falsches Passwort | die Anmeldung erfolgt | wird der Zugriff verweigert, ohne zu verraten, ob E-Mail oder Passwort falsch war | `Req01LoginTests.test_tc_a_01_3_failed_login_does_not_reveal_which_field_was_wrong` |
| TC-A-02-1 | REQ-02 AK 1 | ein angemeldeter Chef | er einen Mitarbeitenden mit allen Pflichtfeldern speichert | erscheint dieser in der Liste und kann sich anmelden | `Req02EmployeeTests.test_tc_a_02_1_saved_employee_is_listed_and_can_log_in` |
| TC-A-02-2 | REQ-02 AK 2 | fehlende Pflichtfelder | der Chef speichert | wird nicht gespeichert und das fehlende Feld benannt | `Req02EmployeeTests.test_tc_a_02_2_missing_required_field_is_named_and_nothing_saved` |
| TC-A-02-3 | REQ-02 AK 3 | ein bestehender Mitarbeitender | der Chef eine Qualifikation ändert | gilt sie ab dem nächsten erzeugten Plan; bestehende Pläne bleiben | `Req02EmployeeTests.test_tc_a_02_3_qualification_change_applies_from_next_plan` |
| TC-A-03-1 | REQ-03 AK 1 | Name, Start und Ende am selben Tag | der Chef speichert | ist die Vorlage bei der Bedarfseingabe auswählbar | `Req03TemplateTests.test_tc_a_03_1_saved_template_is_selectable_for_demand` |
| TC-A-03-2 | REQ-03 AK 2 | ein Ende vor dem Start | der Chef speichert | erscheint eine Fehlermeldung | `Req03TemplateTests.test_tc_a_03_2_end_before_start_shows_error` |
| TC-A-03-3 | REQ-03 AK 3 | eine geänderte Vorlage | sie gespeichert wird | wirkt sie nur auf künftige Pläne | `Req03TemplateTests.test_tc_a_03_3_changed_template_affects_only_future_plans` |
| TC-A-04-1 | REQ-04 AK 1 | ein offener Zeitraum | der Chef für „Früh, Montag“ 3 Personen, davon 1 Schlüsselträger, speichert | ist der Bedarf gespeichert und wird bei der Planung berücksichtigt | `Req04DemandTests.test_tc_a_04_1_demand_with_key_holder_is_saved_and_used` |
| TC-A-04-2 | REQ-04 AK 2 | der Bedarf 0 | er gespeichert wird | wird für diese Schicht niemand eingeplant | `Req04DemandTests.test_tc_a_04_2_zero_demand_means_nobody_is_planned` |
| TC-A-04-3 | REQ-04 AK 3 | eine Mindestzahl an Qualifikationen über der Gesamtzahl | der Chef speichert | erscheint eine Fehlermeldung | `Req04DemandTests.test_tc_a_04_3_qualification_minimum_above_total_shows_error` |
| TC-A-05-1 | REQ-05 AK 1 | kein offener Zeitraum | der Chef Monat und Frist speichert | ist der Zeitraum „offen“ und für Mitarbeitende sichtbar | `Req05PeriodTests.test_tc_a_05_1_open_period_is_visible_for_employees` |
| TC-A-05-2 | REQ-05 AK 2 | eine Frist nach dem Beginn des Zeitraums | der Chef speichert | erscheint eine Fehlermeldung | `Req05PeriodTests.test_tc_a_05_2_deadline_after_period_start_shows_error` |
| TC-A-05-3 | REQ-05 AK 3 | die Frist ist abgelaufen | ein Mitarbeitender eintragen will | ist die Eingabe gesperrt, und der Chef kann den Plan erzeugen | `Req05PeriodTests.test_tc_a_05_3_after_deadline_input_locked_and_plan_can_be_generated` |
| TC-A-05-4 | REQ-05 AK 4 | alle aktiven Mitarbeitenden haben vor Ablauf der Frist abgegeben | der Chef den Plan erzeugen will | ist die Erzeugung möglich | `Req05PeriodTests.test_tc_a_05_4_generation_before_deadline_when_all_submitted` |
| TC-A-06-1 | REQ-06 AK 1 | ein offener Zeitraum | ich einen Slot mit Priorität 2 speichere | erscheint er in meiner Übersicht und ist für den Chef sichtbar, für andere Mitarbeitende nicht | `Req06AvailabilityTests.test_tc_a_06_1_priority_visible_for_planner_not_for_colleagues` |
| TC-A-06-2 | REQ-06 AK 2 | ein Slot ohne Priorität | ich speichere | wird das abgelehnt | `Req06AvailabilityTests.test_tc_a_06_2_slot_without_priority_is_rejected` |
| TC-A-06-3 | REQ-06 AK 3 | ein Slot ohne Eintrag | der Plan erzeugt wird | gelte ich dafür als nicht verfügbar | `Req06AvailabilityTests.test_tc_a_06_3_slot_without_entry_means_not_available` |
| TC-A-07-1 | REQ-07 AK 1 | ein offener Zeitraum vor der Frist | ich einen Slot ändere oder lösche (Priorität 0 = nicht verfügbar) | gilt die Änderung für die Planung | `Req07ChangeAvailabilityTests.test_tc_a_07_1_change_and_delete_before_deadline_apply_to_planning` |
| TC-A-07-2 | REQ-07 AK 2 | die Frist ist abgelaufen | ich ändern will | ist das nicht mehr möglich | `Req07ChangeAvailabilityTests.test_tc_a_07_2_no_change_after_deadline` |
| TC-A-07-3 | REQ-07 AK 3 | ich öffne die Übersicht | – | sehe ich nur meine eigenen Slots | `Req07ChangeAvailabilityTests.test_tc_a_07_3_overview_shows_only_own_slots` |
| TC-A-08-1 | REQ-08 AK 1 | ein geschlossener Zeitraum mit Bedarf und Verfügbarkeiten | ich den Plan erzeuge | wird jeder Slot nur mit verfügbaren Personen mit der geforderten Qualifikation besetzt | `Req08GenerationTests.test_tc_a_08_1_only_available_and_qualified_people_are_planned` |
| TC-A-08-2 | REQ-08 AK 2 | mehr verfügbare Personen als Bedarf | der Plan erzeugt wird | haben Personen mit Priorität 1 Vorrang vor 2 und 3 | `Req08GenerationTests.test_tc_a_08_2_priority_1_before_2_and_3` |
| TC-A-08-3 | REQ-08 AK 3 | ein Mitarbeitender | der Plan erzeugt wird | ist er nie in zwei sich überschneidenden Schichten am selben Tag eingeplant | `Req08GenerationTests.test_tc_a_08_3_nobody_in_two_overlapping_shifts` |
| TC-A-08-4 | REQ-08 AK 4 | identische Eingaben | der Plan zweimal erzeugt wird | sind beide Pläne gleich (deterministisch) | `Req08GenerationTests.test_tc_a_08_4_identical_inputs_give_identical_plans` |
| TC-A-09-1 | REQ-09 AK 1 | ein Slot ohne ausreichend qualifizierte verfügbare Personen | der Plan erzeugt wird | erscheint er mit der Zahl fehlender Personen und der fehlenden Qualifikation als „unbesetzt“ (Demo: Fr 06 | `Req09UnfilledTests.test_tc_a_09_1_unfilled_slot_shows_missing_count_and_qualification` |
| TC-A-09-2 | REQ-09 AK 2 | mindestens ein unbesetzter Slot | der Plan erzeugt wird | wird der Plan trotzdem erzeugt und die Gesamtzahl unbesetzter Slots angezeigt | `Req09UnfilledTests.test_tc_a_09_2_plan_is_created_and_total_unfilled_is_shown` |
| TC-A-10-1 | REQ-10 AK 1 | ein erzeugter Plan | der Chef ihn öffnet | sieht er die Schichten je Tag und Woche mit den zugewiesenen Personen | `Req10PlanViewTests.test_tc_a_10_1_planner_sees_shifts_per_day_and_week_with_names` |
| TC-A-10-2 | REQ-10 AK 2 | ein unbesetzter Slot | der Plan angezeigt wird | ist er farblich hervorgehoben (CSS-Klasse ``has-missing``) | `Req10PlanViewTests.test_tc_a_10_2_unfilled_slot_is_highlighted` |
| TC-A-10-3 | REQ-10 AK 3 (Teil Zugriff) | – | – | Mitarbeitende haben keinen Zugriff auf den Planentwurf | `Req10PlanViewTests.test_tc_a_10_3_employees_have_no_access_to_draft_plan` |
| TC-A-11-1 | REQ-11 AK 1 | ein erzeugter Plan | ich eine Person einer Schicht ändere und speichere | erscheint die Änderung im Plan, und „unbesetzt“ wird aktualisiert | `Req11CorrectionTests.test_tc_a_11_1_change_is_shown_and_unfilled_marking_updated` |
| TC-A-11-2 | REQ-11 AK 2 | eine Änderung, die gegen RB-01 verstößt (mehr als 10 Stunden am Tag) | der Chef speichert | wird nicht gespeichert und der Paragraf genannt | `Req11CorrectionTests.test_tc_a_11_2_rb01_violation_is_not_saved_and_paragraph_named` |
| TC-A-11-3 | REQ-11 AK 3 | eine zulässige Änderung, bei der die Person nur Priorität 3 angegeben hat | der Chef speichert | wird gespeichert und ein Hinweis angezeigt | `Req11CorrectionTests.test_tc_a_11_3_allowed_change_with_low_priority_is_saved_with_hint` |
| TC-A-14-1 | REQ-14 AK 1 | ein eingetragener Urlaubstag einer Person | der Plan erzeugt wird | wird sie an diesem Tag nicht eingeplant | `Req14VacationTests.test_tc_a_14_1_person_is_not_planned_on_vacation_days` |
| TC-A-15-1a | REQ-15 AK 1 (Teil 1) | ein erzeugter Plan | der Chef ihn veröffentlicht | sehen Mitarbeitende ihre eigenen Schichten | `Req15PublicationTests.test_tc_a_15_1a_employees_see_own_shifts_after_publication` |
| TC-A-15-1b | REQ-15 AK 1 (Teil 2) | – | – | Liegt die Veröffentlichung weniger als 14 Tage vor Planbeginn, erhält der Chef einen Hinweis (erwarteter Fehlschlag, DEF-02) | `Req15PublicationTests.test_tc_a_15_1b_planner_gets_hint_when_publishing_less_than_14_days_before_start` |
| TC-A-22-1 | REQ-22 AK 1 | ein Planungsmonat mit Sonntag standardmäßig geschlossen | der Chef einen einzelnen Sonntag öffnet | erscheinen für diesen Tag Slots in Bedarf, Verfügbarkeit und Plan | `Req22OpeningDayTests.test_tc_a_22_1_single_sunday_appears_in_demand_availability_and_plan` |
| TC-A-QR01-1 | QR-01 AK 1 | 30 Mitarbeitende, 3 Vorlagen und 30 Tage | der Plan erzeugt wird | dauert das im Mittel von 5 Läufen höchstens 10 Sekunden | `Qr01PerformanceTests.test_tc_a_qr01_1_mean_of_5_runs_at_most_10_seconds` |
| TC-A-QR03-1 | QR-03 AK 1 | zwei Mitarbeitende A und B | A die Verfügbarkeiten von B abrufen will (auch per direkter URL) | wird der Zugriff verweigert (HTTP 403) | `Qr03Qr04PrivacyTests.test_tc_a_qr03_1_colleague_availability_by_direct_url_is_403` |
| TC-A-QR03-3 | QR-03 AK 3 | die Datenbank | – | sind Passwörter nur als Hash gespeichert | `Qr03Qr04PrivacyTests.test_tc_a_qr03_3_passwords_are_stored_as_hash_only` |
| TC-A-QR04-1 | QR-04 AK 1 | das Verfügbarkeitsformular | – | enthält es nur Slot und Priorität, kein Freitextfeld für Gründe | `Qr03Qr04PrivacyTests.test_tc_a_qr04_1_availability_form_has_no_reason_field` |
| TC-A-QR04-2 | QR-04 AK 2 | die Datenbank | – | gibt es kein Feld für Begründungen | `Qr03Qr04PrivacyTests.test_tc_a_qr04_2_no_reason_field_in_database` |

**Anmerkungen:** REQ-10 AK 3 verlangt „keine Bearbeitungsfunktion im MVP“; dieser Teil ist durch REQ-11 (manuelle Korrektur, Sprint 1) überholt und wird im Anforderungsdokument angepasst – geprüft wird nur der weiterhin gültige Teil (kein Zugriff für Mitarbeitende). REQ-15 AK 1 wurde in zwei Tests geteilt, weil das Kriterium zwei unabhängige Bedingungen enthält; Teil 2 (Hinweis bei weniger als 14 Tagen Vorlauf) war zunächst nicht umgesetzt und als erwarteter Fehlschlag markiert (Defekt DEF-02); seit PR #66 ist der Test grün.

---

## 4 Oberflächentests im Browser (TC-UI)

**Vorbedingung:** Demobetrieb aus `seed_demo` (TC-UI-09 mit Testunternehmen, TC-UI-10 zusätzlich `prepare_usertests`) auf einem Django-Testserver; Chromium über Playwright; Fenster 1440 × 1000 px, mobil 360 × 900 px; Datum 20.10.2026. Für TC-UI-03, -05 und -06 sind alle Abgaben gesetzt und ein Plan erzeugt. Screenshots liegen im CI-Artefakt `ui-screenshots`.

| ID | Testfall | Anf. | Schritte | Erwartetes Ergebnis (Orakel) | Verf. | Umsetzung |
|---|---|---|---|---|---|---|
| TC-UI-01 | Bedarf, Schichtvorlage und Qualifikation pflegen | REQ-03, REQ-04 | Nora: Bedarf auf 4 setzen, speichern, neu laden; Vorlage „Wochenendschicht“ 9–15 anlegen; Qualifikation „Lager“ für Lea anlegen | Wert 4 bleibt nach Neuladen; Überschrift „Wochenendschicht“ sichtbar; Link „Lager“ sichtbar; alle Bilder geladen | AB | `test_planner_demand_template_and_qualification` |
| TC-UI-02 | Mobil abgeben, dann Monat erzeugen | REQ-06, REQ-07, REQ-08, REQ-09, QR-02 | Ben und Eva bei 360 px: Prio 1, Entwurf speichern, abgeben; Nora erzeugt Plan, öffnet unbesetzte Schichten | „Entwurf gespeichert“, Wert 1 erhalten, „Alles abgegeben“, kein horizontales Scrollen; „Erzeugt · Bearbeitbar“; Tabelle enthält „06.11.“ | AB | `test_mobile_save_submit_then_generate_month` |
| TC-UI-03 | Position nach Vorschau leeren | REQ-11 | Nora: Plan KW 45, „Besetzung bearbeiten“, Position öffnen, „Änderung prüfen“, „bestätigen“ | „Neue Besetzung:“ sichtbar; Meldung „Plankorrektur wurde gespeichert“ | ZB | `test_planner_can_remove_position_after_preview` |
| TC-UI-04 | Offene Abgaben vor dem Erzeugen bestätigen | REQ-05, REQ-08 | Nora: Erzeugen-Seite, Häkchen setzen, erzeugen | „2 Abgaben noch offen“ und Kontrollkästchen sichtbar; danach „Erzeugt · Bearbeitbar“ | ZB | `test_open_submissions_require_confirmation_before_generating` |
| TC-UI-05 | Auffüllen erhält bestehenden Plan | REQ-09 | Nora: unbesetzte Schichten, „automatisch füllen“ | Meldung „Keine weitere passende Person“; Seite bleibt erhalten | ZB | `test_auto_fill_button_preserves_existing_plan` |
| TC-UI-06 | Veröffentlichen und Sichtbarkeit umschalten | REQ-15, QR-02, RB-02 | Nora veröffentlicht; Lea mobil: eigene Schichten, Wochen blättern; Nora stellt „team“ ein; Lea erneut | „für Mitarbeitende veröffentlicht“; Lea sieht „Meine Schichten“, nicht „Ben Fischer“, KW 46/45 navigierbar, kein Überlauf; nach Umstellung „Schichtplan des Teams“ mit „Unbesetzt“ | AB | `test_publish_plan_and_switch_employee_visibility` |
| TC-UI-07 | Anmeldung per Tastatur und mobile Verfügbarkeit | REQ-01, QR-02 | 360 px: E-Mail, Tab, Passwort, Enter; Verfügbarkeiten öffnen, „Weitere Tage“ | Anmeldung erfolgreich; kein Überlauf; 4 Tageskarten, danach 6 | AB | `test_mobile_360_and_keyboard_login` |
| TC-UI-08 | Fremde und Planungsdaten liefern 403 | QR-03, RB-02 | Lea ruft `/bedarf/` und Bens Verfügbarkeiten auf | HTTP 403, Überschrift „Kein Zugriff“, „Ben Fischer“ nicht sichtbar | SI | `test_employee_privacy_returns_403` |
| TC-UI-09 | Leeres Testunternehmen isoliert | REQ-02 (ABW-03), QR-03 AK 2, QR-02 | planer1 meldet sich an, öffnet Mitarbeitende, legt Vorlage an; Nora und planer2 prüfen ihre Vorlagen | „TESTUNTERNEHMEN 1“; kein „Lea Meyer“; neue Vorlage nur in Testunternehmen 1 sichtbar; kein Überlauf | SI | `test_empty_company_login_and_setup_are_isolated` |
| TC-UI-10 | Vorbereitete Folgemonate erlauben 10 Eingaben | REQ-06, REQ-07, QR-05 | Testperson öffnet Dezember bzw. Januar, füllt ≥ 10 Felder, speichert Entwurf, gibt ab | Felder aktiv; „Entwurf gespeichert“; „Alles abgegeben“; kein Überlauf | AB | `test_prepared_future_months_allow_ten_availability_entries` |

---

## 5 Akzeptanztests mit Nutzenden (TC-M, geplant)

**Vorbedingung:** Online-Demo https://shiftplanner-demo-93eu.onrender.com mit eigens angelegten Testkonten; je zwei Planerinnen/Planer und zwei Mitarbeitende aus den bisherigen Feedbackbetrieben (Netto, Deichmann); Bearbeitung ohne Hilfestellung; Zeit und Probleme werden protokolliert. Umsetzung des Feedbacks aus P4 („Aufgaben auf der Website stellen“).

| ID | Aufgabe | Rolle | Anf. | Erfolgskriterium (Orakel) |
|---|---|---|---|---|
| TC-M-01 | Verfügbarkeiten für eine Woche mit Prioritäten eingeben und abgeben | Mitarbeitende | REQ-06, REQ-07, QR-05 | Abgabe erfolgreich ohne Hilfe; 10 Slots in ≤ 5 min |
| TC-M-02 | Eigenen veröffentlichten Schichtplan auf dem Smartphone finden | Mitarbeitende | REQ-15, QR-02 | eigene Schichten der Woche korrekt benannt |
| TC-M-03 | Personalbedarf für eine Woche eintragen und auf den Monat übernehmen | Planung | REQ-04 | Bedarf gespeichert und übernommen ohne Hilfe |
| TC-M-04 | Plan erzeugen, eine unbesetzte Schicht finden und manuell besetzen | Planung | REQ-08, REQ-09, REQ-11 | Plan erzeugt, Korrektur bestätigt |
| TC-M-05 | Plan veröffentlichen | Planung | REQ-15, QR-06 | Veröffentlichung erfolgreich; gesamter Monatsablauf (TC-M-03 bis -05) in ≤ 30 min |

Aufgabenblatt, Protokollvorlage und Ergebnisse folgen in Schritt 5.
