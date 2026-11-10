# ShiftPlanner – Änderungen am Planungsablauf

Stand: 10. November 2026

## Überblick

Die Erweiterung ergänzt den Weg vom automatisch erzeugten Plan über manuelle
Korrekturen bis zur Veröffentlichung für Mitarbeitende. Sie wurde lokal mit
fiktiven Daten getestet. Die vorhandene Arbeitszeitprüfung wird wiederverwendet;
es wurden keine neuen gesetzlichen Grenzwerte eingeführt.

## Ergänzte Funktionen

### 1. Plan manuell korrigieren (REQ-11, Issue #2)

- Einzelne Positionen besetzen, leeren oder die Besetzung zweier Positionen tauschen.
- Kompakte Auswahl über „Besetzung bearbeiten“ direkt im Schichtplan.
- Vorschau vor dem Speichern; veraltete Bestätigungen werden abgewiesen.
- Überschneidungen und Verstöße gegen vorhandene Arbeitszeitregeln blockieren die Änderung.
- Fehlende Verfügbarkeit, Priorität 3, Urlaub und fehlende Qualifikation werden als
  Hinweise angezeigt. Solche Änderungen können ausdrücklich bestätigt werden.

### 2. Plan trotz offener Abgaben erzeugen

- Die Planung kann vor und nach Fristablauf auch bei fehlenden Abgaben einen Plan erzeugen.
- Die Anzahl offener Abgaben und die Folgen werden angezeigt und müssen bestätigt werden.
- Nur abgegebene Verfügbarkeiten gehen in die automatische Planung ein. Entwürfe oder
  fehlende Abgaben gelten dabei als nicht verfügbar.
- Gespeicherter Bedarf mit positiven Positionen und aktive Mitarbeitende bleiben Voraussetzung.
- Eine Neuberechnung ersetzt bisherige manuelle Korrekturen im bearbeitbaren Plan.

Diese ausdrücklich gewünschte Änderung erweitert das bisherige Verhalten aus REQ-05:
Die vollständige Abgabe oder der Fristablauf ist keine zwingende Sperre mehr.

### 3. Unbesetzte Positionen automatisch füllen

- Neuer Button unter „Unbesetzte Schichten“.
- Bereits vergebene Positionen bleiben erhalten; es werden nur Lücken ergänzt.
- Berücksichtigt werden abgegebene Verfügbarkeiten, Qualifikationen, Urlaub,
  bereits vorhandene Zuweisungen und die bestehenden Arbeitszeitregeln.
- Später eingegangene Abgaben können zum Auffüllen verwendet werden, ohne den gesamten
  Plan neu zu erzeugen. Ein bereits veralteter Plan bleibt als solcher gekennzeichnet.
- Wenn niemand passt, erklärt eine Rückmeldung mögliche Ursachen und verlinkt zur Abgabeübersicht.

Der Button garantiert keine vollständige Besetzung und ersetzt noch nicht das gesamte
Issue #14 zu Vorschlägen für unbesetzte Schichten.

### 4. Plan veröffentlichen (REQ-15, Issue #6)

- Prüfseite mit besetzten und offenen Positionen sowie Hinweis auf veraltete Eingaben.
- Bei Lücken oder veralteten Eingaben ist eine ausdrückliche Bestätigung erforderlich.
- Der veröffentlichte Stand wird unabhängig vom bearbeitbaren Plan gespeichert.
- Korrekturen, Auffüllen und Neuberechnungen sind für Mitarbeitende erst nach erneutem
  „Änderungen veröffentlichen“ sichtbar.
- Zeitpunkt und Status der Veröffentlichung stehen im Schichtplan.
- Neue Migrationen veröffentlichen bestehende Pläne nicht automatisch.

### 5. Sichtbarkeit und Wochen-Stundenplan

- Gemeinsame Einstellung unter „Mitarbeitende → Plansicht für Mitarbeitende“.
- Standard: nur eigene Schichten; alternativ ist der gesamte Teamplan sichtbar.
- Die Einstellung gilt für alle Mitarbeitenden und wirkt sofort.
- Verfügbarkeiten und Prioritäten bleiben privat.
- Mitarbeitende erhalten den Menüpunkt „Schichtplan“ und einen Hinweis auf ihrer Startseite.
- Wochenansicht mit Wochentagen als Spalten und Schichten samt Uhrzeiten als Zeilen.
- Personen und Rollen stehen direkt in den Tagesfeldern. Eigene Schichten sind im Teamplan hervorgehoben.
- Wochenwechsel über Pfeile oder Auswahl; auf kleinen Bildschirmen ist die Tabelle seitlich verschiebbar.

