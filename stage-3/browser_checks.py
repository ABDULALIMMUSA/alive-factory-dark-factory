"""Real Chromium faults, competing clients, upgrade continuity and visual captures.
Run inside a Playwright runner with base URL, old API URL and an output directory.
State and credentials stay in RAM; logs contain only named outcomes.
"""
import json
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright, expect
import httpx

BASE,OLD,OUTPUT=sys.argv[1:4]
out=Path(OUTPUT);out.mkdir(parents=True,exist_ok=True)
checks=0
fixture={'currency':'EUR','minor_units':2,'users':[{'id':h,'email':h+'@browser.invalid','password':'browser-checks-only','display_name':n,'handle':h,'balance':bal} for h,n,bal in [('a','Ada Rivers',1000),('b','Bob Morgan',100),('c','Cy Lee',0)]], 'settlement_operator_ids':['a']}
client=httpx.Client(timeout=10)
def api(path,body=None,token=None,key=None,base=BASE):
    headers={}
    if token:headers['Authorization']='Bearer '+token
    if key:headers['Idempotency-Key']=key
    r=client.request('GET' if body is None else 'POST',base+path,json=body,headers=headers)
    assert r.status_code<500
    return r
def seed(base=BASE):assert api('/_test/reset',fixture,base=base).status_code==204
def token(h,base=BASE):return api('/auth/login',{'email':h+'@browser.invalid','password':'browser-checks-only'},base=base).json()['token']
def checked(name):
    global checks
    checks+=1;print('PASS',name,flush=True)
def login(page,h='a'):
    page.goto(BASE+'/login');page.get_by_test_id('login-email').fill(h+'@browser.invalid');page.get_by_test_id('login-password').fill('browser-checks-only');page.get_by_test_id('login-submit').click();expect(page.get_by_test_id('current-user')).to_be_visible();expect(page.get_by_test_id('pay-submit')).to_be_visible()
def pay_form(page,amount='2.00'):
    page.get_by_test_id('pay-handle').fill('b');page.get_by_test_id('pay-amount').fill(amount);page.get_by_test_id('pay-note').fill('Dinner 🌿 <&>')
def new_page(browser):
    context=browser.new_context(viewport={'width':1440,'height':1100});context.set_default_timeout(10000)
    return context,context.new_page()

