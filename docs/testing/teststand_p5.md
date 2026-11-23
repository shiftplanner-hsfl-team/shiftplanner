# Testbericht P5 – Qualität & Tests

Verantwortlich: Anil Duth (Qualitätssicherung); ab 23.11.2026 vertretungsweise Muhammed Asif Shahul Hameed · Stand: 23.11.2026, 15:00 Uhr (Version 2) · Grundlage: `testkonzept.md`, `testfaelle.md`, `review_richtlinie.md`

Dieser Bericht fasst den Teststand zu P5 zusammen: Ergebnisse je Teststufe, Abdeckung, gefundene Defekte, Ergebnisse der statischen Prüfungen und der Tests mit Nutzenden sowie die Bewertung gegen die Endekriterien des Testkonzepts. Alle Zahlen stammen aus dem zitierten CI-Lauf bzw. den verlinkten Dokumenten. Version 1 (Lauf 45179166147, 13:57 Uhr) wies noch DEF-02 als offen und eine Zweigabdeckung von 89,2 % aus; beide Punkte wurden am selben Tag behoben (Abschnitte 3 und 4).

## 1 Testobjekt und Testlauf

| Feld | Wert |
|---|---|
| Testobjekt | `main`, Commit `d1572be` (nach PR #71), Online-Demo https://shiftplanner-demo-93eu.onrender.com |
| CI-Lauf | GitHub Actions, Lauf 45186525583 vom 23.11.2026, 14:42 Uhr – **erfolgreich** |
| Jobs | `test` (Ruff, Django-Checks, Backend mit SQLite inkl. Abdeckung, Browser mit Chromium) · `Backend mit PostgreSQL` (PostgreSQL 18) |
| Lokale Gegenprobe | 23.11.2026, gleicher Commit: 176 Backendtests, OK |

## 2 Ergebnisse je Teststufe

| Stufe | Testfälle | bestanden | fehlgeschlagen | Ausführung |
|---|---|---|---|---|
| Unit (TC-U) | 20 | 20 | 0 | automatisch, beide Datenbanken |
| Komponente (TC-K) | 113 | 113 | 0 | automatisch, beide Datenbanken |
| Akzeptanz automatisiert (TC-A) | 43 | 43 | 0 | automatisch, beide Datenbanken |
| **Backend gesamt** | **176** | **176** | **0** | SQLite 14,2 s · PostgreSQL 37,3 s |
| Oberfläche (TC-UI) | 10 | 10 | 0 | automatisch, Chromium, 18,2 s |
| Akzeptanz mit Nutzenden (TC-M) | 5 Aufgaben, 15 Durchführungen | 12 auswertbar, alle erfolgreich | 0 | manuell, siehe Abschnitt 5 |

Die 176 Backendtests verteilen sich auf `apps/planning/tests.py` (105), `apps/planning/test_companies.py` (14), `tests/unit/` (14) und `tests/acceptance/` (43). Alle automatisierten Tests laufen bei jedem Push; seit P4 (53 Tests, davon 4 UI) ist die Zahl der automatisierten Testfälle auf **186** gestiegen. **Alle 43 Akzeptanzkriterien der umgesetzten Anforderungen sind bestanden.**

**Nichtfunktionale Messwerte:** QR-01 (Planerzeugung 30 Personen × 3 Vorlagen × 30 Tage) liegt im Mittel von fünf Läufen bei 0,28 s (Maximum 0,31 s, lokale Messung 23.11.2026) und damit weit unter 10 s (TC-A-QR01-1). QR-02 (360 px ohne horizontales Scrollen) und QR-03 (HTTP 403 bzw. 404 bei fremden Daten) sind in TC-UI-02, -06, -07, -08, -09 sowie in 13 Komponententests zur Betriebstrennung bestanden.

## 3 Abdeckung (strukturbasierter Test)

| Messgröße (`coverage.py`, App `apps`, ohne Migrationen und `tests.py`) | Version 1 (13:57) | **Version 2 (14:42)** |
|---|---|---|
| Anweisungsabdeckung | 95,9 % | **97,3 %** (1.305 von 1.341) |
| Zweigabdeckung | 89,2 % | **93,3 %** (321 von 344) |
| Kombinierter Wert (Anzeige in CI, `fail_under = 90`) | 95 % | **96 %** |

**Befund und Maßnahme:** Version 1 zeigte, dass das Endekriterium „Zweigabdeckung ≥ 90 %“ (Testkonzept, Abschnitt 7) mit 89,2 % knapp verfehlt war, obwohl die CI grün war – die CI prüft den kombinierten Wert. Daraufhin wurden zehn Tests für bis dahin nicht ausgeführte Fehlerpfade ergänzt (`ErrorPathTests`, TC-K-104 bis TC-K-113: ungültige Frist, Bedarf als Text bzw. außerhalb 0–30, ungültige Plansicht, Urlaub mit Ende vor Beginn, Korrektur mit Person und Tausch zugleich u. a.; Issue #65, PR #66). Die Zweigabdeckung liegt jetzt bei 93,3 %. Offen bleibt, die Zweigabdeckung als eigene Prüfung in die CI aufzunehmen (Abschnitt 8, N3).

## 4 Defekte

| ID | Beschreibung | gefunden durch | Schwere | Status | Ticket / Nachweis |
|---|---|---|---|---|---|
| DEF-01 | Manuelle Korrektur (REQ-11) bricht in der Online-Demo mit HTTP 500 ab: `select_for_update()` sperrte unter PostgreSQL auch die optionale Join-Seite. Auf SQLite nicht reproduzierbar. | Nutzung der Online-Demo (11.11.2026) | hoch | **behoben** (PR #42, 18.11.2026) | #63 (nachträglich angelegt); Regressionsschutz durch CI-Job „Backend mit PostgreSQL“ mit allen 16 `ManualCorrectionTests` |
| DEF-02 | Bei Veröffentlichung weniger als 14 Tage vor Planbeginn erhält die Planung keinen Hinweis (REQ-15 AK 1, Teil 2). | Akzeptanztest TC-A-15-1b (18.11.2026) | mittel | **behoben** (PR #66, 23.11.2026) | #64; Hinweis auf der Veröffentlichungsseite, Veröffentlichen bleibt möglich; TC-A-15-1b grün, Grenzwerttests TC-K-101 bis TC-K-103 (14 / 13 / 1 Tag, nach Beginn) |
| DEF-03 | UI-Test `test_mobile_360_and_keyboard_login` schlägt sporadisch fehl (Zeitverhalten im Browser). | CI (P4) | gering | offen, beobachtet; in allen Läufen seit 18.11. bestanden | #39 |

**Lebenszyklus am Beispiel DEF-02:** Der automatisierte Akzeptanztest fand die Lücke, der Test wurde als erwarteter Fehlschlag markiert (CI bleibt grün, der Fehler sichtbar), das Ticket #64 beschreibt Schritte, Erwartung und Ist-Zustand, PR #66 behebt den Fehler mit Grenzwerttests, und der vorher fehlschlagende Test ist jetzt grün – entsprechend Testkonzept, Abschnitt 8.

**Lehre aus DEF-01:** Ein Fehler, der nur auf der Produktionsdatenbank auftritt, wurde von 85 grünen Tests auf SQLite nicht erkannt. Seitdem laufen alle Backendtests zusätzlich gegen PostgreSQL (ISTQB 2023, produktionsnahe Testumgebung).

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
| Code-Reviews | bis #55: 21 von 21 PRs freigegeben, 9 ohne Begründung, 0 Inline-Kommentare; seit Einführung der Richtlinie (23.11.) Review-Kommentare nach Vorlage, fehlende nachgetragen | `review_ergebnisse_p5.md`, Abschnitt 1 |
| Inspektion Entwurfsdiagramme (#58, Prüfliste A1–A9) | 16 Befunde (3 hoch, 9 mittel, 4 gering), **alle behoben** in #60 und #71 | `review_ergebnisse_p5.md`, Abschnitt 2 |

## 7 Bewertung gegen die Endekriterien (Testkonzept, Abschnitt 7)

| Endekriterium | Stand | erfüllt? |
|---|---|---|
| Alle Testfälle des Katalogs ausgeführt und dokumentiert | 186 automatisiert ausgeführt; TC-M bis auf M2 ausgewertet | weitgehend (M2 offen) |
| Alle Akzeptanzkriterien der umgesetzten Anforderungen bestanden | 43 von 43 | **ja** |
| Zweigabdeckung `planning` ≥ 90 % | 93,3 % | **ja** |
| Kein offener Fehler „kritisch“ oder „hoch“ | DEF-01 und DEF-02 behoben; offen nur DEF-03 (gering) | **ja** |
| Verbleibende Fehler mit Begründung dokumentiert | Abschnitt 4 | **ja** |

**Gesamtbewertung:** Die automatisierten Tests decken alle Stufen ab, laufen bei jedem Push auf zwei Datenbanken und im Browser und sind vollständig grün; alle Akzeptanzkriterien sind erfüllt, und beide gefundenen Defekte der Schwere „hoch“ bzw. „mittel“ sind behoben. Offen sind die Aufgabe M2 der Nutzertests und – inhaltlich wichtigster Befund – die Monatsplanung beim ersten Kontakt, die länger dauert als gefordert (QR-06); dafür sind Verbesserungen vor P6 eingeplant.

## 8 Nächste Schritte bis P6 (09.12.2026)

| Nr. | Maßnahme | Verantwortlich | Status |
|---|---|---|---|
| N1 | DEF-02 beheben | Bennet / Claude | erledigt (#66) |
| N2 | Inspektion abschließen, Diagramme nachziehen | Bennet, Moderation Asif | erledigt (#60, #71) |
| N3 | Zweigabdeckung ≥ 90 % (erledigt, #66); Zweigprüfung als eigener CI-Schritt | Asif, Bennet | teilweise, bis 02.12. |
| N4 | Verbesserungen #50–#52 umsetzen, QR-05/QR-06 und M2 im Nutzertest P6 erneut messen (eigene Konten je Person) | Bennet, Asif | bis 02.12. |
| N5 | Review-Kennzahlen erneut erheben (Wirkung der Richtlinie, M1–M4) | Asif | bis 09.12. |

## Literatur

- ISTQB (2023): *Certified Tester Foundation Level Syllabus*, Version 4.0.
