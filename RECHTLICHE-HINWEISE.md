# MACHBAR: Prüfung vor Veröffentlichung der Rechtstexte

Stand: 28. September 2026. Interne Arbeitsnotiz, kein Bestandteil der öffentlich ausgelieferten Seiten.

Die Seiten `/#/impressum` und `/#/datenschutz` sind **Entwürfe**. Sie beschreiben den derzeitigen Code und verwenden die von Birk genannten Kontaktdaten. Sie ersetzen keine auf den konkreten Betrieb abgestimmte rechtliche Prüfung. Die Entwurfskennzeichnung erst nach Klärung der folgenden Punkte entfernen. Der Upload zu GitHub wurde von Birk am 28. September 2026 beauftragt; die Entwurfskennzeichnung bleibt bestehen.

## 1. Tatsächlicher Betreiber und Verantwortlicher

Bestätigt: Birk Dinkelacker, Mühlenweg 10, 69412 Eberbach, Deutschland; birkdinkelacker3@gmail.com; +49 176 84 266 852. Zusätzlich bestehender Servicekontakt: info.machbar@gmx.de.

Birk hat mitgeteilt, dass er MACHBAR mit einem Freund betreibt und das Unternehmen noch nicht angemeldet ist. Name und Anschrift des Freundes, genaue Anbieterbezeichnung, Rechtsform und Vertretung sind bislang nicht bekannt. Eine fehlende Gewerbeanmeldung beantwortet nicht die Frage nach der zivilrechtlichen Rechtsform; eine GbR kann gegebenenfalls bereits durch gemeinsames Handeln entstehen. Keine Einzelunternehmerschaft oder alleinige datenschutzrechtliche Verantwortlichkeit unterstellen.

Vor Veröffentlichung klären:

- Vollständiger Anbieter nach § 5 DDG einschließlich gegebenenfalls beider Gesellschafter und Vertretungsregelung; tatsächlicher Verantwortlicher nach DSGVO.
- Bei getrennter gemeinsamer Verantwortlichkeit gegebenenfalls Regelung nach Art. 26 DSGVO; nicht automatisch aus zwei beteiligten Personen ableiten.
- Register und Registernummer, falls vorhanden; USt-ID oder Wirtschafts-ID, falls vorhanden. Keine persönliche Steuer-ID oder Steuernummer veröffentlichen.
- Ob MACHBAR nur vermittelt/koordiniert oder selbst Leistungen anbietet; bei erlaubnispflichtigen oder reglementierten Tätigkeiten zusätzliche Pflichtangaben prüfen.
- Anwendbarkeit der Informationspflichten nach § 36 VSBG sowie tatsächliche Bereitschaft/Verpflichtung zur Verbraucherschlichtung. Keine ungeprüfte Teilnahme- oder Nichtteilnahmeerklärung einsetzen. Keinen veralteten Link zur eingestellten EU-OS-Plattform ergänzen.

## 2. Hosting und E-Mail

Frontend: Vercel (`machbar-rose.vercel.app`). Die Vercel-Rewrite leitet auch API-Anfragen und deren Inhalte weiter. Backend: europäische PythonAnywhere-Instanz (`birk.eu.pythonanywhere.com`), SQLite-Datenbank und Fotos. Ein europäischer Hostname garantiert keine ausschließlich europäische Verarbeitung durch alle Beteiligten.

Laut Birk sind Datenschutzverträge noch nicht abgeschlossen. Tatsächliche Vertragslage prüfen: Manche Anbieter beziehen ihre DPA bereits in den Hauptvertrag ein. Vertrag/Bestätigung sichern, Leistungsumfang, Unterauftragnehmer, Sicherheitsmaßnahmen, internationale Zugriffe und Lösch-/Protokollfristen prüfen. Vercel veröffentlicht eine DPA mit Standardvertragsklauseln; deren Veröffentlichung allein beweist weder den konkreten Vertragsschluss noch die Zulässigkeit sämtlicher Übermittlungen. Bei PythonAnywhere genaue Vertragsgesellschaft klären; deren Anbieterinformationen nennen PythonAnywhere LLP und Anaconda Services (UK) Limited.

Für GMX und Gmail geschäftliche Nutzbarkeit, datenschutzrechtliche Rollen, Verträge, internationale Übermittlungen und Einstellungen prüfen. Nicht behaupten, dass ein privates Gmail-Konto bereits unter einen Google-Workspace-Auftragsverarbeitungsvertrag fällt. Die öffentlich angegebenen Adressen können manuell kontaktiert werden; automatische E-Mails der Anwendung sind deaktiviert.

Im Anbieter-Dashboard zusätzlich prüfen, ob außerhalb des Repositorys Analytics, Vercel Speed Insights, Tracking oder andere Dienste aktiviert wurden. Der Code bindet solche Dienste nicht ein. Entsprechend die Erklärung anpassen, falls das Hosting zusätzliche Dienste verwendet.

