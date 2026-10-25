# ShiftPlanner

Web-App zur fairen, nachvollziehbaren automatischen Schichtplanung für kleine Betriebe
und Filialen mit 5–30 Mitarbeitenden. Software-Projekt WS 2026/27, Hochschule Flensburg.

## Team
| Rolle | Verantwortlich |
|---|---|
| Anforderungen + Management | Muhammed Asif Shahul Hameed |
| Architektur & Entwurf | Mahdi Fazeli |
| Implementierung | Bennet Schalow |
| Qualitätssicherung | Anil Duth |

## Starten (lokal)
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Ordner
- `docs/` – Anforderungen, Entwurf, Feedback, Tests, Management
- `apps/` – Django-Apps
- `tests/` – automatisierte Tests
