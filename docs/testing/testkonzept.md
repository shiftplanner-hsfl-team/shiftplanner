# Testkonzept ShiftPlanner

Verantwortlich: Anil Duth (Qualitätssicherung) · Mitwirkung: Muhammed Asif Shahul Hameed, Bennet Schalow, Mahdi Fazeli · Stand: 18.11.2026 · Version 1.0

Dieses Dokument legt fest, wie ShiftPlanner geprüft wird: auf welchen Teststufen, mit welchen Verfahren und Werkzeugen, nach welchen Kriterien ein Stand als „getestet“ gilt und wie gefundene Fehler verfolgt werden. Es ist die Grundlage für den Testfallkatalog (`testfaelle.md`), die Review- und Inspektionsrichtlinie (`review_richtlinie.md`) und die Testberichte (`teststand_*.md`). Aufbau und Begriffe folgen dem ISTQB-Lehrplan (ISTQB 2023) und der Normenreihe ISO/IEC/IEEE 29119 (2021).

## 1 Testobjekt und Ziele

Testobjekt ist die Django-Webanwendung im Repository `shiftplanner-hsfl-team/shiftplanner` (Branch `main`) mit allen bis Sprint 1 umgesetzten Anforderungen: REQ-01 bis REQ-11, REQ-14, REQ-15 und REQ-22, die Qualitätsanforderungen QR-01 bis QR-07 sowie die Rahmenbedingungen RB-01 bis RB-03 (Umsetzungsstand siehe `docs/requirements/mvp.md`). Funktionen späterer Sprints werden in diesen Katalog aufgenommen, sobald sie umgesetzt sind.

Die Tests verfolgen vier Ziele. Erstens soll jede umgesetzte Anforderung und jedes ihrer Akzeptanzkriterien durch mindestens einen Testfall mit eindeutigem Testorakel nachgewiesen sein. Zweitens sollen die fachlich kritischen Regeln – Prioritätsreihenfolge, keine Überschneidungen, Urlaub, Qualifikationen und Arbeitszeitgesetz – so geprüft werden, dass ein Planungsfehler nicht unbemerkt in einen veröffentlichten Plan gelangt. Drittens müssen alle automatisierten Tests bei jedem Push wiederholbar und ohne manuelle Eingriffe laufen. Viertens soll die Anwendung von realen Planerinnen, Planern und Mitarbeitenden mit echten Aufgaben bedient werden, damit nicht nur geprüft wird, ob sie richtig rechnet, sondern auch, ob sie verständlich ist.

## 2 Teststufen

Die Teststufen folgen der Testpyramide (Cohn 2009): viele schnelle Unit-Tests an der Basis, darüber Komponententests mit Datenbank, an der Spitze wenige, aber realistische Akzeptanz- und Oberflächentests.

| Stufe | Kürzel | Was wird geprüft? | Testbasis | Umsetzung | Ort im Repository |
|---|---|---|---|---|---|
| Unit-Test | TC-U | Einzelne Funktionen ohne Datenbank und ohne HTTP: ArbZG-Regeln, Feiertagsberechnung, Überschneidungsprüfung, Zuordnungsalgorithmus | Detailentwurf, Docstrings, RB-01/RB-03 | `django.test.SimpleTestCase` | `tests/unit/` |
| Komponententest | TC-K | Die App `planning` als Komponente: Views, Formulare, Services und Modelle zusammen gegen eine Testdatenbank, angesprochen über den Django-Testclient | Anforderungen, Architektur, Sequenzdiagramm | `django.test.TestCase` | `apps/planning/tests.py` |
| Akzeptanztest (automatisiert) | TC-A | Je ein Testfall pro Akzeptanzkriterium der User Stories im Format Gegeben/Wenn/Dann | User Stories und Use Cases UC-01 bis UC-05 | `django.test.TestCase`, Gegeben/Wenn/Dann im Docstring | `tests/acceptance/` |
| Oberflächentest (Ende-zu-Ende) | TC-UI | Vollständige Abläufe im echten Browser, inkl. 360-px-Ansicht und Tastaturbedienung | UC-01 bis UC-05, QR-02, QR-03, QR-07 | Playwright mit Chromium gegen `StaticLiveServerTestCase` | `tests/ui/` |
| Akzeptanztest mit Nutzenden (manuell) | TC-M | Reale Planerinnen, Planer und Mitarbeitende lösen Aufgaben in der Online-Demo; gemessen werden Erfolg, Dauer und Probleme | Use Cases, QR-05, QR-06 | Aufgabenblatt und Beobachtungsprotokoll | `docs/testing/nutzertests/` |

