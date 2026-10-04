"""HTTP contract checks; no private state is printed or written to disk."""
from concurrent.futures import ThreadPoolExecutor
import copy
import json
import sys
import time
import http.client
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
DEST = sys.argv[2] if len(sys.argv) > 2 else BASE
COUNT = 0


def call(method, path, body=None, token=None, key=None, base=BASE, raw=None):
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["Authorization"] = "Bearer " + token
    if key is not None:
        headers["Idempotency-Key"] = key
    data = raw if raw is not None else None if body is None else json.dumps(body, ensure_ascii=False).encode()
    request = urllib.request.Request(base + path, data=data, headers=headers, method=method)
    try:
        response = urllib.request.urlopen(request, timeout=10 if path.startswith("/_test/") else 5)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        content = response.read()
        assert response.headers.get("Content-Type") == "application/json; charset=utf-8"
        return response.status, json.loads(content) if content else None


def check(result, status, code=None):
    global COUNT
    assert result[0] == status, ("Unexpected HTTP status", result[0], "expected", status)
    if code:
        assert result[1]["error"]["code"] == code, ("Unexpected error code", code)
    COUNT += 1
    return result[1]


FIXTURE = {"currency": "EUR", "minor_units": 2, "settlement_operator_ids": ["u_ada"], "users": [
    {"id": "u_ada", "email": "ada@example.com", "password": "correct horse", "display_name": "Ada", "handle": "ada", "balance": 10000},
    {"id": "u_bob", "email": "bob@example.com", "password": "correct horse", "display_name": "Bob", "handle": "bob", "balance": 2500},
    {"id": "u_cy", "email": "cy@example.com", "password": "correct horse", "display_name": "Cy", "handle": "cy", "balance": 0}],
    "payments": [{"id": "seed", "from_user_id": "u_ada", "to_user_id": "u_bob", "amount": 500, "visibility": "public", "note": "seed"}],
    "requests": []}


def login(handle, base=BASE):
    return check(call("POST", "/auth/login", {"email": handle + "@example.com", "password": "correct horse"}, base=base), 200)["token"]


def me(token, base=BASE):
    return check(call("GET", "/me", token=token, base=base), 200)


def export(base=BASE):
    return check(call("GET", "/_test/export", base=base), 200)


def total(tokens, base=BASE):
    balances = [me(token, base)["balance"] for token in tokens]
    assert min(balances) >= 0 and sum(balances) == 12500


started = time.monotonic()
while True:
    try:
        check(call("GET", "/health"), 200)
        break
    except (urllib.error.URLError, http.client.RemoteDisconnected):
        if time.monotonic() - started > 60:
            raise
        time.sleep(0.1)
check(call("POST", "/_test/reset", FIXTURE), 204)
ada, bob, cy = [login(handle) for handle in ("ada", "bob", "cy")]
assert me(ada)["balance"] == 10000  # Seed payments must not be replayed.
check(call("GET", "/me"), 401, "unauthenticated")
check(call("GET", "/me", token="unknown"), 401, "unauthenticated")
check(call("POST", "/auth/login", {"email": "ada@example.com", "password": "wrong"}), 401, "unauthenticated")
signup = check(call("POST", "/auth/signup", {"email": "New.User+tag@example.com", "password": "12345678", "display_name": "新🌟"}), 201)
assert me(signup["token"])["handle"] == "new_user_tag"
check(call("POST", "/auth/signup", {"email": "New.User+tag@example.com", "password": "12345678", "display_name": "New"}), 409, "email_taken")
check(call("POST", "/auth/signup", {"email": "ada@other.com", "password": "12345678", "display_name": "New"}), 409, "handle_taken")
check(call("POST", "/auth/signup", {"email": "bad", "password": "12345678", "display_name": "New"}), 422, "validation_failed")
check(call("POST", "/auth/signup", {"email": "new@example.com", "password": "short", "display_name": "New"}), 422, "validation_failed")
check(call("POST", "/auth/signup", {"email": 4, "password": "12345678", "display_name": "New"}), 400, "malformed_request")
payment = {"to_handle": "bob", "amount": 100, "note": "  café 🌍\n<>&  ", "visibility": "private", "unknown": {"z": 1}}
check(call("POST", "/payments", payment, ada), 400, "missing_idempotency_key")
check(call("POST", "/payments", payment, ada, "x" * 256), 422, "validation_failed")
receipt = check(call("POST", "/payments", payment, ada, "payment"), 201)
assert receipt["note"] == payment["note"] and receipt["settlement_id"] is None
reordered = dict(reversed(list(payment.items())))
assert check(call("POST", "/payments", reordered, ada, "payment"), 200) == receipt
check(call("POST", "/payments", {"amount": False}, ada, "payment"), 409, "idempotency_key_reuse")
check(call("POST", "/payments", token=ada, key="payment", raw=b"[1]"), 400, "malformed_request")
check(call("POST", "/payments", token=ada, key="payment", raw=b"{"), 400, "malformed_request")
for value in [0, -1, 1000000001, 0.5, True, "100", None]:
    check(call("POST", "/payments", {"to_handle": "bob", "amount": value}, ada, "invalid"), 422, "validation_failed")
