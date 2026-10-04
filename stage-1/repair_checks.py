"""HTTP regressions for reset types and semantic retry import; snapshots stay in RAM."""
import copy
from concurrent.futures import ThreadPoolExecutor
import http.client
import json
import sys
import time
import threading
from urllib.parse import urlsplit

A = sys.argv[1]
B = sys.argv[2] if len(sys.argv) > 2 else A
COUNT = 0
MAX_TIME = 0


def call(method, path, body=None, token=None, key=None, base=A, raw=None):
    global COUNT, MAX_TIME
    url = urlsplit(base)
    conn = http.client.HTTPConnection(url.hostname, url.port, timeout=10 if path.startswith('/_test/') else 5)
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if key:
        headers['Idempotency-Key'] = key
    data = raw if raw is not None else json.dumps(body).encode() if body is not None else None
    started = time.monotonic()
    try:
        conn.request(method, path, data, headers)
        response = conn.getresponse()
        data = response.read()
        assert response.headers['Content-Type'] == 'application/json; charset=utf-8'
        COUNT += 1
        MAX_TIME = max(MAX_TIME, time.monotonic() - started)
        return response.status, json.loads(data) if data else None
    finally:
        conn.close()


def expect(result, status, code=None):
    assert result[0] == status, ('HTTP status', result[0], 'expected', status)
    if code:
        assert result[1]['error']['code'] == code, ('error code', code)
    return result[1]


def snap(base=A):
    return expect(call('GET', '/_test/export', base=base), 200)


def login(handle, base=A):
    return expect(call('POST', '/auth/login', {'email': handle + '@test.invalid', 'password': 'repair-tests-only'}, base=base), 200)['token']


fixture = {'currency': 'EUR', 'minor_units': 2, 'users': [
    {'id': h, 'email': h + '@test.invalid', 'password': 'repair-tests-only', 'display_name': h,
     'handle': h, 'balance': 100 if h in 'ab' else 0} for h in 'abc'],
    'settlement_operator_ids': ['a'],
    'payments': [{'id': 'seed', 'from_user_id': 'a', 'to_user_id': 'b', 'amount': 1, 'note': '', 'visibility': 'public'}],
    'requests': [{'id': 'seed-request', 'requester_id': 'b', 'payer_id': 'a', 'amount': 1, 'note': '', 'status': 'pending'}]}
expect(call('POST', '/_test/reset', fixture), 204)
tokens = {h: login(h) for h in 'abc'}

# Build successful receipts for every path, including defaults, unknown fractional
# values, zero shares and original pending receipts whose resources change later.
operations = []
def write(path, body, actor, key):
    response = expect(call('POST', path, body, tokens[actor], key), 201)
    operations.append((path, body, actor, key, response))
    return response

p = write('/payments', {'to_handle': 'b', 'amount': 1, 'unknown': {'fraction': 0.125, 'nested': [True, None]}}, 'a', 'payment')
explicit = write('/payments', {'to_handle': 'b', 'amount': 1, 'note': '', 'visibility': 'public'}, 'a', 'explicit')
r = write('/requests', {'payer_handle': 'a', 'amount': 2, 'extra': 'ignored'}, 'b', 'request')
paid_path = '/requests/' + r['request_id'] + '/pay'
paid = write(paid_path, {}, 'a', 'pay')
s = write('/splits', {'amount': 1, 'participant_handles': ['a', 'b', 'c'], 'extra': 0.25}, 'a', 'split')
expect(call('POST', '/requests/' + s['requests'][0]['request_id'] + '/decline', {}, tokens['b']), 200)
zero_path = '/requests/' + s['requests'][1]['request_id'] + '/pay'
zero = write(zero_path, {'visibility': 'private'}, 'c', 'zero-pay')
terminal = write('/requests', {'payer_handle': 'c', 'amount': 3}, 'b', 'cancelled-original')
expect(call('POST', '/requests/' + terminal['request_id'] + '/cancel', {}, tokens['b']), 200)
settlement_body = {'transfers': [{'from_handle': 'a', 'to_handle': 'b', 'amount': 1},
                                {'from_handle': 'b', 'to_handle': 'c', 'amount': 2, 'note': 'x', 'visibility': 'private'}], 'extra': True}
st = write('/settlements', settlement_body, 'a', 'settlement')
baseline = snap()


