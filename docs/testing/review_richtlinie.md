# Review- und Inspektionsrichtlinie ShiftPlanner

Verantwortlich: Anil Duth (Qualitätssicherung); ab 23.11.2026 vertretungsweise Muhammed Asif Shahul Hameed · Stand: 23.11.2026 · Version 1.0 · Grundlage: `testkonzept.md`, Abschnitt 4; `CONTRIBUTING.md`, Abschnitt 3

Diese Richtlinie legt fest, wie Code und Dokumente ohne Ausführung geprüft werden (statische, manuelle Qualitätssicherung). Sie ergänzt die automatische statische Analyse durch Ruff und die dynamischen Tests. Sie unterscheidet zwei Verfahren: das **Code-Review** jedes Pull Requests als leichtgewichtiges, werkzeuggestütztes Review (Modern Code Review nach Bacchelli/Bird 2013; Sadowski et al. 2018) und die **Inspektion** wichtiger Dokumente als formales Verfahren mit Rollen, Prüfliste und Protokoll (Fagan 1976; IEEE 1028-2008).

## 1 Was wird wie geprüft?

| Prüfgegenstand | Verfahren | Auslöser | Prüfliste | Dokumentation |
|---|---|---|---|---|
| Jeder Pull Request (Code, Tests, Konfiguration) | Code-Review | PR geöffnet | Abschnitt 3 | Review-Kommentar im PR (Vorlage Abschnitt 3.3) |
| Pull Requests mit reiner Dokumentation | Code-Review (verkürzt) | PR geöffnet | Abschnitt 3.2 | Review-Kommentar im PR |
| Entwurfsdiagramme und Architekturbeschreibung | Inspektion | vor jeder Präsentation mit Entwurfsbezug und nach Änderungen am Datenmodell | Abschnitt 4.3 A | Protokoll `inspektion_*.md` |
| Anforderungsdokument | Inspektion | vor Abgabe; nach neuen Anforderungen | Abschnitt 4.3 B | Protokoll `inspektion_*.md` |
| Testfallkatalog und Testberichte | Inspektion | vor jeder Präsentation mit Testbezug | Abschnitt 4.3 C | Protokoll `inspektion_*.md` |

## 2 Grundregeln

Jeder Pull Request wird von mindestens einer anderen Person freigegeben; niemand mergt eigene Änderungen ohne Freigabe (Branch-Schutz auf `main`). Die Perspektive richtet sich nach der Rolle: Implementierung prüft Coding-Standards und Struktur, Architektur die Konsistenz mit dem Entwurf, Qualitätssicherung die Tests, Anforderungen die Erfüllung der Akzeptanzkriterien. Ein Review bewertet die Änderung, nicht die Person. Eine Freigabe ohne Begründung ist nicht zulässig: Der Review-Kommentar nennt, **was** geprüft wurde und **mit welchem Ergebnis** (Vorlage Abschnitt 3.3). Befunde, die nicht im selben PR behoben werden, werden als Issue angelegt und im Kommentar verlinkt.

## 3 Code-Review

### 3.1 Ablauf

1. **Autor/in** öffnet den PR mit ausgefüllter PR-Vorlage (Issue verlinkt, Checkliste ehrlich angekreuzt) und trägt eine Reviewerin oder einen Reviewer passend zur Rolle ein.
2. **Reviewer/in** prüft innerhalb von 24 Stunden anhand der Prüfliste 3.2. Bei Code wird der Branch lokal ausgecheckt und mindestens einmal ausgeführt; reines Lesen im Browser genügt nur bei Dokumentation.
3. Konkrete Stellen werden als **Inline-Kommentar** an der betroffenen Zeile angemerkt; der zusammenfassende Review-Kommentar folgt der Vorlage 3.3.
4. Ergebnis: **Approve**, **Comment** (Fragen ohne Blockade) oder **Request changes** (Befund der Schwere „hoch“ oder „kritisch“, Abschnitt 5).
5. Gemergt wird erst bei Freigabe **und** grünem CI. Nach dem Merge wird der Branch gelöscht.

### 3.2 Prüfliste Code-Review

