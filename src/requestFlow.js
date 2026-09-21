export const SERVICES = {
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

export const STEPS = ['Leistung', 'Ort', 'Arbeiten', 'Umfang', 'Termin', 'Details', 'Kontakt', 'Übersicht']
export const TIMINGS = ['So bald wie möglich', 'In den nächsten 2 Wochen', 'In den nächsten 1–3 Monaten', 'An einem bestimmten Tag', 'Ich bin flexibel']
export const EMPTY_FORM = {category:'', postal_code:'', city:'', address:'', work:[], amount:'', detail:'', destination_postal_code:'', destination_city:'', timing:'', desired_date:'', description:'', contact_name:'', contact_email:''}

export function selectService(form, category) {
  if (form.category === category) return form
  return {...form, category, work:[], amount:'', detail:'', destination_postal_code:'', destination_city:''}
}

export function validateStep(step, form, user, today) {
  if (step === 0 && !SERVICES[form.category]) return 'Bitte wähle eine Leistung aus.'
  if (step === 1) {
    if (!/^\d{5}$/.test(form.postal_code)) return 'Bitte gib eine fünfstellige Postleitzahl ein.'
    if (form.city.trim().length < 2) return 'Bitte gib den Ort des Auftrags ein.'
  }
  if (step === 2 && (!form.work.length || form.work.some(work=>!SERVICES[form.category]?.choices.includes(work)))) return 'Bitte wähle mindestens eine passende Arbeit aus.'
  if (step === 3) {
    if (form.amount && (!Number.isFinite(Number(form.amount)) || Number(form.amount) <= 0 || Number(form.amount) > 1000000)) return 'Bitte gib eine gültige Größe an oder lasse die Schätzung frei.'
    if (!SERVICES[form.category]?.detailChoices.includes(form.detail)) return 'Bitte wähle die passende Angabe aus.'
    if (form.category === 'Umzug' && (!/^\d{5}$/.test(form.destination_postal_code) || form.destination_city.trim().length < 2)) return 'Bitte gib die fünfstellige PLZ und den Ort des Umzugsziels ein.'
  }
  if (step === 4) {
    if (!TIMINGS.includes(form.timing)) return 'Bitte wähle einen Zeitraum aus.'
    if (form.timing === 'An einem bestimmten Tag') {
      const date = new Date(form.desired_date+'T12:00:00Z')
      if (!/^\d{4}-\d{2}-\d{2}$/.test(form.desired_date) || !Number.isFinite(date.getTime()) || date.toISOString().slice(0,10)!==form.desired_date || form.desired_date < today) return 'Bitte wähle einen heutigen oder zukünftigen Termin.'
    }
  }
  if (step === 5 && form.category === 'Sonstiges' && form.description.trim().length < 15) return 'Beschreibe dein Anliegen bitte mit mindestens 15 Zeichen.'
  if (step === 6 && !user) {
    if (form.contact_name.trim().length < 2) return 'Bitte gib deinen Namen ein.'
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.contact_email.trim())) return 'Bitte gib eine gültige E-Mail-Adresse ein.'
  }
  return ''
}

export function buildPayload(form, user) {
  const config = SERVICES[form.category]
  const date = form.timing === 'An einem bestimmten Tag' ? form.desired_date : ''
  const details = {
    work: form.work,
    amount: form.amount ? `${form.amount} ${config.unit}` : '',
    detail_label: config.detailLabel,
    detail: form.detail,
    timing: form.timing,
    destination: form.category === 'Umzug' ? `${form.destination_postal_code} ${form.destination_city.trim()}` : '',
    notes: form.description.trim(),
  }
  const description = [
    `Arbeiten: ${details.work.join(', ')}`,
    details.amount && `${config.amountLabel}: ${details.amount}`,
    `${details.detail_label} ${details.detail}`,
    details.destination && `Umzugsziel: ${details.destination}`,
    `Zeitraum: ${details.timing}${date ? ` (${date})` : ''}`,
    details.notes && `Zusätzliche Angaben: ${details.notes}`,
  ].filter(Boolean).join('\n')
  return {
    category:form.category, title:`${form.category}: ${form.work.join(', ')}`.slice(0,120),
    description, postal_code:form.postal_code, city:form.city.trim(), address:form.address.trim(),
    desired_date:date, contact_name:user?.name || form.contact_name.trim(), contact_email:user?.email || form.contact_email.trim(),
    details,
  }
}
