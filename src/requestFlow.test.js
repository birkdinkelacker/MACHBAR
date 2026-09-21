import test from 'node:test'
import assert from 'node:assert/strict'
import { SERVICES, EMPTY_FORM, selectService, validateStep, buildPayload } from './requestFlow.js'

const valid = () => ({...EMPTY_FORM,category:'Entrümpelung',postal_code:'69412',city:'Eberbach',work:['Wohnung','Garage'],amount:'60',detail:'Über Treppen',timing:'Ich bin flexibel',contact_name:'Testkunde',contact_email:'test@example.com'})

test('Every service can produce a complete request with its own questions',()=>{
  for(const [category,service] of Object.entries(SERVICES)){
    const form={...valid(),category,work:[service.choices[0]],detail:service.detailChoices[0],destination_postal_code:'69115',destination_city:'Heidelberg',description:'Bitte vorab die Details gemeinsam besprechen.'}
    for(let step=0;step<8;step++)assert.equal(validateStep(step,form,null,'2026-09-21'),'')
    const payload=buildPayload(form,null)
    assert.ok(payload.description.includes(service.choices[0]))
    assert.ok(payload.description.includes(service.detailChoices[0]))
    assert.ok(payload.description.includes('60 '+service.unit))
    if(category==='Umzug')assert.ok(payload.description.includes('69115 Heidelberg'))
  }
})

test('Changing services removes incompatible answers and retains contact and place',()=>{
  const form=selectService({...valid(),destination_city:'Heidelberg'},'Reinigung')
  assert.deepEqual(form.work,[])
  assert.equal(form.detail,'')
  assert.equal(form.destination_city,'')
  assert.equal(form.city,'Eberbach')
  assert.equal(form.contact_email,'test@example.com')
  assert.ok(validateStep(2,form,null,'2026-09-21'))
  assert.ok(validateStep(3,{...form,detail:'Über Treppen'},null,'2026-09-21'))
})

test('Required answers and invalid dates are rejected; optional estimates and notes can be skipped',()=>{
  const form=valid()
  assert.ok(validateStep(1,{...form,postal_code:'123'},null,'2026-09-21'))
  assert.ok(validateStep(2,{...form,work:[]},null,'2026-09-21'))
  assert.ok(validateStep(3,{...form,amount:'-1'},null,'2026-09-21'))
  assert.ok(validateStep(6,{...form,contact_email:'invalid@'},null,'2026-09-21'))
  assert.equal(validateStep(3,{...form,amount:''},null,'2026-09-21'),'')
  assert.equal(validateStep(5,form,null,'2026-09-21'),'')
  for(const date of ['', '2026-01-01','2026-02-30','2026-13-01'])assert.ok(validateStep(4,{...form,timing:'An einem bestimmten Tag',desired_date:date},null,'2026-01-10'))
  assert.equal(validateStep(4,{...form,timing:'An einem bestimmten Tag',desired_date:'2026-09-21'},null,'2026-09-21'),'')
})

test('Payload preserves answers, trims contact, and never sends a stale exact date',()=>{
  const payload=buildPayload({...valid(),desired_date:'2026-10-01',description:'  Zugang über den Hof.  ',contact_email:' test@example.com '},null)
  assert.equal(payload.desired_date,'')
  assert.equal(payload.contact_email,'test@example.com')
  assert.equal(payload.details.notes,'Zugang über den Hof.')
  for(const answer of ['Wohnung, Garage','60 m²','Über Treppen','Ich bin flexibel','Zugang über den Hof.'])assert.ok(payload.description.includes(answer))
  assert.ok(!payload.description.includes('2026-10-01'))
})
