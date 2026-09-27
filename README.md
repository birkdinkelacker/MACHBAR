# MACHBAR

Responsive Website mit React/Vite und schlankem Python-Backend (SQLite und Pillow für die Bildverarbeitung). Öffentliche Kontaktadresse: [info.machbar@gmx.de](mailto:info.machbar@gmx.de).

## Lokal starten

Für die Entwicklung unter Windows im Projektordner:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-dev.ps1
```

Das startet Backend und Vite im Hintergrund. Öffne `http://127.0.0.1:5173/` bzw. `http://127.0.0.1:5173/#/admin`. Frontend-Änderungen werden direkt übernommen. Nach Änderungen am Python-Code muss der Backend-Prozess neu gestartet werden; seine PID wird beim Start ausgegeben (`Stop-Process -Id <PID>`, danach das Startskript erneut ausführen). Logs stehen unter `.local/`.

Vite leitet `/api` ausschließlich an `127.0.0.1:8000` weiter. Die lokale Datenbank ist `backend/machbar.db`; Online-Konten und Online-Aufträge liegen getrennt auf PythonAnywhere. Die externe Weiterleitung in `vercel.json` wird nur beim Vercel-Deployment verwendet. Zum lokalen Testen muss sie nicht umgeschaltet werden.

## Erst lokal testen, danach veröffentlichen

Änderungen bleiben lokal, bis sie ausdrücklich veröffentlicht werden. Nach Tests und `npm run build` den geprüften Stand auf GitHub pushen. Vercel baut daraus das Frontend. Bei PythonAnywhere den Backend-Code auf denselben Stand bringen und unter **Web → Reload** neu laden; ein GitHub-Push allein aktualisiert das Backend nicht. Den dort konfigurierten Datenbankpfad beibehalten und keine lokale Testdatenbank hochladen. Vor Schemaänderungen die Online-Datenbank sichern.

Neue Registrierungen verlangen eine Telefonnummer. Bestehende Konten bleiben gültig. Das Backend ergänzt fehlende Spalten automatisch beim Initialisieren. Die Terminwahl unterstützt optionale Zeitfenster pro Wochentag; diese bleiben in der Auftragsbeschreibung und als strukturierte Daten erhalten.

### Alternative: zwei Terminals

Für die bereits installierte und gebaute Windows-Version startet `./start-local.ps1` den lokalen Server in einem ausgeblendeten Hintergrundprozess. Er bleibt nach dem Ende der Chat-Antwort erreichbar. Nach einem Windows-Neustart muss das Skript erneut gestartet werden. Die Admin-Anmeldung ist unter `http://127.0.0.1:8000/#/admin` erreichbar; Serverprotokolle liegen im ignorierten Ordner `.local/`.

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

Das Adminportal unter `/#/admin` ist ausschließlich für **info.machbar@gmx.de** freigeschaltet. Backend-Endpunkte prüfen sowohl die Rolle als auch die feste E-Mail-Adresse. Die öffentliche Registrierung reserviert diese Adresse und kann keine Adminrechte vergeben. Andere frühere Adminrollen werden beim Start zu Kundenrollen zurückgestuft. Ein bereits vorhandenes Konto mit der vorgesehenen Adresse erhält die Adminrolle und behält sein Passwort.

Falls das Konto noch nicht existiert, im Projektordner einmal ausführen:

```powershell
python backend/create_admin.py
```

Das Programm fragt verdeckt ein neues Passwort mit mindestens zwölf Zeichen ab. Es überschreibt kein bestehendes Konto. Alternativ kann beim ersten Serverstart `MACHBAR_ADMIN_PASSWORD` sicher über die Hosting-Konfiguration bereitgestellt werden. Eine frei wählbare `MACHBAR_ADMIN_EMAIL` wird nicht mehr verwendet. Passwörter gehören nicht ins Repository.

Das Dashboard bietet offene Aufträge nach Priorität, Suche und Statusfilter, Partnerzuweisung, Statuspflege, interne Notizen, Kundenkontakte und Auftragsfotos. Interne Notizen werden nicht an Kunden oder Dienstleister ausgeliefert. Kennzahlen umfassen Statusverteilung, Anfragen der letzten 30 Tage, Abschlussquote, Alter offener Anfragen, Nachfrage nach Leistungen/Orten und Partnerauslastung. Die Daten werden beim Öffnen, nach Änderungen und über „Aktualisieren“ geladen. Datumsauswertungen verwenden UTC-Tagesgrenzen; Anzeigezeiten werden im Browser lokal formatiert. Wunschtermine sind noch keine verbindlich vereinbarten Termine. Umsatz und Gewinn werden mangels finanzieller Daten nicht ausgewiesen.

Prüfungen des Adminbereichs: `node --test src/adminMetrics.test.js` und `python -m unittest backend.test_api`.

## Anfrageablauf

### Angebote und Rollen

Kunden und Dienstleister wechseln unter **Einstellungen** zwischen ihren Rollen. Die Telefonnummer ist bei der Registrierung Pflicht und wird in den Einstellungen nicht bearbeitet. Bestehende Aufträge bleiben erhalten und werden in der jeweiligen Rolle angezeigt. Adminrechte lassen sich nicht über diesen Weg vergeben.

