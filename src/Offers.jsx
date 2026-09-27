import React, {useState} from 'react'
import './portal.css'

export const money = cents => new Intl.NumberFormat('de-DE',{style:'currency',currency:'EUR'}).format(cents/100)
export const slotLabel = s => `${new Date(s.date+'T12:00:00').toLocaleDateString('de-DE',{weekday:'long',day:'2-digit',month:'2-digit',year:'numeric'})}, ${s.from}–${s.to} Uhr`
const states = {pending:'Antwort ausstehend',accepted:'Angenommen',rejected:'Abgelehnt',superseded:'Durch neues Angebot ersetzt'}

export function OfferFields({price,onPrice,slots,onSlots,disabled=false}) {
  const update=(i,key,value)=>onSlots(slots.map((s,n)=>n===i?{...s,[key]:value}:s))
  return <div className="offer-fields">
    <label>Geschätzter Gesamtpreis (€)<input required disabled={disabled} inputMode="decimal" placeholder="z. B. 250,00" value={price} onChange={e=>onPrice(e.target.value)}/></label>
    <p>Bis zu fünf mögliche Termine. Der Kunde wählt bei der Annahme einen davon aus. Zeiten gelten am Auftragsort in Deutschland.</p>
    {slots.map((s,i)=><fieldset className="offer-slot" key={i}><legend>Terminvorschlag {i+1}</legend><label>Datum<input type="date" aria-label={`Termin ${i+1} Datum`} required disabled={disabled} value={s.date} onChange={e=>update(i,'date',e.target.value)}/></label><label>Von<input type="time" aria-label={`Termin ${i+1} von`} required disabled={disabled} value={s.from} onChange={e=>update(i,'from',e.target.value)}/></label><label>Bis<input type="time" aria-label={`Termin ${i+1} bis`} required disabled={disabled} value={s.to} onChange={e=>update(i,'to',e.target.value)}/></label>{slots.length>1&&<button type="button" className="portal-text-btn" disabled={disabled} onClick={()=>onSlots(slots.filter((_,n)=>n!==i))}>Entfernen</button>}</fieldset>)}
    {slots.length<5&&<button type="button" className="portal-text-btn" disabled={disabled} onClick={()=>onSlots([...slots,{date:'',from:'',to:''}])}>+ Weiteren Termin hinzufügen</button>}
  </div>
}

export function OfferForm({job,request,onSaved,providers}) {
  const [price,setPrice]=useState(''),[slots,setSlots]=useState([{date:'',from:'',to:''}]),[provider,setProvider]=useState(job.provider_id||'')
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('')
  if(job.contact_released||['in_progress','done'].includes(job.status))return null
  async function send(e){e.preventDefault();setBusy(true);setError('');setNotice('');try{
    await request(`/jobs/${job.id}/offers`,{method:'POST',body:JSON.stringify({price,slots,...(providers?{provider_id:Number(provider)}:{})})})
    setNotice('Angebot im Kundenportal bereitgestellt.');setPrice('');await onSaved()
  }catch(e){setError(e.message)}finally{setBusy(false)}}
  return <form className="offer-form" onSubmit={send}><h3>Termin & Preis vorschlagen</h3>
    {providers&&<label>Dienstleister<select required disabled={busy} value={provider} onChange={e=>setProvider(e.target.value)}><option value="">Bitte auswählen</option>{providers.filter(p=>p.id!==job.customer_id).map(p=><option key={p.id} value={p.id}>{p.company||p.name}</option>)}</select></label>}
    <OfferFields price={price} onPrice={setPrice} slots={slots} onSlots={setSlots} disabled={busy}/>
    {job.offers?.some(o=>o.status==='pending')&&<p>Dieses Angebot ersetzt den noch offenen Vorschlag.</p>}
    {error&&<p role="alert" className="error">{error}</p>}{notice&&<p role="status">{notice}</p>}
    <button className="button button-red" disabled={busy}>{busy?'Wird gesendet…':'Angebot an Kunden senden'}</button>
  </form>
}

export function Offers({job,customer=false,request,onSaved}) {
  const [selected,setSelected]=useState({}),[busy,setBusy]=useState(false),[error,setError]=useState('')
  async function decide(offer,decision){setBusy(true);setError('');try{await request(`/offers/${offer.id}/decision`,{method:'POST',body:JSON.stringify({decision,selected_slot:selected[offer.id]===undefined?null:Number(selected[offer.id])})});await onSaved()}catch(e){setError(e.message)}finally{setBusy(false)}}
  return <section className="offers" aria-label="Angebote">{error&&<p className="error" role="alert">{error}</p>}{(job.offers||[]).map(offer=><article className={`offer offer-${offer.status}`} key={offer.id}>
    <div className="offer-heading"><h3>Angebot #{offer.id}</h3><span>{states[offer.status]}</span></div><p>{offer.provider_name}</p><strong className="offer-price">{money(offer.price_cents)}</strong><small>Geschätzter Gesamtpreis</small>
    {offer.status==='accepted'?<p><b>Bestätigter Termin:</b> {slotLabel(offer.slots[offer.selected_slot])}</p>:<fieldset className="offer-options"><legend>Terminvorschläge</legend>{offer.slots.map((s,i)=><label key={i}>{customer&&offer.status==='pending'&&<input type="radio" name={`offer-${offer.id}`} checked={selected[offer.id]===String(i)} onChange={()=>setSelected({...selected,[offer.id]:String(i)})}/>}<span>{slotLabel(s)}</span></label>)}</fieldset>}
    {customer&&offer.status==='pending'&&<><p>Mit der Annahme beauftragst du den vorgeschlagenen Dienstleister auf Basis dieser Schätzung. Name, Telefonnummer, E-Mail und genaue Adresse werden für ihn freigegeben.</p><div className="offer-actions"><button type="button" className="button button-red" disabled={busy||selected[offer.id]===undefined} onClick={()=>decide(offer,'accepted')}>Termin wählen & Auftrag annehmen</button><button type="button" className="portal-text-btn" disabled={busy} onClick={()=>decide(offer,'rejected')}>Angebot ablehnen</button></div></>}
  </article>)}</section>
}
