import React,{useEffect,useRef,useState} from 'react'
import JobPhotos from './JobPhotos'
import {Offers,OfferForm} from './Offers'
import './portal.css'
const STATUS={open:'Anfrage eingegangen',assigned:'Dienstleister zugewiesen',in_progress:'In Bearbeitung',done:'Abgeschlossen'}

function Settings({user,request,onUser}){
  const [role,setRole]=useState(user.role),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('')
  async function save(e){e.preventDefault();setBusy(true);setError('');try{const data=await request('/auth/settings',{method:'PATCH',body:JSON.stringify({role})});onUser(data.user);setNotice('Einstellungen gespeichert.')}catch(e){setError(e.message)}finally{setBusy(false)}}
  return <section className="portal-panel"><h2>Einstellungen</h2><p>{user.email}</p><form className="portal-settings" onSubmit={save}><label>Aktive Rolle<select value={role} onChange={e=>setRole(e.target.value)}><option value="customer">Kunde</option><option value="provider">Dienstleister</option></select></label><p>Deine bisherigen Aufträge bleiben erhalten. Wechsle zurück, um die Aufträge der anderen Rolle zu sehen.</p>{error&&<p role="alert" className="error">{error}</p>}{notice&&<p role="status">{notice}</p>}<button className="button button-red" disabled={busy}>{busy?'Speichert…':'Einstellungen speichern'}</button></form></section>
}

export function JobCard({job,customer,request,refresh,token,guestToken}){
  return <article className="portal-job"><div className="offer-heading"><span>Auftrag #{job.id} · {job.category}</span><span>{STATUS[job.status]}</span></div><h2>{job.title}</h2><p>{job.region||`${job.postal_code} ${job.city}`}</p>
    {job.description&&<p className="portal-description">{job.description}</p>}
    {!customer&&!job.contact_released&&<p className="portal-notice">Auftragsdetails und Fotos helfen dir bei der Einschätzung. Kontaktdaten und genaue Adresse werden nach der Annahme freigegeben. Bis dahin siehst du die grobe Region.</p>}
    {!customer&&job.contact_released&&<section className="portal-contact"><h3>Kundenkontakt</h3><b>{job.contact_name}</b><a href={`mailto:${job.contact_email}`}>{job.contact_email}</a>{job.contact_phone?<a href={`tel:${job.contact_phone.replace(/[^+0-9]/g,'')}`}>{job.contact_phone}</a>:<span>Telefonnummer nicht hinterlegt</span>}<span>{job.address||'Straße nicht angegeben'}, {job.postal_code} {job.city}</span></section>}
    <JobPhotos photos={job.photos} token={token} guestToken={guestToken}/><Offers job={job} customer={customer} request={request} onSaved={refresh}/>
    {!customer&&<OfferForm job={job} request={request} onSaved={refresh}/>}
    {customer&&!job.offers?.length&&<p>Wir prüfen deine Anfrage. Angebote erscheinen hier automatisch.</p>}
  </article>
}

export default function Portal({user,request,onUser,token}){
  const [tab,setTab]=useState('jobs'),[jobs,setJobs]=useState([]),[loading,setLoading]=useState(true),[error,setError]=useState('')
  const pending=useRef(false)
  async function refresh(){if(pending.current)return;pending.current=true;try{const data=await request('/jobs');setJobs(data.jobs);setError('')}catch(e){setError(e.message)}finally{setLoading(false);pending.current=false}}
  useEffect(()=>{refresh();const timer=setInterval(()=>{if(!document.hidden)refresh()},15000);return()=>clearInterval(timer)},[])
  const customer=user.role==='customer',count=jobs.filter(j=>j.offers?.some(o=>o.status==='pending')).length
  return <main className="page-bg portal"><div className="container"><div className="portal-heading"><div><span className="kicker">{customer?'KUNDENPORTAL':'DIENSTLEISTERPORTAL'}</span><h1>Hallo, {user.name.split(' ')[0]}.</h1><p>{customer?'Anfragen, Angebote und Termine an einem Ort.':'Anfragen prüfen und Termin- und Preisvorschläge senden.'}</p></div>{customer&&<a className="button button-red" href="#/anfrage">Neue Anfrage</a>}</div>
    <nav className="portal-tabs" aria-label="Portalbereiche"><button className={tab==='jobs'?'active':''} onClick={()=>setTab('jobs')}>Meine Aufträge</button><button className={tab==='settings'?'active':''} onClick={()=>setTab('settings')}>Einstellungen</button></nav>
    {tab==='settings'?<Settings user={user} request={request} onUser={onUser}/>:<><div className="portal-notice" role="status">{customer&&count?`${count} ${count===1?'Angebot wartet':'Angebote warten'} auf deine Antwort.`:`${jobs.length} ${jobs.length===1?'Auftrag':'Aufträge'} · ${count} ${count===1?'offenes Angebot':'offene Angebote'}`}</div><button className="portal-text-btn" onClick={refresh}>Aktualisieren</button>{error&&<p role="alert" className="error">{error}</p>}{loading?<p>Lade Aufträge…</p>:!jobs.length?<section className="portal-panel"><h2>Noch keine Aufträge</h2><p>{customer?'Stelle deine erste Anfrage.':'Zugewiesene Anfragen erscheinen hier automatisch.'}</p></section>:jobs.map(job=><JobCard key={job.id} job={job} customer={customer} request={request} refresh={refresh} token={token}/>)}</>}
  </div></main>
}

export function GuestJob({request,token}){
  const id=location.hash.split('?')[0].split('/').pop(),key=new URLSearchParams(location.hash.split('?')[1]||'').get('key')||''
  const [job,setJob]=useState(null),[error,setError]=useState('')
  const guestRequest=(path,options={})=>request(path,{...options,headers:{...options.headers,'X-Guest-Token':key}})
  async function refresh(){try{const data=await guestRequest(`/jobs/${id}`);setJob(data.job);setError('')}catch(e){setJob(null);setError(e.message)}}
  useEffect(()=>{refresh();const timer=setInterval(()=>{if(!document.hidden)refresh()},15000);return()=>clearInterval(timer)},[id,key])
  return <main className="page-bg portal"><div className="container"><h1>Deine Anfrage</h1><p>Bewahre diesen persönlichen Link vertraulich auf. Hier kannst du Angebote beantworten.</p><button className="portal-text-btn" onClick={refresh}>Aktualisieren</button>{error&&<p role="alert" className="error">{error}</p>}{job&&<JobCard job={job} customer request={guestRequest} refresh={refresh} token={token} guestToken={key}/>}</div></main>
}
