# Management-Dokumentation ShiftPlanner

Autorinnen und Autoren (Anteil): Muhammed Asif Shahul Hameed 100 % (erste Fassung)
Stand: 10.11.2026 · Verantwortlich: Management (Product Owner)

## 1 Vorgehensmodell und Praktiken

Wir arbeiten hybrid: Scrum gibt den Rahmen vor, XP-Praktiken sichern die Codequalität, und eine Lean-Startup-Feedbackschleife sorgt dafür, dass wir das Richtige bauen. Diese Kombination passt zu einem kleinen Team, das echtes Kundenfeedback braucht und alle zwei Wochen ein lauffähiges Produkt zeigen soll.

**Scrum:** Wir planen in Sprints von zwei Wochen, die in GitHub als Milestones abgebildet sind (Sprint 1: 02.11.–15.11.2026). Seit dem Feedback zu P1 sind die Sprints bewusst von den Präsentationsterminen entkoppelt (Schwaber & Sutherland 2020).

**XP:** Für den Code gelten Coding-Standards, die GitHub Actions bei jedem Push automatisch prüft (Issue #22, PR #28). Jede Änderung läuft über einen Pull Request mit Review, und zu jedem Akzeptanzkriterium gibt es mindestens einen Test (Beck & Andres 2004).

**Lean Startup:** In drei Feedbackrunden mit realen Planerinnen, Planern und Mitarbeitenden (FB-01 bis FB-15) prüfen wir unsere Annahmen und leiten daraus Entscheidungen ab (E-01 bis E-03, siehe `docs/feedback/feedback.md`) (Ries 2011).

**Tracking:** Seit dem Feedback zu P2 führen wir zwei Boards, eines für das Produkt und eines für das Management. Alle Issues tragen eine Aufwandsschätzung.

## 2 Planung und Sprints

*Folgt in Sprint 2.*

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

## 5 Statistik

### 5.1 Aufwand je Person und Tätigkeit (Stunden)

*Folgt in Sprint 2.*

### 5.2 Produktivität

*Folgt in Sprint 2.*

## 6 Reflexion (fortlaufend)

**Sprint 1 – was gut lief:** Das Feedback der Planerinnen und Planer kam schnell und hat zwei offene Abweichungen (ABW-01, ABW-02) direkt geschlossen. Die automatischen Prüfungen in GitHub Actions haben Fehler früh sichtbar gemacht.

**Was wir ändern:** Wir schneiden Tickets kleiner und verteilen sie gleichmäßiger, damit alle regelmäßig committen. Reviews enthalten künftig immer einen schriftlichen Kommentar dazu, was geprüft wurde.

## Literatur

Beck, K. & Andres, C. (2004). *Extreme Programming Explained: Embrace Change* (2. Aufl.). Addison-Wesley.

Ries, E. (2011). *The Lean Startup*. Crown Business.

Schwaber, K. & Sutherland, J. (2020). *The Scrum Guide*. https://scrumguides.org
