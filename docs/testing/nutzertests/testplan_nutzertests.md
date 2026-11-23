# Testplan Akzeptanztests mit Nutzenden (TC-M)

Verantwortlich: Muhammed Asif Shahul Hameed (Anforderungen/PO) · QS: Anil Duth · Stand: 18.11.2026 · Grundlage: `testkonzept.md`, Abschnitt 2; `testfaelle.md`, Abschnitt 5

## 1 Ziel und Anlass

Prof. Petersen hat in P4 empfohlen, künftiges Feedback zu erheben, indem Planerinnen, Planer und Mitarbeitende konkrete Aufgaben auf unserer Website lösen. Diese Tests prüfen, ob reale Nutzende die Kernabläufe ohne Hilfe bewältigen (Akzeptanz aus Nutzersicht), messen die Bearbeitungszeiten aus QR-05 und QR-06 und liefern Feedback, das wie bisher als FB-Eintrag mit Konsequenz dokumentiert wird. Der Durchgang vor P5 (20.–23.11.) ist ein Pilot mit vier Personen; der vollständige Durchgang folgt zu P6 (02.12.).

## 2 Teilnehmende

| Kennung | Rolle | Betrieb | Betreut von | Demokonto | Planungsmonat | Aufgabenwoche |
|---|---|---|---|---|---|---|
| NT-P1 | Planung | Deichmann | Asif | nora.krueger@example.com | Dezember 2026 | P1: 07.–12.12.2026 |
| NT-P2 | Planung | Netto | Anil | nora.krueger@example.com | Januar 2027 | P1: 04.–09.01.2027 |
| NT-M1 | Mitarbeitende | Deichmann | Asif | mia.hansen@example.com | Dezember 2026 | M1: 07.–11.12.2026 |
| NT-M2 | Mitarbeitende | Netto | Anil | tom.weber@example.com | Januar 2027 | M1: 04.–08.01.2027 |
| NT-P3 | Planung | Dienstleistung (ergänzt) | Bennet | nora.krueger@example.com | Januar 2027 | P1: 04.–09.01.2027 |
| NT-M3 | Mitarbeitende | Dienstleistung (ergänzt) | Bennet | tom.weber@example.com (M2-Wiederholung: lea.meyer@example.com) | Januar 2027 | M1: 04.–08.01.2027 |

Vor dem Versand trägt die betreuende Person Konto, Planungsmonat und Aufgabenwoche in die Leerfelder des Aufgabenblatts ein. Für Aufgabe M2 (Novemberplan, Woche 09.–14.11.2026) sind die richtigen Antworten nach der Vorbereitung im veröffentlichten Plan nachzusehen.

NT-P3 und NT-M3 wurden nachträglich aufgenommen, um die reine Einzelhandels-Stichprobe um einen Dienstleistungsbetrieb zu erweitern; sie teilten Konten und Monat mit NT-P2/NT-M2 (Einschränkung, siehe `ergebnisse_p5.md`, Abschnitt 5). NT-P1 bis NT-M2 sind dieselben Personen wie in den Feedbackrunden 2 und 3, damit Veränderungen vergleichbar sind. Jede Planungsperson arbeitet in einem eigenen Monat, damit sich die Tests in der gemeinsamen Demo nicht gegenseitig stören. Passwort aller Demokonten: `ShiftDemo2026!`. Es werden ausschließlich fiktive Daten eingegeben; die Ergebnisse werden pseudonymisiert als FB-16 bis FB-21 in `docs/feedback/feedback.md` übernommen.

## 3 Vorbereitung der Demo (vor dem ersten Test, Bennet)

Die Online-Demo arbeitet mit dem echten Datum. Der Demomonat November ist deshalb für Eingaben bereits gesperrt (Frist 28.10.); jede Testperson braucht einen eigenen offenen Monat. Die Vorbereitung übernimmt das Kommando `python manage.py prepare_usertests`, das im Startbefehl der Demo nach `seed_demo` ausgeführt wird. Es stellt folgenden Zustand her:

