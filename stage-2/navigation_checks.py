"""Fabricator navigation barrier and outcome regressions; no product imports.

Run in a Playwright client sharing only a resource-limited service's network
namespace (localhost8080). Snapshots, credentials and tokens stay in memory.
"""
import asyncio,json
from urllib.request import Request,urlopen
from playwright.async_api import async_playwright,expect

BASE='http://127.0.0.1:8080'
def fixture():
    return {'currency':'EUR','minor_units':2,'users':[
        {'id':h,'handle':h,'email':h+'@nav.invalid','password':'nav-private-password',
         'display_name':h.upper(),'balance':1000 if h=='a' else 0} for h in 'abc']}
def setup():
    response=urlopen(Request(BASE+'/_test/reset',json.dumps(fixture()).encode(),{'Content-Type':'application/json'}),timeout=10)
    assert response.status==204

async def session(browser):
    setup();page=await browser.new_page()
    await page.goto(BASE+'/login')
    await page.get_by_test_id('login-email').fill('a@nav.invalid')
    await page.get_by_test_id('login-password').fill('nav-private-password')
    await page.get_by_test_id('login-submit').click()
    await expect(page.get_by_test_id('wallet-balance')).to_have_attribute('data-amount','1000')
    return page

async def pending(page,path,outcome='success'):
    blocked=asyncio.Event();release=asyncio.Event();reads=[];bodies=[]
    async def handler(route):
        bodies.append((route.request.headers.get('idempotency-key'),route.request.post_data))
        blocked.set();await asyncio.wait_for(release.wait(),10)
        if outcome=='success':await route.continue_()
        elif outcome=='refused':await route.fulfill(status=409,content_type='application/json',body=json.dumps({'error':{'code':'insufficient_funds','message':'refused'}}))
        else:
            response=await route.fetch();assert response.status==201
            await route.abort('failed')
    await page.route(BASE+path,handler)
    def observe(req):
        if blocked.is_set() and not release.is_set() and req.method=='GET' and any(part in req.url for part in ['/me','/requests?','/activity?','/authorizations?']):reads.append(req.url)
    page.on('request',observe)
    return blocked,release,reads,bodies,handler

async def main():
    groups=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch()
        # Cover all three wallet writes and split, not only the original payment.
        for kind,path,target in [('pay','/payments','Requests'),('request','/requests','Reservations'),('authorize','/authorizations','Requests'),('split','/splits','Wallet')]:
            page=await session(browser)
            if kind=='split':
                await page.get_by_role('link',name='Split a bill',exact=True).click()
                await page.get_by_test_id('split-amount').fill('1.00');await page.get_by_test_id('split-handles').fill('a,b,c')
            else:
                await page.get_by_test_id(kind+'-handle').fill('b');await page.get_by_test_id(kind+'-amount').fill('1.00')
            blocked,release,reads,bodies,handler=await pending(page,path)
            original=page.url
            await page.get_by_test_id(kind+'-submit').click();await asyncio.wait_for(blocked.wait(),5)
            await page.get_by_role('link',name=target,exact=True).click();await page.wait_for_timeout(200)
            assert not reads and page.url==original,(kind,reads)
            release.set();await expect(page).to_have_url(BASE+{'Requests':'/requests','Reservations':'/authorizations','Wallet':'/'}[target])
            groups.append(kind+' waits before navigation');await page.close()
        for outcome,testid in [('refused','pay-error'),('uncertain','pay-uncertain')]:
            page=await session(browser)
            await page.get_by_test_id('pay-handle').fill('b');await page.get_by_test_id('pay-amount').fill('1.00')
            blocked,release,reads,bodies,handler=await pending(page,'/payments',outcome)
            await page.get_by_test_id('pay-submit').click();await asyncio.wait_for(blocked.wait(),5)
            await page.get_by_role('link',name='Requests',exact=True).click();await page.wait_for_timeout(200)
            assert not reads
            release.set();await expect(page.get_by_test_id(testid)).to_be_visible();await page.wait_for_timeout(100)
            assert page.url==BASE+'/'
            await expect(page.get_by_test_id('pay-amount')).to_have_value('1.00')
            await page.unroute(BASE+'/payments',handler)
            retried=[]
            page.on('request',lambda req:retried.append((req.headers.get('idempotency-key'),req.post_data)) if req.method=='POST' and req.url==BASE+'/payments' else None)
            await page.get_by_test_id('pay-submit').click();await expect(page.get_by_test_id('wallet-balance')).to_have_attribute('data-amount','900')
            await expect(page.get_by_test_id('pay-error')).to_have_count(0);await expect(page.get_by_test_id('pay-uncertain')).to_have_count(0)
            assert retried==bodies
            groups.append(outcome+' cancels queued navigation and retains same retry');await page.close()
        page=await session(browser);await page.get_by_test_id('pay-handle').fill('b');await page.get_by_test_id('pay-amount').fill('1.00')
        blocked,release,reads,bodies,handler=await pending(page,'/payments')
        await page.get_by_test_id('pay-submit').click();await asyncio.wait_for(blocked.wait(),5)
        await page.get_by_role('link',name='Requests',exact=True).click();await page.get_by_role('link',name='Reservations',exact=True).click()
        await page.wait_for_timeout(200);assert not reads
        release.set();await expect(page).to_have_url(BASE+'/authorizations')
        await expect(page.get_by_test_id('wallet-balance')).to_have_attribute('data-amount','900')
        groups.append('latest queued destination wins');await page.close()
        page=await session(browser)
        await page.get_by_role('link',name='Requests',exact=True).click();await page.get_by_role('link',name='Wallet',exact=True).click()
        await expect(page.get_by_test_id('wallet-balance')).to_have_attribute('data-amount','1000')
        await page.get_by_test_id('pay-handle').fill('b');await page.get_by_test_id('pay-amount').fill('1.00')
        blocked,release,reads,bodies,handler=await pending(page,'/payments')
        await page.get_by_test_id('pay-submit').click();await asyncio.wait_for(blocked.wait(),5)
        await page.evaluate('history.back()');await page.wait_for_timeout(200);assert not reads
        release.set();await expect(page.get_by_test_id('incoming-list')).to_be_visible()
        await page.get_by_role('link',name='Wallet',exact=True).click();await expect(page.get_by_test_id('wallet-balance')).to_have_attribute('data-amount','900')
        groups.append('history navigation waits before data read');await page.close()
        page=await session(browser);await page.get_by_test_id('pay-handle').fill('b');await page.get_by_test_id('pay-amount').fill('1.00')
        blocked,release,reads,bodies,handler=await pending(page,'/payments')
        await page.get_by_test_id('pay-submit').click();await asyncio.wait_for(blocked.wait(),5)
        await page.get_by_test_id('logout-button').click();await page.wait_for_timeout(200)
        assert not reads and await page.evaluate("localStorage.getItem('pocketful-token')")
        release.set();await expect(page).to_have_url(BASE+'/login')
        assert await page.evaluate("localStorage.getItem('pocketful-token')") is None
        groups.append('logout waits before clearing live session');await page.close()
        await browser.close()
    print(json.dumps({'passed_groups':groups,'failures':0,'state':'credentials/retries only in memory'}),flush=True)

if __name__=='__main__':asyncio.run(main())
