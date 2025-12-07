# IT-Lagerverwaltung – Starter
Einfaches Flask-Grundgerüst für dein Projekt.

## Schnellstart (Windows, PowerShell)
1) Python 3.11+ installieren (falls noch nicht vorhanden).
2) In diesen Ordner wechseln.
3) Virtuelle Umgebung anlegen und aktivieren:
   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
4) Abhängigkeiten installieren:
   ```powershell
   pip install -r requirements.txt
   ```
5) Starten:
   ```powershell
   python app.py
   ```
6) Im Browser öffnen: http://127.0.0.1:5000

## Nächste Schritte
- Datenbankmodell mit SQLAlchemy
- Blueprints/Routes
- Barcode, PDF, Signatur, Warnungen