def set_path(value, path, replacement):
    target = value
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement


def reject_reset(path, replacement, status, missing=False):
    candidate = copy.deepcopy(fixture)
    if missing:
        target = candidate
        for key in path[:-1]:
            target = target[key]
        del target[path[-1]]
    else:
        set_path(candidate, path, replacement)
    expect(call('POST', '/_test/reset', candidate), status, 'malformed_request' if status == 400 else 'validation_failed')
    assert snap() == baseline, 'Failed reset mutated private state'


string_fields = [('currency',)] + [('users', 0, name) for name in ['id', 'email', 'password', 'display_name', 'handle']]
string_fields += [('payments', 0, name) for name in ['id', 'from_user_id', 'to_user_id']]
string_fields += [('requests', 0, name) for name in ['id', 'requester_id', 'payer_id', 'status']]
number_fields = [('minor_units',), ('users', 0, 'balance')]
for path in string_fields + number_fields:
    reject_reset(path, None, 422, missing=True)
    wrong = [None, True, 2, [], {}] if path in string_fields else [None, True, '2', [], {}]
    for value in wrong:
        reject_reset(path, value, 400)
for array in ['users', 'payments', 'requests', 'settlement_operator_ids']:
    for value in [None, True, '2', 2, {}]:
        reject_reset((array,), value, 400)
    for value in [None, True, 2, '2', []]:
        reject_reset((array, 0), value, 422 if array == 'settlement_operator_ids' and isinstance(value, str) else 400)
for collection in ['payments', 'requests']:
    for field in ['amount', 'note', 'visibility'] if collection == 'payments' else ['amount', 'note']:
        for value in [None, True, [], {}]:
            reject_reset((collection, 0, field), value, 422)
    reject_reset((collection, 0, 'amount'), None, 422, missing=True)
for path, value in [(('minor_units',), 1), (('minor_units',), 2.5), (('users', 0, 'balance'), -1),
                    (('users', 0, 'balance'), 0.5), (('users', 0, 'balance'), 2**53 + 1),
                    (('users', 0, 'id'), ''), (('users', 0, 'id'), 'x'*65),
                    (('payments', 0, 'from_user_id'), 'absent'), (('requests', 0, 'payer_id'), 'absent'),
                    (('settlement_operator_ids', 0), 'absent')]:
    reject_reset(path, value, 422)
valid = copy.deepcopy(fixture)
valid['minor_units'] = 2.0
valid['users'][0]['balance'] = 1e2
valid['requests'][0]['amount'] = 1.0
for optional in ['payments', 'requests', 'settlement_operator_ids']:
    del valid[optional]
valid['unknown'] = {'field': None}
expect(call('POST', '/_test/reset', valid), 204)
valid_snapshot = snap()
assert valid_snapshot['state']['operators'] == [] and valid_snapshot['state']['payments'] == {} and valid_snapshot['state']['requests'] == {}
expect(call('POST', '/_test/import', valid_snapshot), 204)
expect(call('POST', '/_test/import', baseline), 204)
assert snap() == baseline
print('PASS reset scalar/ID/reference/array/member omission/type/value and rollback matrix', flush=True)


def claim(snapshot, path, key):
    return next(e for e in snapshot['state']['idempotency'] if e['path'] == path and e['key'] == key)


def field(tree, name):
    return next(pair[1] for pair in tree[1] if pair[0] == name)


def change_body(path, key, name, tree):
    def mutate(snapshot):
        target = field(claim(snapshot, path, key)['body'], name)
        target[:] = tree
    return mutate


def reject_import(mutate):
    candidate = copy.deepcopy(baseline)
    mutate(candidate)
    expect(call('POST', '/_test/import', candidate), 422, 'validation_failed')
    assert snap() == baseline, 'Invalid import mutated destination'


mutations = []
for path, key, amount_value in [('/payments', 'payment', '9e0'), ('/requests', 'request', '9e0'), ('/splits', 'split', '9e0')]:
    mutations.append(change_body(path, key, 'amount', ['number', amount_value]))
mutations += [change_body('/payments', 'payment', 'to_handle', ['string', 'c']),
              change_body('/requests', 'request', 'payer_handle', ['string', 'c']),
              lambda e: claim(e, paid_path, 'pay')['body'][1].append(['visibility', ['string', 'private']]),
              change_body(zero_path, 'zero-pay', 'visibility', ['string', 'public']),
              change_body('/splits', 'split', 'participant_handles', ['array', [['string', 'c'], ['string', 'b'], ['string', 'a']]])]
