"""HTTP numeric-value regressions; credentials and portable snapshots stay in RAM."""
import copy
import datetime as dt
import http.client
import json
import sys
import time
from urllib.parse import urlsplit

sys.set_int_max_str_digits(0)
A = sys.argv[1]
B = sys.argv[2] if len(sys.argv) > 2 else A
COUNT = 0
MAX_TIME = 0


def call(method, path, body=None, token=None, key=None, raw=None, base=A):
    global COUNT, MAX_TIME
    url = urlsplit(base)
    conn = http.client.HTTPConnection(url.hostname, url.port, timeout=10 if path.startswith('/_test/') else 5)
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if key:
        headers['Idempotency-Key'] = key
    data = raw.encode() if raw is not None else json.dumps(body).encode() if body is not None else None
    start = time.monotonic()
    try:
        conn.request(method, path, data, headers)
        response = conn.getresponse()
        content = response.read()
        elapsed = time.monotonic() - start
        COUNT += 1
        MAX_TIME = max(MAX_TIME, elapsed)
        assert elapsed < (10 if path.startswith('/_test/') else 5)
        assert response.headers['Content-Type'] == 'application/json; charset=utf-8'
        assert response.status < 500
        return response.status, json.loads(content) if content else None
    finally:
        conn.close()


def need(result, status, code=None):
    assert result[0] == status, ('status', result[0], 'expected', status)
    if code:
        assert result[1]['error']['code'] == code
    return result[1]


def snapshot(base=A):
    return need(call('GET', '/_test/export', base=base), 200)


fixture = {'currency': 'EUR', 'minor_units': 2, 'users': [
    {'id': h, 'email': h + '@numeric.invalid', 'password': 'numeric-tests-only',
     'display_name': h, 'handle': h, 'balance': 1000 if h in 'ab' else 0} for h in 'abc'],
    'settlement_operator_ids': ['a'],
    'requests': [{'id': 'seed', 'requester_id': 'b', 'payer_id': 'a', 'amount': 1, 'status': 'pending'}],
    'authorizations': [{'id':'seed-hold','from_user_id':'b','to_user_id':'a','amount':200,'status':'open',
                        'expires_at':(dt.datetime.now(dt.timezone.utc)+dt.timedelta(hours=2)).isoformat()}]}


def seed():
    need(call('POST', '/_test/reset', fixture), 204)
    return need(call('POST', '/auth/login', {'email': 'a@numeric.invalid', 'password': 'numeric-tests-only'}), 200)['token']


paths = [('/payments', {'to_handle': 'b', 'amount': 1}),
         ('/requests', {'payer_handle': 'b', 'amount': 1}),
         ('/requests/seed/pay', {'visibility': 'private'}),
         ('/splits', {'amount': 1, 'participant_handles': ['a', 'b', 'c']}),
         ('/settlements', {'transfers': [{'from_handle': 'a', 'to_handle': 'b', 'amount': 1}]}),
         ('/authorizations', {'to_handle':'b','amount':1}),
         ('/authorizations/seed-hold/capture', {'amount':1})]
huge = '10000000000000000000'
enormous = '9' * 5000
pairs = [('7' * 5000 + '.0', '7' * 5000),
         ('-' + '7' * 5000 + '.00', '-' + '7' * 5000),
         ('10e' + enormous, '1e' + str(int(enormous) + 1)),
         ('1e-' + enormous, '10e-' + str(int(enormous) + 1)),
         ('0e' + enormous, '-0.000e-' + enormous),
         ('1.2500e-2', '0.0125'), ('1000.000e-3', '1'),
         ('0.' + '0' * 5000 + '1e5001', '1')]


def with_number(body, number, reversed_keys=False):
    value = copy.deepcopy(body)
    value['ignored'] = {'nested': [True, None, '__NUMBER__']}
    if reversed_keys:
        value = dict(reversed(list(value.items())))
    return json.dumps(value).replace('"__NUMBER__"', number)


for path, body in paths:
    for index, (left, right) in enumerate(pairs):
        token = seed()
        key = 'numeric-' + str(index)
        original = need(call('POST', path, token=token, key=key, raw=with_number(body, left)), 201)
        before = snapshot()
        assert need(call('POST', path, token=token, key=key, raw=with_number(body, right, True)), 200) == original
        need(call('POST', path, token=token, key=key, raw=with_number(body, '2')), 409, 'idempotency_key_reuse')
        assert snapshot() == before
        need(call('POST', '/_test/import', before, base=B), 204)
        assert snapshot(B) == before
        assert need(call('POST', path, token=token, key=key, raw=with_number(body, right), base=B), 200) == original
        assert need(call('GET', '/me', token=token, base=B), 200)['handle'] == 'a'
    print('PASS exact numeric identity/conflict and portable receipts:', path, flush=True)

invalid = ['9' * 5000, '1e' + huge, '1e-' + huge, '-1e' + enormous,
           '1e-' + enormous, '1.00000000000000000001', '1000000001', '-1',
           '0e' + enormous, 'true', '"1"', 'null', '[]', '{}']
for path, body in [item for item in paths if not item[0].endswith(('/pay','/capture'))]:
    token = seed()
    for index, number in enumerate(invalid):
        value = copy.deepcopy(body)
        target = value['transfers'][0] if path == '/settlements' else value
        target['amount'] = '__NUMBER__'
        raw = json.dumps(value).replace('"__NUMBER__"', number)
        before = snapshot()
        key = 'failed-' + str(index)
        need(call('POST', path, token=token, key=key, raw=raw), 422, 'validation_failed')
        assert snapshot() == before
        need(call('POST', path, body, token, key), 201)
    print('PASS numeric amount classification, rollback and failed-key reuse:', path, flush=True)

token = seed()
for number in ['1.0', '1e0', '10e-1', '0.' + '0' * 5000 + '1e5001', '1000000000.0', '1e9']:
    need(call('POST', '/requests', token=token, key='valid-' + number[-20:],
              raw='{"payer_handle":"b","amount":' + number + '}'), 201)
for raw in ['{"amount":1e}', '{"amount":01}', '{"amount":NaN}', '{"amount":Infinity}',
            '{"amount":1.}', '{"amount":+1}', '[1]', 'null']:
    before = snapshot()
    need(call('POST', '/payments', token=token, key='malformed', raw=raw), 400, 'malformed_request')
    assert snapshot() == before

# Capture has a specific error for integral numeric amounts above its remainder.
for number in ['9'*5000, '1e'+enormous, '201']:
    token=seed();before=snapshot();path='/authorizations/seed-hold/capture'
    need(call('POST',path,token=token,key='capture-excess',raw='{"amount":'+number+'}'),422,'capture_exceeds_authorization')
    assert snapshot()==before
    need(call('POST',path,{},token,'capture-excess'),201)

# Numeric type errors differ from valid numeric values violating a fixture rule.
for field, value, status in [('minor_units', '1e' + huge, 422), ('minor_units', 'true', 400)]:
    value_fixture = json.dumps(fixture).replace('"minor_units": 2', '"minor_units": ' + value)
    before = snapshot()
    need(call('POST', '/_test/reset', raw=value_fixture), status,
         'validation_failed' if status == 422 else 'malformed_request')
    assert snapshot() == before
need(call('GET', '/health'), 200)
print(f'PASS numeric regressions: {COUNT} HTTP checks; max {MAX_TIME:.3f}s; private state only in RAM', flush=True)
