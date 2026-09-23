import test from 'node:test'
import assert from 'node:assert/strict'
import {metrics,filterJobs,isAdmin} from './adminMetrics.js'
const now='2026-09-22T12:00:00Z'
const job=(id,status,created_at,extra={})=>({id,status,created_at,title:'Auftrag '+id,contact_name:'Kunde',contact_email:'kunde@example.com',city:'Eberbach',postal_code:'69412',category:'Reinigung',photos:[],...extra})
const jobs=[job(1,'open','2026-09-18 12:00:00'),job(2,'open','2026-09-22 09:00:00',{desired_date:'2026-09-21',details:{services:['Fensterreinigung','Streichen','Streichen']}}),job(3,'in_progress','2026-09-15 12:00:00',{provider_id:9,photos:[{}]}),job(4,'done','2026-08-01 12:00:00',{desired_date:'2026-08-02'})]
test('KPIs use real statuses, rolling dates and distinct service selections',()=>{
  const m=metrics(jobs,now)
  assert.deepEqual(m.counts,{open:2,assigned:0,in_progress:1,done:1})
  assert.equal(m.total,4);assert.equal(m.new30,3);assert.equal(m.completion,25)
  assert.equal(m.overdue,1);assert.equal(m.waiting,1);assert.equal(m.unassigned,2)
  assert.equal(m.avgOpen,2.1);assert.equal(m.contacts,1);assert.equal(m.photoJobs,1)
  assert.equal(m.services.find(([name])=>name==='Streichen')[1],1)
  assert.equal(m.trend.length,14);assert.equal(m.trend.at(-1).count,1)
})
test('Priority puts overdue first; search and filters remain composable',()=>{
  assert.deepEqual(filterJobs(jobs,{status:'open'},now).map(j=>j.id),[2,1])
  assert.deepEqual(filterJobs(jobs,{status:'all',search:'Fenster'},now).map(j=>j.id),[2])
  assert.equal(filterJobs(jobs,{status:'done',search:'Fenster'},now).length,0)
  assert.deepEqual(filterJobs(jobs,{status:'all',sort:'newest'},now).map(j=>j.id),[2,1,3,4])
})
test('Empty dashboard has finite values and administration needs email and role',()=>{
  const m=metrics([],now)
  assert.equal(m.avgOpen,0);assert.equal(m.completion,0);assert.equal(m.total,0)
  assert.equal(isAdmin({role:'admin',email:'other@example.com'}),false)
  assert.equal(isAdmin({role:'customer',email:'info.machbar@gmx.de'}),false)
  assert.equal(isAdmin({role:'admin',email:'info.machbar@gmx.de'}),true)
})
