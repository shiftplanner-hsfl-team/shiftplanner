# Architektur des ersten Prototyps

Stand: 25.10.2026. Entwurf und Implementierung mit Codex als Hilfswerkzeug;
fachlicher Review durch das Team steht aus.

## Struktur

Django rendert HTML auf dem Server. CSS überträgt Farben, Schrift, Abstände,
Karten und Navigation aus dem Figma-Mockup. Wenig JavaScript synchronisiert die
mobile Slot-Eingabe, blendet weitere Tage ein und schützt vor dem Verlust
ungespeicherter Eingaben. Kein externer Dienst wird zur Laufzeit aufgerufen.

| Schicht | Dateien | Verantwortung |
|---|---|---|
| Darstellung | `templates/planning/`, `static/planning/` | Desktop/Mobil, Formulare, Feedback |
| Zugriff und Abläufe | `views.py`, `forms.py` | Anmeldung, Rollen, Validierung, Transaktionen |
| Planung | `services.py` | Monatsaufbau, Vorbedingungen, deterministische Zuordnung |
| Persistenz | `models.py`, `migrations/` | SQLite, Beziehungen, Constraints, Plansnapshot |
| Qualität | `tests.py`, `tests/ui/` | Logik, HTTP-Zugriffe, Browserabläufe |

## Daten und Zugriffe

- User: Django-Konto. Die Gruppe `Planung` erhält Planungszugriff.
- Employee: Mitarbeitendenprofil mit beliebig vielen Qualifikationen.
- ShiftTemplate: Name, Anfang, Ende. Ende muss am selben Tag nach Anfang liegen.
- Month: Planungsmonat, Bedarfsstatus und Revisionszähler.
- Slot: Kombination aus Datum und Vorlage, Gesamtbedarf 0–30.
- Need: Anzahl erforderlicher Personen je Qualifikation pro Slot. Positionen
  sind getrennt: eine Person besetzt nicht gleichzeitig zwei Positionen.
- Availability: private Priorität pro Employee und Slot, 0–3.
- Submission: Monatsstatus Entwurf/abgegeben. Nur aktive Mitarbeitende zählen
  für die Vollständigkeitsprüfung.
- Vacation: Zeitraum ohne Begründungsfeld, durch die Planung erfasst.
- Plan/Assignment: persistierter nur lesbarer Plan, einschließlich nicht
  besetzbarer Positionen. Datum, Zeit, Namen und Rollen werden als Snapshot
  gespeichert. Nach einer Eingabeänderung zeigt der Revisionsvergleich einen
  Hinweis auf den veralteten Stand.

Mitarbeitende lesen und bearbeiten ausschließlich eigene Verfügbarkeiten.
Planung darf alle Angaben lesen, aber nicht als Mitarbeitende abgeben.
Rollen- und Objektprüfungen finden auf dem Server für GET und POST statt.
Django schützt Formulare mit CSRF; Abmelden erfolgt per POST.

## Algorithmus (REQ-08 laut Zusammenfassung)

1. Vorbedingungen prüfen: gespeicherter Bedarf, positive Positionenzahl,
   mindestens eine aktive Person, alle Monatsabgaben vorhanden.
2. Slots chronologisch nach Datum, Beginn und stabiler ID bearbeiten.
3. Bedarf in einzelne Positionen mit Qualifikationsvorgabe auflösen; Rest ohne Vorgabe.
4. Personen ohne positive Slot-Verfügbarkeit, im Urlaub oder in einer bereits
   zeitlich überlappenden Schicht ausschließen.
5. Pro Slot ein deterministisches Minimum-Cost-Maximum-Matching berechnen:
   zuerst möglichst viele Positionen besetzen, danach möglichst viele P1 und
   dann P2 verwenden. Die Restgraph-Zuordnung vermeidet vermeidbare Lücken
   durch eine vorzeitige Zuteilung mehrfach qualifizierter Personen.
6. Bei gleichen Kosten entscheidet die feste Reihenfolge der Personen- und
   Positions-IDs. Angrenzende Schichten ohne zeitliche Überlappung sind möglich.
7. Ergebnisse atomar als Snapshot speichern. Fehlende Personen bleiben `NULL`
   und erscheinen ausdrücklich als „Unbesetzt“.

Die Prioritätsoptimierung erfolgt **je chronologisch bearbeitetem Slot**.
Es handelt sich nicht um eine globale Optimierung des ganzen Monats. Frühe
Entscheidungen können die Besetzbarkeit späterer, überlappender Slots beeinflussen.
Eine Rotation/Belastungsfairness wird nicht behauptet. Es gibt keinen Zufall,
keine KI-Planung und keinen versteckten Planverlauf als Einflussgröße.

## Erweiterungspunkt RB-01

ArbZG-Prüfung ist gemäß Zusammenfassung eine spätere Rahmenbedingung.
Die Filterung von Kandidaten in der Engine ist die Stelle, an der ein getrenntes
Regelmodul ergänzt werden kann. Im vorliegenden Stand ist noch kein solches
Modul implementiert. Insbesondere werden weder Ruhezeiten, Pausen noch
Höchstarbeitszeiten geprüft. Dieser offene Punkt muss vor betrieblichem Einsatz
bearbeitet werden.

## Offene technische Grenzen

Ein Betrieb je Installation; kein Mandantenmodell. SQLite und der Django-
Entwicklungsserver sind für den lokalen Prototyp gewählt. Parallele Änderungen
und Planerzeugungen sind durch Transaktionen gekapselt; ein Mehrbenutzer-
Produktivbetrieb benötigt eine gesonderte Last-/Nebenläufigkeitsprüfung und eine
geeignete Serverdatenbank. Es gibt keine öffentliche Registrierung,
Passwort-Zurücksetzung oder Audit-Historie. Fachlich vollständige Arbeitszeit-
und Datenschutzfreigabe sind nicht Gegenstand dieses Implementierungsnachweises.
