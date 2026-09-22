# MACHBAR

Responsive Website mit React/Vite und schlankem Python-Backend (SQLite und Pillow für die Bildverarbeitung). Öffentliche Kontaktadresse: [info.machbar@gmx.de](mailto:info.machbar@gmx.de).

## Lokal starten

Node.js 20+ und Python 3.10+ werden benötigt. In zwei Terminals:

```powershell
python -m pip install -r backend/requirements.txt
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

Unter `/#/anfrage` führt ein Formular durch Leistungen, Ort, Umfang, Termin, ergänzende Angaben, Kontakt und eine bearbeitbare Zusammenfassung mit optionalem Foto-Upload. 35 konkrete Leistungen können bereichsübergreifend kombiniert werden. Suche, Bereichsfilter und Auswahlchips erleichtern die Auswahl. Die Leistungskarten der Startseite öffnen den passenden Bereich. Angaben zum Umfang werden je ausgewähltem Bereich erfasst, der Zielort nur bei Umzug oder Möbeltransport.

Anfragen sind als Gast oder mit Kundenkonto möglich. Textentwürfe bleiben im aktuellen Browser-Tab bis zum erfolgreichen Absenden erhalten. Fotos bleiben bis zum Absenden nur im Arbeitsspeicher und müssen nach Neuladen oder Verlassen der Seite erneut ausgewählt werden. Alle Antworten werden als lesbare Beschreibung für die Portale und strukturiert in SQLite gespeichert. Beim Start ergänzt das Backend die erforderlichen Tabellen automatisch in bestehenden Datenbanken.

Bis zu 6 Fotos (JPG, PNG, WebP; jeweils höchstens 5 MB und 20 Megapixel) werden zusammen mit dem Auftrag gespeichert. Pillow prüft die Bilder, berücksichtigt ihre Ausrichtung, begrenzt die lange Seite auf 2400 Pixel und speichert JPEGs ohne ursprüngliche Metadaten. Bilder liegen als BLOBs in der SQLite-Datenbank und werden über authentifizierte Endpunkte entsprechend den Auftragsrechten ausgeliefert. Die Portale zeigen Vorschaubilder mit Vergrößerung. Ist ein Bild ungültig, wird die gesamte Anfrage abgewiesen; es entsteht kein Teilauftrag. Ein vorgeschalteter Proxy muss für `/api/jobs` mindestens 42 MiB Request-Größe zulassen.

Prüfungen: `node --test src/requestFlow.test.js`, `python -m unittest backend.test_api` und `npm run build`. Die API-Tests verwenden eine separate Testdatenbank.

## Wichtige Hinweise zum Live-Betrieb

Der MVP speichert Daten lokal in `backend/machbar.db` (oder `MACHBAR_DB`). Für einen öffentlichen Betrieb müssen eine eigene Domain, HTTPS, ein dauerhaftes Datenvolume samt Backup, Impressum und Datenschutzerklärung ergänzt werden. Die offenen Anfragen werden derzeit manuell im Adminportal zugewiesen; automatische Benachrichtigungen, Zahlungen und Terminbuchungen sind noch nicht integriert.

Ein kleiner Python-Host mit persistentem Speicher genügt technisch. Alternativ können Frontend und API getrennt gehostet werden; dann müssen API-URL und CORS passend konfiguriert werden. Der aktuelle Stand geht von gemeinsamem Origin mit `/api`-Weiterleitung aus.
