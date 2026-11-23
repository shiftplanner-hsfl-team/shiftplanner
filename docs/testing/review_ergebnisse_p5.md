# Review- und Inspektionsergebnisse P5

Verantwortlich: Anil Duth (Qualitätssicherung); ab 23.11.2026 vertretungsweise Muhammed Asif Shahul Hameed · Stand: 23.11.2026 · Grundlage: `review_richtlinie.md` · Datenquelle: GitHub-API (Pull Requests, Reviews, Kommentare), Abruf 23.11.2026

Dieses Dokument wertet alle bisherigen Code-Reviews aus und dokumentiert die erste Inspektion nach der neuen Richtlinie. Die Zahlen stammen unverändert aus GitHub; die Bewertung benennt auch die Schwächen unseres bisherigen Vorgehens, weil daraus die Richtlinie entstanden ist.

## 1 Code-Reviews aller gemergten Pull Requests (#1 bis #55)

### 1.1 Kennzahlen

| Kennzahl | Wert |
|---|---|
| Gemergte Pull Requests | 21 |
| davon mit mindestens einer Freigabe (Approve) durch eine andere Person | **21 von 21 (100 %)** |
| davon mit begründetem Review-Kommentar | 12 von 21 (57 %) |
| davon Freigabe **ohne** Kommentar | 9 von 21 (43 %): #1, #15, #28, #29, #30, #31, #32, #36, #55 |
| Inline-Kommentare an Codezeilen | **0** in allen 21 PRs |
| Median Zeit vom Öffnen des PR bis zur Freigabe | 14 Minuten (11 von 21 PRs in ≤ 15 Minuten) |
| Freigaben je Person | Asif 8 · Bennet 5 · Mahdi 5 · Anil 3 |

### 1.2 Bewertung

