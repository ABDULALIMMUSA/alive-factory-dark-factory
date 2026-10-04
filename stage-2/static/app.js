'use strict';
const $ = (id) => document.querySelector(`[data-testid="${id}"]`);
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const state = {token:localStorage.getItem('pocketful-token'), me:null, route:location.pathname, forms:{}, ops:new Map(), walletGeneration:0, listGeneration:0};
const nav = [['/','◉','Wallet'],['/requests','↗','Requests'],['/split','▦','Split a bill'],['/authorizations','◇','Reservations']];
class Refused extends Error { constructor(status,code,message){super(message);this.status=status;this.code=code;} }
const messages = {insufficient_funds:'There isn’t enough available money for this. Your wallet has been refreshed.',not_found:'We couldn’t find that person or item. Check the handle and try again.',self_payment:'Choose someone else to receive this payment.',self_request:'Choose someone else to receive this request.',request_not_pending:'This request has already changed. The latest status is shown below.',authorization_expired:'This reservation has expired. Its remaining funds have been released.',authorization_not_open:'This reservation has already closed. We’ve refreshed its status.',capture_exceeds_authorization:'The capture is larger than the amount remaining in this reservation.',forbidden:'This action is available only to the permitted person.',email_taken:'That email already has an account. Try signing in.',handle_taken:'That email would create a handle that is already in use.',unauthenticated:'We couldn’t sign you in. Check your email and password.',idempotency_key_reuse:'This retry no longer matches the original action. Edit the form to start a new action.',validation_failed:'Check the amount and other details, then try again.'};
async function api(path,method='GET',body,key){
  const headers = {'Accept':'application/json'};
  if(state.token) headers.Authorization='Bearer '+state.token;
  if(body !== undefined) headers['Content-Type']='application/json';
  if(key) headers['Idempotency-Key']=key;
  const response = await fetch(path,{method,headers,body:body===undefined?undefined:JSON.stringify(body)});
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if(!response.ok){
    if(response.status >= 500) throw new Error('The response could not confirm the outcome.');
    const code=data?.error?.code;
    throw new Refused(response.status,code,messages[code] || data?.error?.message || 'This action was refused.');
  }
  // Existing signed-in clients may read the Stage1 shape before an in-place
  // upgrade. No holds existed there, so its balance is also fully available.
  if(path==='/me' && data){data.total ??= data.balance;data.held ??= 0;data.available ??= data.total-data.held;}
  return data;
}
function money(value){
  const units=state.me?.minor_units ?? 2, currency=state.me?.currency ?? 'EUR';
  let digits=BigInt(value).toString().padStart(units+1,'0');
  return (units?digits.slice(0,-units)+'.'+digits.slice(-units):digits)+' '+currency;
}
function minor(value){
  const units=state.me?.minor_units ?? 2;
  if(!/^\d+(?:\.\d+)?$/.test(value)) throw new Error('Enter an amount using digits and a decimal point.');
  const [whole,fraction='']=value.split('.');
  if(fraction.length>units) throw new Error(`Use no more than ${units} decimal places for ${state.me.currency}. Amounts are never rounded.`);
  const result=BigInt(whole)*10n**BigInt(units)+BigInt(fraction.padEnd(units,'0')||'0');
  if(result<1n || result>1000000000n) throw new Error('Enter an amount greater than zero, up to '+money(1000000000)+'.');
  return Number(result);
}
const date = value => new Date(value).toLocaleString(undefined,{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'});
function field(name,label,placeholder='',type='text',defaultValue=''){
  const value=state.forms[name] ?? defaultValue;
  return `<div class="field"><label for="${name}">${label}</label><input id="${name}" data-testid="${name}" type="${type}" value="${esc(value)}" placeholder="${esc(placeholder)}" ${name.endsWith('amount')?'inputmode="decimal"':''} ${type==='password'?'autocomplete="current-password"':''}></div>`;
}
function visibility(name){return `<div class="field"><label for="${name}">Who can see it?</label><select id="${name}" data-testid="${name}"><option value="public" ${state.forms[name]!=='private'?'selected':''}>Public activity</option><option value="private" ${state.forms[name]==='private'?'selected':''}>Just the two of you</option></select></div>`;}
function feedback(name,kind,text){
  const host=document.getElementById(name+'-feedback');
  if(!host)return;
  const test=kind==='error'?name+'-error':kind==='uncertain'?name+'-uncertain':null;
  host.innerHTML=text?`<div class="feedback ${kind}" ${test?`data-testid="${test}"`:''} role="${kind==='loading'?'status':'alert'}">${esc(text)}</div>`:'';
}
function shell(){
  const identity=state.me?`<div class="identity"><div class="avatar">${esc(state.me.display_name.slice(0,1).toUpperCase())}</div><div class="person"><strong data-testid="current-user">${esc(state.me.display_name)}</strong><span class="handle" data-testid="current-handle">${esc(state.me.handle)}</span></div><button class="button quiet tiny" data-testid="logout-button">Sign out</button></div>`:`<div class="identity"><a class="button quiet tiny" href="/login">Sign in</a><a class="button tiny" href="/signup">Join Pocketful</a></div>`;
  document.getElementById('app').innerHTML=`<header class="topbar"><a class="brand" href="/"><span class="brandmark">p</span>Pocketful <small>Money, thoughtfully</small></a>${identity}</header><div class="shell"><aside><nav class="navigation" aria-label="Main navigation">${nav.map(([path,icon,label])=>`<a class="navlink ${state.route===path?'active':''}" href="${path}" ${state.route===path?'aria-current="page"':''}><span class="navicon" aria-hidden="true">${icon}</span>${label}</a>`).join('')}</nav><div class="sidebar-note">A little more clarity.<br>A little more peace of mind.<br><br>One wallet, everyday connections.</div></aside><main id="main"></main></div>`;
  $('logout-button')?.addEventListener('click',()=>{localStorage.removeItem('pocketful-token');state.token=null;state.me=null;state.ops.clear();state.forms={};state.walletGeneration++;state.listGeneration++;go('/login');});
  document.querySelectorAll('a[href^="/"]').forEach(link=>link.addEventListener('click',event=>{if(!event.ctrlKey&&!event.metaKey){event.preventDefault();go(link.getAttribute('href'));}}));
}
function heading(kicker,title,subtitle,action=''){return `<div class="heading"><div><div class="eyebrow">${kicker}</div><h1>${title}</h1><p class="subtext">${subtitle}</p></div>${action}</div>`;}
function walletMarkup(){
  if(!state.me)return '<div class="loading-block">Loading your wallet…</div>';
  return `<section class="wallet" aria-label="Your balance"><div class="eyebrow">Available to spend</div><div class="available" data-testid="wallet-available" data-amount="${state.me.available}">${money(state.me.available)}</div><div class="wallet-meta"><dl><dt>Total balance</dt><dd data-testid="wallet-balance" data-amount="${state.me.total}">${money(state.me.total)}</dd></dl>${state.me.held?`<dl><dt>Reserved for later</dt><dd data-testid="wallet-held" data-amount="${state.me.held}">${money(state.me.held)}</dd></dl>`:''}</div><div class="wallet-caption">Your money. A clearer picture.</div></section>`;
}
function transferForm(name,title,subtitle){
  const target=name==='request'?'Who are you asking?':'Who’s receiving it?';
  return `<section class="card" id="${name}-card"><div class="card-title"><h2>${title}</h2></div><p class="subtext spaced">${subtitle}</p><form id="${name}-form" novalidate><div class="form-grid">${field(name+'-handle',target,'Their handle')}${field(name+'-amount','Amount','0.00')}${field(name+'-note','A note (optional)','What’s it for?')}${name==='request'?'':visibility(name+'-visibility')}</div><div class="form-footer"><small>${name==='authorize'?'Reserve now.<br>They collect it later.':name==='pay'?'Money moves immediately.<br>Review your details before sending.':'A friendly reminder.<br>No money moves until they pay.'}</small><button class="button" data-testid="${name}-submit">${name==='pay'?'Send payment':name==='request'?'Send request':'Reserve money'} <span aria-hidden="true">↗</span></button></div><div id="${name}-feedback"></div></form></section>`;
}
function formBody(name){
  const body={amount:minor($(name+'-amount').value),note:$(name+'-note').value};
  body[name==='request'?'payer_handle':'to_handle']=$(name+'-handle').value;
  if(name!=='request')body.visibility=$(name+'-visibility').value;
  return body;
}
function bindFields(){
  document.querySelectorAll('input[data-testid],select[data-testid]').forEach(input=>{
    input.addEventListener('input',()=>{state.forms[input.dataset.testid]=input.value;const name=input.dataset.testid.split('-')[0];state.ops.delete(name);feedback(name,'success','');if(name==='split')preview();});
  });
}
async function write(name,path,body,button,success){
  let operation=state.ops.get(name);
  if(!operation){operation={key:crypto.randomUUID(),body:structuredClone(body),path};state.ops.set(name,operation);}
  button.disabled=true;feedback(name,'loading','Confirming your action…');
  try{
    await api(operation.path,'POST',operation.body,operation.key);
    feedback(name,'success',success);
    try{await refreshPage();}catch{feedback(name,'success',success+' We couldn’t refresh the view yet; use Refresh to load it.');}
  }catch(error){
    if(error instanceof Refused){feedback(name,'error',error.message);try{await refreshPage();}catch{}}
    else feedback(name,name==='pay'?'uncertain':'uncertain',name==='pay'?'We couldn’t confirm whether your payment arrived. Keep these details and retry safely; it will only move once.':'We couldn’t confirm the outcome. Retry with these unchanged details to check the original action.');
  }finally{button.disabled=false;}
}
function bindTransfer(name,path,success){
  document.getElementById(name+'-form')?.addEventListener('submit',event=>{
    event.preventDefault();let body;
    try{body=formBody(name);}catch(error){feedback(name,'error',error.message);return;}
    write(name,path,body,$(name+'-submit'),success);
  });
}
function activity(records){
  const host=document.getElementById('feed-content');if(!host)return;
  if(!records.length){host.innerHTML='<div class="empty" data-testid="empty-activity"><span class="empty-symbol">↗</span>Your next connection starts here.<br>Payments will appear in your activity.</div>';return;}
  host.innerHTML=`<div data-testid="activity-list">${records.map(p=>`<article class="row" data-testid="activity-item-${esc(p.payment_id)}" data-visibility="${p.visibility}"><div class="row-head"><div class="row-title" data-testid="activity-parties-${esc(p.payment_id)}">@${esc(p.from_handle)} <span aria-hidden="true">→</span> @${esc(p.to_handle)}</div><div class="money" data-testid="activity-amount-${esc(p.payment_id)}">${money(p.amount)}</div></div><div class="row-note" data-testid="activity-note-${esc(p.payment_id)}">${esc(p.note)}</div><div class="row-meta"><span class="badge">${p.visibility==='private'?'Private':'Public'}</span><time datetime="${esc(p.created_at)}">${date(p.created_at)}</time>${p.authorization_id?'<span>Reservation collected</span>':''}</div></article>`).join('')}</div>`;
}
async function refreshWallet(){
  const generation=++state.walletGeneration;
  const [me,feed]=await Promise.all([api('/me'),api('/activity?limit=200')]);
  if(generation!==state.walletGeneration)return;
  state.me=me;
  const wallet=document.getElementById('wallet-content');if(wallet)wallet.innerHTML=walletMarkup();
  activity(feed.payments);
}
async function refreshPage(){
  if(!state.token)return;
  await refreshWallet();
  if(state.route==='/requests')await loadRequests();
  if(state.route==='/authorizations')await loadAuthorizations();
}
async function loadRequests(){
  const generation=++state.listGeneration;
  const data=await api('/requests?limit=200');if(generation!==state.listGeneration||state.route!=='/requests')return;
  const incoming=data.requests.filter(r=>r.payer_id===state.me.user_id),outgoing=data.requests.filter(r=>r.requester_id===state.me.user_id);
  const render=(rows,isIncoming)=>rows.map(r=>`<article class="row" data-testid="request-item-${esc(r.request_id)}" data-status="${r.status}"><div class="row-head"><div class="row-title">${isIncoming?'From @'+esc(r.requester_handle):'To @'+esc(r.payer_handle)}</div><div class="money" data-testid="request-amount-${esc(r.request_id)}">${money(r.amount)}</div></div><div class="row-note">${esc(r.note)}</div><div class="row-meta"><span class="badge ${r.status}">${r.status}</span><span>${date(r.created_at)}</span></div>${r.status==='pending'?`<div class="actions">${isIncoming?`<button class="button tiny" data-testid="request-pay-${esc(r.request_id)}" data-action="pay" data-id="${esc(r.request_id)}">Pay request</button><button class="button quiet tiny" data-testid="request-decline-${esc(r.request_id)}" data-action="decline" data-id="${esc(r.request_id)}">Decline</button>`:`<button class="button quiet tiny" data-testid="request-cancel-${esc(r.request_id)}" data-action="cancel" data-id="${esc(r.request_id)}">Cancel request</button>`}</div>`:''}</article>`).join('');
  $('incoming-list').innerHTML=render(incoming,true)||'<div class="empty">You’re all caught up.<br>No incoming requests yet.</div>';
  $('outgoing-list').innerHTML=render(outgoing,false)||'<div class="empty">Nothing waiting on someone else.<br>Send a request from your wallet.</div>';
  document.getElementById('requests-empty').innerHTML=data.requests.length?'':'<div class="feedback loading" data-testid="empty-requests">No requests yet. When you ask or receive one, you’ll see it here.</div>';
  document.querySelectorAll('[data-action]').forEach(button=>button.addEventListener('click',async()=>{
    const id=button.dataset.id, action=button.dataset.action, name='request-action-'+id;
    if(action==='pay'){
      // Preserve the path-scoped retry identity even if a response is lost.
      let op=state.ops.get(name);if(!op){op={key:crypto.randomUUID(),body:{}};state.ops.set(name,op);}
      button.disabled=true;feedback('request','loading','Confirming this request…');
      try{await api('/requests/'+encodeURIComponent(id)+'/pay','POST',op.body,op.key);feedback('request','success','Request paid.');}
      catch(error){feedback('request',error instanceof Refused?'error':'uncertain',error instanceof Refused?error.message:'We couldn’t confirm the payment. Retry to check it safely.');}
    }else{
      button.disabled=true;
      try{await api('/requests/'+encodeURIComponent(id)+'/'+action,'POST',{});feedback('request','success',action==='decline'?'Request declined.':'Request cancelled.');}
      catch(error){feedback('request','error',error.message);}
    }
    try{await refreshPage();}catch(error){feedback('request','error',error.message);}finally{button.disabled=false;}
  }));
}
function preview(){
  const host=$('split-preview');if(!host)return;
  try{
    const amount=minor($('split-amount').value), handles=$('split-handles').value.split(',').map(h=>h.trim());
    if(handles.some(h=>!h)||new Set(handles).size!==handles.length)return void(host.innerHTML='<span class="details">Add each handle once, in the order you want to split.</span>');
    const base=Math.floor(amount/handles.length),extra=amount%handles.length;
    host.innerHTML=handles.map((handle,index)=>`<div class="preview-row"><span>@${esc(handle)}</span><strong data-testid="split-share-${esc(handle)}">${money(base+(index<extra?1:0))}</strong></div>`).join('');
  }catch{host.innerHTML='<span class="details">Enter an amount and handles to see everyone’s share.</span>';}
}
async function loadAuthorizations(){
  const generation=++state.listGeneration;
  const data=await api('/authorizations?limit=200');if(generation!==state.listGeneration||state.route!=='/authorizations')return;
  const host=document.getElementById('authorization-content');
  if(!data.authorizations.length){host.innerHTML='<div class="empty" data-testid="empty-authorizations"><span class="empty-symbol">◇</span>Money set aside, peace of mind ahead.<br>Your reservations will appear here.</div>';return;}
  host.innerHTML=`<div data-testid="authorization-list">${data.authorizations.map(a=>{
    const incoming=a.to_user_id===state.me.user_id,id=esc(a.authorization_id);
    return `<article class="row" data-testid="authorization-item-${id}" data-status="${a.status}"><div class="row-head"><div class="row-title">${incoming?'From @'+esc(a.from_handle):'For @'+esc(a.to_handle)}</div><div class="money" data-testid="authorization-amount-${id}">${money(a.amount)}</div></div><div class="row-note">${esc(a.note)}</div><div class="row-meta"><span class="badge ${a.status}">${a.status==='open'?'Reserved':a.status}</span><span>${incoming?'Incoming':'Outgoing'}</span><span>${a.visibility==='private'?'Private':'Public'}</span></div>${a.status==='captured'?`<p class="details">Collected <strong data-testid="authorization-captured-${id}">${money(a.captured_amount)}</strong></p>`:a.captured_amount?`<p class="details">Collected ${money(a.captured_amount)} · Remaining ${money(a.remaining_amount)}</p>`:''}<p class="details">Expires <time data-testid="authorization-expires-${id}">${esc(a.expires_at)}</time></p>${a.status==='open'?(incoming?`<div class="capture-control"><div><label for="capture-${id}">Amount to collect</label><input id="capture-${id}" data-testid="authorization-capture-amount-${id}" inputmode="decimal" value="${money(a.remaining_amount).split(' ')[0]}"></div><button class="button tiny" data-testid="authorization-capture-${id}" data-capture="${id}">Collect money</button></div><label class="capture-options"><input type="checkbox" id="partial-${id}">Keep the remainder reserved for later</label>`:`<div class="actions"><button class="button quiet tiny" data-testid="authorization-void-${id}" data-void="${id}">Release reservation</button></div>`):''}</article>`;
  }).join('')}</div>`;
  document.querySelectorAll('[data-capture]').forEach(button=>button.addEventListener('click',async()=>{
    const id=button.dataset.capture, input=$('authorization-capture-amount-'+id), partial=document.getElementById('partial-'+id).checked;
    let body;try{body={amount:minor(input.value)};if(partial)body.final=false;}catch(error){feedback('authorization','error',error.message);return;}
    const name='capture-'+id, identity=JSON.stringify(body);let op=state.ops.get(name);
    if(!op||op.identity!==identity){op={key:crypto.randomUUID(),body,identity};state.ops.set(name,op);}
    button.disabled=true;
    try{await api('/authorizations/'+encodeURIComponent(id)+'/capture','POST',op.body,op.key);feedback('authorization','success','Money collected. Your wallet and reservation are up to date.');}
    catch(error){feedback('authorization',error instanceof Refused?'error':'uncertain',error instanceof Refused?error.message:'The outcome is uncertain. Retry these details to confirm the original capture.');}
    try{await refreshPage();}catch{}finally{button.disabled=false;}
  }));
  document.querySelectorAll('[data-void]').forEach(button=>button.addEventListener('click',async()=>{
    button.disabled=true;
    try{await api('/authorizations/'+encodeURIComponent(button.dataset.void)+'/void','POST',{});feedback('authorization','success','Reservation released. The remaining money is available again.');}
    catch(error){feedback('authorization','error',error.message);}
    try{await refreshPage();}catch{}finally{button.disabled=false;}
  }));
}
async function render(){
  if(!state.me&&!['/login','/signup'].includes(state.route)){state.route='/login';history.replaceState({},'',state.route);}
  shell();const main=document.getElementById('main');
  if(['/login','/signup'].includes(state.route)){
    const signup=state.route==='/signup',name=signup?'signup':'login';
    main.innerHTML=`<div class="auth-layout"><section class="auth-intro"><div class="eyebrow">A clearer everyday wallet</div><h1>${signup?'Good things start<br>with a connection.':'Welcome back.<br>Make yourself at home.'}</h1><p class="subtext">Pay someone, share a bill, or set money aside. A little less admin. A little more living.</p><div class="auth-art" aria-hidden="true"><span class="art-dot">↗</span><h3>Money with room to breathe.</h3><div class="art-line"></div><div class="art-line" style="width:42%"></div></div></section><section class="card"><div class="card-title"><h2>${signup?'Create your account':'Sign in to Pocketful'}</h2></div><form id="auth-form" novalidate>${signup?field('signup-display-name','Your name','How should we greet you?'):''}${field(name+'-email','Email address','you@example.com','email')}${field(name+'-password','Password',signup?'At least 8 characters':'Your password','password')}<button class="button" data-testid="${name}-submit" style="width:100%">${signup?'Create account':'Sign in'} <span aria-hidden="true">↗</span></button><div id="auth-feedback"></div></form><p class="auth-footer">${signup?'Already with us? <a href="/login">Sign in</a>':'New here? <a href="/signup">Create an account</a>'}</p></section></div>`;
    document.getElementById('auth-form').addEventListener('submit',async(event)=>{
      event.preventDefault();const button=$(name+'-submit');button.disabled=true;feedback('auth','loading','Signing you in…');
      try{
        const body={email:$(name+'-email').value,password:$(name+'-password').value};if(signup)body.display_name=$('signup-display-name').value;
        const result=await api('/auth/'+name,'POST',body);state.token=result.token;localStorage.setItem('pocketful-token',result.token);state.me=await api('/me');go('/');
      }catch(error){feedback('auth','error',error.message);}finally{button.disabled=false;}
    });
    main.querySelectorAll('a').forEach(link=>link.addEventListener('click',e=>{e.preventDefault();go(link.getAttribute('href'));}));
  }else if(state.route==='/'){
    main.innerHTML=heading('Your everyday wallet','A little more breathing room.',`Welcome, ${esc(state.me.display_name)}. Here’s where things stand.`, '<button class="button quiet tiny" data-testid="wallet-refresh">↻ Refresh</button>')+`<div id="wallet-content">${walletMarkup()}</div><div class="content-grid"><div class="stack">${transferForm('pay','Send a little something','For coffee, dinner, or just because.')}<section>${transferForm('authorize','Set money aside','Reserve money for someone to collect when they’re ready.')}</section></div><div class="stack"><section class="card"><div class="card-title"><h2>Your activity</h2><span>Latest connections</span></div><div id="feed-content"><div class="loading-block">Loading activity…</div></div></section>${transferForm('request','Ask for your share','A clear request keeps everyone on the same page.')}</div></div>`;
    bindTransfer('pay','/payments','Payment confirmed. Your money moved once, and these details are kept for a safe retry.');bindTransfer('request','/requests','Request sent. They can pay whenever they’re ready.');bindTransfer('authorize','/authorizations','Money reserved. Your available balance is up to date.');
    $('wallet-refresh').addEventListener('click',()=>refreshWallet().catch(error=>feedback('pay','error',error.message)));
    await refreshWallet();
  }else if(state.route==='/requests'){
    main.innerHTML=heading('Keep things moving','Requests, without the chasing.','A clear view of what’s coming in and what you’ve asked for.')+`<div id="request-feedback"></div><div id="requests-empty"></div><div class="content-grid section-gap"><section class="card"><div class="card-title"><h2>Incoming</h2><span>People asking you</span></div><div data-testid="incoming-list"><div class="loading-block">Loading requests…</div></div></section><section class="card"><div class="card-title"><h2>Outgoing</h2><span>Your requests to others</span></div><div data-testid="outgoing-list"></div></section></div>`;
    await loadRequests();
  }else if(state.route==='/split'){
    main.innerHTML=heading('Fair shares, good company','Split a bill. Keep it simple.','Add your people in order. We’ll handle the exact shares.')+`<section class="card" style="max-width:670px"><form id="split-form" novalidate>${field('split-amount','Bill total','0.00')}${field('split-handles','Who’s sharing?','ada, bob, cy')}<p class="details spaced">Separate handles with commas. Include yourself if you paid your own share.</p>${field('split-note','A note (optional)','Dinner with the crew')}<h3>Everyone’s share</h3><div class="preview" data-testid="split-preview"></div><div class="form-footer"><small>Every minor unit accounted for.<br>No one’s balance is checked yet.</small><button class="button" data-testid="split-submit">Send requests ↗</button></div><div id="split-feedback"></div></form></section>`;
    document.getElementById('split-form').addEventListener('submit',event=>{event.preventDefault();let body;try{body={amount:minor($('split-amount').value),participant_handles:$('split-handles').value.split(',').map(h=>h.trim()),note:$('split-note').value};}catch(error){feedback('split','error',error.message);return;}write('split','/splits',body,$('split-submit'),'Your shares are ready. Requests sent to everyone except you.');});preview();
  }else if(state.route==='/authorizations'){
    main.innerHTML=heading('Reserved, not spent','A little set aside for later.','See what’s reserved, collect what’s ready, and release what you don’t need.')+`<div id="wallet-content">${walletMarkup()}</div><div id="authorization-feedback"></div><section class="card section-gap"><div class="card-title"><h2>Your reservations</h2><span>Incoming & outgoing</span></div><div id="authorization-content"><div class="loading-block">Loading reservations…</div></div></section>`;
    await loadAuthorizations();
  }
  bindFields();
}
function go(path){state.walletGeneration++;state.listGeneration++;state.route=path;history.pushState({},'',path);render().catch(error=>{document.getElementById('main').insertAdjacentHTML('afterbegin',`<div class="feedback error" role="alert">${esc(error.message)}</div>`);});}
window.addEventListener('popstate',()=>{state.route=location.pathname;state.walletGeneration++;state.listGeneration++;render();});
(async()=>{
  if(state.token){try{state.me=await api('/me');}catch{state.token=null;localStorage.removeItem('pocketful-token');}}
  await render();
})().catch(error=>{document.getElementById('app').innerHTML=`<div class="boot">We couldn’t load your wallet.<span>${esc(error.message)}</span><a class="button" href="/login">Try signing in</a></div>`;});
