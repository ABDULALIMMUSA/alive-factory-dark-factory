"""Extra post-submit specification probes for Pocketful Stage 4.

These are not event-supplied tests. They exercise temporal history, snapshots,
correction idempotency, refunds, and correction batches to reduce hidden-test risk.
"""
import datetime as dt
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:18080"


def key():
    return "k-" + uuid.uuid4().hex


def call(method, path, body=None, token=None, idem=None, params=None):
    if params:
        path += "?" + urllib.parse.urlencode(params)
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, method=method)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    if idem:
        req.add_header("Idempotency-Key", idem)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        return exc.code, json.loads(raw) if raw else None


def expect(status, wanted, body=None):
    assert status == wanted, (status, wanted, body)
    return body


def reset(fixture):
    status, body = call("POST", "/_test/reset", fixture)
    expect(status, 204, body)


def login(email, password):
    status, body = call("POST", "/auth/login", {"email": email, "password": password})
    expect(status, 200, body)
    return body["token"]


def fixture(payments=None):
    return {
        "currency": "EUR",
        "minor_units": 2,
        "settlement_operator_ids": ["u_ada"],
        "users": [
            {"id": "u_ada", "email": "ada@example.test", "display_name": "Ada",
             "handle": "ada", "balance": 10000, "password": "password-a"},
            {"id": "u_bob", "email": "bob@example.test", "display_name": "Bob",
             "handle": "bob", "balance": 5000, "password": "password-b"},
            {"id": "u_cyd", "email": "cyd@example.test", "display_name": "Cyd",
             "handle": "cyd", "balance": 3000, "password": "password-c"},
        ],
        "payments": payments or [],
        "requests": [],
        "authorizations": [],
    }


def main():
    reset(fixture())
    ada = login("ada@example.test", "password-a")
    bob = login("bob@example.test", "password-b")

    # Direct payment and temporal opening-balance semantics.
    status, payment = call("POST", "/payments",
                           {"to_handle": "bob", "amount": 1000, "note": "invoice"},
                           ada, key())
    expect(status, 201, payment)
    created = dt.datetime.fromisoformat(payment["created_at"])
    before = (created - dt.timedelta(microseconds=1)).isoformat()
    status, me_before = call("GET", "/me", token=ada, params={"as_of": before})
    expect(status, 200, me_before)
    assert me_before["balance"] == 10000, me_before

    # Correction moves the current balance but leaves the original receipt intact.
    correction_key = key()
    correction_body = {
        "expected_revision": 1,
        "amount": 800,
        "effective_at": payment["created_at"],
        "reason": "corrected invoice",
    }
    status, correction = call("POST", f"/payments/{payment['payment_id']}/corrections",
                              correction_body, ada, correction_key)
    expect(status, 201, correction)
    assert correction["revision"] == 2
    status, replay = call("POST", f"/payments/{payment['payment_id']}/corrections",
                          correction_body, ada, correction_key)
    expect(status, 200, replay)
    assert replay == correction

    status, revisions = call("GET", f"/payments/{payment['payment_id']}/revisions", token=ada)
    expect(status, 200, revisions)
    assert [r["revision"] for r in revisions["revisions"]] == [1, 2]

    status, me = call("GET", "/me", token=ada)
    expect(status, 200, me)
    assert me["total"] == 9200, me

    # known_at before revision 2 sees original information.
    status, historical_statement = call("GET", "/statement", token=ada,
                                        params={"known_at": payment["created_at"]})
    expect(status, 200, historical_statement)
    assert historical_statement["entries"][0]["payment"]["amount"] == 1000

    # Statement snapshot is stable after later writes.
    status, statement = call("GET", "/statement", token=ada, params={"limit": 1})
    expect(status, 200, statement)
    snap = statement["snapshot"]
    snap_open, snap_close = statement["opening_balance"], statement["closing_balance"]

    status, second = call("POST", "/payments", {"to_handle": "cyd", "amount": 50}, ada, key())
    expect(status, 201, second)
    status, frozen = call("GET", "/statement", token=ada,
                          params={"snapshot": snap, "limit": 200, "offset": 0})
    expect(status, 200, frozen)
    assert (frozen["opening_balance"], frozen["closing_balance"]) == (snap_open, snap_close)

    # Refund is linked, reverse-directional, idempotent, and respects corrected amount.
    refund_key = key()
    status, refund = call("POST", f"/payments/{payment['payment_id']}/refunds",
                          {"amount": 200}, bob, refund_key)
    expect(status, 201, refund)
    assert refund["refund_of"] == payment["payment_id"]
    assert (refund["from_handle"], refund["to_handle"], refund["amount"]) == ("bob", "ada", 200)
    status, refund_replay = call("POST", f"/payments/{payment['payment_id']}/refunds",
                                 {"amount": 200}, bob, refund_key)
    expect(status, 200, refund_replay)
    assert refund_replay == refund

    # A single correction cannot shrink below the already-refunded total.
    status, error = call("POST", f"/payments/{payment['payment_id']}/corrections",
                         {"expected_revision": 2, "amount": 100,
                          "effective_at": payment["created_at"], "reason": "too small"},
                         ada, key())
    expect(status, 422, error)
    assert error["error"]["code"] == "refund_exceeds_payment"

    # Operator batch correction is atomic and replayable.
    batch_key = key()
    batch_body = {"corrections": [{
        "payment_id": payment["payment_id"],
        "expected_revision": 2,
        "amount": 700,
        "effective_at": payment["created_at"],
        "reason": "batch correction",
    }]}
    status, batch = call("POST", "/correction-batches", batch_body, ada, batch_key)
    expect(status, 201, batch)
    assert len(batch["revisions"]) == 1 and batch["revisions"][0]["correction_batch_id"] == batch["correction_batch_id"]
    status, batch_replay = call("POST", "/correction-batches", batch_body, ada, batch_key)
    expect(status, 200, batch_replay)
    assert batch_replay == batch

    # Non-operator cannot run batches.
    status, error = call("POST", "/correction-batches", batch_body, bob, key())
    expect(status, 403, error)
    assert error["error"]["code"] == "forbidden"

    # Naive temporal strings are invalid.
    status, error = call("GET", "/me", token=ada, params={"as_of": "2026-01-01T00:00:00"})
    expect(status, 422, error)

    # Seeded created_at is honored: fixture balances are ending balances, not replayed.
    seeded_time = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=3)).isoformat()
    seeded = fixture([{
        "id": "p_seed",
        "from_user_id": "u_ada",
        "to_user_id": "u_bob",
        "amount": 500,
        "note": "seed",
        "visibility": "private",
        "created_at": seeded_time,
    }])
    # The supplied balances are after the seeded payment; opening Ada is 10500.
    reset(seeded)
    ada = login("ada@example.test", "password-a")
    before_seed = (dt.datetime.fromisoformat(seeded_time) - dt.timedelta(microseconds=1)).isoformat()
    status, prior = call("GET", "/me", token=ada, params={"as_of": before_seed})
    expect(status, 200, prior)
    assert prior["balance"] == 10500, prior

    print("postsubmit Stage 4 probes: PASS")


if __name__ == "__main__":
    main()
