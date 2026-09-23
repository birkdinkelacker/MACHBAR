export const STATUS={open:'Offen',assigned:'Zugewiesen',in_progress:'In Bearbeitung',done:'Abgeschlossen'}
export const isAdmin=user=>user?.role==='admin'&&user?.email?.toLowerCase()==='info.machbar@gmx.de'
export const createdDate=job=>new Date(job.created_at.endsWith('Z')?job.created_at:job.created_at.replace(' ','T')+'Z')
export const ageDays=(job,now)=>Math.max(0,Math.floor((new Date(now)-createdDate(job))/86400000))
export const overdue=(job,now)=>job.status!=='done'&&job.desired_date&&job.desired_date<new Date(now).toISOString().slice(0,10)
export function metrics(jobs,now){
  const current=new Date(now),counts=Object.fromEntries(Object.keys(STATUS).map(k=>[k,jobs.filter(j=>j.status===k).length]))
  const open=jobs.filter(j=>j.status==='open'),active=jobs.filter(j=>j.status!=='done')
  const ranking=key=>{const result={};for(const j of jobs)for(const name of new Set(key(j)))result[name]=(result[name]||0)+1;return Object.entries(result).sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0],'de'))}
  const trend=Array.from({length:14},(_,i)=>{const day=new Date(current);day.setUTCDate(day.getUTCDate()-13+i);const date=day.toISOString().slice(0,10);return {date,count:jobs.filter(j=>createdDate(j).toISOString().slice(0,10)===date).length}})
  return {counts,total:jobs.length,active:active.length,waiting:open.filter(j=>ageDays(j,current)>=3).length,overdue:active.filter(j=>overdue(j,current)).length,unassigned:active.filter(j=>!j.provider_id).length,new30:jobs.filter(j=>current-createdDate(j)>=0&&current-createdDate(j)<30*86400000).length,completion:jobs.length?Math.round(counts.done/jobs.length*100):0,avgOpen:open.length?Math.round(open.reduce((n,j)=>n+(current-createdDate(j))/86400000,0)/open.length*10)/10:0,contacts:new Set(jobs.map(j=>j.contact_email.toLowerCase())).size,photoJobs:jobs.filter(j=>j.photos?.length).length,services:ranking(j=>j.details?.services?.length?j.details.services:[j.category]),cities:ranking(j=>[j.city||'Unbekannt']),trend}
}
export function filterJobs(jobs,{status='all',search='',sort='priority'},now){
  const query=search.trim().toLocaleLowerCase('de')
  const filtered=jobs.filter(j=>(status==='all'||(status==='overdue'?overdue(j,now):status==='unassigned'?j.status!=='done'&&!j.provider_id:j.status===status))&&`${j.id} ${j.title} ${j.contact_name} ${j.contact_email} ${j.city} ${j.postal_code} ${j.details?.services?.join(' ')||j.category}`.toLocaleLowerCase('de').includes(query))
  const score=j=>(overdue(j,now)?100:0)+(j.status==='open'?50:0)+(j.status!=='done'&&!j.provider_id?20:0)
  return filtered.sort((a,b)=>sort==='newest'?createdDate(b)-createdDate(a):sort==='oldest'?createdDate(a)-createdDate(b):score(b)-score(a)||createdDate(a)-createdDate(b)||a.id-b.id)
}
