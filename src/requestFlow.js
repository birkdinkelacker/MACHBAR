export const GROUPS = {
  'Entrümpelung': {
    description: 'Wohnung, Keller oder einzelne Gegenstände', icon: 'boxes',
    question: 'Was soll entrümpelt werden?',
    choices: ['Wohnung', 'Haus', 'Keller oder Dachboden', 'Garage', 'Einzelne Möbel', 'Gewerberäume'],
    amountLabel: 'Ungefähre Fläche', unit: 'm²',
    detailLabel: 'Wie ist der Bereich erreichbar?',
    detailChoices: ['Ebenerdig', 'Über Treppen', 'Mit einem Aufzug', 'Noch unklar'],
    placeholder: 'Zum Beispiel: Die Wohnung ist möbliert. Küche und Bodenbeläge sollen bleiben.',
  },
  'Reinigung': {
    description: 'Räume, Fenster und gemeinsame Flächen', icon: 'sparkles',
    question: 'Was möchtest du reinigen lassen?',
    choices: ['Wohnung oder Haus', 'Treppenhaus', 'Fenster', 'Büro oder Gewerbe', 'Nach einer Renovierung', 'Außenflächen'],
    amountLabel: 'Ungefähre zu reinigende Fläche', unit: 'm²',
    detailLabel: 'Wie häufig wird die Reinigung benötigt?',
    detailChoices: ['Einmalig', 'Wöchentlich', 'Monatlich', 'Nach Absprache'],
    placeholder: 'Zum Beispiel: Grundreinigung vor der Wohnungsübergabe, inklusive Fenster und Küche.',
  },
  'Renovierung': {
    description: 'Wände, Böden und kleinere Reparaturen', icon: 'paint',
    question: 'Welche Arbeiten stehen an?',
    choices: ['Streichen', 'Tapezieren', 'Boden verlegen', 'Ausbessern und reparieren', 'Mehrere Räume renovieren', 'Noch nicht sicher'],
    amountLabel: 'Ungefähre betroffene Fläche', unit: 'm²',
    detailLabel: 'Wer stellt das Material bereit?',
    detailChoices: ['Material ist vorhanden', 'Der Dienstleister soll es mitbringen', 'Noch abzustimmen'],
    placeholder: 'Zum Beispiel: Zwei Zimmer weiß streichen. Die Wände müssen teilweise ausgebessert werden.',
  },
  'Gartenpflege': {
    description: 'Rasen, Hecken und Außenanlagen', icon: 'leaf',
    question: 'Welche Gartenarbeiten brauchst du?',
    choices: ['Rasen mähen', 'Hecke schneiden', 'Beete pflegen', 'Laub entfernen', 'Garten aufräumen', 'Regelmäßige Pflege'],
    amountLabel: 'Ungefähre Gartenfläche', unit: 'm²',
    detailLabel: 'Soll Grünschnitt mitgenommen werden?',
    detailChoices: ['Ja, bitte entsorgen', 'Nein, bleibt vor Ort', 'Noch unklar'],
    placeholder: 'Zum Beispiel: Hecke entlang der Einfahrt schneiden. Der Garten ist seitlich zugänglich.',
  },
  'Hausmeisterservice': {
    description: 'Laufende Betreuung rund ums Objekt', icon: 'wrench',
    question: 'Wobei brauchst du Unterstützung?',
    choices: ['Objektkontrolle', 'Kleine Reparaturen', 'Treppenhaus und Außenbereich', 'Mülltonnenservice', 'Winterdienst', 'Regelmäßige Betreuung'],
    amountLabel: 'Anzahl der zu betreuenden Einheiten', unit: 'Einheiten',
    detailLabel: 'Für welches Objekt wird der Service benötigt?',
    detailChoices: ['Einfamilienhaus', 'Mehrfamilienhaus', 'Gewerbeobjekt', 'Mehrere Objekte', 'Sonstiges'],
    placeholder: 'Zum Beispiel: Regelmäßige Betreuung eines Mehrfamilienhauses mit acht Wohnungen.',
  },
  'Umzug': {
    description: 'Umzug, Möbeltransport und Unterstützung', icon: 'truck',
    question: 'Welche Unterstützung brauchst du?',
    choices: ['Kompletter Umzug', 'Einzelne Möbel transportieren', 'Tragehilfe', 'Möbel auf- und abbauen', 'Ein- und Auspacken'],
    amountLabel: 'Ungefähre Wohnfläche am Startort', unit: 'm²',
    detailLabel: 'Wie ist der Startort erreichbar?',
    detailChoices: ['Ebenerdig', 'Über Treppen', 'Mit einem Aufzug', 'Noch unklar'],
    placeholder: 'Zum Beispiel: Umzug einer Zweizimmerwohnung. Ein Kleiderschrank muss abgebaut werden.',
  },
  'Sonstiges': {
    description: 'Dein Anliegen passt in keine Kategorie', icon: 'message',
    question: 'Worum geht es bei deinem Anliegen?',
    choices: ['Arbeiten im Gebäude', 'Arbeiten im Außenbereich', 'Mehrere Leistungen', 'Beratung zum Vorhaben'],
    amountLabel: 'Ungefähre betroffene Fläche', unit: 'm²',
    detailLabel: 'Für welches Objekt suchst du Unterstützung?',
    detailChoices: ['Wohnung oder Haus', 'Gewerbeobjekt', 'Außenanlage', 'Sonstiges'],
    placeholder: 'Beschreibe, was erledigt werden soll und welche Unterstützung du brauchst.',
  },
}

