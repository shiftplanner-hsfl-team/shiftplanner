# Feedback-Dokumentation ShiftPlanner

Stand: 09.11.2026 · Verantwortlich: Anforderungen (Muhammed Asif Shahul Hameed)

Dieses Dokument sammelt alle Rückmeldungen realer potenzieller Kundinnen und Kunden
(Planer und Mitarbeitende im Einzelhandel und in der Gastronomie) und zeigt für jede
Aussage, welche Konsequenz sie für das Produkt hatte – bis zur Umsetzung im Code
(Rückverfolgbarkeit Feedback → Anforderung → Pull Request → Test). Alle Personen sind
pseudonymisiert; Namen und Betriebe werden nicht genannt.

## 1 Vorgehen

| Runde | Zeitraum | Gegenstand | Methode | Rückmeldungen |
|---|---|---|---|---|
| 1 – Erhebung | 08.–13.10.2026 | Problem, Ablauf, Anforderungen | Leitfaden mit Mehrfachauswahl als Interview oder Fragebogen | FB-01 bis FB-07 |
| 2 – Prototyp | 26.10.2026 | erster lauffähiger Prototyp (MVP) | Fragebogen mit vier Screenshots | FB-08 bis FB-11 |
| 3 – Sprint-1-Inkrement | 09.11.2026 | Abgabefrist, Mitarbeiteranlage, ArbZG, Feiertage/Sonntage, manuelle Korrektur | Fragebogen mit Mehrfachauswahl (Planer 8, Mitarbeitende 6 Fragen) | FB-12 bis FB-15 |

In Runde 2 und 3 wurden bewusst **dieselben Personen** befragt, damit sich Aussagen über
die Zeit vergleichen lassen. Ausgewertet wird je Frage und Gruppe durch Auszählen
(z. B. „2 von 2 Planern“). Widersprüche zwischen Personen werden vom Product Owner
mit Begründung entschieden und hier festgehalten.

## 2 Befragte

| ID | Rolle | Branche und Größe | Methode | Datum | Dauer | Durchgeführt von |
|---|---|---|---|---|---|---|
| FB-01 | Planer 1 | Einzelhandel, 16–30 MA | Fragebogen | 08.10.2026 | 20 min | Anil |
| FB-02 | Planer 2 | Einzelhandel, 6–15 MA | Interview live | 09.10.2026 | 20 min | Asif |
| FB-03 | Mitarbeiter 1 | Gastronomie, Vollzeit | Fragebogen | 09.10.2026 | 15 min | Anil |
| FB-04 | Mitarbeiter 2 | Einzelhandel, Vollzeit | Fragebogen | 09.10.2026 | 10 min | Anil |
| FB-05 | Mitarbeiter 3 | Einzelhandel, Studierend | Telefoninterview | 12.10.2026 | 10 min | Asif |
| FB-06 | Planer 3 | Einzelhandel, 6–15 MA | Fragebogen | 12.10.2026 | 15 min | Mahdi |
| FB-07 | Mitarbeiter 4 | Werkstudent | Fragebogen | 13.10.2026 | 10 min | Bennet |
| FB-08 | Planer 1 (wie FB-01) | Einzelhandel, 16–30 MA | Fragebogen mit Prototyp | 26.10.2026 | – | Mahdi |
| FB-09 | Mitarbeiter 5 | Einzelhandel, Vollzeit | Fragebogen mit Prototyp | 26.10.2026 | – | Mahdi |
| FB-10 | Planer 2 (wie FB-02) | Einzelhandel, 5–15 MA | Fragebogen mit Prototyp | 26.10.2026 | – | Asif |
| FB-11 | Mitarbeiter 6 | Einzelhandel, Vollzeit | Fragebogen mit Prototyp | 26.10.2026 | – | Asif |
| FB-12 | Planer 1 (wie FB-01, FB-08) | Einzelhandel, 16–30 MA | Fragebogen zum Sprint-1-Inkrement | 09.11.2026 | 20 min | Anil |
| FB-13 | Mitarbeiter 5 (wie FB-09) | Einzelhandel, Vollzeit | Fragebogen zum Sprint-1-Inkrement | 09.11.2026 | 20 min | Anil |
| FB-14 | Planer 2 (wie FB-02, FB-10) | Einzelhandel, 5–15 MA | Fragebogen zum Sprint-1-Inkrement | 09.11.2026 | 20 min | Asif |
| FB-15 | Mitarbeiter 6 (wie FB-11) | Einzelhandel, Vollzeit | Fragebogen zum Sprint-1-Inkrement | 09.11.2026 | 20 min | Asif |

