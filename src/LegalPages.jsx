import React, {useEffect} from 'react'
import {ArrowLeft, ArrowUpRight, FileText, ShieldCheck} from 'lucide-react'
import './legal.css'

const EMAIL = 'birkdinkelacker3@gmail.com'
const SERVICE_EMAIL = 'info.machbar@gmx.de'

export function LegalLinks({newTab=false}) {
  const props = newTab ? {target:'_blank', rel:'noopener noreferrer'} : {}
  return <nav className="legal-links" aria-label="Rechtliche Informationen">
    <a href="#/impressum" {...props}>Impressum</a>
    <a href="#/datenschutz" {...props}>Datenschutz</a>
  </nav>
}

export function PrivacyNotice({children}) {
  return <p className="privacy-notice">{children} <a href="#/datenschutz" target="_blank" rel="noopener noreferrer">Datenschutzerklärung <span className="legal-sr-only">(öffnet einen neuen Tab)</span><ArrowUpRight size={12} aria-hidden="true"/></a></p>
}

function Contact() {
  return <address className="legal-contact">
    <strong>Birk Dinkelacker</strong>
    <span>Mühlenweg 10<br/>69412 Eberbach<br/>Deutschland</span>
    <a href={`mailto:${EMAIL}`}>{EMAIL}</a>
    <a href="tel:+4917684266852">+49 176 84 266 852</a>
  </address>
}

function External({href, children}) {
  return <a href={href} target="_blank" rel="noopener noreferrer">{children}<span className="legal-sr-only"> (externer Link, öffnet einen neuen Tab)</span></a>
}

