# Review PR #1 – Erster ShiftPlanner-Prototyp

**Reviewer:** Anil Duth (QS), Mahdi Fazeli (Architektur)
**Datum:** __.__.2026
**Gegenstand:** PR #1 „REQ-08: Erster funktionierender ShiftPlanner-Prototyp“ (Branch `feature/REQ-08-erster-prototyp`)
**Ergebnis:** ☐ freigegeben ☐ freigegeben mit Auflagen ☐ Änderungen nötig

> Vorlage: Jede Prüfung selbst durchführen und das tatsächliche Ergebnis eintragen. Nichts ankreuzen, was nicht geprüft wurde.

## 1. Ausführung (Anil)

| Prüfung | Befehl | Ergebnis (Anzahl, bestanden/fehlgeschlagen) |
|---|---|---|
| Django-Systemcheck | `python manage.py check` | |
| Migrationen vollständig | `python manage.py makemigrations --check --dry-run` | |
| Backend-/Integrationstests | `python manage.py test apps.planning` | |
| Browser-Tests | `python manage.py test tests.ui` | |
| GitHub-Actions-Lauf des PR | Tab „Checks“ im PR | |
| Demo-Ablauf laut README | `python manage.py seed_demo`, dann manuell | |

## 2. Inspektion (Anil)

| Prüfpunkt | Ergebnis / Fundstelle |
|---|---|
| Rollenprüfung bei GET **und** POST (QR-03) | |
| Kein Begründungsfeld in `Availability`, `Vacation` (QR-04) | |
| Neutrale Fehlermeldung bei falschem Passwort (REQ-01 AK 3) – manuell prüfen | |
| Mobile Ansicht 360 px (QR-02): Navigationsleiste überdeckt Hinweistext → Issue # | |
| README: „Python 3.14“ → „Python 3.12 oder neuer“ | |

## 3. Architektur (Mahdi)

| Prüfpunkt | Ergebnis / Fundstelle |
|---|---|
| Struktur entspricht `docs/design/architektur_ist_stand.md` (Schichten, Abhängigkeiten nur nach unten) | |
| Klassen in `models.py` entsprechen Abb. 4 (Namen, Beziehungen, Multiplizitäten) | |
| `match_positions` ohne Django-Abhängigkeit | |
| Andockstelle für das Regelmodul RB-01 (Kandidatenfilter in `generate_plan`) | |

## 4. Befunde

| Nr. | Befund | Schwere (hoch/mittel/gering) | Issue | Status |
|---|---|---|---|---|
| 1 | | | # | |
