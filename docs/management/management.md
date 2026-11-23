# Management-Dokumentation ShiftPlanner

Autorinnen und Autoren (Anteil): Muhammed Asif Shahul Hameed 100 % (Entwürfe ab 23.11.2026 KI-gestützt, siehe Abschnitt 1)
Stand: 23.11.2026 · Verantwortlich: Management (Product Owner)

## 1 Vorgehensmodell und Praktiken

Wir arbeiten hybrid: Scrum gibt den Rahmen vor, XP-Praktiken sichern die Codequalität, und eine Lean-Startup-Feedbackschleife sorgt dafür, dass wir das Richtige bauen. Diese Kombination passt zu einem kleinen Team, das echtes Kundenfeedback braucht und alle zwei Wochen ein lauffähiges Produkt zeigen soll.

**Scrum:** Wir planen in Sprints von zwei Wochen, die in GitHub als Milestones abgebildet sind (Sprint 1: 02.11.–15.11.2026). Seit dem Feedback zu P1 sind die Sprints bewusst von den Präsentationsterminen entkoppelt (Schwaber & Sutherland 2020).

**XP:** Für den Code gelten Coding-Standards, die GitHub Actions bei jedem Push automatisch prüft (Issue #22, PR #28). Jede Änderung läuft über einen Pull Request mit Review, und zu jedem Akzeptanzkriterium gibt es mindestens einen Test (Beck & Andres 2004).

**Lean Startup:** In drei Feedbackrunden mit realen Planerinnen, Planern und Mitarbeitenden (FB-01 bis FB-15) prüfen wir unsere Annahmen und leiten daraus Entscheidungen ab (E-01 bis E-03, siehe `docs/feedback/feedback.md`) (Ries 2011).

**KI-Unterstützung (seit Sprint 1):** Wir nutzen KI-Assistenten als Werkzeug. Claude (Anthropic) ist über eine GitHub-App mit dem Repository verbunden und erstellt auf Anweisung des Teams Entwürfe für Tests, Dokumente und kleinere Korrekturen; diese Commits tragen den Autor „Claude“ und werden über das Konto der beauftragenden Person gepusht. Bennet nutzte für die Inspektion in #58 Codex als Prüfwerkzeug. Regeln: KI-Beiträge sind im Commit bzw. Kommentar gekennzeichnet; nichts wird ohne Review und Merge durch ein Teammitglied übernommen; fachliche Entscheidungen und Kundenkontakte bleiben beim Team. Die Statistik in Abschnitt 5.2 weist KI-Commits deshalb getrennt aus.

**Tracking:** Seit dem Feedback zu P2 führen wir zwei Boards, eines für das Produkt und eines für das Management. Alle Issues tragen eine Aufwandsschätzung.

## 2 Planung und Sprints

| Sprint | Zeitraum | Ziel laut Milestone | Erreicht | Nicht erreicht → Konsequenz |
|---|---|---|---|---|
| 1 | 02.11.–15.11.2026 | MVP-Erweiterungen aus Feedbackrunde 3, Coding-Standards | ABW-01, ABW-02, RB-01/RB-03, REQ-22, REQ-11, REQ-15, Coding-Standards in CI (19 von 21 Issues) | Statistik (#25) → Sprint 2; P4-Ticket (#24) erst am 23.11. geschlossen |
| 2 | 16.11.–29.11.2026 | Qualität und Tests (P5), REQ-23, REQ-13 | Testkonzept, Testfallkatalog, 57 neue Tests, Abdeckungsmessung in CI, PostgreSQL in CI, Review- und Inspektionsrichtlinie, Inspektion #58, Nutzertest mit drei Betrieben (Feedback P4), DEF-01 und DEF-02 behoben, Betriebstrennung (ABW-03, #46) | **REQ-23 und REQ-13 nicht begonnen**: Der Schwerpunkt verschob sich vollständig auf Qualität, Nutzertest und den Ausfall zweier Teammitglieder → Sprint 3 |
| 3 | 30.11.–13.12.2026 | geplant: Verbesserungen aus dem Nutzertest (#50–#52), REQ-23, REQ-13, Nutzertest P6 (02.12.) | – | – |

## 3 Werkzeuge und Infrastruktur

*Folgt in Sprint 2.*

## 4 Probleme und Lösungen

| Problem | Wann | Auswirkung | Lösung | Lehre |
|---|---|---|---|---|
| GitHub-Konto als „spammy“ gesperrt | Oktober 2026 | Board und Repository nicht nutzbar | Neue Organisation, eingerichtet von Bennet | Infrastruktur nicht an ein einzelnes Konto binden |
| Diagramme nicht mit dem Code aktualisiert | P3 → P4 | Entwurf und Code widersprüchlich | Aktualisierung in PR #37 | Diagramme im selben Sprint wie den Code anpassen |
| Commits auf wenige Tage und Personen konzentriert | Sprint 1 | Fortschritt schwer nachvollziehbar | Kleinere Tickets je Person ab Sprint 2 | Regelmäßige Commits einplanen |
| Reviews ohne Kommentar | PRs #28–#32 | Review nicht nachvollziehbar | Review-Leitfaden bis P5 | Jedes Review hält fest, was geprüft wurde |
| Widersprüchliches Feedback (FB-12 vs. FB-14) | 09.11.2026 | REQ-11 unklar | PO-Entscheidung E-01 mit Begründung | Konflikte offen dokumentieren |
| Zwei Teammitglieder (QS, Architektur) fallen bis Projektende aus | ab 23.11.2026 | Rollen QS und Architektur unbesetzt; Reviews und Inspektion fehlen Personen | Vertretung: Asif übernimmt QS, Bennet Architektur; Dokumente tragen „vertretungsweise“; Professor informiert | Rollen von Beginn an doppelt absichern (Vertretung je Rolle festlegen) |
| Fehler nur auf der Produktionsdatenbank (DEF-01) | 11.11.2026 | Manuelle Korrektur in der Online-Demo mit HTTP 500; 85 grüne Tests auf SQLite | Korrektur in PR #42, zusätzlicher CI-Job mit PostgreSQL 18 | Tests in produktionsnaher Umgebung ausführen |
| Nutzertest: identische Antworten zu Aufgabe M2 | 20.–23.11.2026 | Ergebnis M2 nicht auswertbar | Offen dokumentiert, Wiederholung mit Screenshot, in P6 eigene Konten je Person | Wissensfragen mit Beleg erheben, keine Beispielantworten vorgeben |
| Freigaben weiterhin teils ohne Begründung | #55, #60, #62 (23.11.) | Review nicht nachvollziehbar, obwohl Richtlinie am selben Tag beschlossen | Review-Kommentare nach Vorlage werden nachgetragen; Kennzahlen werden zu P6 erneut erhoben | Richtlinie aktiv einfordern, nicht nur beschließen |
| Keine Commits in KW 45 (02.–08.11.) | Sprint 1 | Fortschritt nicht kontinuierlich sichtbar | ab KW 46 tägliche kleine PRs | Arbeit in kleine, sichtbare Schritte schneiden |

## 5 Statistik

### 5.1 Aufwand je Person und Tätigkeit (Stunden)

*Folgt in Sprint 2.*

### 5.2 Produktivität

Quelle: `git log` auf `main` ohne Merge-Commits, Stand 23.11.2026, 14:45 Uhr (Repository seit 25.10.2026 nach Neuaufbau). Hinzugefügte Zeilen ohne Bilddateien.

| Person | Commits | hinzugefügte Zeilen | Schwerpunkt |
|---|---|---|---|
| Bennet Schalow | 21 | 5.202 | Implementierung, Demo-Betrieb, Diagramm-Nacharbeit |
| Muhammed Asif Shahul Hameed | 6 | 655 | Feedback- und QS-Dokumente; zusätzlich Reviews und Merges der meisten PRs sowie die Beauftragung der KI-Commits |
| Anil Duth | 5 | 561 | Testkonzept, Testfallkatalog, Teststand P4 |
| Mahdi Fazeli | 5 | 336 | UML-Diagramme |
| Claude (KI, über Asifs Konto) | 16 | 4.331 | Tests, Coding-Standards, Dokumententwürfe |

| Kalenderwoche | Bennet | Asif | Anil | Mahdi | Claude |
|---|---|---|---|---|---|
| KW 43 (19.–25.10.) | 14 | – | – | – | – |
| KW 44 (26.10.–01.11.) | 2 | – | 1 | 5 | – |
| KW 45 (02.–08.11.) | – | – | – | – | – |
| KW 46 (09.–15.11.) | 2 | 3 | 2 | – | 13 |
| KW 47 (16.–22.11.) | 2 | – | 2 | – | 2 |
| KW 48 (ab 23.11.) | 1 | 3 | – | – | 1 |

**Bewertung:** Die Arbeit ist ungleich verteilt: Bennet trägt den Großteil des Codes, Asifs Anteil liegt vor allem in Anforderungen, Feedback, Reviews und Steuerung der KI-Entwürfe. KW 45 zeigt eine Lücke ohne Commits. Der Fortschritt verläuft in Schüben um die Präsentationstermine; ab Sprint 2 sind die Commits gleichmäßiger, aber weiterhin auf wenige Personen konzentriert.

## 6 Reflexion (fortlaufend)

**Sprint 1 – was gut lief:** Das Feedback der Planerinnen und Planer kam schnell und hat zwei offene Abweichungen (ABW-01, ABW-02) direkt geschlossen. Die automatischen Prüfungen in GitHub Actions haben Fehler früh sichtbar gemacht.

**Was wir ändern:** Wir schneiden Tickets kleiner und verteilen sie gleichmäßiger, damit alle regelmäßig committen. Reviews enthalten künftig immer einen schriftlichen Kommentar dazu, was geprüft wurde.

## Literatur

Beck, K. & Andres, C. (2004). *Extreme Programming Explained: Embrace Change* (2. Aufl.). Addison-Wesley.

Ries, E. (2011). *The Lean Startup*. Crown Business.

Schwaber, K. & Sutherland, J. (2020). *The Scrum Guide*. https://scrumguides.org
