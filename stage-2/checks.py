"""Cumulative Stage 2 HTTP invariants, captures, migration and contention.
Private snapshots/tokens exist only in memory. Run against isolated test services.
"""
import copy
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import http.client
import json
import sys
import threading
import time
from urllib.parse import urlsplit

A=sys.argv[1]
B=sys.argv[2] if len(sys.argv)>2 else A
OLD=sys.argv[3] if len(sys.argv)>3 else None
COUNT=0
MAX=0

def call(path,body=None,token=None,key=None,base=A):
    global COUNT,MAX
    address=urlsplit(base);conn=http.client.HTTPConnection(address.hostname,address.port,timeout=10 if path.startswith('/_test/') else 5)
    headers={'Accept':'application/json','Content-Type':'application/json'}
    if token:headers['Authorization']='Bearer '+token
    if key:headers['Idempotency-Key']=key
    start=time.monotonic()
    try:
        conn.request('GET' if body is None else 'POST',path,None if body is None else json.dumps(body).encode(),headers)
        response=conn.getresponse();raw=response.read();elapsed=time.monotonic()-start
        COUNT+=1;MAX=max(MAX,elapsed)
        assert response.status<500 and elapsed<(10 if path.startswith('/_test/') else 5)
        return response.status,json.loads(raw) if raw else None
    finally:conn.close()

def need(result,status,code=None):
    assert result[0]==status,('status',result[0],status)
    if code:assert result[1]['error']['code']==code
    return result[1]
def snapshot(base=A):return need(call('/_test/export',base=base),200)
def login(h,base=A):return need(call('/auth/login',{'email':h+'@checks.invalid','password':'stage-two-tests'},base=base),200)['token']
fixture={'currency':'EUR','minor_units':2,'authorization_ttl_seconds':600,
         'users':[{'id':h,'email':h+'@checks.invalid','password':'stage-two-tests','display_name':h,'handle':h,'balance':balance} for h,balance in zip('abc',[1000,100,0])],
         'settlement_operator_ids':['a']}
def seed(value=fixture):
    need(call('/_test/reset',value),204)
    return {h:login(h) for h in 'abc'}
def me(token,base=A):return need(call('/me',token=token,base=base),200)
def conserved(base=A):
    state=snapshot(base)['state']
    assert sum(u['balance'] for u in state['users'].values())==state['seeded_total']
    for uid,u in state['users'].items():
        held=sum(a['amount']-a['captured_amount'] for a in state['authorizations'].values() if a['status']=='open' and a['from_user_id']==uid)
        assert 0<=held<=u['balance']
    return state
def wave(fn):
    barrier=threading.Barrier(50)
    def run(i):barrier.wait(timeout=10);return fn(i)
    with ThreadPoolExecutor(max_workers=50) as pool:return list(pool.map(run,range(50)))

t=seed();authbody={'to_handle':'b','amount':600,'note':'deposit','visibility':'private'}
auth=need(call('/authorizations',authbody,t['a'],'hold'),201);aid=auth['authorization_id'];path='/authorizations/'+aid+'/capture'
assert (me(t['a'])['total'],me(t['a'])['available'],me(t['a'])['held'])==(1000,400,600)
before=snapshot();need(call('/payments',{'to_handle':'b','amount':401},t['a'],'unfunded'),409,'insufficient_funds');assert snapshot()==before
need(call(path,{'amount':1},t['a'],'wrong-party'),403,'forbidden')
need(call('/authorizations/'+aid+'/void',{},t['b']),403,'forbidden')
partial=need(call(path,{'amount':200,'final':False},t['b'],'partial'),201)
assert partial['authorization_id']==aid and partial['request_id'] is None and partial['visibility']=='private'
assert (me(t['a'])['total'],me(t['a'])['available'],me(t['a'])['held'])==(800,400,400)
net={'transfers':[{'from_handle':'a','to_handle':'b','amount':450},{'from_handle':'b','to_handle':'a','amount':50}]}
need(call('/settlements',net,t['a'],'net'),201);assert me(t['a'])['available']==0
final=need(call(path,{'amount':100},t['b'],'final'),201)
view=need(call('/authorizations',token=t['a']),200)['authorizations'][0]
assert view['status']=='captured' and view['captured_amount']==300 and view['remaining_amount']==0 and view['payment_ids']==[partial['payment_id'],final['payment_id']]
assert view['payment_id']==final['payment_id'] and me(t['a'])['available']==300 and me(t['a'])['held']==0
assert need(call(path,{'amount':200,'final':False},t['b'],'partial'),200)==partial
assert need(call('/authorizations',authbody,t['a'],'hold'),200)==auth
need(call(path,{},t['b'],'closed'),409,'authorization_not_open')
need(call(path,{'amount':201,'final':False},t['b'],'partial'),409,'idempotency_key_reuse')
state=conserved();portable=snapshot();need(call('/_test/import',portable,base=B),204);assert snapshot(B)==portable
assert me(t['a'],B)['available']==300 and login('a',B)
assert need(call(path,{'amount':100},t['b'],'final',base=B),200)==final
for mutate in ['amount','actor','order','receipt','final']:
    bad=copy.deepcopy(portable);record=bad['state']['authorizations'][aid]
    if mutate=='amount':record['captured_amount']=301
    if mutate=='actor':record['to_user_id']='c'
    if mutate=='order':record['payment_ids'].reverse()
    if mutate=='receipt':next(e for e in bad['state']['idempotency'] if e['key']=='partial')['response']['amount']=201
    if mutate=='final':
        entry=next(e for e in bad['state']['idempotency'] if e['key']=='partial')
        entry['body'][1]=[pair for pair in entry['body'][1] if pair[0]!='final']
    baseline=snapshot(B);need(call('/_test/import',bad,base=B),422,'validation_failed');assert snapshot(B)==baseline