def settlement_field(name, value):
    def mutate(snapshot):
        transfer = field(claim(snapshot, '/settlements', 'settlement')['body'], 'transfers')[1][0]
        field(transfer, name)[:] = value
    return mutate
mutations += [settlement_field('amount', ['number', '9e0']), settlement_field('from_handle', ['string', 'c']),
              settlement_field('to_handle', ['string', 'c'])]
for path, body, actor, key, response in operations:
    mutations += [lambda snapshot, path=path, key=key, actor=actor: claim(snapshot, path, key).update(user_id='c' if actor != 'c' else 'b'),
                  lambda snapshot, path=path, key=key: claim(snapshot, path, key).update(method='GET'),
                  lambda snapshot, path=path, key=key: claim(snapshot, path, key).update(path='/invalid'),
                  lambda snapshot, path=path, key=key: claim(snapshot, path, key)['response'].update(currency='JPY')]
mutations += [lambda e: e['state'].update(operators=[]),
              lambda e: claim(e, '/payments', 'payment')['response'].update(amount=True),
              lambda e: claim(e, '/requests', 'request')['response'].update(amount=True),
              lambda e: claim(e, '/settlements', 'settlement')['response']['payments'][0].update(amount=True),
              lambda e: claim(e, '/requests', 'request')['response'].update(note='contradiction'),
              lambda e: claim(e, '/requests', 'request').update(path='/payments'),
              lambda e: claim(e, paid_path, 'pay').update(path='/payments'),
              lambda e: claim(e, paid_path, 'pay').update(path=zero_path),
              lambda e: claim(e, '/splits', 'split')['response']['requests'][0].update(amount=1),
              lambda e: claim(e, '/splits', 'split')['response']['requests'].reverse(),
              lambda e: claim(e, '/settlements', 'settlement')['response']['payments'].reverse(),
              lambda e: e['state']['idempotency'].append({**copy.deepcopy(claim(e, '/payments', 'payment')), 'key': 'duplicate-operation'})]
def alter_payment_and_receipt(snapshot):
    entry = claim(snapshot, '/payments', 'payment')
    entry['response']['amount'] = 9
    snapshot['state']['payments'][entry['response']['payment_id']]['amount'] = 9
mutations.append(alter_payment_and_receipt)
def alter_request_and_resources(snapshot):
    entry = claim(snapshot, '/requests', 'request')
    entry['response']['amount'] = 9
    current = snapshot['state']['requests'][entry['response']['request_id']]
    current['amount'] = 9
    snapshot['state']['payments'][current['payment_id']]['amount'] = 9
    claim(snapshot, paid_path, 'pay')['response']['amount'] = 9
mutations.append(alter_request_and_resources)
def alter_split_and_resources(snapshot):
    entry = claim(snapshot, '/splits', 'split')
    entry['response']['amount'] = 2
    entry['response']['shares'][1]['amount'] = 1
    entry['response']['requests'][0]['amount'] = 1
    snapshot['state']['requests'][entry['response']['requests'][0]['request_id']]['amount'] = 1
mutations.append(alter_split_and_resources)
def alter_settlement_and_resources(snapshot):
    entry = claim(snapshot, '/settlements', 'settlement')
    entry['response']['payments'][0]['amount'] = 9
    sid = entry['response']['settlement_id']
    snapshot['state']['settlements'][sid]['payments'][0]['amount'] = 9
    snapshot['state']['payments'][entry['response']['payments'][0]['payment_id']]['amount'] = 9
mutations.append(alter_settlement_and_resources)
for mutate in mutations:
    reject_import(mutate)
print('PASS all five successful retry paths: body/receipt/resource/path/actor/permission contradictions rejected atomically', flush=True)

# Import replacement into a separate process when B differs, then original receipts
# replay after terminal changes, unchanged hashes/tokens/permissions and numeric forms.
expect(call('POST', '/_test/reset', {'currency': 'JPY', 'minor_units': 0, 'users': []}, base=B), 204)
expect(call('POST', '/_test/import', baseline, base=B), 204)
assert snap(B) == baseline
for path, body, actor, key, response in operations:
    assert expect(call('POST', path, body, tokens[actor], key, base=B), 200) == response
