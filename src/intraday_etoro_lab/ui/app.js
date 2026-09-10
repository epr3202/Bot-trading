'use strict';
let controlToken = '';
let pendingAction = '';
const $ = (id) => document.getElementById(id);
const money = (v) => Number(v ?? 0).toLocaleString('es-CO', {style:'currency', currency:'USD', maximumFractionDigits:2});
const text = (id, value) => { $(id).textContent = value ?? '—'; };
async function request(path, body) {
  const response = await fetch(path, {method:body ? 'POST' : 'GET', credentials:'omit', cache:'no-store', headers:{Authorization:`Bearer ${controlToken}`, ...(body ? {'Content-Type':'application/json'} : {})}, ...(body ? {body:JSON.stringify(body)} : {})});
  const result = await response.json();
  if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : result.error || `HTTP ${response.status}`);
  return result;
}
function rows(target, data, columns, empty) {
  const body = $(target); body.replaceChildren();
  if (!data.length) { const tr = document.createElement('tr'), td = document.createElement('td'); td.colSpan=columns.length; td.className='empty'; td.textContent=empty; tr.append(td); body.append(tr); return; }
  for (const item of data) { const tr=document.createElement('tr'); for(const column of columns) { const td=document.createElement('td'); td.textContent=String(column(item) ?? '—'); if (['UNKNOWN','SUBMITTING','CANCEL_PENDING'].includes(td.textContent)) td.className='warn'; tr.append(td); } body.append(tr); }
}
function chart(points) {
  const box=$('equity-chart'); box.replaceChildren();
  if(!points.length) {const p=document.createElement('p'); p.textContent='Sin observaciones de cartera.'; box.append(p); return;}
  const values=points.map(x=>Number(x.equity ?? x.value ?? x));
  const lo=Math.min(...values), hi=Math.max(...values), spread=hi-lo || 1;
  const ns='http://www.w3.org/2000/svg'; const svg=document.createElementNS(ns,'svg'); svg.setAttribute('viewBox','0 0 1000 200'); svg.setAttribute('role','img'); svg.setAttribute('aria-label','Curva de equity sintética de las sesiones reproducidas');
  const poly=document.createElementNS(ns,'polyline'); poly.setAttribute('points',values.map((v,i)=>`${20+i*960/Math.max(1,values.length-1)},${175-(v-lo)*145/spread}`).join(' ')); poly.setAttribute('fill','none'); poly.setAttribute('stroke','#31886b'); poly.setAttribute('stroke-width','2.5'); svg.append(poly);
  const label=document.createElementNS(ns,'text'); label.setAttribute('x','20'); label.setAttribute('y','18'); label.setAttribute('fill','#81968b'); label.setAttribute('font-size','11'); label.textContent=`SINTÉTICO · ${money(lo)} — ${money(hi)}`; svg.append(label); box.append(svg);
}
function render(s) {
  text('mode',String(s.mode).toUpperCase()); text('budget',money(s.budget)); text('cash',`Efectivo utilizable: ${money(s.cash)}`); text('pnl',money(s.realized_pnl)); text('exposure',money(s.exposure)); text('risk',`Reservas: ${money(s.reserved_cash)} · Límite diario: ${money(s.daily_loss_limit)}`); text('armed',s.entries_armed ? 'ARMADAS DEMO' : 'DESARMADAS'); text('broker',`eToro: ${s.broker_status}`); text('data-status',s.data_status); text('ny',s.time_new_york); text('bogota',s.time_bogota); text('session',s.session); text('freshness',s.data_freshness); text('readiness',s.readiness); text('unrealized',`${money(s.unrealized_pnl)} / ${money(s.costs)}`);
  rows('selection-rows',s.selection || [],[x=>x.symbol,x=>x.rank,x=>x.rvol,x=>x.orh,x=>x.orl,x=>x.reason || 'Seleccionada'], 'Sin selección disponible.');
  rows('orders',s.orders || [],[x=>x.symbol,x=>x.state,x=>x.units,x=>String(x.intent_id).slice(0,12)],'Sin órdenes');
  rows('positions',s.positions || [],[x=>x.symbol,x=>x.units,x=>x.entry_price,x=>x.stop_price],'Sin exposición abierta');
  text('order-count',(s.orders || []).length); text('position-count',(s.positions || []).length); text('research-status',s.research_status);
  const list=$('incident-list'); list.replaceChildren(); for(const item of (s.incidents || ['Sin incidencias.'])){const li=document.createElement('li'); li.textContent=typeof item === 'string' ? item : JSON.stringify(item); list.append(li);}
  if(s.report){text('report-json',JSON.stringify(s.report,null,2)); chart(s.chart || []); const metrics=$('report-metrics'); metrics.replaceChildren(); for(const [key,value] of Object.entries(s.summary_metrics || {})){const item=document.createElement('div'); item.textContent=key; const b=document.createElement('b'); b.textContent=value===null ? 'N/A' : String(value); item.append(b); metrics.append(item);}}
}
async function refresh(){try{render(await request('/api/state')); text('feedback','Estado actualizado desde el ejecutor local.');}catch(error){text('feedback',error.message);}}
async function command(action,confirm='',budget=null){const buttons=document.querySelectorAll('button'); buttons.forEach(b=>b.disabled=true); text('feedback','Procesando comando…'); try{const result=await request('/api/commands',{action,confirm,budget}); render(result); text('feedback',`Comando completado: ${action}.`);}catch(error){text('feedback',error.message);}finally{buttons.forEach(b=>b.disabled=false);}}
$('login-form').addEventListener('submit',async(event)=>{event.preventDefault();controlToken=$('token').value;$('token').value='';try{render(await request('/api/state'));$('login').hidden=true;text('feedback','Conectado. Los comandos quedan auditados.');}catch(error){controlToken='';text('feedback',error.message);}});
$('refresh').addEventListener('click',refresh);
document.querySelectorAll('[data-command]').forEach(button=>button.addEventListener('click',()=>{const action=button.dataset.command;if(['arm-demo','flatten-owned-demo'].includes(action)){pendingAction=action;text('confirmation-title',action==='arm-demo'?'Activar entradas Demo':'Solicitar cierre de posiciones propias');text('confirmation-message',action==='arm-demo'?'Acepta el presupuesto virtual configurado. Solo se habilita si todos los controles y la integración están verificados.':'Cancela entradas y solicita cerrar exclusivamente posiciones virtuales reconocidas como propias.');$('confirm-text').value='';$('confirm-budget').value='';$('confirmation').showModal();}else command(action);}));
$('confirmation').addEventListener('close',()=>{if($('confirmation').returnValue==='confirm')command(pendingAction,$('confirm-text').value,$('confirm-budget').value || null);});