for bad in [{"note": None}, {"note": 4}, {"note": "x" * 201}, {"visibility": None}, {"visibility": True}, {"visibility": "secret"}]:
    check(call("POST", "/payments", {"to_handle": "bob", "amount": 1, **bad}, ada, "invalid"), 422, "validation_failed")
check(call("POST", "/payments", {"to_handle": 7, "amount": 1}, ada, "invalid"), 400, "malformed_request")
check(call("POST", "/payments", {"to_handle": "ada", "amount": 1}, ada, "invalid"), 422, "self_payment")
check(call("POST", "/payments", {"to_handle": "missing", "amount": 1}, ada, "invalid"), 404, "not_found")
check(call("POST", "/payments", {"to_handle": "bob", "amount": 1}, ada, "invalid"), 201)
numeric = check(call("POST", "/payments", token=ada, key="numeric", raw=b'{"to_handle":"bob","amount":1e2,"extra":0.10}'), 201)
assert check(call("POST", "/payments", token=ada, key="numeric", raw=b'{"extra":0.100,"amount":100.0,"to_handle":"bob"}'), 200) == numeric
for token in [ada, bob]:
    assert receipt in check(call("GET", "/activity", token=token), 200)["payments"]
assert receipt not in check(call("GET", "/activity", token=cy), 200)["payments"]
for path in ["/activity?limit=1e2", "/activity?limit=0", "/activity?offset=-1", "/requests?offset=4.0", "/requests?limit=201", "/requests?direction=other", "/requests?status=no"]:
    check(call("GET", path, token=ada), 422, "validation_failed")
assert check(call("GET", "/activity?limit=1&unused=x", token=ada), 200)["has_more"]
check(call("POST", "/requests", {"payer_handle": "ada", "amount": 1}, ada, "self"), 422, "self_request")
request = check(call("POST", "/requests", {"payer_handle": "cy", "amount": 100, "note": "later"}, bob, "payment"), 201)
rid = request["request_id"]
assert check(call("POST", "/requests", {"payer_handle": "cy", "amount": 100, "note": "later"}, bob, "payment"), 200) == request
check(call("POST", "/requests/" + rid + "/pay", {}, bob, "pay"), 403, "forbidden")
check(call("POST", "/requests/" + rid + "/pay", {}, cy, "pay"), 409, "insufficient_funds")
assert request in check(call("GET", "/requests?direction=incoming&status=pending", token=cy), 200)["requests"]
assert request not in check(call("GET", "/requests", token=ada), 200)["requests"]
check(call("POST", "/payments", {"to_handle": "cy", "amount": 100}, ada, "fund"), 201)
paid = check(call("POST", "/requests/" + rid + "/pay", {}, cy, "pay"), 201)
assert paid["request_id"] == rid
assert check(call("POST", "/requests/" + rid + "/pay", {}, cy, "pay"), 200) == paid
check(call("POST", "/requests/" + rid + "/pay", {"visibility": "public"}, cy, "pay"), 409, "idempotency_key_reuse")
check(call("POST", "/requests/" + rid + "/pay", {}, cy, "another"), 409, "request_not_pending")
check(call("POST", "/requests/" + rid + "/cancel", {}, bob), 409, "request_not_pending")
for action, owner, status in [("cancel", bob, "cancelled"), ("decline", cy, "declined")]:
    pending = check(call("POST", "/requests", {"payer_handle": "cy", "amount": 1000000000}, bob, action), 201)
    path = "/requests/" + pending["request_id"] + "/" + action
    terminal = check(call("POST", path, token=owner), 200)
    assert terminal["status"] == status and check(call("POST", path, token=owner), 200) == terminal
    assert check(call("POST", "/requests", {"payer_handle": "cy", "amount": 1000000000}, bob, action), 200) == pending