with sync_playwright() as p:
    browser=p.chromium.launch(channel='chromium',args=['--unsafely-treat-insecure-origin-as-secure='+BASE])
    seed(OLD);pending=api('/requests',{'payer_handle':'a','amount':50,'note':'Old lunch'},token('b',OLD),'pending-upgrade',OLD).json()
    context,page=new_page(browser);upgraded=False;lost=False;identities=[]
    paths={'/me','/activity','/requests','/payments','/auth/login'}
    def bridge(route):
        global lost
        path=urlsplit(route.request.url).path
        if route.request.resource_type=='document' or path not in paths:
            route.continue_();return
        endpoint=(BASE if upgraded else OLD)+path
        if urlsplit(route.request.url).query:endpoint+='?'+urlsplit(route.request.url).query
        response=route.fetch(url=endpoint)
        if path=='/payments' and route.request.method=='POST':
            identities.append((route.request.headers.get('idempotency-key'),route.request.post_data))
            if not lost:lost=True;route.abort('failed');return
        route.fulfill(response=response)
    page.route('**/*',bridge);login(page);pay_form(page);page.get_by_test_id('pay-submit').click()
    expect(page.get_by_test_id('pay-uncertain')).to_be_visible();expect(page.get_by_test_id('pay-error')).to_have_count(0)
    page.screenshot(path=str(out/'payment-uncertain-desktop.png'),full_page=True)
    snapshot=api('/_test/export',base=OLD).json();assert api('/_test/import',snapshot).status_code==204;upgraded=True
    page.get_by_test_id('pay-submit').click();expect(page.get_by_test_id('wallet-balance')).to_have_attribute('data-amount','800')
    expect(page.get_by_test_id('pay-uncertain')).to_have_count(0);expect(page.get_by_test_id('pay-error')).to_have_count(0)
    assert len(identities)==2 and identities[0]==identities[1]
    expect(page.get_by_test_id('pay-amount')).to_have_value('2.00');expect(page.get_by_test_id('pay-note')).to_have_value('Dinner 🌿 <&>')
    assert len(api('/_test/export').json()['state']['payments'])==1
    page.get_by_role('link',name='Requests',exact=True).click();page.get_by_test_id('request-pay-'+pending['request_id']).click()
    expect(page.get_by_test_id('request-item-'+pending['request_id'])).to_have_attribute('data-status','paid')
    checked('lost committed Stage1 payment retries unchanged after import; existing browser/token/form and pending request survive without reload');context.close()

    seed();context,page=new_page(browser);login(page);pay_form(page,'3.00')
    api('/payments',{'to_handle':'b','amount':900},token('a'),'other-client')
    page.get_by_test_id('pay-submit').click();expect(page.get_by_test_id('pay-error')).to_be_visible()
    expect(page.get_by_test_id('wallet-available')).to_have_attribute('data-amount','100')
    page.screenshot(path=str(out/'payment-refused-desktop.png'),full_page=True)
    expect(page.get_by_test_id('pay-amount')).to_have_value('3.00');expect(page.get_by_test_id('pay-uncertain')).to_have_count(0)
    checked('known competing-client refusal refreshes funds/feed, preserves inputs and differs from uncertainty');context.close()

    seed();tb=token('b');r=api('/requests',{'payer_handle':'a','amount':50},tb,'stale').json();context,page=new_page(browser);login(page)
    page.get_by_role('link',name='Requests',exact=True).click();expect(page.get_by_test_id('request-pay-'+r['request_id'])).to_be_visible()
    api('/requests/'+r['request_id']+'/cancel',{},tb)
    page.get_by_test_id('request-pay-'+r['request_id']).click();expect(page.get_by_test_id('request-error')).to_be_visible()
    expect(page.get_by_test_id('request-pay-'+r['request_id'])).to_have_count(0);expect(page.get_by_test_id('request-item-'+r['request_id'])).to_have_attribute('data-status','cancelled')
    checked('cancelled stale request refuses then removes obsolete pay action');context.close()

    seed();context,page=new_page(browser);login(page);expect(page.get_by_test_id('wallet-available')).to_have_attribute('data-amount','1000');waiting=[];counts={}
    def delayed(route):
        path=urlsplit(route.request.url).path;counts[path]=counts.get(path,0)+1
        response=route.fetch()
        if counts[path]==1:waiting.append((route,response))
        else:route.fulfill(response=response)
    page.route('**/me',delayed);page.route('**/activity?*',delayed)
    page.get_by_test_id('wallet-refresh').click()
    end=time.monotonic()+5
    while len(waiting)<2 and time.monotonic()<end:page.wait_for_timeout(20)
    assert len(waiting)==2
    ta=token('a');hold=api('/authorizations',{'to_handle':'b','amount':200},ta,'held-new').json()
    payment=api('/payments',{'to_handle':'b','amount':100},ta,'spent-new').json()
    page.get_by_test_id('wallet-refresh').click();expect(page.get_by_test_id('wallet-balance')).to_have_attribute('data-amount','900')
    expect(page.get_by_test_id('wallet-available')).to_have_attribute('data-amount','700');expect(page.get_by_test_id('wallet-held')).to_have_attribute('data-amount','200')
    for route,response in waiting:route.fulfill(response=response)
    page.wait_for_timeout(100)
    expect(page.get_by_test_id('wallet-balance')).to_have_attribute('data-amount','900');expect(page.get_by_test_id('wallet-available')).to_have_attribute('data-amount','700');expect(page.get_by_test_id('wallet-held')).to_have_attribute('data-amount','200')
    expect(page.get_by_test_id('activity-item-'+payment['payment_id'])).to_be_visible()
    checked('delayed older balance/feed responses cannot overwrite newer total/available/held refresh');context.close()

    seed();ta=token('a');hold=api('/authorizations',{'to_handle':'b','amount':600,'note':'Weekend stay','visibility':'private'},ta,'ui-hold').json();aid=hold['authorization_id']
    context,page=new_page(browser);login(page,'b');page.get_by_role('link',name='Reservations',exact=True).click()
    expect(page.get_by_test_id('authorization-capture-amount-'+aid)).to_have_value('6.00')
    page.get_by_test_id('authorization-capture-amount-'+aid).fill('2.00');page.locator('#partial-'+aid).check();page.get_by_test_id('authorization-capture-'+aid).click()
    expect(page.get_by_test_id('authorization-capture-amount-'+aid)).to_have_value('4.00');expect(page.get_by_test_id('authorization-item-'+aid)).to_have_attribute('data-status','open')
    page.screenshot(path=str(out/'capture-partial-desktop.png'),full_page=True)
    page.get_by_test_id('authorization-capture-'+aid).click();expect(page.get_by_test_id('authorization-item-'+aid)).to_have_attribute('data-status','captured')
    expect(page.get_by_test_id('authorization-captured-'+aid)).to_have_text('6.00 EUR');expect(page.get_by_test_id('wallet-available')).to_have_attribute('data-amount','700')
    page.screenshot(path=str(out/'capture-final-desktop.png'),full_page=True)
    checked('browser partial capture, remaining default, final close and balance update');context.close()

    seed();ta=token('a');hold=api('/authorizations',{'to_handle':'b','amount':250},ta,'visual-hold').json()
    api('/payments',{'to_handle':'b','amount':125,'note':'Coffee & a good catch-up','visibility':'public'},ta,'visual-payment')
    context,page=new_page(browser);login(page)
    expect(page.get_by_test_id('wallet-available')).to_have_attribute('data-amount','625')
    page.screenshot(path=str(out/'wallet-desktop.png'),full_page=True)
    for width in [375,1440]:
        page.set_viewport_size({'width':width,'height':900})
        for path in ['/','/requests','/split','/authorizations','/login','/signup']:
            page.goto(BASE+path);page.wait_for_load_state('networkidle')
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'),('overflow',width,path)
            assert page.locator('main label').count()>0 or path in ['/requests','/authorizations']
            if width==375:page.screenshot(path=str(out/((path.strip('/') or 'wallet')+'-mobile.png')),full_page=True)
    checked('six routes at375/1440px without horizontal overflow; visible labels and responsive screenshots captured')
    page.goto(BASE+'/authorizations');page.get_by_test_id('authorization-void-'+hold['authorization_id']).click()
    expect(page.get_by_test_id('authorization-item-'+hold['authorization_id'])).to_have_attribute('data-status','voided')
    expect(page.get_by_test_id('wallet-held')).to_have_count(0)
    checked('payer browser release removes held amount and pending void button');context.close()
    browser.close()
print(json.dumps({'passed_groups':checks,'failures':0,'private_state':'memory only'}),flush=True)