Nichtfunktionale Anforderungen werden auf der Stufe geprüft, auf der sie sich am genauesten messen lassen: QR-01 (Laufzeit der Planerzeugung) als Komponententest mit Zeitmessung, QR-02 (360 px) und QR-07 als Oberflächentest, QR-03 (HTTP 403) als Komponenten- und Oberflächentest, QR-04 durch Inspektion des Datenmodells und QR-05/QR-06 (Bearbeitungszeiten) in den Tests mit Nutzenden.

Die bestehenden 85 Tests in `apps/planning/tests.py` bleiben als Komponententests erhalten; ihre Zuordnung zu Stufe, Anforderung und Orakel erfolgt im Testfallkatalog. Neu hinzu kommen reine Unit-Tests für `rules.py` und die Zuordnungsfunktionen in `services.py`, die bisher nur indirekt über die Datenbank geprüft werden, sowie ein eigener Ordner mit Akzeptanztests, der die Akzeptanzkriterien eins zu eins abbildet.

## 3 Testentwurfsverfahren

Testfälle werden nicht frei erfunden, sondern systematisch abgeleitet (Myers et al. 2011; Spillner/Linz 2019).

**Äquivalenzklassen und Grenzwerte** werden überall dort eingesetzt, wo Eingaben Wertebereiche haben. Beispiele sind die Priorität (0 = nicht verfügbar, 1–3 gültig, 4 und Text ungültig), die Abgabefrist (am Fristtag noch offen, am Folgetag gesperrt), die tägliche Höchstarbeitszeit (genau 10 Stunden erlaubt, darüber nicht), die Ruhezeit (genau 11 Stunden erlaubt, 10:59 nicht), die Wochenhöchstarbeitszeit von 48 Stunden und die Bildschirmbreite von 360 px.

**Entscheidungstabellen** werden für die Frage verwendet, ob eine Person für eine Schicht infrage kommt. Die Bedingungen sind: verfügbar mit Priorität 1–3, nicht im Urlaub, Qualifikation vorhanden, keine Überschneidung, keine ArbZG-Verletzung. Jede relevante Kombination wird mindestens einmal geprüft.

**Zustandsbasierter Test** wird für den Lebenszyklus eines Planungsmonats eingesetzt: Eingabe offen → Frist abgelaufen → Plan erzeugt → korrigiert → veröffentlicht → erneut erzeugt. Geprüft wird, dass nur die erlaubten Übergänge möglich sind, etwa dass eine Korrektur einen bereits veröffentlichten Plan nicht verändert.

**Strukturbasierte Abdeckung** wird mit `coverage.py` gemessen, und zwar als Anweisungs- und Zweigabdeckung. Die Messung dient nicht als Selbstzweck, sondern zeigt, welche Zweige noch durch keinen Test ausgeführt werden; diese Lücken werden im Testbericht benannt und entweder durch Tests geschlossen oder begründet.

## 4 Statische Qualitätssicherung

Neben den dynamischen Tests wird der Code auch ohne Ausführung geprüft. Automatisch geschieht das durch Ruff, das bei jedem Push die in `CONTRIBUTING.md` begründeten Coding-Standards durchsetzt (PEP 8, Docstrings, typische Fehlerquellen, zyklomatische Komplexität ≤ 10). Manuell geschieht es durch Code-Reviews jedes Pull Requests vor dem Merge und durch Inspektionen der Dokumente (Anforderungen, Entwurfsdiagramme, Testfälle) nach dem Vorbild von Fagan (1976). Ablauf, Rollen, Prüflisten und Protokollvorlagen stehen in der Review- und Inspektionsrichtlinie.

## 5 Testfallschablone