1. Der Novemberplan ist erzeugt und veröffentlicht, damit Mitarbeitende in Aufgabe M2 einen Plan finden.
2. Dezember 2026 ist geöffnet mit Abgabefrist 30.11.2026, Januar 2027 mit Abgabefrist 15.12.2026.
3. In beiden Monaten haben alle Mitarbeitenden außer Mia (Dezember) bzw. Tom (Januar) bereits Verfügbarkeiten abgegeben, damit die Planungspersonen einen realistischen Plan erzeugen können.
4. In beiden Monaten ist **kein** Personalbedarf eingetragen; das ist Aufgabe P1.
5. Je Monat ist eine Spätschicht (18.12.2026 bzw. 15.01.2027) für niemanden verfügbar, damit Aufgabe P2 eine Lücke findet.

Das Kommando ist idempotent: Bereits vorhandene Testmonate bleiben unverändert, sodass ein Neustart der Demo laufende Tests nicht überschreibt. Abgesichert ist es durch die Komponententests `UserTestSetupTests`. Vor dem ersten Test einmal selbst durchklicken (Rauchtest), danach nichts mehr ändern.

## 4 Ablauf je Person

Die Tests laufen unmoderiert: Die Person erhält das Aufgabenblatt per E-Mail oder Messenger, bearbeitet die Aufgaben allein auf ihrem eigenen Gerät und trägt Ergebnis, Zeit und Einschätzung direkt in das Blatt ein. Es wird bewusst keine Hilfe gegeben; genau das zeigt, wo die Oberfläche nicht selbsterklärend ist (Nielsen/Landauer 1993: bereits wenige Testpersonen decken die meisten Bedienprobleme auf). Die betreuende Person ist nur bei technischen Problemen erreichbar und notiert jede Rückfrage, weil sie selbst ein Befund ist.

Reihenfolge: Mitarbeitende können jederzeit testen. Planungspersonen sollten nach der jeweiligen Mitarbeiterperson testen (gleicher Monat), damit deren Abgabe im erzeugten Plan berücksichtigt wird; zwingend ist das nicht.

## 5 Messgrößen und Erfolgskriterien

| Messgröße | Erhebung | Kriterium |
|---|---|---|
| Aufgabenerfolg | Selbstauskunft je Aufgabe (ja / teilweise / nein) und Kontrolle in der Demo durch das Team | alle Aufgaben „ja“ |
| Bearbeitungszeit | Uhrzeit Beginn/Ende je Aufgabe | M1 (10 Slots) ≤ 5 min (QR-05); P1–P3 zusammen ≤ 30 min (QR-06) |
| Schwierigkeit je Aufgabe | Single Ease Question, 1 = sehr schwer bis 7 = sehr leicht (Sauro/Dumas 2009) | Median ≥ 5 |
| Gesamturteil | UMUX-LITE, zwei Aussagen, 1–7 (Lewis et al. 2013) | Mittelwert ≥ 5 |
| Probleme | Freitext je Aufgabe, Rückfragen an die Betreuung | jedes Problem wird FB-Eintrag mit Konsequenz |

Die Kontrolle in der Demo erfolgt direkt nach dem Test: Abgabe vorhanden (M1), Bedarf gespeichert (P1), Plan erzeugt und Korrektur gespeichert (P2), Plan veröffentlicht (P3).

## 6 Auswertung und Dokumentation

Die ausgefüllten Blätter werden in `docs/testing/nutzertests/ergebnisse_p5.md` übertragen (Vorlage `auswertung_vorlage.md`). Jedes Problem wird als FB-Eintrag mit Konsequenz in die Feedback-Dokumentation übernommen; echte Fehler werden zusätzlich als Bug-Issue angelegt (Testkonzept, Abschnitt 8). Die Ergebnisse fließen in den Testbericht P5 und die P5-Präsentation (Abschnitt „Feedback seit P4“) ein.

## Literatur

- Lewis, J. R.; Utesch, B. S.; Maher, D. E. (2013): UMUX-LITE: When there's no time for the SUS. In: *Proc. CHI 2013*, S. 2099–2102.
- Nielsen, J.; Landauer, T. K. (1993): A mathematical model of the finding of usability problems. In: *Proc. INTERACT/CHI '93*, S. 206–213.
- Sauro, J.; Dumas, J. S. (2009): Comparison of three one-question, post-task usability questionnaires. In: *Proc. CHI 2009*, S. 1599–1608.