split_body = {"amount": 1, "participant_handles": ["ada", "bob", "cy"], "note": "zero"}
split = check(call("POST", "/splits", split_body, ada, "payment"), 201)
assert [s["amount"] for s in split["shares"]] == [1, 0, 0]
assert [r["payer_handle"] for r in split["requests"]] == ["bob", "cy"]
for r, token in zip(split["requests"], [bob, cy]):
    assert check(call("POST", "/requests/" + r["request_id"] + "/pay", {}, token, "zero"), 201)["amount"] == 0
assert check(call("POST", "/splits", split_body, ada, "payment"), 200) == split
assert check(call("POST", "/splits", {"amount": 2, "participant_handles": ["ada"]}, ada, "solo"), 201)["requests"] == []
ordered = check(call("POST", "/splits", {"amount": 10, "participant_handles": ["cy", "bob", "ada"]}, ada, "ordered"), 201)
assert ordered["shares"] == [{"handle": "cy", "amount": 4}, {"handle": "bob", "amount": 3}, {"handle": "ada", "amount": 3}]
for handles, code in [([], "validation_failed"), (["bob", "bob"], "validation_failed"), (["bob", "unknown"], "not_found")]:
    check(call("POST", "/splits", {"amount": 1, "participant_handles": handles}, ada, "bad-split"), 404 if code == "not_found" else 422, code)
total([ada, bob, cy])

# Fifty simultaneous identical retries: only one mutation and one creation.
body = {"to_handle": "bob", "amount": 1}
with ThreadPoolExecutor(max_workers=50) as pool:
    results = list(pool.map(lambda _: call("POST", "/payments", body, ada, "concurrent"), range(50)))
assert [r[0] for r in results].count(201) == 1 and [r[0] for r in results].count(200) == 49
assert all(r[1] == results[0][1] for r in results)
COUNT += 50

# Competing request transitions have one winner and preserve conservation.
race = check(call("POST", "/requests", {"payer_handle": "ada", "amount": 1}, bob, "race"), 201)
path = "/requests/" + race["request_id"]
with ThreadPoolExecutor(max_workers=3) as pool:
    futures = [pool.submit(call, "POST", path + "/pay", {}, ada, "race-pay"),
               pool.submit(call, "POST", path + "/decline", {}, ada),
               pool.submit(call, "POST", path + "/cancel", {}, bob)]
    results = [future.result() for future in futures]
assert sum(r[0] in [200, 201] for r in results) == 1
assert all(r[0] in [200, 201, 409] for r in results)
COUNT += 3
total([ada, bob, cy])

# Net funding permits a zero-balance wallet to send before its incoming entry.
batch = {"transfers": [{"from_handle": "cy", "to_handle": "bob", "amount": 100, "visibility": "private"},
                       {"from_handle": "ada", "to_handle": "cy", "amount": 100}]}