const privacySections = [
  {id:'kontakt', title:'Verantwortlichkeit und Kontakt', content:<>
    <p>Diese Datenschutzerklärung beschreibt die Verarbeitung personenbezogener Daten auf der MACHBAR-Webseite und in den Kunden-, Dienstleister- und Administrationsportalen.</p>
    <p>Als Ansprechpartner für Inhalte und Datenschutz wurde folgende Person benannt:</p><Contact/>
    <p>Allgemeine Anfragen zu unseren Leistungen kannst du auch an <a href={`mailto:${SERVICE_EMAIL}`}>{SERVICE_EMAIL}</a> richten.</p>
    <p className="legal-pending">Noch zu ergänzen: die vollständige Identität des rechtlich verantwortlichen Betreibers. MACHBAR wird von zwei Personen vorbereitet; die Rechtsform und die Angaben zum weiteren Betreiber sind noch nicht geklärt.</p>
  </>},
  {id:'zwecke', title:'Wofür wir deine Daten verwenden', content:<>
    <p>Wir verwenden deine Angaben, um die Webseite bereitzustellen, dein Konto zu verwalten, Auftragsanfragen zu koordinieren, Angebote zu übermitteln und die Durchführung angenommener Aufträge zu ermöglichen.</p>
    <ul><li><strong>Vertrag und vorvertragliche Anfragen:</strong> Art. 6 Abs. 1 Buchst. b DSGVO, insbesondere für Registrierung, Anfragen und Angebote.</li>
    <li><strong>Berechtigte Interessen:</strong> Art. 6 Abs. 1 Buchst. f DSGVO, insbesondere für den sicheren und störungsfreien Betrieb, die Abwehr von Missbrauch und die Bearbeitung allgemeiner Nachrichten.</li>
    <li><strong>Gesetzliche Pflichten:</strong> Art. 6 Abs. 1 Buchst. c DSGVO, soweit beispielsweise gesetzliche Aufbewahrungspflichten einschlägig sind.</li></ul>
    <p>Freiwillige Angaben sind in den Formularen entsprechend gekennzeichnet. Ohne die als Pflichtangaben gekennzeichneten Informationen können wir die jeweilige Registrierung oder Anfrage nicht bearbeiten. Wir verwenden keine automatisierte Entscheidungsfindung mit rechtlicher oder ähnlich erheblicher Wirkung und kein Profiling im Sinne von Art. 22 DSGVO. Die Zuordnung von Dienstleistern erfolgt durch die Administration.</p>
  </>},
  {id:'hosting', title:'Webseitenaufruf und Hosting', content:<>
    <p>Das Frontend wird über <strong>Vercel</strong> bereitgestellt. Auch die Anfragen an unsere Schnittstelle werden über Vercel an das Backend weitergeleitet. Das Backend einschließlich Konten, Aufträgen und Fotos läuft auf der europäischen PythonAnywhere-Instanz unter <strong>birk.eu.pythonanywhere.com</strong>.</p>
    <p>Beim Aufruf können die Hosting-Anbieter technische Verbindungs- und Protokolldaten verarbeiten, insbesondere IP-Adresse, Zeitpunkt, angeforderte Adresse, HTTP-Status, Browserinformationen und gegebenenfalls die zuvor besuchte Seite. Formular- und Auftragsdaten werden bei ihrer Übermittlung ebenfalls über die eingesetzte Hosting-Infrastruktur verarbeitet. Zweck ist die Auslieferung der Webseite sowie die Fehleranalyse und Absicherung des Betriebs; Rechtsgrundlage für die technischen Betriebsdaten ist Art. 6 Abs. 1 Buchst. f DSGVO.</p>
    <ul><li><strong>Vercel Inc.</strong>, 440 N Barranca Avenue #4133, Covina, CA 91723, USA. Weitere Angaben: <External href="https://vercel.com/legal/privacy-notice">Datenschutzhinweise von Vercel</External>.</li>
    <li><strong>PythonAnywhere:</strong> Der Anbieter nennt PythonAnywhere LLP und Anaconda Services (UK) Limited, 5 The Green, Richmond TW9 1PL, Vereinigtes Königreich. Weitere Angaben: <External href="https://www.pythonanywhere.com/about/company_details/">Anbieterinformationen</External> und <External href="https://www.pythonanywhere.com/privacy_v2/">Datenschutzhinweise</External>.</li></ul>
    <p>Bei international tätigen Anbietern können Daten auch außerhalb des Europäischen Wirtschaftsraums verarbeitet werden, insbesondere in den USA. Der Einsatz einer europäischen Instanz allein schließt Zugriffe aus anderen Ländern nicht aus. Vercel stellt in seinem <External href="https://vercel.com/legal/dpa">Datenschutzvertrag</External> unter anderem Standardvertragsklauseln bereit.</p>
    <p className="legal-pending">Noch zu prüfen und zu ergänzen: die tatsächlich geltenden Verträge zur Auftragsverarbeitung, die genaue Vertragsgesellschaft von PythonAnywhere, Speicherorte und Protokollfristen sowie die konkret anwendbaren Garantien oder Angemessenheitsbeschlüsse für Drittlandübermittlungen. Ein wirksamer Abschluss dieser Verträge ist bislang nicht bestätigt.</p>
  </>},
  {id:'konto', title:'Registrierung und Benutzerkonto', content:<>
    <p>Bei der Registrierung erheben wir deinen Namen, deine E-Mail-Adresse, deine Telefonnummer und ein Passwort. Optional kannst du ein Unternehmen angeben. Außerdem speichern wir deine Rolle als Kunde oder Dienstleister und den Erstellungszeitpunkt deines Kontos. Dein Passwort wird als gesalzener Passwort-Hash gespeichert, nicht im Klartext.</p>
    <p>Diese Daten dienen der Anmeldung, der Zuordnung deiner Anfragen und Angebote sowie der Kontaktaufnahme im Zusammenhang mit dem Auftrag. Rechtsgrundlage ist Art. 6 Abs. 1 Buchst. b DSGVO. Berechtigte Administratoren können die für die Koordination erforderlichen Kontaktdaten, einschließlich Telefonnummer, einsehen.</p>
  </>},
  {id:'auftraege', title:'Anfragen, Angebote und Auftragsdaten', content:<>
    <p>Bei einer Anfrage verarbeiten wir die gewählten Leistungen, Umfang und Beschreibung, Ort und Postleitzahl, eine gegebenenfalls angegebene genaue Adresse, bei Transporten den Zielort, Terminwünsche einschließlich Wochentagen und Zeitfenstern sowie deine Kontaktdaten. Hinzu kommen gegebenenfalls Fotos, Angebote mit Preis- und Terminvorschlägen, deine Annahme oder Ablehnung, Zeitpunkte, Auftragsstatus und interne Koordinationsnotizen.</p>
    <p>Diese Verarbeitung erfolgt zur Bearbeitung deiner Anfrage, Vermittlung und Abstimmung der gewünschten Leistung auf Grundlage von Art. 6 Abs. 1 Buchst. b DSGVO. Die Administration kann Aufträge und ihren Verlauf einsehen. Interne Koordinationsnotizen sind der Administration vorbehalten.</p>
    <p>Eine Anfrage ist auch ohne Konto möglich. Dabei sind Name und E-Mail-Adresse Pflichtangaben; eine Telefonnummer ist bei der Gastanfrage freiwillig. Dein persönlicher Auftragslink ermöglicht den Zugriff auf die Anfrage und ihre Angebote. <strong>Jeder, der diesen Link besitzt, kann auf diese Informationen zugreifen und Angebote beantworten.</strong> Bewahre ihn vertraulich auf. Der Link hat derzeit kein festes Ablaufdatum und verliert seine Funktion mit der Löschung des Auftrags.</p>
    <p>Neue Angebote erscheinen im Portal beziehungsweise über den persönlichen Auftragslink. Automatische Benachrichtigungen per E-Mail werden derzeit nicht versendet.</p>
  </>},
  {id:'dienstleister', title:'Welche Informationen Dienstleister erhalten', content:<>
    <p>Ein einem Auftrag zugewiesener Dienstleister erhält bereits vor deiner Annahme die zur Einschätzung erforderlichen Auftragsinformationen, insbesondere Leistungen, Beschreibung, Umfang, Terminwünsche und Fotos. Als Region werden der Ort und eine verkürzte Postleitzahl angezeigt.</p>
    <p><strong>Die gesondert erfassten Kontaktinformationen und die genaue Adresse werden dem zugewiesenen Dienstleister erst nach deiner Annahme eines Angebots freigegeben.</strong> Dazu gehören Name, E-Mail-Adresse, gegebenenfalls Telefonnummer, vollständige Postleitzahl und die angegebene Straße und Hausnummer. Dies dient der vereinbarten Kontaktaufnahme und Leistungserbringung auf Grundlage von Art. 6 Abs. 1 Buchst. b DSGVO.</p>
    <p>Bitte schreibe keine Kontaktdaten oder genaue Anschrift in frei zugängliche Beschreibungen und zeige sie nicht auf Fotos. Die technische Filterung von Texten kann nicht alle personenbezogenen Angaben erkennen; Bildinhalte werden nicht automatisch anonymisiert.</p>
    <p>Soweit Dienstleister Daten für ihre eigene Vertragsabwicklung verarbeiten, sind sie hierfür selbst verantwortlich. Ihre eigenen Datenschutzhinweise sind ergänzend zu beachten.</p>
  </>},
  {id:'fotos', title:'Freiwillige Auftragsfotos', content:<>
    <p>Du kannst bis zu sechs Fotos zur Erläuterung deines Vorhabens hochladen. Wir verarbeiten die Bildinhalte zur Einschätzung und Bearbeitung der Anfrage auf Grundlage von Art. 6 Abs. 1 Buchst. b DSGVO. Aufträge können auch ohne Fotos angefragt werden.</p>
    <p>Die hochgeladenen Bilder werden technisch verkleinert und neu als JPEG gespeichert. Ursprüngliche Bildmetadaten werden dabei nicht übernommen. Erkennbare Personen, Dokumente, Adressen oder andere Informationen im Bild bleiben jedoch sichtbar. Bitte lade nur Bilder hoch, die du weitergeben darfst, und vermeide unnötige personenbezogene oder besonders sensible Inhalte.</p>
    <p>Die Fotos werden dem Auftrag zugeordnet und können von dir, der Administration und zugewiesenen Dienstleistern eingesehen werden. Mit der Löschung eines Auftrags werden auch dessen Fotos aus der aktiven Datenbank gelöscht.</p>
  </>},
  {id:'browserspeicher', title:'Technisch notwendiger Browserspeicher', content:<>
    <p>Die Anwendung nutzt Browserspeicher für die ausdrücklich angeforderten Funktionen Anmeldung und Anfrageentwurf. Das Speichern und Auslesen stützen wir auf § 25 Abs. 2 Nr. 2 TDDDG; die anschließende Verarbeitung personenbezogener Daten auf Art. 6 Abs. 1 Buchst. b DSGVO.</p>
    <div className="legal-table-wrap"><table><caption>Speicherung durch die MACHBAR-Anwendung</caption><thead><tr><th scope="col">Funktion</th><th scope="col">Inhalt und Speicherdauer</th></tr></thead><tbody>
      <tr><th scope="row">Angemeldet bleiben</th><td>Im Local Storage wird eine Anmeldekennung gespeichert. Ihre serverseitige Gültigkeit endet nach 14 Tagen. Der Browsereintrag wird beim Abmelden oder bei einer festgestellten ungültigen Anmeldung entfernt; andernfalls kann er über seine Gültigkeit hinaus bestehen bleiben.</td></tr>
      <tr><th scope="row">Anfrageentwurf</th><td>Im Session Storage werden eingegebene Formulardaten einschließlich Kontakt- und Ortsangaben sowie der Bearbeitungsschritt gespeichert. Der Entwurf wird nach erfolgreichem Absenden entfernt. Ansonsten endet die Speicherung üblicherweise mit der Tab-Sitzung; eine Sitzungswiederherstellung des Browsers kann sie verlängern. Die Fotodateien werden dort nicht gespeichert.</td></tr>
    </tbody></table></div>
    <p>Du kannst diese Daten über die Einstellungen deines Browsers löschen. Danach musst du dich gegebenenfalls neu anmelden oder deinen Anfrageentwurf erneut eingeben. Das Löschen des Browserspeichers entfernt keine bereits an uns übermittelten Auftrags- oder Kontodaten.</p>
  </>},
  {id:'nachrichten', title:'Kontakt per E-Mail oder Telefon', content:<>
    <p>Wenn du uns kontaktierst, verarbeiten wir deine Kontaktangaben, den Inhalt deiner Nachricht und gegebenenfalls Anhänge oder Gesprächsnotizen, um dein Anliegen zu beantworten. Rechtsgrundlage ist bei vertragsbezogenen Anliegen Art. 6 Abs. 1 Buchst. b DSGVO, ansonsten unser berechtigtes Interesse an der Bearbeitung von Anfragen nach Art. 6 Abs. 1 Buchst. f DSGVO.</p>
    <p>Für die angegebenen E-Mail-Adressen werden Gmail (Google) und GMX (1&amp;1 Mail &amp; Media GmbH) genutzt. Dabei verarbeiten die E-Mail-Anbieter Nachrichten und Verbindungsdaten. Informationen findest du in den <External href="https://policies.google.com/privacy?hl=de">Datenschutzhinweisen von Google</External> und den <External href="https://agb-server.gmx.net/datenschutz">Datenschutzhinweisen von GMX</External>. Bei Google können auch Verarbeitungen außerhalb des Europäischen Wirtschaftsraums stattfinden.</p>
    <p className="legal-pending">Die für die geschäftliche Nutzung dieser Postfächer geltenden Vertragsbedingungen und gegebenenfalls erforderlichen Datenschutzvereinbarungen sowie Grundlagen für internationale Übermittlungen sind noch zu prüfen.</p>
  </>},
  {id:'speicherdauer', title:'Speicherdauer und Löschung', content:<>
    <p>Konten, Aufträge, Angebote, Statusverläufe und Fotos werden im aktuellen System nicht automatisch nach einer festen Frist gelöscht. Auch abgeschlossene oder abgelehnte Aufträge bleiben bis zur manuellen Löschung in der Administration vorhanden. Es gibt noch kein festgelegtes Löschkonzept.</p>
    <p className="legal-pending">Vor der Veröffentlichung sind Fristen und tatsächliche Löschabläufe festzulegen: für nicht weiterverfolgte Anfragen, abgeschlossene Aufträge, Konten, Fotos, Nachrichten, Protokolle und Sicherungskopien. Dabei sind Zweckfortfall, gegebenenfalls anwendbare gesetzliche Aufbewahrungspflichten und erforderliche Unterlagen zur Geltendmachung oder Abwehr von Ansprüchen zu unterscheiden. Eine unbegrenzte Vorratsspeicherung ist damit nicht gerechtfertigt.</p>
    <p>Du kannst dich mit einem Löschungsanliegen an <a href={`mailto:${EMAIL}`}>{EMAIL}</a> wenden. Soweit eine weitere Speicherung gesetzlich erforderlich ist, ist zu prüfen, welche Daten aufbewahrt werden müssen und ob ihre sonstige Nutzung einzuschränken ist. Für Sicherungskopien müssen entsprechende Lösch- und Wiederherstellungsabläufe eingerichtet werden.</p>
  </>},
  {id:'rechte', title:'Deine Datenschutzrechte', content:<>
    <p>Unter den jeweiligen gesetzlichen Voraussetzungen hast du folgende Rechte:</p>
    <ul><li>Auskunft über deine personenbezogenen Daten (Art. 15 DSGVO),</li><li>Berichtigung unrichtiger oder Vervollständigung unvollständiger Daten (Art. 16 DSGVO),</li><li>Löschung deiner Daten (Art. 17 DSGVO),</li><li>Einschränkung der Verarbeitung (Art. 18 DSGVO),</li><li>Datenübertragbarkeit bei dafür geeigneten Verarbeitungen (Art. 20 DSGVO),</li><li>Widerspruch gegen Verarbeitungen auf Grundlage berechtigter Interessen (Art. 21 DSGVO).</li></ul>
    <p><strong>Widerspruch:</strong> Soweit wir Daten auf Grundlage von Art. 6 Abs. 1 Buchst. f DSGVO verarbeiten, kannst du aus Gründen, die sich aus deiner besonderen Situation ergeben, jederzeit widersprechen. Wir verarbeiten die Daten dann nicht weiter, sofern keine zwingenden schutzwürdigen Gründe überwiegen oder die Verarbeitung der Geltendmachung, Ausübung oder Verteidigung von Rechtsansprüchen dient.</p>
    <p>Soweit eine Verarbeitung auf einer gesonderten Einwilligung beruht, kannst du diese jederzeit mit Wirkung für die Zukunft widerrufen. Die Rechtmäßigkeit der Verarbeitung bis zum Widerruf bleibt davon unberührt.</p>
    <p>Für die Ausübung deiner Rechte genügt eine Nachricht an die oben genannte Kontaktadresse. Außerdem kannst du dich nach Art. 77 DSGVO bei einer Datenschutzaufsichtsbehörde beschweren, insbesondere am Ort deines gewöhnlichen Aufenthalts, deines Arbeitsplatzes oder des vermuteten Verstoßes.</p>
    <p>Für Baden-Württemberg: <External href="https://www.baden-wuerttemberg.datenschutz.de/beschwerde/">Der Landesbeauftragte für den Datenschutz und die Informationsfreiheit Baden-Württemberg</External>, Heilbronner Straße 35, 70191 Stuttgart.</p>
  </>},
  {id:'externe-inhalte', title:'Schriftarten, Bilder und Analyse', content:<>
    <p>Die auf dieser Version der Webseite verwendeten Schriftarten, Logos und das Titelbild werden über unser eigenes Frontend ausgeliefert. Dadurch baut dein Browser für diese Inhalte keine gesonderte Verbindung zu Google Fonts oder Unsplash auf.</p>
    <p>In die Anwendung sind derzeit keine Werbetracker, externen Analysedienste, Karten, Zahlungsdienste oder Newsletter-Funktionen eingebunden. Die internen Auftragsstatistiken dienen der betrieblichen Übersicht. Externe Informationsseiten werden erst aufgerufen, wenn du einen entsprechenden Link anklickst; dort gelten die Hinweise des jeweiligen Anbieters.</p>
  </>},
]