## Lokal testen

Voraussetzung: Python-Umgebung mit den Paketen aus `requirements.txt`.
Nach dem Übernehmen der Änderungen die neuen Migrationen anwenden:

```sh
python manage.py migrate
```

Die lokale Demo kann mit diesen Befehlen gestartet werden. `seed_demo` verändert
keine Datenbank, in der bereits Benutzerkonten vorhanden sind:

```sh
python manage.py seed_demo
export SHIFTPLANNER_TODAY=2026-10-20
python manage.py runserver 127.0.0.1:8000
```

Das Demo-Datum hält die Eingabephase für November 2026 offen. Ohne die Variable gilt
das tatsächliche Datum. Unter Windows PowerShell das Datum stattdessen mit
`$env:SHIFTPLANNER_TODAY="2026-10-20"` setzen.

1. Als Planung mit `nora.krueger@example.com` anmelden.
2. „Schichtplan → Plan erzeugen“ öffnen, offene Abgaben prüfen und bestätigen.
3. Über „Besetzung bearbeiten“ eine Position ändern, prüfen und bestätigen.
4. Unter „Unbesetzte Schichten“ das automatische Auffüllen ausprobieren. Wenn keine
   geeignete Person verfügbar ist, bleibt die Position offen.
5. „Plan veröffentlichen“ öffnen und die Freigabe bestätigen.
6. Als `lea.meyer@example.com` anmelden und „Schichtplan“ öffnen.
7. Als Planung unter „Mitarbeitende“ die gemeinsame Plansicht ändern und die Wirkung
   in der Mitarbeitendenansicht prüfen.
8. Eine weitere Korrektur vornehmen: Sie darf erst nach erneutem Veröffentlichen bei
   Mitarbeitenden sichtbar werden.

Das Passwort der vorhandenen fiktiven Demo-Zugänge lautet `ShiftDemo2026!`.
Es handelt sich um gemeinsam genutzte Testkonten.

## Testergebnis

Am 10. November 2026 wurden die folgenden Prüfungen lokal erfolgreich ausgeführt:

- 85 Backend- und Integrationstests sowie 8 Chromium-Browsertests, insgesamt **93 Tests**.
- Ruff-Formatprüfung und Ruff-Codeprüfung.
- Django-Systemprüfung sowie Prüfung auf fehlende Migrationen.
- Prüfung auf fehlerhafte Leerzeichen im Diff.
- Sichtkontrolle des Wochenplans auf Desktop und bei 360 Pixel Breite.

Die Tests umfassen Rollenrechte, eigene und gemeinsame Plansicht, signierte
Bestätigungen, konkurrierende Änderungen, atomare Veröffentlichung, Snapshot-Erhalt
bei Korrektur/Auffüllen/Neuberechnung und den Wochenwechsel einschließlich Jahresgrenze.
Die Tests ersetzen keine fachliche Abnahme durch das Team.

## Datenbank und technische Hinweise

- `0005_published_plans`: gemeinsame Plansicht und unabhängige Veröffentlichung mit Positionen.
- `0006_publication_input_revision`: Eingabestand der Veröffentlichung zur Änderungsanzeige.
- Die Migrationen ergänzen Tabellen und verändern keine bestehende Besetzung.
- Ein erneutes Veröffentlichen ersetzt den letzten freigegebenen Stand atomar.
  Eine vollständige Historie älterer Veröffentlichungen wird noch nicht geführt.

## Weiter offen

- Vertragsstunden und Minijob-Grenzen in der automatischen Planung.
- Prüfung von Arbeitszeiten über Monatsgrenzen hinweg.
- Wochenmuster für die Eingabe von Verfügbarkeiten.
- Erinnerungen und Benachrichtigungen bei Planänderungen.
- Schichttausch durch Mitarbeitende, Krankmeldung und Fairness-Historie.
- Supabase-Anbindung und dauerhafte Betriebsumgebung.

Diese Änderung umfasst keine Bereitstellung auf Render. Der Pull Request ist für
Team-Review und GitHub-Prüfungen vorgesehen; das Zusammenführen erfolgt anschließend
nach den Projektregeln.
