import test from 'node:test'
import assert from 'node:assert/strict'
import {SERVICES,GROUPS,EMPTY_FORM,selectService,selectedGroups,needsDestination,validateStep,buildPayload} from './requestFlow.js'

test('Availability survives payload and rejects incomplete or conflicting time windows',()=>{
  const form={...valid(),availability:[{day:'Montag',from:'09:00',to:'12:30'},{day:'Freitag',from:'14:00',to:'18:00'}]}
  assert.equal(validateStep(3,form,null,'2026-09-25'),'')
  const payload=buildPayload(form,null)
  assert.deepEqual(payload.details.availability,form.availability)
  assert.ok(payload.description.includes('Montag: 09:00–12:30 Uhr'))
  for(const slot of [{day:'Montag',from:'',to:''},{day:'Montag',from:'12:00',to:'11:00'},{day:'Montag',from:'24:00',to:'25:00'}])assert.ok(validateStep(3,{...form,availability:[slot]},null,'2026-09-25'))
  assert.ok(validateStep(3,{...form,timing:'An einem bestimmten Tag',desired_date:'2026-09-26'},null,'2026-09-25'))
  assert.equal(validateStep(3,{...form,timing:'An einem bestimmten Tag',desired_date:'2026-09-28'},null,'2026-09-25'),'')
})
const valid=()=>({...EMPTY_FORM,services:['Wohnung entrümpeln','Fensterreinigung'],scopes:{Entrümpelung:{amount:'60',detail:'Über Treppen'},Reinigung:{amount:'20',detail:'Einmalig'}},postal_code:'69412',city:'Eberbach',timing:'Ich bin flexibel',contact_name:'Testkunde',contact_email:'test@example.com'})
test('All specific services can be requested, including optional estimates',()=>{
  for(const group of ['Elektrik','Montage','Bad & Sanitär','Weitere'])assert.ok(Object.values(SERVICES).some(s=>s.group===group))
  for(const service of Object.keys(SERVICES)){
    const form={...valid(),services:[service],scopes:{},destination_postal_code:'69115',destination_city:'Heidelberg',description:'Bitte die Arbeiten vorab besprechen.'}
    for(let step=0;step<7;step++)assert.equal(validateStep(step,form,null,'2026-09-22'),'')
    assert.deepEqual(buildPayload(form,null).details.services,[service])
  }
})
test('Cross-category selection preserves answers; removing the last item clears only its group',()=>{
  const form=selectService(valid(),'Wände und Decken streichen')
  assert.equal(form.services.length,3)
  assert.equal(form.scopes.Reinigung.detail,'Einmalig')
  const removed=selectService(form,'Wohnung entrümpeln')
  assert.equal(removed.scopes.Entrümpelung,undefined)
  assert.equal(removed.scopes.Reinigung.amount,'20')
  assert.equal(removed.city,'Eberbach')
  const twoInGroup=selectService(valid(),'Treppenhausreinigung')
  assert.equal(selectService(twoInGroup,'Fensterreinigung').scopes.Reinigung.detail,'Einmalig')
})
test('Destination is required only for a move or furniture transport and is cleared on deselection',()=>{
  const moving=selectService(valid(),'Möbeltransport')
  assert.ok(needsDestination(moving))
  assert.ok(validateStep(1,moving,null,'2026-09-22'))
  const complete={...moving,destination_postal_code:'69115',destination_city:'Heidelberg'}
  assert.equal(validateStep(1,complete,null,'2026-09-22'),'')
  assert.ok(buildPayload(complete,null).description.includes('69115 Heidelberg'))
  const removed=selectService(complete,'Möbeltransport')
  assert.equal(removed.destination_city,'')
  assert.equal(needsDestination(selectService(removed,'Tragehilfe')),false)
})
test('Payload preserves every selection and per-group answers without a stale date',()=>{
  const form={...valid(),desired_date:'2026-10-01',description:'  Zugang über den Hof.  '}
  const payload=buildPayload(form,null)
  assert.equal(payload.category,'Mehrere Leistungen')
  assert.deepEqual(payload.details.services,form.services)
  assert.equal(payload.details.scopes.length,2)
  for(const answer of ['Wohnung entrümpeln','Fensterreinigung','60 m²','20 m²','Über Treppen','Einmalig','Zugang über den Hof.'])assert.ok(payload.description.includes(answer))
  assert.equal(payload.desired_date,'')
  assert.ok(!payload.description.includes('2026-10-01'))
  const all={...form,services:Object.keys(SERVICES),scopes:Object.fromEntries(Object.entries(GROUPS).map(([group,c])=>[group,{amount:'1000000',detail:c.detailChoices[0]}]))}
  assert.ok(buildPayload(all,null).description.length<5000)
})
test('Empty selections, invalid contacts, past dates and impossible dates are rejected',()=>{
  const form=valid()
  assert.ok(validateStep(0,{...form,services:[]},null,'2026-09-22'))
  assert.ok(validateStep(0,{...form,services:['invalid']},null,'2026-09-22'))
  assert.ok(validateStep(5,{...form,contact_email:'invalid@'},null,'2026-09-22'))
  assert.ok(validateStep(2,{...form,scopes:{Reinigung:{amount:'-1'}}},null,'2026-09-22'))
  for(const date of ['2026-02-30','2026-13-01','2026-01-01'])assert.ok(validateStep(3,{...form,timing:'An einem bestimmten Tag',desired_date:date},null,'2026-09-22'))
  assert.ok(validateStep(4,{...form,services:['Anderes Anliegen']},null,'2026-09-22'))
})
