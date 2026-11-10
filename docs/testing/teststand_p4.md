# Teststand P4 – Qualitätssicherung und Testbericht

## 1. Automatisierter Testlauf (GitHub Actions)
* **Datum/Uhrzeit:** 10.11.2026
* **Umgebung:** GitHub Actions, Ubuntu
* **Testergebnis:** 49 Tests erfolgreich durchgelaufen (Status: **OK**)
* **Performance-Benchmark (QR-01):** 30 Mitarbeitende × 3 Vorlagen × 30 Tage in **0,133 s** (Anforderung: < 10 Sekunden, somit mühelos erfüllt).

## 2. Testabdeckung je Ebene
* **Modell- & Logik-Tests:** Überprüfung der Datenbankstrukturen und des Planungsalgorithmus.
* **Sicherheits- & Rollentests:** Absicherung gegen unberechtigte Zugriffe und Rollenkonflikte.
* **UI-Browser-Tests:** Automatisierte End-to-End-Tests (u. a. Playwright) für Oberflächenabläufe.

## 3. Manuelle Prüfung (Funktionstests)
* **ABW-Gh (Abgabefrist):** Getestet als Nora (Frist gesetzt) und Eva (Eingabe nach Fristablauf gesperrt). Funktioniert wie erwartet.
* **REQ-22 (Öffnungstage):** Getestet durch das Öffnen eines Sonntags. Der Tag taucht korrekt im Personalbedarf auf.

## 4. Bekannte Fehler / Issues
* **Flüchtiger UI-Test-Fehler:** Dokumentiert in Issue **#39** (*BUG: UI-Test test_mobile_360_and_keyboard_login schlägt sporadisch fehl*). Für den nächsten Sprint eingeplant.

## 5. Fazit
Die automatisierte Test-Pipeline ist stabil und grün, die Leistungsanforderungen werden massiv unterboten und die Kernfunktionen wurden erfolgreich verifiziert. Der Stand ist bereit für die Abgabe.
