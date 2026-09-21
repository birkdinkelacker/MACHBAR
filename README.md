# MACHBAR

Responsive Website mit React/Vite und schlankem Python-Backend (Standardbibliothek + SQLite). Öffentliche Kontaktadresse: [info.machbar@gmx.de](mailto:info.machbar@gmx.de).

## Lokal starten

Node.js 20+ und Python 3.10+ werden benötigt. In zwei Terminals:

```powershell
python backend/server.py
```

```powershell
npm install
npm run dev
```

Vite zeigt die lokale URL an. API-Anfragen werden im Entwicklungsmodus an Port 8000 weitergeleitet. Ein Produktionsbuild entsteht mit `npm run build` im Ordner `dist/`. Der Python-Server liefert danach auch das gebaute Frontend auf Port 8000 aus. Für einen Host kann `MACHBAR_HOST=0.0.0.0` und `MACHBAR_PORT` passend gesetzt werden.

## Admin-Zugang

Vor dem ersten Start des Backends Umgebungsvariablen setzen:

```powershell
$env:MACHBAR_ADMIN_EMAIL='admin@eigene-domain.de'
$env:MACHBAR_ADMIN_PASSWORD='ein-langes-zufälliges-passwort'
python backend/server.py
```

Der Admin wird beim ersten Start mit diesen Werten angelegt. Registrierungen über die Website sind nur als Kunde oder Dienstleister möglich.

## Anfrageablauf

Unter `/#/anfrage` führt ein Formular durch Leistung, Ort, Arbeiten, Umfang, Termin, ergänzende Angaben, Kontakt und eine bearbeitbare Zusammenfassung. Die Fragen passen sich der Leistung an; beim Umzug wird auch der Zielort erfasst. Eine Vorauswahl über die Leistungskarten der Startseite wird übernommen.

Anfragen sind als Gast oder mit Kundenkonto möglich. Entwürfe bleiben im aktuellen Browser-Tab bis zum erfolgreichen Absenden erhalten. Alle Antworten werden sowohl als lesbare Beschreibung für die Portale als auch strukturiert in SQLite gespeichert. Beim Start ergänzt das Backend die dafür benötigte Spalte automatisch in bestehenden Datenbanken.

Prüfungen: `node --test src/requestFlow.test.js`, `python -m unittest backend.test_api` und `npm run build`. Die API-Tests verwenden eine separate Testdatenbank.

## Wichtige Hinweise zum Live-Betrieb

Der MVP speichert Daten lokal in `backend/machbar.db` (oder `MACHBAR_DB`). Für einen öffentlichen Betrieb müssen eine eigene Domain, HTTPS, ein dauerhaftes Datenvolume samt Backup, Impressum und Datenschutzerklärung ergänzt werden. Die offenen Anfragen werden derzeit manuell im Adminportal zugewiesen; automatische Benachrichtigungen, Zahlungen und Terminbuchungen sind noch nicht integriert.

Ein kleiner Python-Host mit persistentem Speicher genügt technisch. Alternativ können Frontend und API getrennt gehostet werden; dann müssen API-URL und CORS passend konfiguriert werden. Der aktuelle Stand geht von gemeinsamem Origin mit `/api`-Weiterleitung aus.
