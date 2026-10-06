"""Fabricator-derived R1/R2 HTTP regressions for the Stage 2 schema-2 export.

No product imports; private snapshot bodies and tokens remain in memory.
Derived from the retained independent Stage 1 probe; its semantic assertions are
unchanged. Only the opaque export schema guard is adapted to Stage 2. The original
peer probe outside this repository remains unchanged.
"""
import argparse
import copy
from decimal import Decimal
import http.client
import json
import time
from urllib.parse import urlsplit

class Checks:
    def __init__(self, source, destination):
        self.source, self.destination = source, destination
        self.calls = self.cases = 0
        self.failures = []
        self.max_seconds = 0

    def call(self, base, method, path, body=None, token=None, key=None, raw=None):
        address = urlsplit(base)
        timeout = 10 if path.startswith('/_test/') else 5
        connection = http.client.HTTPConnection(address.hostname, address.port, timeout=timeout)
        headers = {'Content-Type': 'application/json'}
        if token is not None:
            headers['Authorization'] = 'Bearer ' + token
        if key is not None:
            headers['Idempotency-Key'] = key
        data = raw if raw is not None else json.dumps(body, ensure_ascii=False).encode() if body is not None else None
        started = time.monotonic()
        try:
            connection.request(method, path, data, headers)
            response = connection.getresponse()
            content = response.read()
            elapsed = time.monotonic() - started
            self.calls += 1
            self.max_seconds = max(self.max_seconds, elapsed)
            assert response.getheader('Content-Type') == 'application/json; charset=utf-8', 'content type'
            assert elapsed < timeout, 'request timeout'
            assert response.status < 500, 'HTTP 5xx'
            return response.status, json.loads(content) if content else None
        finally:
            connection.close()

    @staticmethod
    def need(result, status, code=None):
        assert result[0] == status, 'expected status %s, observed %s' % (status, result[0])
        if code:
            assert (result[1] or {}).get('error', {}).get('code') == code, 'unexpected error code'
        return result[1]

    def snapshot(self, base):
        return self.need(self.call(base, 'GET', '/_test/export'), 200)

    def run(self, name, function):
        self.cases += 1
        try:
            function()
            print('PASS', name, flush=True)
        except Exception as error:
            # Metadata only: do not serialize exception response bodies or exports.
            self.failures.append(name)
            print('FAIL', name, type(error).__name__, flush=True)

    def rejects_atomically(self, base, path, body, status, before):
        result = self.call(base, 'POST', path, body)
        after = self.snapshot(base)
        try:
            self.need(result, status, 'malformed_request' if status == 400 else 'validation_failed')
            assert after == before, 'rejected control changed complete snapshot'
        finally:
            # A broken implementation must not cascade into misleading later cases.
            if after != before:
                self.need(self.call(base, 'POST', '/_test/import', before), 204)
                assert self.snapshot(base) == before, 'could not restore baseline'


def fixture():
    return {'currency': 'EUR', 'minor_units': 2, 'settlement_operator_ids': ['a'],
            'users': [{'id': h, 'email': h+'@r1r2.invalid', 'password': 'r1r2-private-pass',
                       'display_name': h, 'handle': h, 'balance': bal}
                      for h, bal in zip('abc', (1000, 100, 0))],
            'payments': [{'id': 'seedp', 'from_user_id': 'a', 'to_user_id': 'b',
                          'amount': 7, 'note': 'seed', 'visibility': 'public'}],
            'requests': [{'id': 'seedrq', 'requester_id': 'b', 'payer_id': 'a',
                          'amount': 4, 'note': 'seed', 'status': 'pending'}]}


