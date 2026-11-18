# Getrennte Testunternehmen

Stand: 18.11.2026

Das bisherige Unternehmen Nordlicht bleibt mit allen Mitarbeitenden, Eingaben, erzeugten
Plänen und veröffentlichten Ständen erhalten. Zusätzlich stehen drei leere Unternehmen
mit jeweils einem Planungskonto bereit.

| Unternehmen | Planungskonto |
| --- | --- |
| Nordlicht · Filiale Flensburg | nora.krueger@example.com |
| Testunternehmen 1 | planer1@example.com |
| Testunternehmen 2 | planer2@example.com |
| Testunternehmen 3 | planer3@example.com |

Demo-Passwort für die neuen Planungskonten: `ShiftDemo2026!`.
Das bestehende Nordlicht-Kennwort wird nicht verändert.

Anmeldung: <https://shiftplanner-demo-93eu.onrender.com/anmelden/>

## Ausprobieren

1. Mit einem neuen Planungskonto anmelden. Das Unternehmen steht in der Seitenleiste
   und im Kopfbereich. Es enthält noch keine Mitarbeitenden, Vorlagen oder Pläne.
2. Mitarbeitende und Schichtvorlagen selbst anlegen, danach den Personalbedarf erfassen.
3. Abmelden und mit einem anderen Planungskonto anmelden. Die dortigen Daten bleiben
   getrennt; jedes Konto verwaltet genau ein Unternehmen.
4. Mit Nora anmelden: Die bisherigen Nordlicht-Daten sind weiterhin vorhanden.

Ein leerer Planungsmonat wird beim ersten Aufruf automatisch vorbereitet. Er enthält
keinen Bedarf und keine Schichtpositionen, solange keine Vorlagen angelegt sind.

## Umsetzung und Prüfung

- Unternehmen und Kontozuordnung werden in der Datenbank gespeichert.
- Migration `0007_company_isolation` ordnet bestehende Daten und Konten Nordlicht zu.
  Positionen und Veröffentlichungssnapshots werden nicht neu berechnet oder ersetzt.
- Vorlagen, Qualifikationen, Monate, Mitarbeitende und Plansicht sind je Unternehmen
  getrennt. Fremde IDs und Formularauswahlen werden serverseitig abgefangen.
- Die bisherigen Planungsrechte gelten nur für das Unternehmen des Kontos.
  Konten ohne Unternehmenszuordnung erhalten keinen Zugriff auf die Planung.
- `seed_demo` ergänzt über `seed_test_companies` die fehlenden Testkonten.
  Wiederholtes Ausführen erhält bestehende Kennwörter und Daten.
- Tests prüfen Trennung, manipulierte IDs, Anlage eigener Mitarbeitender, Erhalt der
  Veröffentlichungen bei der Migration und Anmeldung im Desktop- und Mobilbrowser.

Es gibt weiterhin keine öffentliche Registrierung oder Unternehmensauswahl innerhalb
eines Kontos. Für einen anderen Testbetrieb abmelden und das zugehörige Konto verwenden.