print('PASS reserved affordability, partial/final captures, net funding, semantic portable claims',flush=True)

t=seed();auth=need(call('/authorizations',{'to_handle':'b','amount':200},t['a'],'contend'),201);path='/authorizations/'+auth['authorization_id']+'/capture'
results=wave(lambda _:call(path,{},t['b'],'same-capture'))
assert sum(r[0]==201 for r in results)==1 and sum(r[0]==200 for r in results)==49
assert all(r[1]==results[0][1] for r in results);conserved();assert me(t['a'])['total']==800
t=seed();results=wave(lambda i:call('/authorizations',{'to_handle':'b','amount':30},t['a'],'reserve-'+str(i)))
assert sum(r[0]==201 for r in results)==33 and sum(r[0]==409 for r in results)==17
assert me(t['a'])['available']==10 and me(t['a'])['total']==1000;conserved()
t=seed();auth=need(call('/authorizations',{'to_handle':'b','amount':600},t['a'],'race'),201);aid=auth['authorization_id']
results=wave(lambda i:call('/authorizations/'+aid+('/void' if i==49 else '/capture'),{} if i==49 else {'amount':10,'final':False},t['a'] if i==49 else t['b'],'capture-'+str(i) if i!=49 else None))
assert results[49][0]==200 and all(r[0] in [201,409] for r in results[:49]);state=conserved();assert state['authorizations'][aid]['status']=='voided' and me(t['a'])['held']==0
print('PASS 50-way capture replay, distinct reserve overspend and capture/void contention',flush=True)

short=copy.deepcopy(fixture);short['authorization_ttl_seconds']=1;t=seed(short)
auth=need(call('/authorizations',{'to_handle':'b','amount':200},t['a'],'expires'),201);aid=auth['authorization_id'];path='/authorizations/'+aid+'/capture'
p=need(call(path,{'amount':50,'final':False},t['b'],'exp-partial'),201)
time.sleep(1.15)
assert me(t['a'])['available']==950 and me(t['a'])['held']==0
view=need(call('/authorizations',token=t['a']),200)['authorizations'][0]
assert view['status']=='expired' and view['captured_amount']==50 and view['remaining_amount']==0
need(call(path,{},t['b'],'too-late'),409,'authorization_expired');need(call(path,{},t['c'],'outsider'),403,'forbidden')
assert need(call(path,{'amount':50,'final':False},t['b'],'exp-partial'),200)==p
clock=dt.datetime.now(dt.timezone.utc);seeded=copy.deepcopy(fixture)
seeded['authorizations']=[{'id':'past','from_user_id':'a','to_user_id':'b','amount':900,'status':'open','expires_at':(clock-dt.timedelta(hours=2)).isoformat()},
                          {'id':'future','from_user_id':'a','to_user_id':'b','amount':600,'status':'open','expires_at':(clock+dt.timedelta(hours=2)).isoformat()}]
t=seed(seeded);assert me(t['a'])['available']==400
before=snapshot();bad=copy.deepcopy(seeded);bad['authorizations'][1]['amount']=1001
need(call('/_test/reset',bad),422,'validation_failed');assert snapshot()==before
need(call('/authorizations/future/capture',{'amount':601},t['b'],'excess'),422,'capture_exceeds_authorization')
need(call('/authorizations/future/capture',{},t['b'],'excess'),201);assert me(t['a'])['held']==0;conserved()
print('PASS clock expiry, partial remainder release, seeded expiry and atomic over-held reset',flush=True)

if OLD:
    old_fixture=copy.deepcopy(fixture);old_fixture.pop('authorization_ttl_seconds')
    need(call('/_test/reset',old_fixture,base=OLD),204);old_tokens={h:login(h,OLD) for h in 'abc'}
    p=need(call('/payments',{'to_handle':'b','amount':7},old_tokens['a'],'lost-before-upgrade',base=OLD),201)
    request=need(call('/requests',{'payer_handle':'a','amount':3},old_tokens['b'],'old-request',base=OLD),201)
    old=snapshot(OLD);need(call('/_test/import',old),204)
    assert me(old_tokens['a'])['balance']==993 and me(old_tokens['a'])['held']==0
    assert need(call('/payments',{'to_handle':'b','amount':7},old_tokens['a'],'lost-before-upgrade'),200)==p
    need(call('/requests/'+request['request_id']+'/pay',{},old_tokens['a'],'pay-old'),201)
    migrated=snapshot();need(call('/_test/import',migrated,base=B),204);assert snapshot(B)==migrated
    assert need(call('/payments',{'to_handle':'b','amount':7},old_tokens['a'],'lost-before-upgrade',base=B),200)==p
    login('a',B);conserved(B)
    print('PASS shipped Stage1 export, old sessions/passwords/receipts/pending requests, repeat portable upgrade',flush=True)
print(f'PASS Stage2: {COUNT} HTTP checks; max {MAX:.3f}s; private snapshots only in RAM',flush=True)