assert expect(call('POST', '/payments', token=tokens['a'], key='payment', base=B,
                   raw=b'{"unknown":{"nested":[true,null],"fraction":0.1250},"amount":1e0,"to_handle":"b"}'), 200) == p
expect(call('POST', '/payments', {'to_handle': 'b', 'amount': 1, 'note': '', 'visibility': 'public', 'unknown': {'fraction': 0.125, 'nested': [True, None]}}, tokens['a'], 'payment', base=B), 409, 'idempotency_key_reuse')
login('a', B)
expect(call('POST', '/settlements', settlement_body, tokens['a'], 'new-operator', base=B), 201)
expect(call('POST', '/payments', {'to_handle': 'b', 'amount': 1000000000}, tokens['a'], 'failed-key', base=B), 409, 'insufficient_funds')
expect(call('POST', '/payments', {'to_handle': 'b', 'amount': 1}, tokens['a'], 'failed-key', base=B), 201)
expect(call('POST', '/_test/import', baseline, base=B), 204)
assert snap(B) == baseline

# Password work may race replacement, but cannot install old sessions afterward.
barrier = threading.Barrier(50)
def reset_login_race(index):
    barrier.wait(timeout=10)
    if index == 49:
        return call('POST', '/_test/reset', {'currency': 'EUR', 'minor_units': 2, 'users': []}, base=B)
    return call('POST', '/auth/login', {'email': 'a@test.invalid', 'password': 'repair-tests-only'}, base=B)
with ThreadPoolExecutor(max_workers=50) as pool:
    race = list(pool.map(reset_login_race, range(50)))
assert race[49][0] == 204 and all(result[0] in [200, 401] for result in race[:49])
cleared = snap(B)['state']
assert cleared['users'] == {} and cleared['tokens'] == {}
for status, response in race[:49]:
    if status == 200:
        expect(call('GET', '/me', token=response['token'], base=B), 401, 'unauthenticated')
expect(call('POST', '/_test/import', baseline, base=B), 204)
assert snap(B) == baseline
print('PASS 49 concurrent password checks versus reset: no stale account/session installation', flush=True)

# API response fields do not extend the reset fixture schema. Unknown fields
# must be ignored for every legal seeded request state and JSON value type.
for status in ['pending', 'paid', 'declined', 'cancelled']:
    for unknown in ['not-a-link', 'seed', True, {'ignored': True}, None, 123, []]:
        candidate = copy.deepcopy(fixture)
        candidate['requests'][0].update(status=status, payment_id=unknown, created_at={'ignored': True}, visibility=False)
        candidate['payments'][0].update(request_id={'ignored': True}, settlement_id=True)
        expect(call('POST', '/_test/reset', candidate), 204)
        seeded = snap()
        assert seeded['state']['requests']['seed-request']['status'] == status
        assert seeded['state']['requests']['seed-request']['payment_id'] is None
        assert seeded['state']['payments']['seed']['request_id'] is None
        assert seeded['state']['payments']['seed']['settlement_id'] is None
        assert [seeded['state']['users'][h]['balance'] for h in 'abc'] == [100, 100, 0]
        expect(call('POST', '/_test/import', seeded, base=B), 204)
        assert snap(B) == seeded
expect(call('POST', '/_test/reset', fixture), 204)
seed_token = login('a')
seed_payment = expect(call('POST', '/requests/seed-request/pay', {'visibility': 'private'}, seed_token, 'seed-pay'), 201)
linked = snap()
assert seed_payment['request_id'] == 'seed-request' and seed_payment['payment_id'] != 'seed'
assert linked['state']['requests']['seed-request']['payment_id'] == seed_payment['payment_id']
assert linked['state']['payments']['seed']['request_id'] is None
expect(call('POST', '/_test/import', linked, base=B), 204)
assert snap(B) == linked
assert expect(call('POST', '/requests/seed-request/pay', {'visibility': 'private'}, seed_token, 'seed-pay', base=B), 200) == seed_payment
print('PASS unknown fixture response/link fields ignored across all statuses; API-created links and retries survive portable import', flush=True)
print(f'PASS repair boundaries: {COUNT} HTTP checks; max request {MAX_TIME:.3f}s; private artifacts only in memory', flush=True)