def canonical(value):
    """Independent format adapter for existing tagged JSON snapshot values."""
    if value is None:
        return ['null']
    if type(value) is bool:
        return ['bool', value]
    if isinstance(value, (int, float, Decimal)):
        number = Decimal(str(value))
        sign, digits, power = number.as_tuple()
        digits = ''.join(map(str, digits))
        if not any(int(char) for char in digits):
            return ['number', '0']
        trimmed = digits.rstrip('0')
        power += len(digits) - len(trimmed)
        return ['number', ('-' if sign else '') + trimmed + 'e' + str(power)]
    if isinstance(value, str):
        return ['string', value]
    if isinstance(value, list):
        return ['array', [canonical(item) for item in value]]
    return ['object', [[key, canonical(value[key])] for key in sorted(value)]]


def modify_path(value, path, replacement=None, remove=False):
    target = value
    for part in path[:-1]:
        target = target[part]
    if remove:
        del target[path[-1]]
    else:
        target[path[-1]] = replacement


def create_history(checks):
    c, base = checks, checks.source
    c.need(c.call(base, 'POST', '/_test/reset', fixture()), 204)
    tokens = {h: c.need(c.call(base, 'POST', '/auth/login',
              {'email': h+'@r1r2.invalid', 'password': 'r1r2-private-pass'}), 200)['token'] for h in 'abc'}
    receipts = []

    def create(key, path, body, actor, raw=None):
        response = c.need(c.call(base, 'POST', path, body, tokens[actor], key, raw=raw), 201)
        receipts.append({'key': key, 'path': path, 'body': body, 'actor': actor, 'response': response})
        return response

    create('p-default', '/payments', {'to_handle': 'b', 'amount': 11,
           'unknown': {'number': 0.1, 'bool': True, 'array': [None, '🌍']}}, 'a',
           raw='{"to_handle":"b","amount":1.1e1,"unknown":{"number":0.10,"bool":true,"array":[null,"🌍"]}}'.encode())
    create('p-explicit', '/payments', {'to_handle': 'b', 'amount': 7, 'note': '', 'visibility': 'public'}, 'a')
    request = create('rq-paid', '/requests', {'payer_handle': 'a', 'amount': 13, 'note': '  rent 🌍  ', 'unknown': 1}, 'b')
    create('pay-main', '/requests/'+request['request_id']+'/pay', {'unknown': {'x': 2}}, 'a')
    terminal = create('rq-cancelled', '/requests', {'payer_handle': 'c', 'amount': 2000}, 'b')
    c.need(c.call(base, 'POST', '/requests/'+terminal['request_id']+'/cancel', {}, tokens['b']), 200)
    split = create('split-main', '/splits', {'amount': 1, 'participant_handles': ['a', 'b', 'c'],
                   'unknown': ['order', 1]}, 'a')
    assert [x['amount'] for x in split['shares']] == [1, 0, 0]
    create('pay-zero', '/requests/'+split['requests'][0]['request_id']+'/pay', {'visibility': 'private'}, 'b')
    c.need(c.call(base, 'POST', '/requests/'+split['requests'][1]['request_id']+'/cancel', {}, tokens['a']), 200)
    create('split-explicit', '/splits', {'amount': 5, 'participant_handles': ['a'], 'note': ''}, 'a')
    create('settlement-main', '/settlements', {'transfers': [
        {'from_handle': 'a', 'to_handle': 'b', 'amount': 3, 'unknown': False},
        {'from_handle': 'b', 'to_handle': 'c', 'amount': 2, 'note': 'nested', 'visibility': 'private'}], 'unknown': 99}, 'a')
    other = create('rq-other', '/requests', {'payer_handle': 'a', 'amount': 2}, 'b')
    c.need(c.call(base, 'POST', '/payments', {'to_handle': 'a', 'amount': 50}, tokens['c'], 'failed-key'), 409, 'insufficient_funds')
    export = c.snapshot(base)
    assert export.get('track') == 'pocketful' and export.get('format_version') == 1
    state = export['state']
    assert state.get('schema') == 2 and isinstance(state.get('idempotency'), list), 'review new opaque format adapter'
    for original in receipts:
        entry = next(x for x in state['idempotency'] if x['key'] == original['key'])
        assert entry['body'] == canonical(original['body']), 'canonical adapter mismatch'
        assert entry['response'] == original['response'], 'response changed'
    return tokens, receipts, export, other['request_id']


