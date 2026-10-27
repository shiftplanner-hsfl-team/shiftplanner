# ShiftPlanner

Erster funktionierender Django-Prototyp zur automatischen Schichtplanung für einen
Betrieb mit 5–30 Mitarbeitenden. Software-Projekt WS 2026/27, Hochschule Flensburg.
Oberfläche und Dokumentation sind auf Deutsch.

Designgrundlage: [ShiftPlanner · Erstes Produktmockup](https://www.figma.com/design/S2McEv43f8NntGPuEdCjMR/ShiftPlanner--Erstes-Produktmockup).
Fachliche Grundlage: bereitgestellte Projektzusammenfassung vom 25.10.2026.

## Lokal starten

Voraussetzung: Python 3.12 oder neuer. SQLite ist enthalten.
Kein Node.js, Cloudkonto oder KI-Schlüssel erforderlich.

```bash
python3 -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8000
```

Danach [http://127.0.0.1:8000](http://127.0.0.1:8000) öffnen.
Alternativ unter macOS/Linux im Projektordner `./start.sh` ausführen.
Alle Daten bleiben lokal in der ignorierten Datei `db.sqlite3` gespeichert.

## Demo ausprobieren

Alle Namen und Angaben in den Demodaten sind fiktiv. Das Passwort lautet für alle
Demo-Zugänge **`ShiftDemo2026!`**. Nur lokal mit diesen Konten arbeiten.

| Rolle | Anmeldung |
|---|---|
| Planung | `nora.krueger@example.com` |
| Mitarbeitende | `lea.meyer@example.com` |
| Noch offene Abgabe | `ben.fischer@example.com` |
| Noch offene Abgabe | `eva.koch@example.com` |

1. Als Nora anmelden. Bedarf, Vorlagen und Qualifikationen prüfen. Unter **Mix**
   kann je Slot die Anzahl pro Qualifikation eingestellt werden. Der Mix darf
   die Gesamtzahl nicht übersteigen. Restliche Positionen haben keine Vorgabe.
2. Unter **Verfügbarkeiten** die Abgaben und einzelne Angaben ansehen. Urlaub
   kann hier durch die Planung eingetragen werden.
3. Abmelden und als Ben und danach Eva anmelden. **Verfügbarkeiten bearbeiten**,
   Priorität wählen und **Angaben abgeben**. Entwürfe sind getrennt von Abgaben.
4. Wieder als Nora anmelden, **Schichtplan → Plan erzeugen** öffnen und
   **Schichtplan erzeugen** klicken. Bei offenen Abgaben bleibt diese Aktion gesperrt.
5. Den nur lesbaren Plan und **Unbesetzte Schichten** prüfen. Am 06.11. ist die
   Spätschicht in der Demo bewusst für alle gesperrt, damit Lücken sichtbar werden.
6. Eingaben ändern: Der bisherige Plan wird als veraltet markiert und kann neu
   erzeugt werden. Der alte Stand bleibt bis dahin lesbar.

Die Demo enthält tatsächlich **75 Slots / 225 Positionen** im November 2026:
25 Tage von Montag bis Samstag × 3 Vorlagen × 3 Personen. Die statischen
Mockup-Zahlen 72 / 216 werden nicht als echte Berechnung ausgegeben.
`seed_demo` verändert eine bereits mit Benutzerkonten belegte Datenbank nicht.

## Enthalten

- Anmeldung/Abmeldung mit Django-Sitzungen und zwei Rollen; HTTP 403 bei
  unberechtigtem Zugriff, auch bei direkten URLs und POST-Anfragen.
- Schichtvorlagen, Qualifikationen und Zuordnung zu Mitarbeitenden.
- Monats-/Wochenwahl; Bedarf pro Tag und Vorlage, Gesamtzahl und Besetzungsmix;
  Kopieren einer Woche auf gleiche Wochentage des gesamten Monats.
- Private Verfügbarkeiten pro Slot: 1 bevorzugt, 2 möglich, 3 nur wenn nötig,
  0 nicht verfügbar. Keine Begründung erforderlich. Entwurf und Monatsabgabe.
- Urlaub, deterministische Zuordnung, keine zeitlichen Überschneidungen,
  unbesetzte Positionen mit benötigter Qualifikation, nur lesbarer Plan.
- Responsive Mitarbeitendenansicht ab 360 px, lokale Figma-Icons und Manrope.
- Automatisierte Backend-, Integrations- und Chromium-UI-Tests in GitHub Actions.

## Bewusste MVP-Grenzen

Ein Betrieb pro Installation, standardmäßig Montag bis Samstag. Nachtvorlagen
über Mitternacht sind noch nicht unterstützt. Konten werden durch die
Administration angelegt; eine öffentliche Registrierung ist nicht enthalten.

Manuelle Plankorrektur, Freigabe/Veröffentlichung, KI-Erklärungen,
Fairness-Verlauf, Krankmeldung und Schichttausch folgen später. Die Engine
enthält **noch keine ArbZG-/Feiertagsprüfung**. Der Prototyp dient der
Demonstration und Erprobung, nicht einem betrieblich freigegebenen Dienstplan.
Die vollständigen Kursunterlagen und REQ-/QR-Texte lagen nicht vor; eine
vollständige Abnahme aller ursprünglichen Anforderungs-IDs wird nicht behauptet.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test apps.planning
python manage.py test tests.ui --verbosity 2
```

Unter Linux: `python -m playwright install --with-deps chromium`.
UI-Tests verwenden eine isolierte Testdatenbank und schreiben Screenshots nach
`test-artifacts/`. In Actions werden diese als Artefakt hochgeladen.

Details: [Architektur](docs/design/architektur.md),
[MVP-Abgrenzung](docs/requirements/mvp.md), [Testnachweis](docs/testing/prototyp.md).

## Einstellungen und Administration

Die Voreinstellung ist ein lokaler Entwicklungsserver. Für eine spätere
Bereitstellung: `DJANGO_DEBUG=0`, einen zufälligen `DJANGO_SECRET_KEY` und
`DJANGO_ALLOWED_HOSTS` setzen, HTTPS und einen passenden WSGI-/ASGI-Server
konfigurieren, statische Dateien mit `collectstatic` bereitstellen. Der
Demo-Seed ist bei `DEBUG=0` gesperrt. Ein Produktivdeployment gehört nicht zu
diesem Prototyp.

Für weitere lokale Benutzer: `python manage.py createsuperuser`, dann `/admin/`.
Planungskonten kommen in die Gruppe **Planung**. Mitarbeitendenkonten bekommen
zusätzlich ein **Employee**-Profil und passende Qualifikationen. Der vorhandene
Demo-Planungszugang hat bewusst keinen Admin-Zugriff.

## Team

| Rolle | Verantwortlich |
|---|---|
| Anforderungen + Management | Muhammed Asif Shahul Hameed |
| Architektur & Entwurf | Mahdi Fazeli |
| Implementierung | Bennet Schalow |
| Qualitätssicherung | Anil Duth |

Dieser Implementierungsstand wurde mit Codex als Hilfswerkzeug erstellt.
Team-Review, fachliche Abnahme und tatsächliche prozentuale Autorenbeiträge
werden vom Team bestätigt; dafür wurden keine Werte erfunden.