Die Administration oder ein zugewiesener Dienstleister sendet einen geschätzten Gesamtpreis und ein bis fünf konkrete Termine. Angebote erscheinen automatisch im Kundenportal (Aktualisierung alle 15 Sekunden bei sichtbarem Tab). Annahme verlangt eine Terminauswahl; Ablehnung lässt die Kontaktdaten gesperrt. Frühere offene Angebote werden bei einem neuen Vorschlag oder einer Neuzuweisung ungültig. Nach Annahme sind Preis, Termin und Dienstleister festgehalten; ein Austausch des Dienstleisters über die Zuweisung ist dann gesperrt.

Zugewiesene Dienstleister sehen schon vor Annahme die Auftragsdetails, Leistungen, Terminwünsche und Fotos. Kundenkontaktdaten und genaue Adresse werden erst nach Annahme freigegeben; zuvor erscheint nur der Ort mit grobem PLZ-Gebiet. Bekannte Kontaktdaten werden auch in Freitexten ausgeblendet, Fotodateinamen vor Annahme neutral benannt. Bildinhalte werden nicht automatisch anonymisiert; der Foto-Upload weist deshalb darauf hin, keine Kontaktdaten oder genaue Adresse im Bild zu zeigen. Die Administration sieht die Kontaktdaten einschließlich Telefonnummer schon vorher.

Nur die Administration kann den Auftragsstatus manuell ändern. Im gemeinsamen Bereich **Auftrag koordinieren** werden Dienstleister, Status und interne Notiz gepflegt. Über **Termin & Preis mitsenden** kann beim Speichern ein Angebot ergänzt werden. Zuweisung, Notiz und Angebot werden dabei gemeinsam gespeichert; der Status wird auf **Zugewiesen** gesetzt. Bisherige Angebote stehen im aufklappbaren Verlauf. Unter **Aufträge** werden standardmäßig alle Status angezeigt, auch abgeschlossene Aufträge. Aufträge bleiben gespeichert, bis ein Admin sie mit zusätzlicher Bestätigung endgültig löscht. Dabei werden auch zugehörige Angebote, Fotos und interne Notizen entfernt.

Automatische E-Mails sind vollständig pausiert. Angebote und Entscheidungen werden in den Portalen angezeigt. Gäste speichern dafür ihren persönlichen Auftragslink auf der Bestätigungsseite. Weitere Hinweise: [EMAIL.md](EMAIL.md).

Angebots- und Berechtigungsprüfungen: `python -m unittest backend.test_api`.

Unter `/#/anfrage` führt ein Formular durch Leistungen, Ort, Umfang, Termin, ergänzende Angaben, Kontakt und eine bearbeitbare Zusammenfassung mit optionalem Foto-Upload. 54 konkrete Leistungen können bereichsübergreifend kombiniert werden. Suche, Bereichsfilter und Auswahlchips erleichtern die Auswahl. Die Leistungskarten der Startseite öffnen den passenden Bereich. Angaben zum Umfang werden je ausgewähltem Bereich erfasst, der Zielort nur bei Umzug oder Möbeltransport.

Anfragen sind als Gast oder mit Kundenkonto möglich. Textentwürfe bleiben im aktuellen Browser-Tab bis zum erfolgreichen Absenden erhalten. Fotos bleiben bis zum Absenden nur im Arbeitsspeicher und müssen nach Neuladen oder Verlassen der Seite erneut ausgewählt werden. Alle Antworten werden als lesbare Beschreibung für die Portale und strukturiert in SQLite gespeichert. Beim Start ergänzt das Backend die erforderlichen Tabellen automatisch in bestehenden Datenbanken.

Bis zu 6 Fotos (JPG, PNG, WebP; jeweils höchstens 5 MB und 20 Megapixel) werden zusammen mit dem Auftrag gespeichert. Pillow prüft die Bilder, berücksichtigt ihre Ausrichtung, begrenzt die lange Seite auf 2400 Pixel und speichert JPEGs ohne ursprüngliche Metadaten. Bilder liegen als BLOBs in der SQLite-Datenbank und werden über authentifizierte Endpunkte entsprechend den Auftragsrechten ausgeliefert. Die Portale zeigen Vorschaubilder mit Vergrößerung. Ist ein Bild ungültig, wird die gesamte Anfrage abgewiesen; es entsteht kein Teilauftrag. Ein vorgeschalteter Proxy muss für `/api/jobs` mindestens 42 MiB Request-Größe zulassen.

Prüfungen: `node --test src/requestFlow.test.js`, `python -m unittest backend.test_api` und `npm run build`. Die API-Tests verwenden eine separate Testdatenbank.

## Wichtige Hinweise zum Live-Betrieb

Der MVP speichert Daten lokal in `backend/machbar.db` (oder `MACHBAR_DB`). Für einen öffentlichen Betrieb müssen eine eigene Domain, HTTPS, ein dauerhaftes Datenvolume samt Backup, Impressum und Datenschutzerklärung ergänzt werden. Die offenen Anfragen werden derzeit manuell im Adminportal zugewiesen; Terminangebote und Kundenentscheidungen sind integriert. Automatische E-Mails sind pausiert. Zahlungen werden noch nicht abgewickelt.

Ein kleiner Python-Host mit persistentem Speicher genügt technisch. Alternativ können Frontend und API getrennt gehostet werden; dann müssen API-URL und CORS passend konfiguriert werden. Der aktuelle Stand geht von gemeinsamem Origin mit `/api`-Weiterleitung aus.