## 3. Löschung tatsächlich organisieren

Bestätigt: Noch keine festen Löschfristen. Der Code bewahrt Konten und sämtliche Auftragsstatus ohne automatische Löschfrist auf. Admin kann Aufträge manuell löschen; dabei werden zugehörige Fotos, Notizen und Angebote aus der aktiven Datenbank entfernt. Gastlinks laufen nicht zeitgesteuert ab. Kontolöschung muss bislang administrativ bearbeitet werden; es gibt keine Selbstbedienungsfunktion.

Vor Veröffentlichung ein umsetzbares Löschkonzept beschließen und technisch/organisatorisch einrichten, anschließend konkrete Fristen oder nachvollziehbare Kriterien in Abschnitt „Speicherdauer“ einsetzen:

- Unverfolgte, zurückgezogene und abgelehnte Anfragen getrennt von abgeschlossenen Aufträgen behandeln.
- Für Auftragstexte, Fotos, Angebote, Rechnungs-/Buchhaltungsunterlagen, Konten, Sitzungsdatensätze, E-Mails und Protokolle jeweils Zweck und Aufbewahrungsbedarf bestimmen. Gesetzliche Aufbewahrung nicht pauschal auf alle Fotos oder Kontodaten übertragen.
- Verantwortliche Person und regelmäßige Prüfung/Löschung festlegen; Löschbegehren dokumentiert bearbeiten.
- Sicherungen mit begrenzter Vorhaltezeit und Wiederherstellungsverfahren berücksichtigen. Die manuelle Sicherung auf PythonAnywhere enthält alte Daten weiter; kein sofortiges rückstandsloses Löschen aller Kopien behaupten.
- Zugriffsberechtigungen prüfen und Gastlinks bei Bedarf sperren können. Die serverseitige Anmeldung läuft nach 14 Tagen ab; abgelaufene Sitzungsdatensätze werden derzeit nicht automatisch bereinigt.

## 4. Umgesetzte technische Anpassungen

- Impressum und Datenschutzerklärung aus globalem Footer, Anfrageprozess und Adminportal erreichbar; ohne Anmeldung und unabhängig vom erfolgreichen Laden der API.
- Datenschutzhinweis bei Registrierung und vor dem Absenden einer Anfrage; Links aus dem Anfrageprozess öffnen einen separaten Tab, damit die aktuelle Fotoauswahl erhalten bleibt.
- Keine pauschale Pflicht-Einwilligung für notwendige Vertragsverarbeitung hinzugefügt.
- DM Sans, Manrope und das bereits verwendete Titelbild lokal eingebunden. Keine direkten Font-/Bildabrufe zu Google Fonts oder Unsplash mehr. Lizenzdateien und Quellen unter `public/fonts` beziehungsweise `public/ASSET-SOURCES.md`.
- Datenfreigabe beschrieben: Administration sieht Kontakte; zugewiesene Dienstleister sehen Details und Fotos vor Annahme, gesonderte Kontakt-/Adressfelder erst danach. Foto-Inhalte werden nicht automatisch anonymisiert.

## Quellen für die rechtliche Prüfung

- [§ 5 DDG – Anbieterkennzeichnung](https://www.gesetze-im-internet.de/ddg/__5.html)
- [DSGVO, insbesondere Art. 5, 6, 13–22, 26, 28, 44 ff. und 77](https://eur-lex.europa.eu/eli/reg/2016/679/oj)
- [§ 25 TDDDG – Endgerätespeicherung](https://www.gesetze-im-internet.de/ttdsg/__25.html)
- [§ 36 VSBG – Verbraucherstreitbeilegung](https://www.gesetze-im-internet.de/vsbg/__36.html)
- [Vercel DPA](https://vercel.com/legal/dpa), [Privacy Notice](https://vercel.com/legal/privacy-notice)
- [PythonAnywhere Anbieterinformationen](https://www.pythonanywhere.com/about/company_details/), [Datenschutz](https://www.pythonanywhere.com/privacy_v2/)
- [Google Datenschutz](https://policies.google.com/privacy?hl=de), [GMX Datenschutz](https://agb-server.gmx.net/datenschutz)
- [LfDI Baden-Württemberg: Kontakt](https://www.baden-wuerttemberg.datenschutz.de/kontakt-aufnehmen/), [Beschwerde](https://www.baden-wuerttemberg.datenschutz.de/beschwerde/)

Die öffentlich verfügbaren PythonAnywhere-Datenschutzhinweise enthalten teils ältere Rechtsbezüge; für aktuelle Übermittlungsgarantien und Vertragsunterlagen direkt den Anbieter heranziehen.