| Nr. | Prüfpunkt | Gilt für |
|---|---|---|
| C1 | Das verlinkte Issue bzw. die Akzeptanzkriterien werden vollständig erfüllt; nichts darüber hinaus ohne Begründung. | Code |
| C2 | Struktur entspricht der Architektur (`docs/design/architektur.md`): Views ohne Geschäftslogik, Regeln in `rules.py`/`services.py`, Abhängigkeiten nur nach unten. | Code |
| C3 | Coding-Standards aus `CONTRIBUTING.md`, Abschnitt 4: Ruff ohne Befund, sprechende Namen, Docstrings mit Ein- und Ausgaben, Komplexität ≤ 10. | Code |
| C4 | Zugriffsschutz: Jede neue View prüft Rolle und Betrieb bei GET **und** POST; CSRF-Schutz bleibt aktiv (QR-03, RB-02). | Code |
| C5 | Datenschutz: keine neuen Freitextfelder für Begründungen (QR-04), keine personenbezogenen Daten in Logs. | Code |
| C6 | Datenbank: Migration vorhanden und rückwärtskompatibel; Transaktionen bei Mehrfachänderungen; Verhalten auf PostgreSQL bedacht (vgl. DEF-01). | Code |
| C7 | Tests: Für neues Verhalten gibt es Tests auf passender Stufe; jeder behobene Fehler hat einen Regressionstest; Abdeckung bleibt ≥ 90 %. | Code |
| C8 | Fehlerfälle: ungültige Eingaben werden abgefangen, Meldungen sind auf Deutsch und verständlich. | Code |
| C9 | Dokumentation: Architektur, Diagramme, Anforderungen und Testfallkatalog sind angepasst, wenn sich Verhalten oder Datenmodell ändert. | Code, Doku |
| C10 | Inhalt fachlich richtig und mit Quellen/Daten belegt; Zahlen stimmen mit Repository bzw. CI überein. | Doku |
| C11 | Konsistenz: IDs (REQ, QR, TC, FB) und Querverweise stimmen; keine Widersprüche zu anderen Dokumenten. | Doku |

### 3.3 Vorlage Review-Kommentar

```
Review nach review_richtlinie.md (Perspektive: <Rolle>) – Ergebnis: <freigegeben | Änderungen nötig>

Geprüft:
- <Prüfpunkt Cx>: <was genau, mit welchem Ergebnis>
- Ausführung: <lokal ausgecheckt / Befehl / Testergebnis> bzw. „nur Dokumentation gelesen“
- CI: <Jobs und Status>

Befunde:
1. <Fundstelle> – <Beschreibung> – Schwere <kritisch|hoch|mittel|gering> – <im PR behoben | Issue #NN>
(oder: „keine Befunde“)
```

## 4 Inspektion

### 4.1 Rollen

| Rolle | Aufgabe | Besetzung |
|---|---|---|
| Moderation | plant die Inspektion, prüft Eingangskriterien, leitet die Sitzung, verfolgt die Nacharbeit | Qualitätssicherung (Anil; Vertretung: Asif) |
| Autor/in | stellt das Dokument bereit, beantwortet Fragen, behebt die Befunde | Verantwortliche Rolle des Dokuments (bei Abwesenheit: ihre Vertretung) |
| Inspektor/innen | prüfen das Dokument vorab einzeln anhand der Prüfliste | mindestens zwei Personen, **nicht** der Autor; mindestens eine kennt den Code |
| Protokoll | hält Befunde, Schwere und Entscheidungen fest | Moderation oder eine Inspektorin |

### 4.2 Ablauf

1. **Planung:** Moderation legt Gegenstand (Dateien, Commit-Stand), Prüfliste, Rollen und Termin fest und eröffnet ein Issue „INSP: …“.
2. **Eingangskriterien:** Das Dokument ist vollständig, versioniert und auf `main`; die Prüfliste ist gewählt.
3. **Einzelprüfung (Vorbereitung):** Jede Inspektorin prüft allein (Richtwert 30–60 Minuten) und notiert Befunde mit Fundstelle. Werkzeuggestützte Vorprüfungen (z. B. automatischer Abgleich Diagramm ↔ Code) sind zulässig, wenn sie im Protokoll als solche gekennzeichnet und von einer Inspektorin bestätigt werden.
4. **Sitzung:** Befunde werden zusammengeführt, Duplikate entfernt, Schwere festgelegt. Es werden **keine Lösungen** diskutiert, nur Befunde. Asynchron als Kommentar-Thread im Issue zulässig, wenn alle Rollen beteiligt sind.
5. **Nacharbeit:** Autor/in behebt die Befunde in einem PR, der das Inspektions-Issue verlinkt.
6. **Nachverfolgung und Endekriterium:** Moderation prüft, dass alle Befunde der Schwere „kritisch“ und „hoch“ behoben sind; die übrigen sind behoben oder als Issue mit Begründung offen. Erst dann wird das Inspektions-Issue geschlossen.

**Kennzahlen je Inspektion:** Vorbereitungszeit je Person, Anzahl Befunde je Schwere, Anzahl behobener Befunde. Sie fließen in den Testbericht und die Projektstatistik ein.

### 4.3 Prüflisten

**A Entwurf (Diagramme in `docs/design/`, `architektur.md`)**

