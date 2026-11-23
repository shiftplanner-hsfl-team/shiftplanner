# Testbericht P5 – Qualität & Tests

Verantwortlich: Anil Duth (Qualitätssicherung); ab 23.11.2026 vertretungsweise Muhammed Asif Shahul Hameed · Stand: 23.11.2026 · Grundlage: `testkonzept.md`, `testfaelle.md`, `review_richtlinie.md`

Dieser Bericht fasst den Teststand zu P5 zusammen: Ergebnisse je Teststufe, Abdeckung, gefundene Defekte, Ergebnisse der statischen Prüfungen und der Tests mit Nutzenden sowie die Bewertung gegen die Endekriterien des Testkonzepts. Alle Zahlen stammen aus dem zitierten CI-Lauf bzw. den verlinkten Dokumenten.

## 1 Testobjekt und Testlauf

| Feld | Wert |
|---|---|
| Testobjekt | `main`, Commit `0edb475` (nach PR #57), Online-Demo https://shiftplanner-demo-93eu.onrender.com |
| CI-Lauf | GitHub Actions, Lauf 45179166147 vom 23.11.2026, 13:57 Uhr – **erfolgreich** |
| Jobs | `test` (Ruff, Django-Checks, Backend mit SQLite inkl. Abdeckung, Browser mit Chromium) · `Backend mit PostgreSQL` (PostgreSQL 18) |
| Lokale Gegenprobe | 23.11.2026, gleicher Commit: 163 Backendtests, OK (1 erwarteter Fehlschlag) |

## 2 Ergebnisse je Teststufe

| Stufe | Testfälle | bestanden | fehlgeschlagen | erwarteter Fehlschlag | Ausführung |
|---|---|---|---|---|---|
| Unit (TC-U) | 20 | 20 | 0 | 0 | automatisch, beide Datenbanken |
| Komponente (TC-K) | 100 | 100 | 0 | 0 | automatisch, beide Datenbanken |
| Akzeptanz automatisiert (TC-A) | 43 | 42 | 0 | 1 (DEF-02) | automatisch, beide Datenbanken |
| **Backend gesamt** | **163** | **162** | **0** | **1** | SQLite 16,2 s · PostgreSQL 25,8 s |
| Oberfläche (TC-UI) | 10 | 10 | 0 | 0 | automatisch, Chromium, 20,6 s |
| Akzeptanz mit Nutzenden (TC-M) | 5 Aufgaben, 15 Durchführungen | 12 auswertbar, alle erfolgreich | 0 | – | manuell, siehe Abschnitt 5 |

Die 163 Backendtests verteilen sich auf `apps/planning/tests.py` (85 + 7 Vorbereitung der Nutzertests), `apps/planning/test_companies.py` (14, Betriebstrennung aus PR #46), `tests/unit/` (14) und `tests/acceptance/` (43). Alle automatisierten Tests laufen bei jedem Push; seit P4 (53 Tests, davon 4 UI) ist die Zahl der automatisierten Testfälle damit auf 173 gestiegen.

**Nichtfunktionale Messwerte:** QR-01 (Planerzeugung 30 Personen × 3 Vorlagen × 30 Tage) liegt im Mittel von fünf Läufen bei 0,31 s (Maximum 0,41 s, lokale Messung 23.11.2026) und damit weit unter 10 s (TC-A-QR01-1, bestanden). QR-02 (360 px ohne horizontales Scrollen) und QR-03 (HTTP 403 bei fremden Daten) sind in TC-UI-02, -06, -07, -08 sowie in 13 Komponententests zur Betriebstrennung bestanden.

## 3 Abdeckung (strukturbasierter Test)

| Messgröße (`coverage.py`, App `apps`, ohne Migrationen und `tests.py`) | Wert |
|---|---|
| Anweisungsabdeckung | 1.284 von 1.339 Anweisungen = **95,9 %** |
| Zweigabdeckung | 307 von 344 Zweigen = **89,2 %** |
| Kombinierter Wert (Anzeige in CI, `fail_under = 90`) | **95 %** |
| Module mit vollständiger Abdeckung | 7 (u. a. `rules.py`) |
| Niedrigste Werte | `seed_test_companies.py` 88 %, `models.py` 92 % (nur `__str__`), `seed_demo.py` 92 % |

**Befund:** Das Endekriterium des Testkonzepts (Abschnitt 7) verlangt eine **Zweig**abdeckung von mindestens 90 %; die CI prüft dagegen den kombinierten Wert aus Anweisungen und Zweigen. Mit 89,2 % ist das Kriterium knapp **nicht erfüllt**, obwohl die CI grün ist. Die meisten offenen Zweige liegen in `views.py` (13 teilweise abgedeckte Zweige, überwiegend Fehlerpfade ungültiger Formulareingaben) und `services.py` (8). Maßnahme: Tests für diese Fehlerpfade ergänzen und Testkonzept und CI-Konfiguration angleichen (eine eigene Zweigprüfung im CI-Schritt), siehe Abschnitt 7.

## 4 Defekte

| ID | Beschreibung | gefunden durch | Schwere | Status | Nachweis |
|---|---|---|---|---|---|
| DEF-01 | Manuelle Korrektur (REQ-11) bricht in der Online-Demo mit HTTP 500 ab: `select_for_update()` sperrte unter PostgreSQL auch die optionale Join-Seite. Auf SQLite nicht reproduzierbar. | Nutzung der Online-Demo (11.11.2026) | hoch | **behoben** (PR #42, 18.11.2026) | Korrektur `select_for_update(of=('self',))`; Regressionsschutz durch neuen CI-Job „Backend mit PostgreSQL“, in dem alle 16 `ManualCorrectionTests` gegen PostgreSQL 18 laufen |
| DEF-02 | Bei Veröffentlichung weniger als 14 Tage vor Planbeginn erhält die Planung keinen Hinweis (REQ-15 AK 1, Teil 2). | Akzeptanztest TC-A-15-1b (18.11.2026) | mittel | **in Arbeit** (Bennet, Issue und PR am 23.11.) | Test ist bis zur Korrektur als `expectedFailure` markiert; nach der Korrektur wird die Markierung entfernt |
| DEF-03 | UI-Test `test_mobile_360_and_keyboard_login` schlägt sporadisch fehl (Zeitverhalten im Browser). | CI (P4) | gering | offen, beobachtet; in den letzten Läufen bestanden | Issue #39 |

**Lehre aus DEF-01:** Ein Fehler, der nur auf der Produktionsdatenbank auftritt, wurde von 85 grünen Tests auf SQLite nicht erkannt. Seitdem laufen alle Backendtests zusätzlich gegen PostgreSQL. Das bestätigt die Empfehlung, Tests in einer produktionsnahen Umgebung auszuführen (ISTQB 2023, Testumgebung).

## 5 Akzeptanztests mit Nutzenden (Kurzfassung)

Umsetzung des Feedbacks aus P4. Drei Betriebe (je eine Planungsperson und eine Mitarbeitende) lösten unmoderiert Aufgaben in der Online-Demo; vollständige Werte in `nutzertests/ergebnisse_p5.md`, Feedback als FB-16 bis FB-21 in `docs/feedback/feedback.md`.

| Ergebnis | Wert | Ziel | bewertet |
|---|---|---|---|
| Aufgaben ohne Hilfe gelöst (P1–P3, M1) | 12 von 12 | alle | erfüllt |
| QR-05: 10 Verfügbarkeiten in ≤ 5 min | 2 von 3 | alle | teilweise |
| QR-06: Monatsplanung P1–P3 in ≤ 30 min | 1 von 3 (40 / 65 / 25 min) | alle | **nicht erfüllt** |
| Schwierigkeit je Aufgabe (SEQ, Median) | 5 | ≥ 5 | erfüllt |
| UMUX-LITE „erfüllt Anforderungen“ / „einfach“ | 5,3 / 5,5 | ≥ 5 | erfüllt |
| M2 „eigenen Plan finden“ | nicht auswertbar | – | Wiederholung mit Screenshot |

Die Befunde führten zu drei Verbesserungen vor P6 (#50 Wochenauswahl, #51 „Nächste Schritte“, #52 Hinweis im Bedarfsformular) und einer neuen Anforderung (#53 REQ-26). QR-06 wird in P6 erneut gemessen.

## 6 Statische Prüfungen

| Prüfung | Ergebnis | Nachweis |
|---|---|---|
| Statische Analyse (Ruff, Coding-Standards) | ohne Befund in jedem CI-Lauf; Merge nur bei grünem CI | `CONTRIBUTING.md`, Abschnitt 4 |
| Code-Reviews | 21 von 21 gemergten PRs freigegeben; 9 davon ohne Begründung, 0 Inline-Kommentare; 6 Reviews mit dokumentierten Befunden | `review_ergebnisse_p5.md`, Abschnitt 1 |
| Inspektion Entwurfsdiagramme (Prüfliste A1–A9) | läuft seit 23.11.2026; werkzeuggestützte Vorprüfung: 5 von 17 Modellklassen fehlen im Klassen- und ER-Diagramm (Schwere hoch) | `review_ergebnisse_p5.md`, Abschnitt 2; Issue „INSP: Entwurfsdiagramme P5“ |

## 7 Bewertung gegen die Endekriterien (Testkonzept, Abschnitt 7)

| Endekriterium | Stand | erfüllt? |
|---|---|---|
| Alle Testfälle des Katalogs ausgeführt und dokumentiert | 173 automatisiert ausgeführt; TC-M teilweise (M2 offen) | teilweise |
| Alle Akzeptanzkriterien der umgesetzten Anforderungen bestanden | 42 von 43; offen REQ-15 AK 1 Teil 2 (DEF-02) | nein (Korrektur in Arbeit) |
| Zweigabdeckung `planning` ≥ 90 % | 89,2 % | **nein** (knapp) |
| Kein offener Fehler „kritisch“ oder „hoch“ | DEF-01 behoben; offen nur DEF-02 (mittel), DEF-03 (gering) | ja |
| Verbleibende Fehler mit Begründung dokumentiert | Abschnitt 4 | ja |

**Gesamtbewertung:** Die automatisierten Tests decken alle Stufen ab, laufen bei jedem Push auf zwei Datenbanken und im Browser und sind vollständig grün. Drei Punkte erfüllen das Endekriterium noch nicht, und keiner davon ist kritisch: der fehlende 14-Tage-Hinweis (DEF-02, Korrektur läuft), die Zweigabdeckung knapp unter 90 % und die Aufgabe M2 der Nutzertests. Inhaltlich wichtigster Befund ist, dass die Monatsplanung beim ersten Kontakt länger dauert als gefordert (QR-06); dafür sind Verbesserungen vor P6 eingeplant.

## 8 Nächste Schritte bis P6 (09.12.2026)

| Nr. | Maßnahme | Verantwortlich | bis |
|---|---|---|---|
| N1 | DEF-02 beheben, `expectedFailure` entfernen | Bennet | 24.11. |
| N2 | Inspektion abschließen, Diagramme nachziehen (V1–V3 und Befunde) | Bennet (Vertretung Architektur), Moderation Asif | 24.11. |
| N3 | Tests für offene Fehlerpfade in `views.py`/`services.py`; Zweigabdeckung ≥ 90 % als eigene Prüfung in CI | Asif (Vertretung QS), Bennet | 02.12. |
| N4 | Verbesserungen #50–#52 umsetzen, QR-05/QR-06 und M2 im Nutzertest P6 erneut messen (eigene Konten je Person) | Bennet, Asif | 02.12. |
| N5 | Review-Kennzahlen erneut erheben (Wirkung der Richtlinie, M1–M4) | Asif | 09.12. |

## Literatur

- ISTQB (2023): *Certified Tester Foundation Level Syllabus*, Version 4.0.
