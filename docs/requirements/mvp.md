# Umgesetzter MVP und Quellenabgrenzung

Grundlage: Projektzusammenfassung vom 25.10.2026 und Figma-Datei
„ShiftPlanner · Erstes Produktmockup“. Die vollständige Kursbeschreibung,
Vorlesungsfolien und das P2-Anforderungsdokument lagen diesem Arbeitsstand
nicht bei. Daher werden keine fehlenden REQ-01–REQ-10-Texte rekonstruiert und
keine unbekannten Akzeptanzkriterien als erfüllt ausgegeben.

## Unterstützter Ablauf

1. Planung richtet Vorlagen und Qualifikationen ein, ordnet Qualifikationen zu,
   erfasst Bedarf und Besetzungsmix pro Slot und trägt Urlaub ein.
2. Mitarbeitende erfassen pro Slot P1/P2/P3 oder nicht verfügbar, speichern
   Zwischenstände und geben ihre Angaben für den Monat ab.
3. Planung prüft den Abgabestand und erzeugt den deterministischen Plan.
4. Planung liest Besetzungen und offene Positionen. Nach Änderungen der
   Eingaben wird der Plan neu erzeugt; direkte Plankorrektur ist nicht enthalten.

Die Wochen 1–3 werden in der Oberfläche als Orientierung dargestellt. Harte
Datumsfristen sind nicht implementiert: Demo und frühe Erprobung bleiben auch
außerhalb der tatsächlichen Eingabephase möglich.

## Nachprüfbare Kriterien aus der Zusammenfassung

| Kriterium | Umsetzung / Nachweis |
|---|---|
| Priorität 1 vor 2 vor 3, deterministisch | Matching je Slot, Wiederholungs- und Prioritätstests |
| Keine Überschneidungen | Intervallprüfung je Person/Tag; angrenzende Schichten erlaubt |
| Fehlende Besetzung sichtbar | Unbesetzte Position im Plan und eigene Detailansicht |
| Verfügbarkeit privat | Rollen-/Objektprüfung, direkte Zugriffe ergeben HTTP 403 |
| Keine Sperrzeit-Begründung | Ein solches Datenfeld existiert nicht |
| Mobile Nutzung ab 360 px | Chromium-Test mit 360 × 900 und Prüfung auf Seitenüberlauf |
| Plan ≤10 Sekunden bei 30/3/30 | Automatisierter Lasttest |
| UI-Tests in Actions | Workflow enthält Chromium-End-to-End-Tests und Screenshots |
| 10 Slots ≤5 Minuten, Monatsplan ≤30 Minuten | **Noch nicht empirisch geprüft**, reale Nutzertests erforderlich |

Keine Erweiterung um Krankmeldung, Schichttausch, KI-Erklärungen, Freigaben,
manuelle Plankorrekturen oder Verlaufsfairness. Die Regelprüfung zum ArbZG
bleibt offen und ist in der Architektur als nächster Schritt ausgewiesen.

Die Mockup-Texte und -Zahlen werden durch echte Daten ersetzt. Insbesondere
hat November 2026 bei Sonntagsschließung 25 Planungstage; die Demo zeigt
entsprechend 75 Slots und 225 Positionen statt statischer Beispielzahlen.