Jeder Testfall im Katalog enthält dieselben Felder, damit er für Außenstehende nachvollziehbar und wiederholbar ist.

| Feld | Inhalt |
|---|---|
| ID | Stufenkürzel und laufende Nummer, z. B. `TC-U-07` |
| Titel | Kurzbeschreibung des geprüften Verhaltens |
| Stufe | Unit, Komponente, Akzeptanz, UI oder manuell |
| Anforderung | REQ-, QR- oder RB-Nummer inkl. Akzeptanzkriterium (AK) |
| Vorbedingung / Testdaten | Ausgangszustand der Datenbank, angemeldete Rolle, festes Datum |
| Eingabe / Schritte | Konkrete Eingabewerte bzw. Bedienschritte |
| Erwartetes Ergebnis (Orakel) | Beobachtbares Ergebnis, an dem bestanden/fehlgeschlagen eindeutig entschieden wird |
| Verfahren | Äquivalenzklasse, Grenzwert, Entscheidungstabelle, Zustand oder Ablauf |
| Umsetzung | Testmethode (`Datei::Klasse::Methode`) oder „manuell“ |
| Ergebnis | bestanden / fehlgeschlagen / blockiert mit Datum und Lauf |
| Fehler | Verweis auf das Bug-Issue, falls fehlgeschlagen |

## 6 Testumgebung und Testdaten

Automatisierte Tests laufen lokal mit `python manage.py test` und in GitHub Actions (`.github/workflows/tests.yml`) auf Ubuntu. Die Backendtests laufen sowohl gegen SQLite als auch gegen PostgreSQL 18, weil die Online-Demo PostgreSQL nutzt und der Fehler aus PR #42 nur dort auftrat. Die Oberflächentests verwenden Chromium über Playwright; Screenshots werden als Artefakt des CI-Laufs gespeichert.

Damit Tests wiederholbar sind, sind Datum und Daten fest vorgegeben. Das „heutige“ Datum wird über `SHIFTPLANNER_TODAY` gesetzt, sodass Fristen unabhängig vom Ausführungstag gleich bewertet werden. Testdaten entstehen entweder im `setUp` des jeweiligen Tests oder über das Kommando `seed_demo`, das immer denselben Demobetrieb mit denselben Personen, Schichtvorlagen und Verfügbarkeiten erzeugt. Die Zuordnung ist deterministisch, sodass gleiche Eingaben immer zum gleichen Plan führen; das wird selbst getestet.

