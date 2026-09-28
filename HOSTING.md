# MACHBAR auf Vercel und PythonAnywhere aktualisieren

- Frontend: https://www.machbar-handwerk.de/ (machbar-handwerk.de leitet auf die www-Adresse weiter)
- Backend: https://birk.eu.pythonanywhere.com/
- Repository: https://github.com/birkdinkelacker/MACHBAR

Das Frontend verwendet `/api`. `vercel.json` leitet diese Aufrufe bereits an das Backend weiter. Lokal bleibt Vite mit `127.0.0.1:8000` verbunden; es ist kein Umschalten im Code nötig.

## 1. Bestehende PythonAnywhere-Konfiguration notieren und Daten sichern

Im [Web-Tab](https://eu.pythonanywhere.com/user/birk/webapps/) die bestehende App öffnen. Projektordner unter **Code**, Python-Version, Virtualenv und WSGI-Konfigurationsdatei prüfen. Die Beispiele unten setzen `/home/birk/MACHBAR` voraus; bei einem anderen Projektordner den Pfad entsprechend anpassen.

Den bestehenden Wert von `MACHBAR_DB` in der WSGI-Konfiguration bzw. der dort geladenen Umgebung beibehalten. Ohne diesen Wert liegt die Datenbank standardmäßig unter `backend/machbar.db` im Projektordner. Keinen neuen, leeren Datenbankpfad einsetzen: Sonst wären bisherige Konten und Aufträge nicht sichtbar.

Vor dem ersten Reload mit dem neuen Stand eine SQLite-Sicherung erstellen. Dazu in einer Bash-Konsole den **tatsächlich verwendeten** Datenbankpfad einsetzen:

```bash
python - <<'PY'
from pathlib import Path
import sqlite3
from datetime import datetime

source = Path('/home/birk/MACHBAR/backend/machbar.db')  # ggf. bestehenden MACHBAR_DB-Wert einsetzen
assert source.is_file(), f'Datenbank nicht gefunden: {source}'
target = source.with_name(source.stem + '-backup-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.db')
with sqlite3.connect(source.as_uri() + '?mode=ro', uri=True) as src, sqlite3.connect(target) as dst:
    src.backup(dst)
print('Sicherung:', target)
PY
```

Diese Sicherung enthält auch die gespeicherten Auftragsfotos. Die lokale Entwicklungsdatenbank nicht auf den Server kopieren.

## 2. Code und Abhängigkeiten aktualisieren

Unter **Web → Virtualenv → Start a console in this virtualenv** eine Konsole öffnen. Damit werden die Pakete in derselben Python-Umgebung installiert, die die Web-App verwendet.

```bash
cd /home/birk/MACHBAR
git status --short
git pull --ff-only origin main
python -m pip install -r backend/requirements.txt
```

Bei lokalen Änderungen oder Git-Konflikten anhalten und die Änderungen prüfen; kein `git reset --hard` verwenden. Falls der Projektordner bisher kein Git-Checkout ist, die aktuellen Repository-Dateien über **Files** in den bestehenden Projektordner übertragen. Datenbank und Hosting-Konfiguration dabei beibehalten. Die Pakete aus `backend/requirements.txt` trotzdem installieren.

## 3. WSGI-Einstieg prüfen

Die **im Web-Tab verlinkte WSGI-Konfigurationsdatei** muss die aktuelle Anwendung aus `backend/wsgi.py` importieren. Eine alte, direkt in dieser Datei kopierte API-Implementierung würde die neuen Funktionen nicht übernehmen.

Beispiel für den Standard-Datenbankpfad; bestehende abweichende Pfade übernehmen:

```python
import os
import sys

sys.path.insert(0, '/home/birk/MACHBAR')
os.environ['MACHBAR_DB'] = '/home/birk/MACHBAR/backend/machbar.db'

from backend.wsgi import application
```

Der aktuelle WSGI-Einstieg unterstützt GET, POST, PATCH und DELETE sowie persönliche Gastlinks. Er ergänzt das Datenbankschema beim Laden automatisch. Bestehende Konten und Aufträge bleiben erhalten. Das Admin-Konto muss nicht neu erstellt werden. Automatische E-Mails sind ausgeschaltet; SMTP-Zugangsdaten werden nicht benötigt.

## 4. Reload und Kontrolle

Im Web-Tab **Reload birk.eu.pythonanywhere.com** klicken. Danach prüfen:

- https://birk.eu.pythonanywhere.com/api/health liefert `{"ok": true}`.
- https://www.machbar-handwerk.de/api/health liefert ebenfalls `{"ok": true}`.
- Adminportal: alle Auftragsstatus und der gemeinsame Bereich **Auftrag koordinieren** erscheinen.
- Bei einem dafür angelegten Testauftrag ein Angebot samt Notiz speichern; anschließend im Kundenportal kontrollieren.

Ein erfolgreicher Healthcheck allein bestätigt noch nicht, dass der neue Code geladen wurde. Bei Fehlern den **Error log** aus dem Web-Tab ansehen.

## Vercel

Bei bestehender GitHub-Verknüpfung veröffentlicht Vercel einen Push auf den konfigurierten Produktionsbranch automatisch. Im Projekt unter **Deployments** prüfen, dass der neueste Commit den Status **Ready** hat. Andernfalls das Deployment dort neu anstoßen. Ein GitHub-Push aktualisiert PythonAnywhere nicht automatisch.

Quellen: [PythonAnywhere: Code, Virtualenv, WSGI und Reload](https://help.pythonanywhere.com/pages/DeployExistingDjangoProject/), [PythonAnywhere: Konsole der Web-App-Umgebung](https://help.pythonanywhere.com/pages/DebuggingImportError/).
