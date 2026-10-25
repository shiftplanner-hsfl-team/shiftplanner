# Testnachweis · erster funktionierender Prototyp

Stand: 25.10.2026. Automatisiert mit Codex als Hilfswerkzeug geprüft.
Die Tests ersetzen keine fachliche Abnahme und keine Nutzertests mit echten Personen.

## Umgebung und Ergebnis

- macOS auf Apple Silicon, Python 3.14, Django 6.1.2, SQLite.
- Playwright 1.64.1 und Chromium 156.
- 23 Backend-/Integrationstests und 4 Browsertests bestanden (27 insgesamt).
- Lastfall 30 Mitarbeitende × 3 Vorlagen × 30 Kalendertage (90 Slots,
  270 Positionen): lokal etwa **0,05–0,06 Sekunden**, Ziel ≤10 Sekunden.
- Django-Systemprüfung und Prüfung auf fehlende Migrationen ohne Befund.
- Browserkonsole ohne JavaScript-Fehler; verwendete Icons laden lokal.
- Visuelle Kontrolle anhand von Desktop- und Mobil-Screenshots; Farben,
  Manrope, Navigation, Karten und Statusdarstellung folgen dem Figma-Mockup.
  Funktionale Formulare ersetzen die statischen Beispielwerte.

## Automatisierte Abdeckung

| Bereich | Geprüft |
|---|---|
| Planung | P1 vor P2 vor P3, P0 ausgeschlossen, stabile Wiederholung |
| Qualifikationen | Unqualifizierte ausgeschlossen, knappe Qualifikationen bleiben besetzbar |
| Zeit | Überlappungen ausgeschlossen, angrenzende Schichten erlaubt |
| Urlaub | Verfügbarkeit wird für den Zeitraum übersteuert |
| Unbesetzt | Nicht zuordenbare Positionen gespeichert und in der UI angezeigt |
| Abgaben | Entwurf/Monatsabgabe getrennt, fehlende Abgabe blockiert Erzeugung |
| Daten | Bedarf und Verfügbarkeiten nach Neuladen gespeichert; andere Wochen bleiben erhalten |
| Validierung | Ungültige Priorität, Besetzungsmix, Schichtzeit und Monat abgefangen |
| Zugriff | Anmeldung erforderlich; Planung/andere Personen per GET und POST gesperrt |
| Schutz | CSRF aktiv, Logout nur POST, fremde Angaben nur lesbar für Planung |
| Plan | Nur lesbar; geänderte Eingaben markieren bisherigen Snapshot als veraltet |
| Oberfläche | Bedarf, Vorlagen und Qualifikationen im Browser anlegen/ändern |
| Mobil | 360 × 900, kein horizontaler Seitenüberlauf, Priorität ändern, Abgabe, weitere Tage |
| Tastatur | Anmeldung mit Tab und Enter |

## Reproduzieren

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test apps.planning tests.ui --verbosity 2
```

Tests laufen in einer **separaten Testdatenbank**, ohne die lokale Demodatenbank
zu verändern. Browser-Screenshots liegen in `test-artifacts/` (ignoriert) und
werden in GitHub Actions als Artefakt `ui-screenshots` veröffentlicht.

## Noch offene Nachweise

- Zehn Slots in ≤5 Minuten und Monatsplanung in ≤30 Minuten mit echten Nutzern.
- Vollständiger Abgleich gegen die im Team vorliegenden Original-REQ/QR-Texte.
- Breitere Accessibility-Prüfung und weitere Browser/Geräte.
- Mehrbenutzerbetrieb unter Last und auf einer späteren Serverdatenbank.
- ArbZG-Regelmodul, Feiertage und fachliche Freigabe vor betrieblichem Einsatz.
- Die im Anhang genannten Interviews wurden hier nicht als neue Nutzertests ausgegeben.