**Einschränkungen:** Die Planer kommen ausschließlich aus dem Einzelhandel; die meisten
Rückmeldungen kamen als Fragebogen. Zu den Planerfragen der Runde 1 liegen keine
Originalnotizen vor. Runde 3 hat nur zwei Planer – bei 1 : 1-Widersprüchen entscheidet
der Product Owner (Abschnitt 4).

## 3 Ergebnisse und Konsequenzen

### Runde 1 – Erhebung (FB-01 bis FB-07)

| Quelle | Rückmeldung | Konsequenz | Umsetzung |
|---|---|---|---|
| Planer (FB-01/02/06), 3 von 3 | Priorität 1–3 je Slot „sehr sinnvoll“ | REQ-06, REQ-08 (MVP) | Prototyp, PR #1 |
| Planer (FB-01/02/06), 3 von 3 | Arbeitszeitgesetz zwingend | REQ-12 → nach Feedback P2 Rahmenbedingung RB-01 | PR #31 |
| Planer (FB-01/02/06), 3 von 3 | Plan muss manuell korrigierbar sein | REQ-11 Must, Sprint 1 | in Arbeit (Bennet, #2) |
| Planer (FB-01/02/06) | faire Rotation gewünscht | REQ-16 Fairness-Historie (später) | Backlog #7 |
| Planer (FB-01/02/06) | Zustimmung von Geschäftsführung/Zentrale nötig | REQ-18 Genehmigung (Could), RB-04 | Backlog #9 |
| Mitarbeitende (FB-03/04/05/07), 4 von 4 | Smartphone-Nutzung | QR-02 mobile Eingabe ab 360 px | Prototyp, UI-Test |
| Mitarbeitende (FB-03/04/05/07), 3 von 4 | Verfügbarkeiten nur für den Chef, Datenschutz | QR-03 Zugriffsschutz, QR-04 ohne Pflichtgründe, RB-02 | Prototyp, Tests |
| Mitarbeitende (FB-03/04/05/07) | Plan 1–2 Wochen vorher; Frist 2–4 Wochen vorher | REQ-05 Abgabefrist, REQ-15 Veröffentlichung | PR #29 (Frist) |
| Alle (FB-01 bis FB-07) | Schichttausch und Krankmeldung fehlen | REQ-19, REQ-20 (später) | Backlog #10, #11 |

### Runde 2 – Prototyp (FB-08 bis FB-11)

| Quelle | Rückmeldung | Konsequenz | Umsetzung |
|---|---|---|---|
| Planer (FB-08, FB-10) | sonntags gelegentlich geöffnet | REQ-22 Öffnungstage (neu, Sprint 1) | PR #32 |
| Planer (FB-08, FB-10), 1 : 1 | Plan nach Frist **bzw.** erst wenn alle abgegeben haben | ABW-01 entschieden: Frist bleibt Soll, zusätzlich frühere Erzeugung bei vollständiger Abgabe (REQ-05 AK 4) | PR #29 |
| Planer (FB-08, FB-10) | nächste Funktionen: ArbZG (5 Punkte), Veröffentlichung, manuelle Korrektur (je 3) | Sprint 1 bestätigt (RB-01, REQ-11); REQ-15 zuerst in Sprint 2 | PR #31, #2 |
| Mitarbeitende (FB-09, FB-11) | Monatseingabe dauert über 10 Minuten | REQ-23 Wochenmuster (neu); QR-05 im Nutzertest messen | Backlog #13 (Sprint 2) |
| Mitarbeitende (FB-09, FB-11) | keine Gründe, nur Chef sieht Angaben „sehr wichtig“ | QR-03, QR-04, RB-02 bestätigt | Prototyp |
| Planer (FB-08, FB-10) | Planansicht, unbesetzte Schichten, Bedarf verständlich | REQ-04, REQ-09, REQ-10 validiert | Prototyp |

### Runde 3 – Sprint-1-Inkrement (FB-12 bis FB-15)

**Planer (FB-12, FB-14)**

| Frage | FB-12 (Planer 1) | FB-14 (Planer 2) | Ergebnis | Konsequenz |
|---|---|---|---|---|
| Abgabefrist mit Sperre und früherer Erzeugung | passt genau so | passt genau so | 2 von 2 bestätigt | ABW-01 validiert (PR #29) |
| Frist vor Monatsbeginn | 7 Tage | 14 Tage | unterschiedlich | keine Änderung: Frist bleibt frei wählbar (REQ-05) |
| Mitarbeitende anlegen (Vertragsart, Stunden, Qualifikationen) | reicht so | reicht so | 2 von 2 bestätigt | ABW-02 validiert (PR #30) |
| ArbZG-Prüfung in der Planerzeugung (unbesetzt statt Verstoß) | genau richtig | genau richtig | 2 von 2 bestätigt | RB-01 als harte Regel validiert (PR #31) |
| Feiertage markiert, Sonntage einzeln öffnen | passt | passt | 2 von 2 bestätigt | RB-03 und REQ-22 validiert (PR #31, #32) |
| Manuelle Korrektur mit Regelverstoß | **komplett blockieren** | **Warnung, Änderung möglich** | Widerspruch 1 : 1 | PO-Entscheidung E-01 (Abschnitt 4) → REQ-11 |
| Ausprobieren im eigenen Betrieb | ja | ja | 2 von 2 positiv | – |
| Was fehlt für den echten Einsatz? | keine Angabe | „nichts“ | – | – |

**Mitarbeitende (FB-13, FB-15)**

| Frage | FB-13 (Mitarbeiter 5) | FB-15 (Mitarbeiter 6) | Ergebnis | Konsequenz |
|---|---|---|---|---|
| Sperre nach Fristablauf | fair | fair, wenn ich vorher erinnert werde | 2 von 2 akzeptiert | REQ-24 Erinnerung (neu, #33) |
| Kanal für Erinnerung | Push-Nachricht | E-Mail | beide Kanäle | REQ-24 mit Kanalwahl |
| Keine Einteilung bei < 11 h Ruhezeit | möchte selbst entscheiden | gut so | 1 : 1 | PO-Entscheidung E-02: keine Änderung (RB-01) |
| Information über Änderungen des Chefs | ja, gesammelt | ja, sofort | 2 von 2 gewünscht | REQ-25 Benachrichtigung mit Einstellung (neu, #34) |
| Lieber als bisheriges Verfahren | eher ja | ja | 2 von 2 positiv | – |
| Weitere Wünsche | „bis jetzt gar nicht“ | „nichts“ | – | – |

## 4 Entscheidungen des Product Owners

**E-01 Manuelle Korrektur bei Regelverstoß (09.11.2026, FB-12 vs. FB-14)**
Gesetzliche Verstöße (RB-01) werden bei der manuellen Korrektur **blockiert**; weiche
Hinweise (Person nicht verfügbar, nur Priorität 3, Urlaub, fehlende Qualifikation)
erscheinen als **Warnung**, die Änderung ist möglich.
*Begründung:* RB-01 ist eine nicht verhandelbare Rahmenbedingung; beide Planer halten
die harte Prüfung bei der Planerzeugung für „genau richtig“. Planer 1 ist damit vollständig,
Planer 2 für alle zulässigen Änderungen erfüllt. *Folge:* zwei zusätzliche
Akzeptanzkriterien in REQ-11 (Kommentar in Issue #2).

**E-02 Ruhezeit selbst bestimmen (09.11.2026, FB-13)**
Der Wunsch, trotz weniger als 11 Stunden Ruhezeit eingeteilt zu werden, wird **nicht
umgesetzt**. *Begründung:* § 5 ArbZG gilt zwingend; Beschäftigte können darauf nicht
verzichten. Die Rückmeldung bleibt hier dokumentiert; RB-01 bleibt unverändert.

**E-03 Neue Anforderungen aus Runde 3 (09.11.2026)**
REQ-24 „Erinnerung vor Ablauf der Abgabefrist“ (Should, Sprint 3, #33) und
REQ-25 „Benachrichtigung bei Planänderungen“ (Could, später nach REQ-15, #34).

## 5 Rückverfolgbarkeit Feedback → Anforderung → Umsetzung → Test (Sprint 1)

| Feedback | Anforderung | Pull Request | Tests (Auswahl, `apps/planning/tests.py`) |
|---|---|---|---|
| FB-03/04/05/07, FB-08/10 | REQ-05, REQ-07 AK 2 (ABW-01) | #29 | `DeadlineTests` (8 Tests) |
| FB-01/02/06 | REQ-02 (ABW-02) | #30 | `EmployeeManagementTests` (5 Tests) |
| FB-01/02/06, Feedback P2 | RB-01, RB-03 | #31 | `ArbZGRuleTests`, `ArbZGPlanningTests`, `HolidayCalendarTests` |
| FB-08, FB-10 | REQ-22 | #32 | `OpeningDayTests` (4 Tests) |
| FB-01/02/06, FB-12/14 | REQ-11 (+ E-01) | in Arbeit | folgt mit dem PR zu #2 |
| FB-13, FB-15 | REQ-24, REQ-25 | – | Backlog |

Die vollständige Liste aller Anforderungen mit Quellen steht im Anforderungsdokument
(Abschnitt 10, Rückverfolgbarkeit).
