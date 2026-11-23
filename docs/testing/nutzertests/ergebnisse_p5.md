# Ergebnisse Akzeptanztests mit Nutzenden – Durchgang P5

Erfasst von: Muhammed Asif Shahul Hameed (Anforderungen) · QS: Anil Duth · Stand: 23.11.2026 · Testplan: `testplan_nutzertests.md` · Testfälle: TC-M-01 bis TC-M-05 (`testfaelle.md`, Abschnitt 5)

Umgesetzt wurde das Feedback aus P4: Statt Fragebögen zu Screenshots haben reale Planerinnen, Planer und Mitarbeitende konkrete Aufgaben in der Online-Demo gelöst. Dieses Dokument enthält ausschließlich die tatsächlich zurückgemeldeten Werte; Abweichungen vom Testplan und ein Fehler in der Durchführung sind in Abschnitt 5 offen dokumentiert.

## 1 Durchführung

| Kennung | Rolle | Betrieb (pseudonymisiert in `feedback.md`) | FB-Nr. | Betreut von | Demokonto / Monat | Gerät |
|---|---|---|---|---|---|---|
| NT-P1 | Planung | Einzelhandel (wie FB-02) | FB-16 | Asif | nora.krueger / Dezember 2026 | Laptop, Chrome |
| NT-M1 | Mitarbeitende | Einzelhandel (wie FB-11) | FB-17 | Asif | mia.hansen / Dezember 2026 | iPhone, Safari |
| NT-P2 | Planung | Einzelhandel (wie FB-01) | FB-18 | Anil | nora.krueger / Januar 2027 | Laptop, Chrome |
| NT-M2 | Mitarbeitende | Einzelhandel (wie FB-09) | FB-19 | Anil | tom.weber / Januar 2027 | iPhone, Safari |
| NT-P3 | Planung | Dienstleistung (neu) | FB-20 | Bennet | nora.krueger / Januar 2027 | Laptop, Chrome |
| NT-M3 | Mitarbeitende | Dienstleistung (wie FB-07) | FB-21 | Bennet | tom.weber / Januar 2027 | Laptop, Chrome |

Die Tests liefen unmoderiert mit dem Aufgabenblatt (Word) zwischen dem 20. und 23.11.2026. Der dritte Betrieb (NT-P3, NT-M3) war im Testplan nicht vorgesehen und wurde zusätzlich aufgenommen, um die bisher reine Einzelhandels-Stichprobe zu erweitern. Er nutzte dieselben Demokonten und denselben Monat wie NT-P2/NT-M2 (siehe Abschnitt 5). Die Demo war bei allen Durchläufen erreichbar; keine Person meldete eine Sperre oder einen Ladefehler.

## 2 Aufgabenergebnisse

Dauer aus den eingetragenen Uhrzeiten (Ende − Beginn); SEQ = Single Ease Question, 1 = sehr schwer … 7 = sehr leicht.

| Testfall | Aufgabe | NT-P1 / NT-M1 | NT-P2 / NT-M2 | NT-P3 / NT-M3 | Erfolg (selbst) |
|---|---|---|---|---|---|
| TC-M-03 | P1 Bedarf eintragen und auf den Monat übernehmen | 20 min · SEQ 5 | 30 min · SEQ 4 | 10 min · SEQ 4 | 3 von 3 |
| TC-M-04 | P2 Plan erzeugen und Lücke manuell schließen | 10 min · SEQ 6 | 25 min · SEQ 4 | 5 min · SEQ 6 | 3 von 3 |
| TC-M-05 | P3 Plan veröffentlichen | 10 min · SEQ 6 | 10 min · SEQ 5 | 10 min · SEQ 5 | 3 von 3 |
| TC-M-01 | M1 Verfügbarkeiten (10 Slots) eintragen und abgeben | 10 min · SEQ 6 | 5 min · SEQ 5 | 5 min · SEQ 6 | 3 von 3 |
| TC-M-02 | M2 eigenen Schichtplan finden | nicht auswertbar | nicht auswertbar | nicht auswertbar | siehe Abschnitt 5 |

**Kontrolle in der Demo:** NT-P2 nannte die besetzte Lücke konkret (Spätschicht 15.01.2027, 14–20 Uhr, Emma Lange); das ist genau die vorbereitete Lückenschicht. Die übrigen Erfolgsangaben beruhen auf Selbstauskunft; eine Kontrolle der Demo-Daten je Person war nicht mehr eindeutig möglich, weil NT-P2 und NT-P3 im selben Monat gearbeitet haben.

## 3 Qualitätsanforderungen und Gesamturteil

| Anforderung / Kennzahl | Messwerte | Ziel | Ergebnis |
|---|---|---|---|
| QR-05 Eingabeaufwand (M1, 10 Slots) | 10 / 5 / 5 min | ≤ 5 min | **2 von 3 erfüllt** |
| QR-06 Planungsaufwand (P1 + P2 + P3) | 40 / 65 / 25 min | ≤ 30 min | **1 von 3 erfüllt – nicht erfüllt** |
| SEQ über alle 12 auswertbaren Aufgaben | 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 6 | Median ≥ 5 | **Median 5 – erfüllt** |
| UMUX-LITE „Funktionen erfüllen meine Anforderungen“ | 5, 6, 4 (Planung) · 5, 6, 6 (Mitarbeitende) | Mittelwert ≥ 5 | **5,3 – erfüllt** |
| UMUX-LITE „einfach zu benutzen“ | 6, 5, 5 (Planung) · 6, 5, 6 (Mitarbeitende) | Mittelwert ≥ 5 | **5,5 – erfüllt** |