| Nr. | Prüfpunkt |
|---|---|
| A1 | Klassendiagramm: Jede Modellklasse in `apps/planning/models.py` ist enthalten – mit Attributen, Beziehungen und Multiplizitäten; keine Klasse ohne Entsprechung im Code. |
| A2 | ER-Diagramm: Jede Tabelle der Migrationen ist enthalten – mit Primär- und Fremdschlüsseln sowie Kardinalitäten; Krähenfuß-Notation korrekt. |
| A3 | Komponentendiagramm: Module und Abhängigkeiten entsprechen der Paketstruktur; Abhängigkeiten nur in erlaubter Richtung. |
| A4 | Sequenzdiagramm: Aufrufreihenfolge entspricht `views.generate` → `services.generate_plan` → `rules`. |
| A5 | Aktivitätsdiagramm: Monatsablauf inkl. Frist, Erzeugung, Korrektur, Veröffentlichung entspricht UC-01 bis UC-05. |
| A6 | Use-Case-Diagramm: alle umgesetzten Use Cases und Akteure enthalten. |
| A7 | Text (`architektur.md`) und Diagramme widersprechen sich nicht; jede im Text genannte Klasse erscheint im Diagramm. |
| A8 | UML-Notation korrekt und einheitlich (Sichtbarkeiten, Stereotype, Pfeilarten); PNG-Exporte entsprechen den `.puml`-Quellen. |
| A9 | Entwurfsprinzipien erkennbar: Modularisierung, Information Hiding, lose Kopplung, hohe Kohäsion, klare Schnittstellen. |

**B Anforderungen (Anforderungsdokument, `docs/requirements/`)**

| Nr. | Prüfpunkt |
|---|---|
| B1 | Jede Anforderung ist eindeutig, testbar und hat Akzeptanzkriterien im Format Gegeben/Wenn/Dann. |
| B2 | Rationale, Stakeholder, Wichtigkeit und Quelle (inkl. FB-Nummer) sind angegeben. |
| B3 | Keine Widersprüche zwischen Anforderungen (z. B. REQ-10 AK 3 vs. REQ-11). |
| B4 | Umsetzungsstand in `mvp.md` stimmt mit Code und Issues überein; Abweichungen (ABW) sind begründet. |
| B5 | Rahmenbedingungen (RB) sind von Anforderungen getrennt. |

**C Testdokumente (`docs/testing/`)**

| Nr. | Prüfpunkt |
|---|---|
| C-T1 | Jede Testfall-ID im Katalog hat eine Entsprechung im Code (Methode) bzw. ein Protokoll (manuell) und umgekehrt. |
| C-T2 | Jeder Testfall hat Vorbedingung, Eingabe und eindeutiges Orakel. |
| C-T3 | Die Rückverfolgbarkeit Anforderung → Testfall ist vollständig für alle umgesetzten Anforderungen. |
| C-T4 | Zahlen im Testbericht stimmen mit dem zitierten CI-Lauf überein. |

### 4.4 Protokollvorlage

Jede Inspektion erhält ein Protokoll `docs/testing/inspektion_<gegenstand>_<datum>.md` mit: Gegenstand und Commit-Stand, Rollen, Vorbereitungszeit je Person, Befundliste (Nr., Prüfpunkt, Fundstelle, Beschreibung, Schwere, Issue, Status), Entscheidung (freigegeben / mit Auflagen / Nacharbeit) und Nachverfolgung.

## 5 Schwere von Befunden

Es gelten dieselben Stufen wie im Fehlermanagement des Testkonzepts (Abschnitt 8), übertragen auf statische Prüfungen:

| Schwere | Bedeutung bei Reviews/Inspektionen | Folge |
|---|---|---|
| kritisch | Datenschutz- oder Sicherheitslücke; falsches Verhalten im Plan | Request changes, kein Merge |
| hoch | Kernanforderung verfehlt; Dokument widerspricht dem Code in einem prüfungsrelevanten Teil | Request changes bzw. Nacharbeit vor Freigabe |
| mittel | Standard verletzt, Dokument unvollständig, Test fehlt | im PR beheben oder Issue vor Merge |
| gering | Formulierung, Formatierung, Schreibfehler | optional, Hinweis genügt |

## Literatur

- Bacchelli, A.; Bird, C. (2013): Expectations, outcomes, and challenges of modern code review. In: *Proc. ICSE 2013*, S. 712–721.
- Fagan, M. E. (1976): Design and code inspections to reduce errors in program development. In: *IBM Systems Journal* 15 (3), S. 182–211.
- IEEE Std 1028-2008: *IEEE Standard for Software Reviews and Audits*.
- Sadowski, C.; Söderberg, E.; Church, L.; Sipko, M.; Bacchelli, A. (2018): Modern code review: A case study at Google. In: *Proc. ICSE-SEIP 2018*, S. 181–190.