Die formale Regel „kein Merge ohne Review durch eine andere Person“ wurde ausnahmslos eingehalten, und jede Rolle hat Reviews übernommen. Die **Tiefe** der Reviews war jedoch uneinheitlich. Fast die Hälfte der Freigaben enthält keine Begründung, es gibt keinen einzigen Inline-Kommentar, und große Änderungen wurden teils sehr schnell freigegeben (z. B. #41 mit 1.693 hinzugefügten Zeilen in 14 Minuten, #32 mit 309 Zeilen in 3 Minuten). Empirische Daten zu Code-Reviews legen nahe, dass die Fehlerfindung oberhalb von etwa 400 Zeilen je Review und 500 Zeilen je Stunde deutlich abnimmt (Cohen 2006). Bei diesen PRs ist daher nicht belegbar, dass sie inhaltlich geprüft wurden; sie wurden durch die CI-Tests abgesichert, nicht durch das Review.

Dem stehen Reviews gegenüber, die nachweislich Fehler gefunden oder Verbesserungen bewirkt haben (Abschnitt 1.3). Sie zeigen, was ein Review leisten kann, wenn es mit Prüfliste und Ausführung erfolgt – und sind die Vorlage für die Richtlinie.

### 1.3 Reviews mit Befunden

| PR | Reviewer/in | Befund | Schwere | Ergebnis |
|---|---|---|---|---|
| #18 (UML-Diagramme P3) | Asif (PO) | Klassen- und ER-Diagramm nennen die Klasse „Leave“, im Code heißt sie `Vacation`; weitere Abweichungen zum Code | mittel | als Issue #26 erfasst, mit PR #37 behoben und von Mahdi gegen `models.py` geprüft |
| #40 (Teststand P4) | Asif (PO) | Testzahlen und Issue-Verweis („Closes #27“) zunächst falsch; Hinweis auf Commit-Konvention | gering | im PR korrigiert, danach freigegeben |
| #41 (REQ-11/REQ-15) | Asif (PO) | lokal ausgecheckt, 93 Tests und Ablauf auf frischer Demo geprüft; keine Befunde | – | freigegeben |
| #42 (DEF-01, PostgreSQL) | Asif (QS/PO) | Ursache und Korrektur nachvollzogen; Hinweis: Abhängigkeit `psycopg` nur im Workflow statt in `requirements-dev.txt` | gering | freigegeben, Hinweis offen |
| #44 (Unit-/Akzeptanztests) | Bennet | Tests und CI geprüft; erwarteter Fehlschlag DEF-02 nachvollziehbar dokumentiert | – | freigegeben |
| #45 (Vorbereitung Nutzertests) | Bennet | Kommando überging einen bereits angelegten, leeren Dezembermonat; bestehender Novemberentwurf wäre neu erzeugt worden; Betriebstrennung nicht berücksichtigt | mittel | vom Reviewer im PR behoben (Commit 2b987e3) inkl. drei zusätzlicher Tests |

### 1.4 Nicht durchgeführte Review-Vorlagen aus P3

Für P3 wurden zwei Prüfvorlagen angelegt (`review_pr1.md`, `review_diagramme.md`), aber **nie ausgefüllt**; die Reviews zu PR #1 und #18 erfolgten stattdessen direkt in GitHub. Die Vorlagen bleiben als Nachweis im Repository und sind mit einem Hinweis versehen; sie werden durch diese Richtlinie und die Inspektion in Abschnitt 2 ersetzt. Ursache war, dass die Vorlagen keinen Verantwortlichen und keinen Termin hatten – beides legt die Richtlinie nun fest (Moderation, Inspektions-Issue).

### 1.5 Maßnahmen

| Nr. | Maßnahme | ab |
|---|---|---|
| M1 | Freigaben nur mit Kommentar nach Vorlage (Richtlinie 3.3): was geprüft, Ausführung, Befunde | sofort |
| M2 | Bei Code-PRs Branch lokal ausführen; Befunde als Inline-Kommentar an der Zeile | sofort |
| M3 | Große Änderungen (> 400 Zeilen) in mehrere PRs aufteilen oder Review-Zeit einplanen | Sprint 3 |
| M4 | Kennzahlen 1.1 vor P6 und P7 erneut erheben, um die Wirkung von M1–M3 zu zeigen | P6, P7 |

## 2 Inspektion der Entwurfsdokumente (P5)

| Feld | Inhalt |
|---|---|
| Gegenstand | `docs/design/klassen.puml`, `er_diagramm.puml`, `komponenten.puml`, `sequenz_plan_erzeugen.puml`, `aktivitaet_monatsablauf.puml`, `use_case.puml`, `architektur.md` (Stand `main`, 23.11.2026) |
| Prüfliste | Richtlinie 4.3 A (A1–A9) |
| Moderation | Muhammed Asif Shahul Hameed (vertretungsweise für Anil Duth, QS) |
| Autor | Mahdi Fazeli (Architektur & Entwurf); Nacharbeit vertretungsweise durch Bennet Schalow |
| Inspektor/innen | Bennet Schalow (A1–A4, kennt den Code), Muhammed Asif Shahul Hameed (A5–A9) |
| Issue | INSP: siehe GitHub |

### 2.1 Werkzeuggestützte Vorprüfung (zu bestätigen)

Ein automatischer Abgleich der Klassennamen in `models.py` mit `klassen.puml` und `er_diagramm.puml` (23.11.2026, KI-gestützt erstellt) ergab:

| Nr. | Prüfpunkt | Fundstelle | Beschreibung | Vorgeschlagene Schwere |
|---|---|---|---|---|
| V1 | A1, A7 | `klassen.puml` | Es fehlen 5 von 17 Modellklassen: `Company`, `CompanyAccount` (PR #46), `PlanningSettings`, `PublishedPlan`, `PublishedAssignment` (PR #41). `architektur.md` beschreibt alle fünf bereits im Text. | hoch |
| V2 | A2 | `er_diagramm.puml` | Dieselben fünf Tabellen fehlen; Fremdschlüssel `company_id` in `Month`, `Employee`, `ShiftTemplate`, `Qualification` nicht dargestellt. | hoch |
| V3 | A8 | `docs/design/png/` | PNG-Exporte sind mit den Quellen erneut abzugleichen, sobald V1 und V2 behoben sind. | gering |

### 2.2 Befunde der Inspektor/innen

Erfasst als Kommentare in Issue #58 (23.11.2026). Beide Einzelprüfungen waren werkzeuggestützt und sind als solche gekennzeichnet (Richtlinie 4.2, Schritt 3).

| Nr. | Prüfpunkt | Fundstelle | Beschreibung | Schwere | gefunden von | Status |
|---|---|---|---|---|---|---|
| B1 (= V1) | A1, A7 | `klassen.puml` | 5 von 17 Modellklassen fehlen (Company, CompanyAccount, PlanningSettings, PublishedPlan, PublishedAssignment) | hoch | Bennet, Asif | behoben in #60 |
| B2 (= V2) | A2 | `er_diagramm.puml` | dieselben 5 Tabellen und `company_id`-Fremdschlüssel fehlen | hoch | Bennet | behoben in #60 |
| B3 | A1, A2 | `klassen.puml`, `er_diagramm.puml` | Namen/Monat als global eindeutig statt je Betrieb | mittel | Bennet | behoben in #60 |
| B4 | A1, A2 | beide | User–Employee als 1:1 statt 1:0..1 | mittel | Bennet | behoben in #60 |
| B5 | A2 | `er_diagramm.puml` | M:N-Tabelle ohne `id` und Eindeutigkeitsregel | mittel | Bennet | behoben in #60 |
| B6 | A3 | `komponenten.puml` | corrections.py, autofill.py, publications.py und Abhängigkeiten fehlen | mittel | Bennet, Asif (A-7) | behoben in #71 |
| B7 | A4 | `sequenz_plan_erzeugen.puml` | veraltete Freigabebedingung; Bestätigung offener Abgaben (`allow_incomplete`) fehlt | hoch | Bennet | behoben in #71 |
| B8 | A4 | `sequenz_plan_erzeugen.puml` | nur INSERT; Redirect auf „nur lesend“ statt bearbeitbaren Entwurf | mittel | Bennet | behoben in #71 |
| A-1 | A5 | `aktivitaet_monatsablauf.puml` | Status „in Arbeit“/„Sprint 2“, „nur lesend“ veraltet | mittel | Asif | behoben in #71 |
| A-2 | A5 | `aktivitaet_monatsablauf.puml` | Bestätigung offener Abgaben, Auffüllen, Vorschau vor Veröffentlichung fehlen | mittel | Asif | behoben in #71 |
| A-3 | A5 | `aktivitaet_monatsablauf.puml` | Mitarbeitende sehen veröffentlichten Plan fehlt | gering | Asif | behoben in #71 |
| A-4 | A6 | `use_case.puml` | Status veraltet | mittel | Asif | behoben in #71 |
| A-5 | A6 | `use_case.puml` | Mitarbeitende ohne Beziehung zum veröffentlichten Plan; Planung nur über <<extend>> | mittel | Asif | behoben in #71 |
| A-7 | A7 | `architektur.md` | Schichtentabelle ohne drei Module und Testordner | mittel | Asif | behoben in #71 |
| A-8 | A7 | `architektur.md` | Persistenz nur SQLite | gering | Asif | behoben in #71 |
| A-9 (= V3) | A8 | alle Diagramme | Titel „Stand Sprint 1“; PNG-Exporte | gering | Asif | Klassen/ER in #60; übrige PNGs in #71 |

A9 (Entwurfsprinzipien): ohne Befund.

| Person | Vorbereitungszeit | geprüfte Prüfpunkte |
|---|---|---|
| Bennet Schalow | ca. 3 min werkzeuggestützt (Codex); persönliche Bestätigung im Issue | A1–A4 |
| Muhammed Asif Shahul Hameed | 15 min (werkzeuggestützte Vorprüfung, am Diagramm bestätigt) | A5–A9 |

**Kennzahlen:** 16 Befunde (3 hoch, 9 mittel, 4 gering); 5 in #60 und 11 in #71 behoben.

### 2.3 Entscheidung und Nachverfolgung

Entscheidung der Moderation (Asif): **Nacharbeit erforderlich** (3 Befunde „hoch“). Nacharbeit durch Bennet (Vertretung Architektur) in PR #60 (Klassen-/ER-Diagramm, gemergt 23.11.2026) und PR #71 (übrige Diagramme mit PNGs, `architektur.md`). Ein paralleler KI-Entwurf derselben Nacharbeit (#68) wurde zuerst gemergt und beim Zusammenführen vollständig durch Bennets geprüfte Fassung aus #71 ersetzt. Abschluss der Inspektion mit dem Merge von #71; danach wird Issue #58 geschlossen.

**Bewertung:** Die Inspektion hat gezeigt, dass die Diagramme nach zwei größeren Features (#41, #46) nicht mitgezogen wurden, obwohl der Text in `architektur.md` bereits aktuell war. Prüfpunkt C9 der Code-Review-Prüfliste („Diagramme angepasst, wenn sich das Datenmodell ändert“) soll das künftig bereits im PR abfangen.

## Literatur

- Cohen, J. (2006): *Best Kept Secrets of Peer Code Review*. Smart Bear Software.
- Fagan, M. E. (1976): Design and code inspections to reduce errors in program development. In: *IBM Systems Journal* 15 (3), S. 182–211.