Manuelle Tests mit Nutzenden laufen in der Online-Demo (https://shiftplanner-demo-93eu.onrender.com) mit eigens angelegten Testkonten. Echte Personendaten der Teilnehmenden werden nicht eingegeben.

## 7 Eingangs- und Endekriterien

Ein Pull Request darf in die Tests und in das Review gehen, wenn er ein verknüpftes Issue hat, die Checkliste der PR-Vorlage ausgefüllt ist und Ruff lokal keinen Befund meldet.

Ein Pull Request darf gemergt werden, wenn alle automatisierten Tests auf beiden Datenbanken und im Browser grün sind, für neues Verhalten Tests ergänzt wurden, mindestens ein anderes Teammitglied den Code nach der Review-Richtlinie freigegeben hat und kein offener Fehler der Schwere „kritisch“ oder „hoch“ durch ihn entsteht.

Ein Stand gilt zur Präsentation bzw. Abgabe als getestet, wenn alle Testfälle des Katalogs ausgeführt und dokumentiert sind, alle Akzeptanzkriterien der umgesetzten Anforderungen bestanden sind, die Zweigabdeckung der App `planning` mindestens 90 % beträgt, kein Fehler der Schwere „kritisch“ oder „hoch“ offen ist und die verbleibenden Fehler mit Begründung im Testbericht stehen.

## 8 Fehlermanagement

Jede Abweichung vom erwarteten Ergebnis – aus automatisierten Tests, Reviews, Inspektionen oder Tests mit Nutzenden – wird als GitHub-Issue mit der Vorlage „Bug“ und dem Label `bug` erfasst. Ein Bug-Issue enthält die Schritte zur Reproduktion, das erwartete und das tatsächliche Ergebnis, die Umgebung, die betroffene Anforderung und die Schwere.

| Schwere | Bedeutung | Beispiel |
|---|---|---|
| kritisch | Datenverlust, Datenschutzverletzung oder falscher veröffentlichter Plan | Mitarbeitende sehen fremde Verfügbarkeiten |
| hoch | Kernfunktion bricht ab, keine Umgehung | Serverfehler 500 bei der manuellen Korrektur |
| mittel | Funktion eingeschränkt, Umgehung möglich | falsche Fehlermeldung bei ungültiger Eingabe |
| gering | kosmetisch oder nur in der Testumgebung | sporadisch fehlschlagender UI-Test |

Ein Fehler durchläuft die Zustände offen → in Arbeit (Branch `fix/…`) → behoben (Pull Request mit „Fixes #…“) → geschlossen. Für jeden behobenen Fehler wird ein Regressionstest ergänzt, der vor der Korrektur fehlschlägt und danach besteht; erst dann wird das Issue geschlossen.

## 9 Rollen

Anil Duth verantwortet als Lead der Qualitätssicherung dieses Konzept, den Testfallkatalog und die Testberichte und committet die QS-Dokumente. Bennet Schalow schreibt als Lead der Implementierung die Tests zu seinem eigenen Code und reviewt Test-Pull-Requests. Muhammed Asif Shahul Hameed führt als Product Owner die Akzeptanztests mit Nutzenden durch und prüft, ob die Testorakel den Akzeptanzkriterien entsprechen. Mahdi Fazeli inspiziert als Lead von Architektur und Entwurf die Entwurfsdiagramme gegen den Code. Die Rollen bezeichnen Verantwortung, nicht alleinige Arbeit; alle Teammitglieder reviewen und testen.

## 10 Zeitplan

| Datum | Aktivität |
|---|---|
| 19.11. | Testkonzept, Testfallkatalog für den bestehenden Stand |
| 20.–22.11. | Unit- und Akzeptanztests ergänzen, Abdeckungsmessung in CI |
| 20.–23.11. | Pilot der Tests mit Nutzenden (je zwei Planer/Mitarbeitende) |
| 21.–22.11. | Review von PR #42 und Inspektion der Entwurfsdiagramme nach Richtlinie |
| 23.11. | Gesamtlauf, Testbericht P5 |
| 25.11. | P5 – Qualität & Tests |
| 02.12. | Tests mit Nutzenden (vollständig), Testbericht P6 |
| 16.12. | Abschließender Testbericht für `testing.pdf` |

## 11 Ausgangslage (18.11.2026)

Auf `main` bestehen 85 Komponententests, die alle bestehen, sowie 8 Oberflächentests mit Chromium. Die gemessene Abdeckung der App `planning` (ohne Migrationen und Testdateien) liegt bei 94 % (Anweisungen und Zweige kombiniert, `coverage run --branch`). Offen ist der sporadisch fehlschlagende Oberflächentest #39. Reine Unit-Tests ohne Datenbank, ein ausgewiesener Akzeptanztest je Akzeptanzkriterium, die Abdeckungsmessung in CI und ausgefüllte Review-Protokolle fehlen bisher; sie werden bis P5 ergänzt.

## Literatur

- Cohn, M. (2009): *Succeeding with Agile: Software Development Using Scrum*. Addison-Wesley.
- Fagan, M. E. (1976): Design and code inspections to reduce errors in program development. In: *IBM Systems Journal* 15 (3), S. 182–211.
- ISO/IEC/IEEE 29119-3 (2021): *Software and systems engineering – Software testing – Part 3: Test documentation*.
- ISTQB (2023): *Certified Tester Foundation Level Syllabus*, Version 4.0. International Software Testing Qualifications Board.
- Myers, G. J.; Badgett, T.; Sandler, C. (2011): *The Art of Software Testing*. 3. Aufl., Wiley.
- Nielsen, J.; Landauer, T. K. (1993): A mathematical model of the finding of usability problems. In: *Proc. INTERACT/CHI '93*, S. 206–213.
- Spillner, A.; Linz, T. (2019): *Basiswissen Softwaretest*. 6. Aufl., dpunkt.verlag.