const catalog = {
  Entrümpelung: ['Wohnung entrümpeln', 'Haus entrümpeln', 'Keller oder Dachboden räumen', 'Garage räumen', 'Möbel und Sperrmüll entsorgen', 'Gewerberäume räumen'],
  Reinigung: ['Wohnungsreinigung', 'Treppenhausreinigung', 'Fensterreinigung', 'Büro- und Gewerbereinigung', 'Bauendreinigung', 'Terrassen- und Hofreinigung'],
  Renovierung: ['Wände und Decken streichen', 'Tapezieren', 'Laminat oder Vinyl verlegen', 'Wände ausbessern', 'Tapeten entfernen', 'Silikonfugen erneuern'],
  Gartenpflege: ['Rasen mähen', 'Hecken schneiden', 'Beete pflegen', 'Laub entfernen', 'Garten aufräumen', 'Grünschnitt entsorgen'],
  Hausmeisterservice: ['Objektkontrolle', 'Kleinreparaturen', 'Möbel montieren', 'Mülltonnenservice', 'Winterdienst', 'Regelmäßige Objektbetreuung'],
  Umzug: ['Kompletter Umzug', 'Möbeltransport', 'Tragehilfe', 'Umzugskartons packen'],
  Sonstiges: ['Anderes Anliegen'],
}
export const SERVICES = Object.fromEntries(Object.entries(catalog).flatMap(([group,labels])=>labels.map(label=>[label,{group,icon:GROUPS[group].icon}])))
export const STEPS = ['Leistungen', 'Ort', 'Umfang', 'Termin', 'Details', 'Kontakt', 'Übersicht & Fotos']
export const TIMINGS = ['So bald wie möglich', 'In den nächsten 2 Wochen', 'In den nächsten 1–3 Monaten', 'An einem bestimmten Tag', 'Ich bin flexibel']
export const EMPTY_FORM = {services:[],scopes:{},postal_code:'',city:'',address:'',destination_postal_code:'',destination_city:'',timing:'',desired_date:'',description:'',contact_name:'',contact_email:''}
export const selectedGroups = form => [...new Set(form.services.map(name=>SERVICES[name]?.group).filter(Boolean))]
export const needsDestination = form => form.services.some(name=>['Kompletter Umzug','Möbeltransport'].includes(name))

