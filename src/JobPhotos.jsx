import React, {useEffect,useRef,useState} from 'react'
import {Camera, X} from 'lucide-react'
export const MAX_PHOTOS=6
export const MAX_PHOTO_BYTES=5*1024*1024
const allowed=['image/jpeg','image/png','image/webp']

export function PhotoUpload({photos,setPhotos,disabled,onProcessing}){
  const [error,setError]=useState(''),[reading,setReading]=useState(false)
  const lock=useRef(false)
  async function add(event){
    const files=Array.from(event.target.files||[]);event.target.value=''
    if(lock.current||!files.length)return
    lock.current=true;setReading(true);onProcessing(true);setError('')
    const accepted=[],errors=[]
    try{
      for(const file of files){
        if(photos.length+accepted.length>=MAX_PHOTOS){errors.push('Es sind höchstens 6 Fotos möglich.');break}
        if(!allowed.includes(file.type)){errors.push(`${file.name}: Bitte JPG, PNG oder WebP wählen.`);continue}
        if(file.size>MAX_PHOTO_BYTES){errors.push(`${file.name}: Das Foto darf höchstens 5 MB groß sein.`);continue}
        if(!file.size){errors.push(`${file.name}: Die Datei ist leer.`);continue}
        try{
          const data=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=reject;reader.readAsDataURL(file)})
          await new Promise((resolve,reject)=>{const img=new Image();img.onload=resolve;img.onerror=reject;img.src=data})
          accepted.push({id:crypto.randomUUID(),name:file.name.slice(0,150),data})
        }catch{errors.push(`${file.name}: Dieses Foto konnte nicht gelesen werden.`)}
      }
      setPhotos(current=>[...current,...accepted]);setError(errors.join(' '))
    }finally{lock.current=false;setReading(false);onProcessing(false)}
  }
  return <section className="rq-upload" aria-labelledby="photo-heading"><h2 id="photo-heading">Fotos hinzufügen <small>optional</small></h2><p>Zeig uns die Räume, Gegenstände oder Arbeiten vor Ort. Fotos helfen bei der Einschätzung.</p>
    <label className={`rq-upload-zone ${disabled||reading?'is-disabled':''}`}><Camera size={25}/><strong>{reading?'Fotos werden vorbereitet…':'Fotos auswählen'}</strong><span>JPG, PNG oder WebP · bis zu 6 Fotos · je max. 5 MB</span><input type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={add} disabled={disabled||reading||photos.length>=MAX_PHOTOS} aria-label="Fotos auswählen"/></label>
    {error&&<p className="rq-error" role="alert">{error}</p>}{!!photos.length&&<><p aria-live="polite">{photos.length} von {MAX_PHOTOS} Fotos ausgewählt</p><div className="rq-photo-grid">{photos.map(photo=><figure key={photo.id}><img src={photo.data} alt={photo.name}/><figcaption>{photo.name}</figcaption><button type="button" disabled={disabled||reading} onClick={()=>setPhotos(current=>current.filter(x=>x.id!==photo.id))} aria-label={`${photo.name} entfernen`}><X size={16}/></button></figure>)}</div></>}
    <p className="rq-photo-note">Fotos werden mit der Anfrage hochgeladen. Nach dem Neuladen oder Verlassen dieser Seite bitte erneut auswählen.</p></section>
}

export default function JobPhotos({photos=[],token}){
  const [items,setItems]=useState([]),[error,setError]=useState(false),[expanded,setExpanded]=useState(null),[retry,setRetry]=useState(0)
  const urls=photos.map(p=>p.url).join('|')
  useEffect(()=>{
    const controller=new AbortController(),created=[]
    setItems([]);setError(false);setExpanded(null)
    Promise.all(photos.map(async photo=>{
      const response=await fetch(photo.url,{headers:{Authorization:`Bearer ${token}`},signal:controller.signal})
      if(!response.ok)throw Error('Foto nicht verfügbar')
      const blob=await response.blob();if(controller.signal.aborted)return null
      const src=URL.createObjectURL(blob);created.push(src);return {...photo,src}
    })).then(result=>{if(!controller.signal.aborted)setItems(result.filter(Boolean))}).catch(()=>{if(!controller.signal.aborted)setError(true)})
    return()=>{controller.abort();created.forEach(url=>URL.revokeObjectURL(url))}
  },[urls,token,retry])
  if(!photos.length)return null
  return <section className="job-photos"><h4>Fotos zum Auftrag ({photos.length})</h4>{error?<p>Fotos konnten nicht geladen werden. <button className="rq-link" onClick={()=>setRetry(n=>n+1)}>Erneut versuchen</button></p>:!items.length?<p>Fotos werden geladen…</p>:<><div className="job-photo-thumbs">{items.map(photo=><button key={photo.id} type="button" onClick={()=>setExpanded(expanded===photo.id?null:photo.id)} aria-label={`${photo.name} ${expanded===photo.id?'verkleinern':'vergrößern'}`} aria-expanded={expanded===photo.id}><img src={photo.src} alt={photo.name}/></button>)}</div>{expanded&&<img className="job-photo-expanded" src={items.find(x=>x.id===expanded)?.src} alt={items.find(x=>x.id===expanded)?.name}/>}</>}</section>
}
