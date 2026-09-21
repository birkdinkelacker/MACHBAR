import React, { useEffect, useRef, useState } from 'react'
import { ArrowLeft, ArrowRight, Boxes, Check, CheckCircle2, ChevronRight, ClipboardCheck, Leaf, Mail, MapPin, MessageSquareText, PaintRoller, Search, ShieldCheck, Sparkles, Truck, Wrench, X } from 'lucide-react'
import { SERVICES, STEPS, TIMINGS, EMPTY_FORM, buildPayload, selectService, validateStep } from './requestFlow'
import './request-wizard.css'

const icons = {boxes:Boxes,sparkles:Sparkles,paint:PaintRoller,leaf:Leaf,wrench:Wrench,truck:Truck,message:MessageSquareText}
const today = () => { const d=new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}` }
const draftKey = user => `machbar_request_v2_${user?.id || 'guest'}`

function readDraft(user, service) {
  try {
    const saved = JSON.parse(sessionStorage.getItem(draftKey(user)))
    if (saved?.form && Array.isArray(saved.form.work)) {
      const form={...EMPTY_FORM,...saved.form}
      if (service && service!==form.category) return {form:selectService(form,service),step:1}
      return {form,step:Math.max(0,Math.min(7,Number(saved.step)||0))}
    }
  } catch { /* A draft is optional; storage may be unavailable. */ }
  return {form:{...EMPTY_FORM,category:service},step:service?1:0}
}

function Choice({label,checked,onChange,multiple=false,icon:Icon,description}) {
  return <label className={`rq-choice ${checked?'is-selected':''} ${Icon?'with-icon':''}`}>
    <input type={multiple?'checkbox':'radio'} checked={checked} onChange={onChange} name={multiple?undefined:'wizard-choice'} />
    {Icon && <Icon size={23} strokeWidth={1.6} aria-hidden="true"/>}
    <span className="rq-choice-text"><strong>{label}</strong>{description&&<small>{description}</small>}</span>
    <span className={`rq-indicator ${multiple?'square':''}`} aria-hidden="true">{checked&&<Check size={13}/>}</span>
  </label>
}

export default function RequestWizard({user,request,Logo}) {
  const selected = new URLSearchParams(location.hash.split('?')[1]||'').get('service')
  const service = SERVICES[selected] ? selected : ''
  const [initial] = useState(()=>readDraft(user,service))
  const [form,setForm] = useState(initial.form)
  const [step,setStep] = useState(initial.step)
  const [search,setSearch] = useState('')
  const [error,setError] = useState('')
  const [busy,setBusy] = useState(false)
  const [result,setResult] = useState(null)
  const [editing,setEditing] = useState(false)
  const [closeDialog,setCloseDialog] = useState(false)
  const heading = useRef(null), errorRef = useRef(null), submitting = useRef(false), editSnapshot = useRef(null), dialogRef = useRef(null), closeRef = useRef(null)
  const config = SERVICES[form.category]
  const update = (key,value) => {setForm(f=>({...f,[key]:value}));setError('')}
  const move = next => {setError('');setStep(next)}
  const progress = Math.round((step+1)/STEPS.length*100)

  useEffect(()=>{
    if(!result) try {sessionStorage.setItem(draftKey(user),JSON.stringify({form,step}))} catch {}
  },[form,step,result,user?.id])
  useEffect(()=>{heading.current?.focus({preventScroll:true});window.scrollTo({top:0,behavior:'instant'})},[step,result])
  useEffect(()=>{if(error)errorRef.current?.focus()},[error])
  useEffect(()=>{
    if(!closeDialog)return
    const onKey=e=>{
      if(e.key==='Escape')setCloseDialog(false)
      if(e.key==='Tab'){
        const items=dialogRef.current?.querySelectorAll('button, a[href]')
        if(!items?.length)return
        const first=items[0],last=items[items.length-1]
        if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}
        else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}
      }
    }
    window.addEventListener('keydown',onKey)
    return()=>{window.removeEventListener('keydown',onKey);closeRef.current?.focus()}
  },[closeDialog])

  async function next(e) {
    e.preventDefault()
    if(submitting.current)return
    const message=validateStep(step,form,user,today())
    if(message){setError(message);return}
    if(step<7){move(editing?7:step+1);setEditing(false);return}
    for(let i=0;i<7;i++) {
      const invalid=validateStep(i,form,user,today())
      if(invalid){setStep(i);setError(invalid);setEditing(true);return}
    }
    submitting.current=true;setBusy(true);setError('')
    try {
      const response=await request('/jobs',{method:'POST',body:JSON.stringify(buildPayload(form,user))})
      setResult(response)
      try{sessionStorage.removeItem(draftKey(user))}catch{}
    } catch(err) {setError(err.message==='Failed to fetch'?'Die Verbindung ist unterbrochen. Deine Angaben bleiben erhalten. Bitte versuche es erneut.':err.message)}
    finally{submitting.current=false;setBusy(false)}
  }
  function edit(target){editSnapshot.current=form;setEditing(true);move(target)}
  function choose(category){
    if(category!==form.category&&editing){setEditing(false);editSnapshot.current=null}
    setForm(f=>selectService(f,category));setError('')
  }
  function back(){
    if(editing&&editSnapshot.current)setForm(editSnapshot.current)
    move(editing?7:step-1);setEditing(false);editSnapshot.current=null
  }

  const titles=[
    'Was möchtest du erledigen lassen?',
    form.category==='Umzug'?'Wo beginnt dein Umzug?':'Wo soll der Auftrag ausgeführt werden?',
    config?.question || 'Welche Arbeiten stehen an?',
    'Ein paar Angaben zum Umfang.',
    'Wann soll es losgehen?',
    'Was sollten wir noch wissen?',
    'Wie erreichen wir dich?',
    'Passt alles so?',
  ]
  const hints=[
    'Wähle die passende Leistung. Wir fragen anschließend nur, was für deinen Auftrag wichtig ist.',
    'Mit dem Ort können wir passende Partner in deiner Region finden.',
    'Du kannst mehrere Antworten auswählen.',
    'Eine grobe Schätzung reicht. Noch offene Details klären wir gemeinsam.',
    'Deine Angabe hilft uns bei der Planung. Der Termin wird anschließend abgestimmt.',
    'Besonderheiten, Zugänge oder deine Wünsche helfen uns, den Auftrag besser einzuschätzen.',
    user?'Für Rückfragen verwenden wir die Kontaktdaten deines Kundenkontos.':'Deine Angaben brauchen wir für Rückfragen zu deiner Anfrage.',
    'Prüfe deine Angaben. Mit dem Absenden stellst du eine kostenlose, unverbindliche Anfrage.',
  ]
  const groups = [['Leistung',0,0],['Auftrag',1,5],['Kontakt',6,6],['Prüfen',7,7]]

  return <div className="request-shell">
    <header className="rq-header"><div className="rq-header-inner"><Logo/><span className="rq-header-caption">Deine Anfrage</span><button type="button" className="rq-close" ref={closeRef} onClick={()=>result?location.hash='/':setCloseDialog(true)} aria-label="Anfrage schließen"><X size={21}/></button></div></header>
    <main className="rq-main">
      {result ? <section className="rq-success">
        <div className="rq-success-icon"><Check size={32}/></div>
        <span className="rq-eyebrow">ANFRAGE #{String(result.id).padStart(4,'0')}</span>
        <h1 ref={heading} tabIndex={-1}>Danke. Wir kümmern uns.</h1>
        <p>Deine Anfrage für <strong>{form.category}</strong> in <strong>{form.city}</strong> ist eingegangen.</p>
        <div className="rq-next-steps"><h2>So geht es weiter</h2><p><span>1</span> Wir prüfen die Angaben und suchen einen passenden Partner.</p><p><span>2</span> Wir melden uns bei dir, um Details und Termin abzustimmen.</p></div>
        {user?<a href="#/portal" className="button button-red">Zu meinen Aufträgen <ArrowRight size={18}/></a>:<><p>Du brauchst jetzt nichts weiter zu tun. Mit einem Kundenkonto unter <strong>{form.contact_email}</strong> kannst du den Status auch online verfolgen.</p><a href="#/register" className="button button-red">Kundenkonto erstellen <ArrowRight size={18}/></a><a className="rq-home" href="#/">Zur Startseite</a></>}
        <p className="rq-help">Fragen? <a href="mailto:info.machbar@gmx.de">info.machbar@gmx.de</a></p>
      </section> : user && user.role!=='customer' ? <section className="rq-success"><h1 ref={heading} tabIndex={-1}>Anfragen werden über ein Kundenkonto erstellt.</h1><p>Du bist als {user.role==='admin'?'Administrator':'Dienstleister'} angemeldet. Deine zugewiesenen Aufträge findest du im Portal.</p><a className="button button-red" href="#/portal">Zum Portal <ArrowRight size={18}/></a></section> : <>
        <div className="rq-progress-head"><span>{form.category || 'Neuer Auftrag'}</span><span>Schritt {step+1} von {STEPS.length}</span></div>
        <div className="rq-progress" role="progressbar" aria-label="Fortschritt deiner Anfrage" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress}><span style={{width:`${progress}%`}}/></div>
        <ol className="rq-stages">{groups.map(([label,start,end],i)=><li key={label} className={step>end?'complete':step>=start?'current':''} aria-current={step>=start&&step<=end?'step':undefined}><span>{step>end?<Check size={12}/>:i+1}</span>{label}</li>)}</ol>
        <div className="rq-layout"><form className="rq-form" onSubmit={next} noValidate>
          <div className="rq-question-head"><span className="rq-eyebrow">{step===0?'DEIN PROJEKT BEGINNT HIER':STEPS[step].toUpperCase()}</span><h1 ref={heading} tabIndex={-1}>{titles[step]}</h1><p>{hints[step]}</p></div>
          {error&&<div className="rq-error" role="alert" tabIndex={-1} ref={errorRef}>{error}</div>}
          {step===0&&<><label className="rq-search"><Search size={19}/><input type="search" aria-label="Leistung suchen" placeholder="z. B. Reinigung oder Umzug" value={search} onChange={e=>setSearch(e.target.value)}/></label><div className="rq-choices services-choices">{Object.entries(SERVICES).filter(([name,c])=>`${name} ${c.description}`.toLocaleLowerCase('de').includes(search.toLocaleLowerCase('de'))).map(([name,c])=><Choice key={name} label={name} description={c.description} icon={icons[c.icon]} checked={form.category===name} onChange={()=>choose(name)}/>)}</div>{!Object.entries(SERVICES).some(([name,c])=>`${name} ${c.description}`.toLocaleLowerCase('de').includes(search.toLocaleLowerCase('de')))&&<div className="rq-no-results"><p>Keine passende Leistung gefunden?</p><button type="button" className="rq-link" onClick={()=>{setSearch('');choose('Sonstiges')}}>Sonstiges auswählen <ArrowRight size={16}/></button></div>}</>}
          {step===1&&<><div className="rq-field-row"><label className="rq-field"><span>Postleitzahl *</span><input required inputMode="numeric" autoComplete="postal-code" maxLength={5} placeholder="z. B. 69412" value={form.postal_code} onChange={e=>update('postal_code',e.target.value.replace(/\D/g,''))}/></label><label className="rq-field"><span>Ort *</span><input required autoComplete="address-level2" maxLength={100} placeholder="z. B. Eberbach" value={form.city} onChange={e=>update('city',e.target.value)}/></label></div><label className="rq-field"><span>Straße und Hausnummer <small>optional</small></span><input autoComplete="street-address" maxLength={200} placeholder="Kannst du auch später ergänzen" value={form.address} onChange={e=>update('address',e.target.value)}/></label><div className="rq-info"><MapPin size={18}/><span>Wir starten im Raum Eberbach. Anfragen aus der Umgebung prüfen wir individuell.</span></div></>}
          {step===2&&<div className="rq-choices">{config?.choices.map(label=><Choice key={label} multiple label={label} checked={form.work.includes(label)} onChange={()=>update('work',form.work.includes(label)?form.work.filter(x=>x!==label):[...form.work,label])}/>)}</div>}
          {step===3&&<><label className="rq-field rq-amount"><span>{config?.amountLabel} <small>optional</small></span><div className="rq-unit-input"><input type="number" min="1" max="1000000" step="any" inputMode="decimal" placeholder="z. B. 60" value={form.amount} onChange={e=>update('amount',e.target.value)}/><span>{config?.unit}</span></div><small>Wenn du es noch nicht weißt, lass dieses Feld frei.</small></label><fieldset className="rq-fieldset"><legend>{config?.detailLabel}</legend><div className="rq-choices">{config?.detailChoices.map(label=><Choice key={label} label={label} checked={form.detail===label} onChange={()=>update('detail',label)}/>)}</div></fieldset>{form.category==='Umzug'&&<div className="rq-destination"><h2>Wohin geht der Umzug?</h2><div className="rq-field-row"><label className="rq-field"><span>PLZ am Zielort *</span><input inputMode="numeric" maxLength={5} value={form.destination_postal_code} onChange={e=>update('destination_postal_code',e.target.value.replace(/\D/g,''))}/></label><label className="rq-field"><span>Zielort *</span><input maxLength={100} value={form.destination_city} onChange={e=>update('destination_city',e.target.value)}/></label></div></div>}</>}
          {step===4&&<><div className="rq-choices rq-choices-single">{TIMINGS.map(label=><Choice key={label} label={label} checked={form.timing===label} onChange={()=>setForm(f=>({...f,timing:label,desired_date:label==='An einem bestimmten Tag'?f.desired_date:''}))}/>)}</div>{form.timing==='An einem bestimmten Tag'&&<label className="rq-field rq-date"><span>Dein Wunschtermin *</span><input type="date" min={today()} value={form.desired_date} onChange={e=>update('desired_date',e.target.value)}/></label>}</>}
          {step===5&&<><label className="rq-field"><span>Zusätzliche Angaben {form.category==='Sonstiges'?'*':<small>optional</small>}</span><textarea rows={6} maxLength={2000} value={form.description} placeholder={config?.placeholder} onChange={e=>update('description',e.target.value)}/><small className="rq-char-count">{form.description.length} / 2.000 Zeichen</small></label><div className="rq-info"><MessageSquareText size={18}/><span>Hilfreich sind Besonderheiten vor Ort, die Zugänglichkeit und was dir wichtig ist.</span></div></>}
          {step===6&&(user?<div className="rq-account"><span className="rq-account-icon"><CheckCircle2 size={22}/></span><div><strong>{user.name}</strong><span>{user.email}</span><small>Angemeldet als Kunde</small></div></div>:<><label className="rq-field"><span>Dein Name *</span><input autoComplete="name" maxLength={100} value={form.contact_name} onChange={e=>update('contact_name',e.target.value)} placeholder="Vor- und Nachname"/></label><label className="rq-field"><span>E-Mail-Adresse *</span><input type="email" autoComplete="email" maxLength={254} value={form.contact_email} onChange={e=>update('contact_email',e.target.value)} placeholder="name@beispiel.de"/></label><p className="rq-contact-note">Du kannst deine Anfrage ohne Registrierung absenden.</p></>)}
          {step===7&&<div className="rq-review">
            <ReviewRow label="Leistung" onEdit={()=>edit(0)}>{form.category}</ReviewRow>
            <ReviewRow label="Auftragsort" onEdit={()=>edit(1)}>{form.postal_code} {form.city}{form.address&&<small>{form.address}</small>}</ReviewRow>
            <ReviewRow label="Arbeiten" onEdit={()=>edit(2)}>{form.work.join(', ')}</ReviewRow>
            <ReviewRow label="Umfang" onEdit={()=>edit(3)}>{form.amount?`${form.amount} ${config?.unit}`:'Größe noch offen'}<small>{config?.detailLabel} {form.detail}</small>{form.category==='Umzug'&&<small>Ziel: {form.destination_postal_code} {form.destination_city}</small>}</ReviewRow>
            <ReviewRow label="Zeitraum" onEdit={()=>edit(4)}>{form.timing}{form.desired_date&&<small>{new Date(form.desired_date+'T12:00:00').toLocaleDateString('de-DE')}</small>}</ReviewRow>
            <ReviewRow label="Zusätzliche Angaben" onEdit={()=>edit(5)}>{form.description||'Keine weiteren Angaben'}</ReviewRow>
            <ReviewRow label="Kontakt" onEdit={user?null:()=>edit(6)}>{user?.name||form.contact_name}<small>{user?.email||form.contact_email}</small></ReviewRow>
          </div>}
          <div className="rq-actions">{step>0&&<button type="button" className="rq-back" disabled={busy} onClick={back}><ArrowLeft size={17}/>{editing?'Abbrechen':'Zurück'}</button>}<button className="button button-red rq-next" type="submit" disabled={busy}>{busy?'Anfrage wird gesendet…':step===7?'Kostenlos Anfrage absenden':editing?'Änderung übernehmen':'Weiter'}{!busy&&<ArrowRight size={18}/>}</button></div>
          {step===7&&<p className="rq-disclosure">Mit dem Absenden speichern wir deine Angaben zur Bearbeitung der Anfrage. Eine Beauftragung erfolgt erst nach persönlicher Abstimmung.</p>}
        </form><aside className="rq-aside"><div className="rq-aside-icon"><ShieldCheck size={23}/></div><h2>Ein Auftrag.<br/>Ein Ansprechpartner.</h2><p>Wir begleiten dein Anliegen von der Anfrage bis zur Abstimmung mit dem passenden Partner.</p><ul><li><Check size={16}/>Kostenlos & unverbindlich anfragen</li><li><Check size={16}/>Persönliche Koordination</li><li><Check size={16}/>Regionale Dienstleister</li></ul><div className="rq-aside-contact"><span>Du hast eine Frage?</span><a href="mailto:info.machbar@gmx.de">info.machbar@gmx.de <ChevronRight size={14}/></a></div></aside></div>
      </>}
    </main>
    <footer className="rq-footer"><span>© {new Date().getFullYear()} MACHBAR</span><a href="mailto:info.machbar@gmx.de"><Mail size={14}/> Kontakt</a></footer>
    {closeDialog&&<div className="rq-dialog-backdrop"><section ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="rq-exit-title" className="rq-dialog"><h2 id="rq-exit-title">Anfrage später fortsetzen?</h2><p>Deine bisherigen Angaben bleiben in diesem Browser-Tab gespeichert. Du kannst deine Anfrage später hier fortsetzen.</p><div><button autoFocus type="button" className="button button-red" onClick={()=>setCloseDialog(false)}>Weiter ausfüllen</button><a href="#/" className="rq-link">Zur Startseite</a></div></section></div>}
  </div>
}

function ReviewRow({label,onEdit,children}) {
  return <div className="rq-review-row"><div><span>{label}</span><p>{children}</p></div>{onEdit&&<button type="button" className="rq-link" onClick={onEdit} aria-label={`${label} bearbeiten`}>Ändern</button>}</div>
}