def reset_matrix(c, baseline):
    destination = c.destination
    c.need(c.call(destination, 'POST', '/_test/import', baseline), 204)
    before = c.snapshot(destination)
    fields = [('currency',), ('minor_units',), ('users',)]
    fields += [('users', 0, name) for name in ('id', 'email', 'password', 'display_name', 'handle', 'balance')]
    fields += [('payments', 0, name) for name in ('id', 'from_user_id', 'to_user_id', 'amount')]
    fields += [('requests', 0, name) for name in ('id', 'requester_id', 'payer_id', 'amount', 'status')]
    for path in fields:
        body = fixture(); modify_path(body, path, remove=True)
        label = '.'.join(map(str, path))
        c.run('R1 missing '+label, lambda b=body: c.rejects_atomically(destination, '/_test/reset', b, 422, before))

    numeric = [('minor_units',), ('users', 0, 'balance')]
    strings = [path for path in fields if path not in numeric and path[-1] not in ('users', 'amount')]
    for path in numeric+strings:
        wrong_values = (None, True, '2', [], {}) if path in numeric else (None, True, 2, [], {})
        for value in wrong_values:
            body = fixture(); modify_path(body, path, value)
            label = '.'.join(map(str, path))+'/'+type(value).__name__
            c.run('R1 type '+label, lambda b=body: c.rejects_atomically(destination, '/_test/reset', b, 400, before))

    for field in ('users', 'payments', 'requests', 'settlement_operator_ids'):
        for value in (None, True, 1, 'x', {}):
            body = fixture(); body[field] = value
            c.run('R1 array type '+field+'/'+type(value).__name__,
                  lambda b=body: c.rejects_atomically(destination, '/_test/reset', b, 400, before))
        for value in (None, True, 1, [], {} if field=='settlement_operator_ids' else 'x'):
            body = fixture(); body[field] = [value]
            c.run('R1 member type '+field+'/'+type(value).__name__,
                  lambda b=body: c.rejects_atomically(destination, '/_test/reset', b, 400, before))

    invalid_values = [(('minor_units',), 1), (('minor_units',), 2.5), (('users',0,'balance'), -1),
        (('users',0,'balance'), 0.5), (('users',0,'balance'), 2**53+1), (('users',0,'id'), 'x'*65),
        (('users',0,'email'), 'no-at'), (('users',0,'handle'), 'Bad!'), (('payments',0,'id'), 'x'*65),
        (('requests',0,'id'), 'x'*65), (('requests',0,'status'), 'unknown'),
        (('settlement_operator_ids',0), 'absent')]
    invalid_values += [(path,'absent') for path in fields if path[-1] in ('from_user_id','to_user_id','requester_id','payer_id')]
    for index,(path,value) in enumerate(invalid_values):
        body=fixture(); modify_path(body,path,value)
        c.run('R1 correct-type invalid '+str(index), lambda b=body:c.rejects_atomically(destination,'/_test/reset',b,422,before))
    for collection in ('payments','requests'):
        for field,values in [('amount',(None,True,'1',[],{},-1,0.5,1000000001)),
                             ('note',(None,True,1,[],{},'x'*201))]:
            for index,value in enumerate(values):
                body=fixture(); body[collection][0][field]=value
                c.run('R1 special422 '+collection+'/'+field+'/'+str(index),
                      lambda b=body:c.rejects_atomically(destination,'/_test/reset',b,422,before))
    for index,value in enumerate((None,True,1,[],{},'secret')):
        body=fixture(); body['payments'][0]['visibility']=value
        c.run('R1 special422 visibility/'+str(index),lambda b=body:c.rejects_atomically(destination,'/_test/reset',b,422,before))

    def numeric_and_optional_controls():
        body=fixture(); body['minor_units']=2.0; body['users'][0]['balance']=1e3
        body['payments'][0]['amount']=7.0; body['requests'][0]['amount']=4e0
        body['unknown']={'nested':True}
        del body['payments'][0]['note']; del body['payments'][0]['visibility']; del body['requests'][0]['note']
        numeric_raw=json.dumps(body).replace('"balance": 1000.0','"balance": 1e3').replace('"minor_units": 2.0','"minor_units": 2e0').encode()
        c.need(c.call(destination,'POST','/_test/reset',raw=numeric_raw),204)
        state=c.snapshot(destination)['state']
        assert state['users']['a']['balance']==1000 and state['payments']['seedp']['note']==''
        assert state['payments']['seedp']['visibility']=='public'
        for field in ('payments','requests','settlement_operator_ids'): body.pop(field)
        c.need(c.call(destination,'POST','/_test/reset',body),204)
        state=c.snapshot(destination)['state']
        assert not state['payments'] and not state['requests'] and not state['operators']
        c.need(c.call(destination,'POST','/_test/import',before),204)
        assert c.snapshot(destination)==before
    c.run('R1 legitimate numeric/unknown/optional controls',numeric_and_optional_controls)