check(call("POST", "/settlements", batch), 401, "unauthenticated")
check(call("POST", "/settlements", batch, bob, "batch"), 403, "forbidden")
check(call("POST", "/settlements", batch, bob), 403, "forbidden")
settlement = check(call("POST", "/settlements", batch, ada, "batch"), 201)
assert check(call("POST", "/settlements", batch, ada, "batch"), 200) == settlement
assert all(p["created_at"] == settlement["committed_at"] and p["request_id"] is None and p["settlement_id"] == settlement["settlement_id"] for p in settlement["payments"])
check(call("POST", "/settlements", {"transfers": []}, ada, "bad-batch"), 422, "validation_failed")
before = export()
badbatch = {"transfers": [{"from_handle": "cy", "to_handle": "bob", "amount": 1000000000}, {"from_handle": "unknown", "to_handle": "bob", "amount": 1}]}
check(call("POST", "/settlements", badbatch, ada, "bad-batch"), 404, "not_found")
assert export() == before
badbatch["transfers"].pop()
check(call("POST", "/settlements", badbatch, ada, "bad-batch"), 409, "insufficient_funds")
assert export() == before
check(call("POST", "/settlements", batch, ada, "bad-batch"), 201)
total([ada, bob, cy])

# Snapshot replacement, malformed state rollback, credential portability and receipts.
snapshot = export()
for mutate in [lambda s: s.update(track="wrong"), lambda s: s.update(format_version=2),
               lambda s: s["state"]["users"]["u_ada"].update(balance=-1),
               lambda s: s["state"]["users"]["u_ada"]["password_hash"].update(digest="bad"),
               lambda s: s["state"].update(tokens={"invalid": "absent"}),
               lambda s: s["state"]["idempotency"][0].update(body=["object"]),
               lambda s: s["state"]["idempotency"][0]["response"].update(amount=999),
               lambda s: s["state"]["requests"][rid].update(payment_id="seed"),
               lambda s: s["state"].update(schema=True)]:
    broken = copy.deepcopy(snapshot)
    mutate(broken)
    check(call("POST", "/_test/import", broken), 422, "validation_failed")
    assert export() == snapshot
broken_fixture = copy.deepcopy(FIXTURE)
broken_fixture["users"][0]["balance"] = -1
check(call("POST", "/_test/reset", broken_fixture), 422, "validation_failed")
assert export() == snapshot
check(call("POST", "/payments", {"to_handle": "bob", "amount": 1}, ada, "after-export"), 201)
check(call("POST", "/_test/reset", {"currency": "JPY", "minor_units": 0, "users": []}, base=DEST), 204)
check(call("POST", "/_test/import", snapshot, base=DEST), 204)
assert export(DEST) == snapshot
for token in [ada, bob, cy, signup["token"]]:
    me(token, DEST)
login("ada", DEST)
assert check(call("POST", "/payments", payment, ada, "payment", base=DEST), 200) == receipt
assert check(call("POST", "/requests/" + rid + "/pay", {}, cy, "pay", base=DEST), 200) == paid
assert check(call("POST", "/splits", split_body, ada, "payment", base=DEST), 200) == split
assert check(call("POST", "/settlements", batch, ada, "batch", base=DEST), 200) == settlement
check(call("POST", "/settlements", batch, ada, "import-operator", base=DEST), 201)
check(call("POST", "/_test/import", snapshot, base=DEST), 204)
assert export(DEST) == snapshot
total([ada, bob, cy], DEST)
check(call("POST", "/_test/reset", {"currency": "BHD", "minor_units": 3, "users": []}, base=DEST), 204)
check(call("GET", "/me", token=ada, base=DEST), 401, "unauthenticated")
check(call("POST", "/auth/login", {"email": "ada@example.com", "password": "correct horse"}, base=DEST), 401, "unauthenticated")