export function selectService(form, name) {
  if (!Object.hasOwn(SERVICES,name)) return form
  const services = form.services.includes(name) ? form.services.filter(x=>x!==name) : [...form.services,name]
  const next={...form,services}
  next.scopes=Object.fromEntries(selectedGroups(next).map(group=>[group,form.scopes[group]||{amount:'',detail:''}]))
  if(!needsDestination(next)){next.destination_postal_code='';next.destination_city=''}
  return next
}

export function validateStep(step, form, user, today) {
  if(step===0 && (!form.services.length || form.services.some(name=>!Object.hasOwn(SERVICES,name)))) return 'Bitte wähle mindestens eine Leistung aus.'
  if(step===1){
    if(!/^\d{5}$/.test(form.postal_code))return 'Bitte gib eine fünfstellige Postleitzahl ein.'
    if(form.city.trim().length<2)return 'Bitte gib den Ort des Auftrags ein.'
    if(needsDestination(form)&&(!/^\d{5}$/.test(form.destination_postal_code)||form.destination_city.trim().length<2))return 'Bitte gib die fünfstellige PLZ und den Ort des Umzugsziels ein.'
  }
  if(step===2)for(const group of selectedGroups(form)){
    const scope=form.scopes[group]||{}
    if(scope.amount&&(!Number.isFinite(Number(scope.amount))||Number(scope.amount)<=0||Number(scope.amount)>1000000))return `${group}: Bitte gib eine gültige Größe an oder lasse die Schätzung frei.`
    if(scope.detail&&!GROUPS[group].detailChoices.includes(scope.detail))return `${group}: Bitte prüfe deine Auswahl.`
  }
  if(step===3){
    if(!TIMINGS.includes(form.timing))return 'Bitte wähle einen Zeitraum aus.'
    if(form.timing==='An einem bestimmten Tag'){
      const date=new Date(form.desired_date+'T12:00:00Z')
      if(!/^\d{4}-\d{2}-\d{2}$/.test(form.desired_date)||!Number.isFinite(date.getTime())||date.toISOString().slice(0,10)!==form.desired_date||form.desired_date<today)return 'Bitte wähle einen heutigen oder zukünftigen Termin.'
    }
  }
  if(step===4&&form.services.includes('Anderes Anliegen')&&form.description.trim().length<15)return 'Beschreibe dein weiteres Anliegen bitte mit mindestens 15 Zeichen.'
  if(step===5&&!user){
    if(form.contact_name.trim().length<2)return 'Bitte gib deinen Namen ein.'
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.contact_email.trim()))return 'Bitte gib eine gültige E-Mail-Adresse ein.'
  }
  return ''
}

export function buildPayload(form,user){
  const groups=selectedGroups(form)
  const date=form.timing==='An einem bestimmten Tag'?form.desired_date:''
  const scopes=groups.map(group=>({group,amount:form.scopes[group]?.amount?`${form.scopes[group].amount} ${GROUPS[group].unit}`:'',detail_label:GROUPS[group].detailLabel,detail:form.scopes[group]?.detail||''}))
  const details={work:form.services,services:form.services,scopes,timing:form.timing,destination:needsDestination(form)?`${form.destination_postal_code} ${form.destination_city.trim()}`:'',notes:form.description.trim()}
  const description=[`Leistungen: ${form.services.join(', ')}`,...scopes.filter(s=>s.amount||s.detail).map(s=>`${s.group}: ${[s.amount,s.detail&&`${s.detail_label} ${s.detail}`].filter(Boolean).join(' · ')}`),details.destination&&`Zielort: ${details.destination}`,`Zeitraum: ${details.timing}${date?` (${date})`:''}`,details.notes&&`Zusätzliche Angaben: ${details.notes}`].filter(Boolean).join('\n')
  return {category:groups.length===1?groups[0]:'Mehrere Leistungen',title:(form.services.length>2?`${form.services[0]} + ${form.services.length-1} weitere Leistungen`:form.services.join(' & ')).slice(0,120),description,postal_code:form.postal_code,city:form.city.trim(),address:form.address.trim(),desired_date:date,contact_name:user?.name||form.contact_name.trim(),contact_email:user?.email||form.contact_email.trim(),details}
}
