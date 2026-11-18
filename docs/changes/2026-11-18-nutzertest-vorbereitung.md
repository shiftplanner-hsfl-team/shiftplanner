# Offene Folgemonate für die Nutzertests

Stand: 18.11.2026

Die Eingabe in Folgemonaten ist bereits möglich. Voraussetzung ist, dass die Planung
im gewählten Monat eine gültige Abgabefrist vor Monatsbeginn hinterlegt. Nach Ablauf
der Frist ist die Eingabe gesperrt; ein Monat ohne Frist ist noch nicht geöffnet.
Die Demo arbeitet weiterhin mit dem tatsächlichen Tagesdatum.

`prepare_usertests` bereitet im bisherigen Nordlicht-Demounternehmen diese Teststände vor:

| Monat | Eingabe bis einschließlich | Person mit noch offener Abgabe | Lückenschicht nach Erzeugung |
| --- | --- | --- | --- |
| Dezember 2026 | 30.11.2026 | mia.hansen@example.com | 18.12., Spätschicht |
| Januar 2027 | 15.12.2026 | tom.weber@example.com | 15.01., Spätschicht |

Die Planung erfolgt mit `nora.krueger@example.com`. Die Bezeichnungen Deichmann/Netto
in den Aufgabenblättern bezeichnen die Testdurchläufe. Die Vorbereitung kopiert keine
Demodaten in die drei neu angelegten leeren Testunternehmen.

Für neue, bislang unbenutzte Testmonate gibt es noch keinen Personalbedarf.
Alle Mitarbeitenden außer der jeweiligen Testperson haben vorbereitete Angaben.
Die Testperson kann ihre Angaben selbst speichern und abgeben. Die Planung kann
anschließend Bedarf erfassen, einen Plan erzeugen und Lücken bearbeiten.

Ein bereits veröffentlichter Novemberplan bleibt erhalten. Existiert nur ein
bearbeiteter Entwurf, wird dieser veröffentlicht, ohne ihn neu zu erzeugen.

## Wiederholte Bereitstellung

Der Befehl initialisiert nur neue oder vollständig unbenutzte Testmonate. Auch ein
bereits über die Monatsauswahl angelegter leerer Dezember wird dadurch geöffnet.
Fristen, Bedarf, Abgaben, Verfügbarkeiten und Pläne laufender Tests werden bei einem
Neustart nicht zurückgesetzt. Der Startablauf in `render.yaml` führt die Vorbereitung
nach `seed_demo` aus. Ein bestehender Render-Dienst muss diesen Startablauf ebenfalls
übernehmen; eine Änderung der Datei allein ersetzt dessen gespeicherte Konfiguration
bei angehaltener Blueprint-Synchronisierung nicht.

## Manuell für weitere Monate

1. Als Planung den gewünschten Planungsmonat auf der Übersicht auswählen.
2. Eine Abgabefrist vor dem Beginn dieses Monats speichern, die noch nicht abgelaufen ist.
3. Mitarbeitende wählen denselben Monat unter Verfügbarkeiten und können dort eingeben.
