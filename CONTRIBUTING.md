# Mitarbeit an ShiftPlanner

Dieses Dokument legt fest, wie das Team Code schreibt, versioniert und prüft.
Die Regeln wurden im Team vereinbart (Issue #22) und werden automatisch in
GitHub Actions geprüft. Ein Pull Request mit Regelverstoß kann nicht gemergt werden.

## 1 Branches

- `main` ist geschützt; Änderungen nur per Pull Request mit 1 Review.
- Ein Branch je Issue, Name mit Typ und ID:
  `feature/REQ-11-plan-korrigieren`, `fix/ABW-01-frist`, `docs/p4-teststand`,
  `chore/coding-standards`.

## 2 Commits

- Nachricht beginnt mit der ID aus dem Board: `REQ-08: Prioritätssortierung ergänzt`,
  `RB-01: Ruhezeitprüfung ergänzt`, `QS: Review PR #18`.
- Kleine, thematisch abgeschlossene Commits; jede Person committet selbst und regelmäßig.

**Begründung:** Die ID verbindet Anforderung, Code und Test (Rückverfolgbarkeit,
Gotel & Finkelstein 1994). Regelmäßige eigene Commits machen den Fortschritt und
die Beiträge je Person über die Git-Historie auswertbar.

## 3 Pull Requests und Reviews

- Im PR das Issue verlinken: `Closes #<Nummer>`.
- Ein anderes Teammitglied reviewt; Implementierung (Bennet) prüft die Coding-Standards,
  Architektur (Mahdi) die Konsistenz mit dem Entwurf, QS (Anil) die Tests.
- Gemergt wird erst, wenn GitHub Actions grün ist.

**Begründung:** Code-Reviews finden Fehler früh und verbreiten Wissen im Team
(Sadowski et al. 2018). Die Rollenaufteilung sorgt dafür, dass jede Perspektive geprüft wird.

## 4 Coding-Standards

Grundlage ist PEP 8 (van Rossum et al. 2001). Coding-Standards sind eine Praxis aus
Extreme Programming, das wir als Teil unseres hybriden Vorgehens nutzen (Beck & Andres 2004):
Einheitlicher Code kann von allen gelesen und geändert werden (Collective Code Ownership).

| Nr. | Regel | Begründung | Durchsetzung |
|---|---|---|---|
| CS-01 | **Formatierung nach PEP 8**, Zeilenlänge max. **99 Zeichen**, einfache Anführungszeichen | PEP 8 erlaubt Teams ausdrücklich bis zu 99 Zeichen; einheitliche Formatierung verhindert Stil-Diskussionen in Reviews | `ruff format --check` (CI) |
| CS-02 | **Namen:** Code-Bezeichner englisch; Klassen `CamelCase`, Funktionen/Variablen `snake_case`, Konstanten `UPPER_CASE` | Englisch passt zu Python und Django; einheitliche Schreibweise zeigt die Art eines Namens auf einen Blick (PEP 8) | ruff `N` |
| CS-03 | **Sprache:** Oberfläche, Docstrings, Kommentare und Dokumentation auf Deutsch | Zielgruppe und alle Projektunterlagen sind deutschsprachig | Review |
| CS-04 | **Docstrings** für jedes Modul, jede öffentliche Klasse und Funktion im Google-Stil: Zweck, `Args`, `Returns`, `Raises`; Bezug zur Anforderung (z. B. `REQ-08`) | Dokumentiert Ein-/Ausgaben und Rolle jeder Klasse (Bewertungskriterium Implementierung); PEP 257 (Goodger & van Rossum 2001) | ruff `D` (Konvention `google`) |
| CS-05 | **Komplexität:** zyklomatische Komplexität je Funktion **≤ 10**; längere Abläufe in benannte Hilfsfunktionen aufteilen | Die Grenze 10 stammt von McCabe (1976); komplexe Funktionen sind fehleranfälliger und schwer zu testen | ruff `C90` |
| CS-06 | **Schichtentrennung:** Fachlogik in `services.py` (bzw. `rules.py`), HTTP und Rollenprüfung in `views.py`, Daten in `models.py`, keine Planungslogik in Templates | Umsetzung der Schichtenarchitektur aus `docs/design/architektur.md`; hohe Kohäsion, lose Kopplung (Parnas 1972) | Review (Architektur) |
| CS-07 | **Importe** sortiert (Standardbibliothek, Drittanbieter, eigene Module), keine ungenutzten Importe oder Variablen | Lesbarkeit; vermeidet tote Abhängigkeiten | ruff `I`, `F` |
| CS-08 | **Keine typischen Fehlerquellen:** z. B. keine veränderlichen Standardargumente, Ausnahmen mit `raise … from …` | Diese Muster verursachen schwer auffindbare Fehler | ruff `B`, `SIM`, `UP` |
| CS-09 | **Django-Regeln:** jedes Model hat `__str__`, Formulare nennen Felder explizit | Lesbare Objekte in Administration und Logs; keine versehentlich offenen Felder | ruff `DJ` |
| CS-10 | **Konstanten statt magischer Zahlen** für fachliche Grenzwerte (z. B. `MAX_PER_SLOT = 30`, ArbZG-Grenzen) | Grenzwerte sind an einer Stelle änderbar (RB-01: mögliche Reform des ArbZG) | Review |
| CS-11 | **Tests:** Jede neue Funktion bzw. jedes Akzeptanzkriterium erhält mindestens einen automatisierten Test; Testname beschreibt das erwartete Verhalten | Wiederholbare Prüfung der Akzeptanzkriterien; Voraussetzung für P5 | Review (QS), CI |
| CS-12 | **Sicherheit:** Rollen- und Objektprüfung serverseitig bei GET und POST; keine Geheimnisse im Repository | QR-03, RB-02 (DSGVO) | Tests, Review |

Ausnahmen: Migrationen werden von Django erzeugt und nicht geprüft; Testdateien
brauchen keine Docstrings, weil der Testname das Verhalten beschreibt.

**Warum automatisch?** Regeln, die nur auf dem Papier stehen, werden im Projektverlauf
zunehmend verletzt (Smit et al. 2011). Werkzeuge werden dann genutzt, wenn sie in den
normalen Arbeitsablauf eingebunden sind (Johnson et al. 2013). Deshalb prüft GitHub Actions
jeden Push und jeden Pull Request; die Konfiguration steht in `pyproject.toml`.

### Lokal prüfen (vor jedem Commit)

```bash
python -m pip install -r requirements-dev.txt
ruff format .          # formatiert automatisch
ruff check --fix .     # behebt einfache Verstöße automatisch
ruff check .           # muss „All checks passed!“ melden
python manage.py test apps.planning
```

In VS Code oder PyCharm kann die Ruff-Erweiterung installiert werden; sie zeigt
Verstöße direkt beim Schreiben an.

## 5 Literatur

- Beck, K.; Andres, C. (2004): *Extreme Programming Explained: Embrace Change*. 2. Aufl., Addison-Wesley.
- Goodger, D.; van Rossum, G. (2001): *PEP 257 – Docstring Conventions*. Python Software Foundation.
- Gotel, O. C. Z.; Finkelstein, A. C. W. (1994): An analysis of the requirements traceability problem. In: *Proc. IEEE International Conference on Requirements Engineering*, S. 94–101.
- Johnson, B.; Song, Y.; Murphy-Hill, E.; Bowdidge, R. (2013): Why don't software developers use static analysis tools to find bugs? In: *Proc. 35th International Conference on Software Engineering (ICSE)*, S. 672–681.
- McCabe, T. J. (1976): A complexity measure. In: *IEEE Transactions on Software Engineering* SE-2 (4), S. 308–320.
- Parnas, D. L. (1972): On the criteria to be used in decomposing systems into modules. In: *Communications of the ACM* 15 (12), S. 1053–1058.
- Sadowski, C.; Söderberg, E.; Church, L.; Sipko, M.; Bacchelli, A. (2018): Modern code review: a case study at Google. In: *Proc. 40th ICSE – Software Engineering in Practice*, S. 181–190.
- Smit, M.; Gergel, B.; Hoover, H. J.; Stroulia, E. (2011): Code convention adherence in evolving software. In: *Proc. 27th IEEE International Conference on Software Maintenance (ICSM)*, S. 504–507.
- van Rossum, G.; Warsaw, B.; Coghlan, N. (2001): *PEP 8 – Style Guide for Python Code*. Python Software Foundation.