# Exercise all five idempotent paths under fifty simultaneous callers.
check(call("POST", "/_test/reset", FIXTURE), 204)
ada, bob, cy = [login(handle) for handle in ("ada", "bob", "cy")]
rq = check(call("POST", "/requests", {"payer_handle": "ada", "amount": 1}, bob, "prepare"), 201)
workloads = [("/payments", {"to_handle": "bob", "amount": 1}),
             ("/requests", {"payer_handle": "bob", "amount": 1}),
             ("/splits", {"amount": 1, "participant_handles": ["ada", "bob", "cy"]}),
             ("/settlements", {"transfers": [{"from_handle": "ada", "to_handle": "bob", "amount": 1}]}),
             ("/requests/" + rq["request_id"] + "/pay", {})]
for path, body in workloads:
    with ThreadPoolExecutor(max_workers=50) as pool:
        results = list(pool.map(lambda _: call("POST", path, body, ada, "all-paths"), range(50)))
    assert [r[0] for r in results].count(201) == 1 and [r[0] for r in results].count(200) == 49
    assert all(r[1] == results[0][1] for r in results)
    COUNT += 50
rq2 = check(call("POST", "/requests", {"payer_handle": "ada", "amount": 1}, bob, "prepare2"), 201)
check(call("POST", "/requests/" + rq2["request_id"] + "/pay", {}, ada, "all-paths"), 201)
with ThreadPoolExecutor(max_workers=50) as pool:
    results = list(pool.map(lambda _: call("POST", "/auth/login", {"email": "ada@example.com", "password": "correct horse"}), range(50)))
assert all(result[0] == 200 for result in results)
assert len({result[1]["token"] for result in results}) == 50
COUNT += 50
total([ada, bob, cy])

# Fifty distinct keys compete for a limited wallet; rejected writes leave no records.
limited = copy.deepcopy(FIXTURE)
limited["payments"] = []
for user, balance in zip(limited["users"], [300, 0, 0]):
    user["balance"] = balance
check(call("POST", "/_test/reset", limited), 204)
ada, bob, cy = [login(handle) for handle in ("ada", "bob", "cy")]
with ThreadPoolExecutor(max_workers=50) as pool:
    results = list(pool.map(lambda i: call("POST", "/payments", {"to_handle": "bob", "amount": 10}, ada, "limited-" + str(i)), range(50)))
assert [r[0] for r in results].count(201) == 30 and [r[0] for r in results].count(409) == 20
assert all(r[0] == 201 or r[1]["error"]["code"] == "insufficient_funds" for r in results)
assert [me(token)["balance"] for token in [ada, bob, cy]] == [0, 300, 0]
limited_export = export()["state"]
assert len(limited_export["payments"]) == 30 and len(limited_export["idempotency"]) == 30
COUNT += 50
failed_index = next(i for i, result in enumerate(results) if result[0] == 409)
check(call("POST", "/payments", {"to_handle": "ada", "amount": 10}, bob, "replenish"), 201)
check(call("POST", "/payments", {"to_handle": "bob", "amount": 10}, ada, "limited-" + str(failed_index)), 201)
for currency, units in [("EUR", 2), ("JPY", 0), ("BHD", 3)]:
    boundary = copy.deepcopy(limited)
    boundary.update(currency=currency, minor_units=units)
    boundary["users"][0]["balance"] = 2 ** 53
    boundary["users"][1]["balance"] = 1000000000
    check(call("POST", "/_test/reset", boundary), 204)
    ada, bob = login("ada"), login("bob")
    before = export()
    check(call("POST", "/payments", {"to_handle": "ada", "amount": 1}, bob, "overflow"), 422, "validation_failed")
    assert export() == before
    check(call("POST", "/payments", {"to_handle": "bob", "amount": 1000000000}, ada, "maximum"), 201)
    check(call("POST", "/payments", {"to_handle": "ada", "amount": 1000000000}, bob, "overflow"), 201)
    assert me(ada)["balance"] == 2 ** 53 and me(bob)["balance"] == 1000000000
    assert me(ada)["currency"] == currency and me(ada)["minor_units"] == units
print(f"PASS: {COUNT} HTTP checks, 50-way retries on all five write paths, competing writes, state races, atomic settlements, portable snapshots, exact balance boundary; private state retained only in process memory.")
