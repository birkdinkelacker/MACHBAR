import React, {useState} from 'react'
import {WEEKDAYS} from './requestFlow'

export default function Availability({value, onChange}) {
  const [expanded, setExpanded] = useState(value.length > 0)
  const toggleDay = day => onChange(value.some(s=>s.day===day)
    ? value.filter(s=>s.day!==day)
    : [...value,{day,from:'',to:''}].sort((a,b)=>WEEKDAYS.indexOf(a.day)-WEEKDAYS.indexOf(b.day)))
  const setTime = (day,key,time) => onChange(value.map(s=>s.day===day?{...s,[key]:time}:s))
  return <section className="rq-availability">
    <label className="rq-availability-toggle"><input type="checkbox" checked={expanded} onChange={e=>{setExpanded(e.target.checked);if(!e.target.checked)onChange([])}}/> Wochentage und Uhrzeiten angeben <small>optional</small></label>
    {expanded&&<><p>Wann passt es dir? Wähle passende Tage und jeweils ein Zeitfenster in Ortszeit. Wir stimmen den Termin mit dir ab.</p>
      <div className="rq-filters" aria-label="Verfügbare Wochentage">{WEEKDAYS.map(day=><button type="button" key={day} aria-pressed={value.some(s=>s.day===day)} onClick={()=>toggleDay(day)}>{day}</button>)}</div>
      {value.map(slot=><fieldset className="rq-time-slot" key={slot.day}><legend>{slot.day}</legend><label>Von<input type="time" required aria-label={`${slot.day} von`} value={slot.from} onChange={e=>setTime(slot.day,'from',e.target.value)}/></label><label>Bis<input type="time" required aria-label={`${slot.day} bis`} value={slot.to} onChange={e=>setTime(slot.day,'to',e.target.value)}/></label></fieldset>)}
      {!value.length&&<p>Noch kein Tag ausgewählt – deine Verfügbarkeit bleibt offen.</p>}
    </>}
  </section>
}