export default function LegalPage({type}) {
  const privacy = type === 'privacy'
  const title = privacy ? 'Datenschutzerklärung' : 'Impressum'
  const Icon = privacy ? ShieldCheck : FileText
  useEffect(() => {const previous=document.title; document.title=`${title} | MACHBAR`; return()=>{document.title=previous}},[title])
  return <main className="legal-page">
    <div className="container legal-container">
      <a className="legal-back" href="#/"><ArrowLeft size={16}/>Zur Startseite</a>
      <header className="legal-header"><span className="kicker"><Icon size={16}/>RECHTLICHE INFORMATIONEN</span><h1>{title}</h1><p>Stand des Entwurfs: 28. September 2026</p></header>
      <aside className="legal-draft" aria-label="Entwurfsstatus"><strong>Entwurf zur Prüfung</strong><p>Die vollständigen Betreiberangaben, Datenschutzverträge und Löschfristen sind noch zu klären. Diese Fassung ist noch nicht zur Veröffentlichung als abschließender Rechtstext bestimmt.</p></aside>
      {privacy?<div className="legal-layout"><nav className="legal-toc" aria-label="Inhalt der Datenschutzerklärung"><strong>Auf dieser Seite</strong>{privacySections.map((section,i)=><button key={section.id} onClick={()=>{const element=document.getElementById(`privacy-${section.id}`);element?.scrollIntoView({behavior:'smooth',block:'start'});element?.focus({preventScroll:true})}}><span>{String(i+1).padStart(2,'0')}</span>{section.title}</button>)}</nav><article className="legal-content">{privacySections.map((section,i)=><section className="legal-section" key={section.id} aria-labelledby={`heading-${section.id}`}><h2 id={`privacy-${section.id}`} tabIndex={-1}><span id={`heading-${section.id}`}>{i+1}. {section.title}</span></h2>{section.content}</section>)}</article></div>:<article className="legal-content legal-imprint">
        <section className="legal-section"><h2>Angaben zum Angebot</h2><p><strong>MACHBAR</strong> – Koordination von Dienstleistungen rund um Haus und Immobilie im Raum Eberbach und Umgebung.</p><p>Die Anbieterkennzeichnung wird nach § 5 Digitale-Dienste-Gesetz (DDG) erstellt. Als Ansprechpartner und Verantwortlicher für die Inhalte wurde benannt:</p><Contact/></section>
        <section className="legal-section"><h2>Kontakt zu MACHBAR</h2><p>Für Anfragen und laufende Aufträge erreichst du uns unter <a href={`mailto:${SERVICE_EMAIL}`}>{SERVICE_EMAIL}</a>.</p></section>
        <section className="legal-section"><h2>Noch zu vervollständigen</h2><p>MACHBAR wird von Birk Dinkelacker und einem weiteren, hier noch nicht benannten Mitbetreiber vorbereitet. Eine Unternehmensanmeldung ist nach den bisherigen Angaben noch nicht erfolgt. Vor Veröffentlichung müssen die genaue Anbieterbezeichnung, Rechtsform, vertretungsberechtigten Personen und gegebenenfalls abweichende Geschäftsanschriften feststehen.</p><p>Soweit vorhanden oder erforderlich, sind Registerangaben, Umsatzsteuer- beziehungsweise Wirtschafts-Identifikationsnummer und Angaben zu erlaubnispflichtigen oder reglementierten Tätigkeiten zu ergänzen. Auch eine gegebenenfalls erforderliche Erklärung zur Verbraucherschlichtung ist noch zu prüfen.</p></section>
        <section className="legal-section"><h2>Datenschutz</h2><p>Wie die Webseite Kontaktdaten, Aufträge und Fotos verarbeitet, beschreiben wir in der <a href="#/datenschutz">Datenschutzerklärung</a>.</p></section>
      </article>}
    </div>
  </main>
}