**Bewertung:** Alle zwölf auswertbaren Aufgaben wurden beim ersten Kontakt ohne Hilfe gelöst, und das Gesamturteil liegt über dem Zielwert. Die Schwäche liegt in der Orientierung beim ersten Durchgang: Die Aufgabe P1 (Bedarf) ist mit SEQ 4–5 die schwierigste, und QR-06 wird in zwei von drei Fällen deutlich verfehlt. QR-06 beschreibt allerdings den regelmäßigen Monatsablauf; gemessen wurde die Erstnutzung ohne Einweisung. Deshalb wird QR-06 nach den Verbesserungen K1–K3 in P6 erneut gemessen, nicht vorzeitig als erfüllt gewertet.

## 4 Befunde und Konsequenzen

| Nr. | Person / Aufgabe | Beobachtung | Art | Konsequenz (PO-Entscheidung 23.11.2026) | Issue |
|---|---|---|---|---|---|
| K1 | NT-P2 / P1 | Nach dem Wechsel der Woche muss zusätzlich „Anzeigen“ geklickt werden; die Ansicht sollte sich direkt aktualisieren. | Bedienproblem | Wochenauswahl aktualisiert die Ansicht sofort (Should, vor P6) | #50 |
| K2 | NT-P1, NT-P2, NT-P3 / P1, P2; NT-M2 / M1 | „Musste erst einmal komplett durchgucken, wo was kommt“; Plan und unbesetzte Schichten zunächst nicht gefunden; Ort der Verfügbarkeitseingabe anfangs unklar. | Bedienproblem, QR-06 verfehlt | Startseite mit „Nächste Schritte“ (Bedarf → Erzeugen → Unbesetzt → Veröffentlichen) bzw. direktem Link zur Verfügbarkeit (Should, vor P6) | #51 |
| K3 | NT-P2 / P1 | Unklar, ob die Gesamtzahl reicht und wie die Kassenqualifikation angegeben wird. | Bedienproblem | Erklärender Hinweis im Bedarfsformular zu Gesamtzahl und Mindestqualifikationen (Should, vor P6) | #52 |
| K4 | NT-P2 / P3 | Veröffentlichen braucht mehrere Schritte. | Hinweis | **Keine Änderung:** Die Vorschau mit Bestätigung verhindert versehentliches Veröffentlichen unvollständiger Pläne (REQ-15); beide anderen Planungspersonen fanden P3 unproblematisch. | – |
| K5 | NT-M3 / Abschluss | Wunsch: Schichten automatisch in den eigenen Kalender übernehmen. | Wunsch | Neue Anforderung REQ-26 Kalenderexport (Could, später) | #53 |
| K6 | NT-P3 / Abschluss | „Ich müsste es in der Praxis testen“ (UMUX 4). | Hinweis | P6: ein vollständiger Planungsdurchlauf mit realitätsnahen Daten | – |

## 5 Abweichungen und Fehler in der Durchführung

**M2 (TC-M-02) nicht auswertbar.** Die drei Mitarbeitenden-Bögen enthielten im ersten Durchgang wörtlich identische Antworten (gleiche Tage, gleiche Schreibweise), obwohl zwei verschiedene Konten mit unterschiedlichen Schichten verwendet wurden. Eine telefonische Nachfrage am 23.11.2026 ergab, dass die Antworten aus der Erinnerung gegeben und von der betreuenden Person eingetragen wurden, nicht durch Nachsehen in der App. Damit prüfen sie die Aufgabe „Schichtplan in der App finden“ nicht; zudem können NT-M2 und NT-M3 mit demselben Konto nicht zwei verschiedene richtige Antworten haben. Beide Durchgänge werden deshalb nicht gewertet. M2 wird mit Screenshot als Nachweis wiederholt; NT-M3 erhält dafür ein eigenes Konto (lea.meyer). Ergebnis: Nachtrag in Abschnitt 6 bzw. vollständige Wiederholung im Nutzertest P6.

**Gemeinsamer Testmonat.** NT-P2 und NT-P3 haben im selben Monat (Januar 2027) und mit demselben Konto gearbeitet, ebenso NT-M2 und NT-M3. Wer später testete, fand bereits eingetragenen Bedarf bzw. einen erzeugten Plan vor. Die kurzen Zeiten von NT-P3 (25 min insgesamt) sind daher nur eingeschränkt mit NT-P1 und NT-P2 vergleichbar.

**Konsequenz für P6:** Jede Testperson erhält ein eigenes Konto und einen eigenen Monat bzw. eigenen Testbetrieb (seit PR #46 möglich); die Betreuung gibt keine Beispielantworten vor; Antworten zu Wissensfragen werden per Screenshot belegt.

## 6 Nachtrag M2 (Wiederholung)

| Person | Konto | Belegt durch | Antwort korrekt? | Dauer | SEQ |
|---|---|---|---|---|---|
| NT-M1 | mia.hansen | | | | |
| NT-M2 | tom.weber | | | | |
| NT-M3 | lea.meyer | | | | |