def import_matrix(c,tokens,receipts,export,other_request):
    base=c.destination
    c.need(c.call(base,'POST','/_test/import',export),204)
    before=c.snapshot(base)
    originals={r['key']:r for r in receipts}
    primary=['p-default','rq-paid','pay-main','split-main','settlement-main']

    def entry(snapshot,key):
        return next(e for e in snapshot['state']['idempotency'] if e['key']==key)

    def corrupt(name,key,mutate):
        changed=copy.deepcopy(export)
        mutate(changed,entry(changed,key))
        c.run('R2 '+name+'/'+key, lambda:c.rejects_atomically(base,'/_test/import',changed,422,before))

    changes={
        'p-default': [('amount',99),('to_handle','c'),('note','changed'),('visibility','private')],
        'rq-paid': [('amount',99),('payer_handle','c'),('note','changed')],
        'pay-main': [('visibility','private')],
        'split-main': [('amount',9),('participant_handles',['c','b','a']),('note','changed')],
        'settlement-main': []}
    for key in primary:
        for field,value in changes[key]:
            body=copy.deepcopy(originals[key]['body']); body[field]=value
            corrupt('body contradicts '+field,key,lambda s,e,b=body:e.update(body=canonical(b)))
        corrupt('wrong actor',key,lambda s,e:e.update(user_id='c'))
        corrupt('wrong path',key,lambda s,e:e.update(path='/payments' if e['path']!='/payments' else '/requests/'+other_request+'/pay'))
        corrupt('wrong method',key,lambda s,e:e.update(method='PUT'))
        if key!='pay-main':
            body=copy.deepcopy(originals[key]['body']); body.pop({'p-default':'to_handle','rq-paid':'payer_handle','split-main':'participant_handles','settlement-main':'transfers'}[key])
            corrupt('missing completed body field',key,lambda s,e,b=body:e.update(body=canonical(b)))
        def receipt_change(s,e):
            response=e['response']
            if 'payments' in response: response['payments'][0]['amount']+=1
            else: response['amount']+=1
        corrupt('cached receipt drift',key,receipt_change)

    for field,value in [('amount',9),('from_handle','c'),('to_handle','c'),('note','changed'),('visibility','private')]:
        body=copy.deepcopy(originals['settlement-main']['body']); body['transfers'][0][field]=value
        corrupt('member body contradicts '+field,'settlement-main',lambda s,e,b=body:e.update(body=canonical(b)))
    body=copy.deepcopy(originals['settlement-main']['body']); body['transfers'].reverse()
    corrupt('transfer order changed','settlement-main',lambda s,e:e.update(body=canonical(body)))
    corrupt('operator permission removed','settlement-main',lambda s,e:s['state'].update(operators=[]))
    corrupt('pay wrong resource path','pay-main',lambda s,e:e.update(path='/requests/'+other_request+'/pay'))

    def coherent_payment_drift(s,e):
        e['response']['amount']=19
        s['state']['payments'][e['response']['payment_id']]['amount']=19
    corrupt('receipt and stored payment contradict body','p-default',coherent_payment_drift)

    def coherent_settlement_drift(s,e):
        sid=e['response']['settlement_id']; pid=e['response']['payments'][0]['payment_id']
        e['response']['payments'][0]['amount']=17
        s['state']['settlements'][sid]['payments'][0]['amount']=17
        s['state']['payments'][pid]['amount']=17
    corrupt('receipt batch and payment contradict body','settlement-main',coherent_settlement_drift)

    def request_relationship(s,e):
        rid=e['response']['request_id']
        s['state']['requests'][rid]['payer_id']='c'
        s['state']['requests'][rid]['payer_handle']='c'
    corrupt('stored request actor contradicts receipt','rq-paid',request_relationship)

    def split_share_receipt(s,e):
        e['response']['shares'][0]['amount']=0
        e['response']['shares'][1]['amount']=1
    corrupt('ordered split shares contradict body','split-main',split_share_receipt)

    def noncanonical_snapshot_number(s,e):
        body=copy.deepcopy(originals['p-default']['body']); body['amount']=True
        e['body']=canonical(body)
    corrupt('boolean body amount','p-default',noncanonical_snapshot_number)

    def legitimate_replays():
        c.need(c.call(base,'POST','/_test/import',export),204)
        assert c.snapshot(base)==export
        # Source performed records include paid/cancelled requests and paid zero split requests;
        # cached create/split responses must remain their original pending receipts.
        for original in receipts:
            replay=c.need(c.call(base,'POST',original['path'],original['body'],tokens[original['actor']],original['key']),200)
            assert replay==original['response'],'original receipt changed'
        numeric=copy.deepcopy(originals['p-default']['body']); numeric['amount']=11.0
        assert c.need(c.call(base,'POST','/payments',numeric,tokens['a'],'p-default'),200)==originals['p-default']['response']
        changed=copy.deepcopy(originals['p-default']['body']); changed.update(note='',visibility='public')
        c.need(c.call(base,'POST','/payments',changed,tokens['a'],'p-default'),409,'idempotency_key_reuse')
        for h in 'abc':
            c.need(c.call(base,'GET','/me',token=tokens[h]),200)
            c.need(c.call(base,'POST','/auth/login',{'email':h+'@r1r2.invalid','password':'r1r2-private-pass'}),200)
        c.need(c.call(base,'POST','/payments',{'to_handle':'c','amount':50},tokens['a'],'fund-c'),201)
        c.need(c.call(base,'POST','/payments',{'to_handle':'a','amount':50},tokens['c'],'failed-key'),201)
        c.need(c.call(base,'POST','/_test/import',export),204)
        assert c.snapshot(base)==export
    c.run('R2 legitimate unchanged exports all path replays and failed keys',legitimate_replays)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',required=True)
    parser.add_argument('--destination',required=True)
    parser.add_argument('--revision',required=True)
    args=parser.parse_args()
    assert len(args.revision)==40 and all(x in '0123456789abcdef' for x in args.revision),'full SHA required'
    c=Checks(args.source,args.destination)
    for base in (args.source,args.destination):
        assert c.need(c.call(base,'GET','/health'),200)=={'status':'ok'}
    tokens,receipts,export,other_request=create_history(c)
    reset_matrix(c,export)
    import_matrix(c,tokens,receipts,export,other_request)
    print(json.dumps({'revision':args.revision,'cases':c.cases,'http_checks':c.calls,
                     'maximum_request_seconds':round(c.max_seconds,3),'failed_cases':c.failures}),flush=True)
    return bool(c.failures)


if __name__=='__main__':
    raise SystemExit(main())
