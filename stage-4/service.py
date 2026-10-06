"""Pocketful: single-process transactional, exact-minor-unit HTTP service."""
import copy
import datetime as dt
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import sys
import threading
from urllib.parse import urlsplit, parse_qs

MAX_BALANCE = 2 ** 53
LOCK = threading.RLock()
REQUEST_CLOCK = threading.local()
CLOCK_LOCK = threading.Lock()
LAST_CLOCK = dt.datetime.min.replace(tzinfo=dt.timezone.utc)


def _next_request_clock():
    global LAST_CLOCK
    current = dt.datetime.now(dt.timezone.utc)
    with CLOCK_LOCK:
        if current <= LAST_CLOCK:
            current = LAST_CLOCK + dt.timedelta(microseconds=1)
        LAST_CLOCK = current
    return current


def request_clock():
    current = getattr(REQUEST_CLOCK, "value", None)
    return current if current is not None else _next_request_clock()


HANDLE = re.compile(r"[a-z0-9_]{1,20}\Z")
EMAIL = re.compile(r"[^\s@]+@[^\s@]+\Z")
STATUSES = {"pending", "paid", "declined", "cancelled"}
# JSON has no integer-token digit limit. Values are validated by endpoint rules.
sys.set_int_max_str_digits(0)


class JSONNumber:
    """Exact finite decimal value, without a machine-sized exponent or expansion."""
    def __init__(self, token):
        mantissa, separator, exponent = token.lower().partition("e")
        self.negative = mantissa.startswith("-")
        mantissa = mantissa.lstrip("-")
        whole, point, fraction = mantissa.partition(".")
        digits = (whole + fraction).lstrip("0")
        if not digits:
            self.negative, self.digits, self.exponent = False, "0", 0
            return
        trimmed = digits.rstrip("0")
        self.digits = trimmed
        self.exponent = (int(exponent) if separator else 0) - len(fraction) + len(digits) - len(trimmed)

    def identity(self):
        if self.digits == "0":
            return "0"
        return ("-" if self.negative else "") + self.digits + "e" + str(self.exponent)

    def bounded_integer(self, low, high):
        if self.digits == "0":
            value = 0
        else:
            # A normalized coefficient has no trailing zeros: a negative exponent
            # is fractional. Check size before constructing any power of ten.
            if self.exponent < 0 or len(self.digits) + self.exponent > len(str(max(abs(low), abs(high)))):
                fail()
            value = int(self.digits) * 10 ** self.exponent
            if self.negative:
                value = -value
        if not low <= value <= high:
            fail()
        return value

    def __eq__(self, other):
        if type(other) is int:
            other = JSONNumber(str(other))
        return isinstance(other, JSONNumber) and self.identity() == other.identity()


class APIError(Exception):
    def __init__(self, status=422, code="validation_failed", message="Invalid request"):
        self.status, self.code, self.message = status, code, message


def fail(status=422, code="validation_failed", message="Invalid request"):
    raise APIError(status, code, message)


def now():
    return request_clock().isoformat(timespec="microseconds")


def identifier(prefix):
    return prefix + secrets.token_hex(16)


def string(body, key, default=None, maximum=None, special=False):
    if key not in body:
        if default is not None:
            return default
        fail(message="Missing " + key)
    value = body[key]
    if not isinstance(value, str):
        fail(422 if special else 400, "validation_failed" if special else "malformed_request")
    if maximum is not None and len(value) > maximum:
        fail()
    return value


def integer(value, low, high):
    if isinstance(value, JSONNumber):
        return value.bounded_integer(low, high)
    if type(value) is not int:
        fail()
    if not low <= value <= high:
        fail()
    return int(value)


def amount(body):
    return integer(body.get("amount"), 1, 1000000000)


def note(body):
    return string(body, "note", "", 200, special=True)


def visibility(body):
    value = body.get("visibility", "public")
    if not isinstance(value, str) or value not in {"public", "private"}:
        fail()
    return value


def handle_field(body, key):
    value = string(body, key)
    if not HANDLE.fullmatch(value):
        fail()
    return value


def canonical(value):
    """Tagged JSON value tree; number equality is exact, including exponent forms."""
    if value is None:
        return ["null"]
    if isinstance(value, bool):
        return ["bool", value]
    if isinstance(value, (int, JSONNumber)):
        number = value if isinstance(value, JSONNumber) else JSONNumber(str(value))
        return ["number", number.identity()]
    if isinstance(value, str):
        return ["string", value]
    if isinstance(value, list):
        return ["array", [canonical(item) for item in value]]
    return ["object", [[key, canonical(value[key])] for key in sorted(value)]]


def password_hash(password):
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=8192, r=8, p=1).hex()
    return {"algorithm": "scrypt-8192-8-1", "salt": salt, "digest": digest}


def password_matches(password, stored):
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(stored["salt"]), n=8192, r=8, p=1).hex()
    return hmac.compare_digest(digest, stored["digest"])


def legacy_blank_state():
    return {"schema": 1, "currency": "EUR", "minor_units": 2, "seeded_total": 0,
            "users": {}, "tokens": {}, "payments": {}, "requests": {},
            "settlements": {}, "operators": [], "idempotency": []}


def blank_state():
    return {**legacy_blank_state(), "schema": 2, "authorizations": {}, "authorization_ttl_seconds": "6e2"}


STATE = blank_state()


def validate_id(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 64:
        fail()
    return value


def fixture_id(body, key):
    return validate_id(string(body, key))


def fixture_integer(body, key, low, high):
    if key not in body:
        fail(message="Missing " + key)
    value = body[key]
    if isinstance(value, bool) or not isinstance(value, (int, JSONNumber)):
        fail(400, "malformed_request")
    return integer(value, low, high)


def currency_fields(body):
    currency = string(body, "currency")
    units = fixture_integer(body, "minor_units", 0, 3)
    if {"EUR": 2, "JPY": 0, "BHD": 3}.get(currency) != units:
        fail()
    return currency, units


def array_field(body, key, default=None):
    if key not in body and default is None:
        fail(message="Missing " + key)
    value = body.get(key, default)
    if not isinstance(value, list):
        fail(400, "malformed_request")
    return value


def object_value(value):
    if not isinstance(value, dict):
        fail(400, "malformed_request")
    return value


def user_by_handle(state, handle):
    for user in state["users"].values():
        if user["handle"] == handle:
            return user
    fail(404, "not_found")


def payment_record(state, sender, receiver, value, memo, scope, timestamp=None, request_id=None, settlement_id=None, payment_id=None):
    record = {"payment_id": payment_id or identifier("p_"), "from_user_id": sender["id"],
            "from_handle": sender["handle"], "to_user_id": receiver["id"], "to_handle": receiver["handle"],
            "amount": value, "currency": state["currency"], "note": memo, "visibility": scope,
            "request_id": request_id, "settlement_id": settlement_id, "created_at": timestamp or now()}
    if "authorizations" in state:
        record["authorization_id"] = None
    return record


def request_record(state, requester, payer, value, memo, timestamp=None, request_id=None):
    return {"request_id": request_id or identifier("rq_"), "requester_id": requester["id"],
            "requester_handle": requester["handle"], "payer_id": payer["id"], "payer_handle": payer["handle"],
            "amount": value, "currency": state["currency"], "note": memo, "status": "pending",
            "payment_id": None, "created_at": timestamp or now()}


def fixture_state(body):
    state = blank_state()
    state["currency"], state["minor_units"] = currency_fields(body)
    emails, handles = set(), set()
    for raw in array_field(body, "users"):
        raw = object_value(raw)
        uid = fixture_id(raw, "id")
        email, handle = string(raw, "email"), handle_field(raw, "handle")
        if not EMAIL.fullmatch(email) or uid in state["users"] or email in emails or handle in handles:
            fail()
        user = {"id": uid, "email": email, "display_name": string(raw, "display_name"), "handle": handle,
                "balance": fixture_integer(raw, "balance", 0, MAX_BALANCE), "password_hash": password_hash(string(raw, "password"))}
        state["users"][uid] = user
        emails.add(email)
        handles.add(handle)
    state["seeded_total"] = sum(user["balance"] for user in state["users"].values())
    state["operators"] = array_field(body, "settlement_operator_ids", [])
    for uid in state["operators"]:
        if not isinstance(uid, str):
            fail(400, "malformed_request")
        if validate_id(uid) not in state["users"]:
            fail()
    timestamp = now()
    for raw in array_field(body, "payments", []):
        raw = object_value(raw)
        pid = fixture_id(raw, "id")
        sender = state["users"].get(fixture_id(raw, "from_user_id"))
        receiver = state["users"].get(fixture_id(raw, "to_user_id"))
        if sender is None or receiver is None or sender is receiver or pid in state["payments"]:
            fail()
        state["payments"][pid] = payment_record(state, sender, receiver, amount(raw), note(raw), visibility(raw),
                                               timestamp, payment_id=pid)
    for raw in array_field(body, "requests", []):
        raw = object_value(raw)
        rid = fixture_id(raw, "id")
        requester = state["users"].get(fixture_id(raw, "requester_id"))
        payer = state["users"].get(fixture_id(raw, "payer_id"))
        status = string(raw, "status")
        if requester is None or payer is None or requester is payer or rid in state["requests"] or status not in STATUSES:
            fail()
        record = request_record(state, requester, payer, integer(raw.get("amount"), 0, 1000000000), note(raw), timestamp, rid)
        record["status"] = status
        # Reset accepts the documented fixture fields only. Payment linkage is
        # created when the API pays a request and is preserved by opaque import.
        state["requests"][rid] = record
    state["authorization_ttl_seconds"] = lifetime(body.get("authorization_ttl_seconds", 600))
    for raw in array_field(body, "authorizations", []):
        object_value(raw)
        aid = fixture_id(raw, "id")
        sender = state["users"].get(fixture_id(raw, "from_user_id"))
        receiver = state["users"].get(fixture_id(raw, "to_user_id"))
        status, deadline = string(raw, "status"), string(raw, "expires_at")
        if sender is None or receiver is None or sender is receiver or aid in state["authorizations"] or status not in AUTH_STATUSES:
            fail()
        instant(deadline)
        record = authorization_record(state, sender, receiver, amount(raw), note(raw), visibility(raw), deadline, timestamp, aid)
        record["status"], record["seeded"] = status, True
        state["authorizations"][aid] = record
    expire(state)
    if any(held(state, uid) > user["balance"] for uid, user in state["users"].items()):
        fail()
    return state


def completed_claim(state, entry, body):
    """Match a completed original request to its immutable operation receipt.

    This deliberately does not execute against current balances/request status:
    those can change after the original successful operation.
    """
    actor = state["users"][entry["user_id"]]
    response, path = entry["response"], entry["path"]
    def expected_payment(raw, sender, receiver, record, request_id=None, settlement_id=None):
        if sender is receiver:
            fail()
        return payment_record(state, sender, receiver, amount(raw), note(raw), visibility(raw),
                              record["created_at"], request_id, settlement_id, record["payment_id"])
    if path == "/payments":
        receiver = user_by_handle(state, handle_field(body, "to_handle"))
        expected = expected_payment(body, actor, receiver, response)
        resources = [("payment", response["payment_id"])]
    elif path == "/requests":
        payer = user_by_handle(state, handle_field(body, "payer_handle"))
        if actor is payer:
            fail()
        expected = request_record(state, actor, payer, amount(body), note(body), response["created_at"], response["request_id"])
        resources = [("request", response["request_id"])]
    elif re.fullmatch(r"/requests/[^/]+/pay", path):
        rid = validate_id(path.split("/")[2])
        request = state["requests"][rid]
        if request["payer_id"] != actor["id"] or request["status"] != "paid" or request["payment_id"] != response["payment_id"]:
            fail()
        expected = payment_record(state, actor, state["users"][request["requester_id"]], request["amount"],
                                  request["note"], visibility(body), response["created_at"], rid,
                                  payment_id=response["payment_id"])
        resources = [("payment", response["payment_id"])]
    elif path == "/splits":
        value, memo = amount(body), note(body)
        handles = array_field(body, "participant_handles")
        if not handles or any(not isinstance(handle, str) or not HANDLE.fullmatch(handle) for handle in handles) or len(set(handles)) != len(handles):
            fail()
        participants = [user_by_handle(state, handle) for handle in handles]
        quotient, remainder = divmod(value, len(handles))
        shares = [{"handle": handle, "amount": quotient + (i < remainder)} for i, handle in enumerate(handles)]
        others = [(user, share) for user, share in zip(participants, shares) if user is not actor]
        if len(response["requests"]) != len(others):
            fail()
        requests = [request_record(state, actor, user, share["amount"], memo, response["created_at"], record["request_id"])
                    for (user, share), record in zip(others, response["requests"])]
        expected = {"split_id": response["split_id"], "amount": value, "currency": state["currency"],
                    "note": memo, "shares": shares, "requests": requests, "created_at": response["created_at"]}
        resources = [("split", response["split_id"])] + [("request", r["request_id"]) for r in requests]
    elif path == "/settlements":
        if actor["id"] not in state["operators"]:
            fail()
        transfers = body.get("transfers")
        if not isinstance(transfers, list) or not 1 <= len(transfers) <= 32 or len(transfers) != len(response["payments"]):
            fail()
        payments = []
        for raw, record in zip(transfers, response["payments"]):
            object_value(raw)
            sender = user_by_handle(state, handle_field(raw, "from_handle"))
            receiver = user_by_handle(state, handle_field(raw, "to_handle"))
            payments.append(expected_payment(raw, sender, receiver, record, settlement_id=response["settlement_id"]))
        expected = {"settlement_id": response["settlement_id"], "committed_at": response["committed_at"], "payments": payments}
        resources = [("settlement", response["settlement_id"])] + [("payment", p["payment_id"]) for p in payments]
    else:
        fail()
    if canonical(expected) != canonical(response):
        fail()
    return resources


def validate_stage1_snapshot(body):
    """Validate into a detached candidate; never alter live state during import."""
    try:
        if body.get("track") != "pocketful" or type(body.get("format_version")) is bool or body.get("format_version") != 1:
            fail()
        state = body["state"]
        if not isinstance(state, dict) or set(state) != set(legacy_blank_state()) or isinstance(state["schema"], bool) or state["schema"] != 1:
            fail()
        currency_fields(state)
        if any(not isinstance(state[key], dict) for key in ("users", "tokens", "payments", "requests", "settlements")):
            fail()
        if not isinstance(state["operators"], list) or not isinstance(state["idempotency"], list):
            fail()
        emails, handles = set(), set()
        for uid, user in state["users"].items():
            validate_id(uid)
            if set(user) != {"id", "email", "display_name", "handle", "balance", "password_hash"}:
                fail()
            if user["id"] != uid or not EMAIL.fullmatch(user["email"]) or not HANDLE.fullmatch(user["handle"]):
                fail()
            if user["email"] in emails or user["handle"] in handles or not isinstance(user["display_name"], str):
                fail()
            emails.add(user["email"])
            handles.add(user["handle"])
            user["balance"] = integer(user["balance"], 0, MAX_BALANCE)
            password = user["password_hash"]
            if password["algorithm"] != "scrypt-8192-8-1" or not re.fullmatch(r"[0-9a-f]{32}", password["salt"]) or not re.fullmatch(r"[0-9a-f]{128}", password["digest"]):
                fail()
        total = integer(state["seeded_total"], 0, MAX_BALANCE * max(1, len(state["users"])))
        if sum(u["balance"] for u in state["users"].values()) != total:
            fail()
        state["seeded_total"] = total
        if any(not isinstance(token, str) or not token or uid not in state["users"] for token, uid in state["tokens"].items()):
            fail()
        if any(uid not in state["users"] for uid in state["operators"]):
            fail()
        def validate_record(rid, record, payment):
            validate_id(rid)
            fields = {"payment_id", "from_user_id", "from_handle", "to_user_id", "to_handle", "amount", "currency", "note", "visibility", "request_id", "settlement_id", "created_at"} if payment else {"request_id", "requester_id", "requester_handle", "payer_id", "payer_handle", "amount", "currency", "note", "status", "payment_id", "created_at"}
            if set(record) != fields:
                fail()
            if record["payment_id" if payment else "request_id"] != rid or record["currency"] != state["currency"]:
                fail()
            left, right = ("from", "to") if payment else ("requester", "payer")
            leftid, rightid = (left + "_user_id", right + "_user_id") if payment else (left + "_id", right + "_id")
            a, b = state["users"][record[leftid]], state["users"][record[rightid]]
            if a is b or record[left + "_handle"] != a["handle"] or record[right + "_handle"] != b["handle"]:
                fail()
            record["amount"] = integer(record["amount"], 0, 1000000000)
            note(record)
            parsed = dt.datetime.fromisoformat(record["created_at"])
            if parsed.tzinfo is None:
                fail()
            if payment:
                visibility(record)
                if record["request_id"] is not None and record["request_id"] not in state["requests"]:
                    fail()
                if record["settlement_id"] is not None and record["settlement_id"] not in state["settlements"]:
                    fail()
            else:
                if record["status"] not in STATUSES:
                    fail()
                if record["payment_id"] is not None and record["payment_id"] not in state["payments"]:
                    fail()
        for pid, record in state["payments"].items():
            validate_record(pid, record, True)
        for rid, record in state["requests"].items():
            validate_record(rid, record, False)
            if record["payment_id"] is not None:
                payment = state["payments"][record["payment_id"]]
                if record["status"] != "paid" or payment["request_id"] != rid or payment["from_user_id"] != record["payer_id"] or payment["to_user_id"] != record["requester_id"] or payment["amount"] != record["amount"] or payment["note"] != record["note"]:
                    fail()
        for pid, payment in state["payments"].items():
            if payment["request_id"] is not None:
                if state["requests"][payment["request_id"]]["payment_id"] != pid or payment["settlement_id"] is not None:
                    fail()
            if payment["settlement_id"] is not None:
                if payment not in state["settlements"][payment["settlement_id"]]["payments"]:
                    fail()
        for sid, settlement in state["settlements"].items():
            validate_id(sid)
            if settlement["settlement_id"] != sid or not 1 <= len(settlement["payments"]) <= 32:
                fail()
            if len({payment["payment_id"] for payment in settlement["payments"]}) != len(settlement["payments"]):
                fail()
            for payment in settlement["payments"]:
                if canonical(payment) != canonical(state["payments"][payment["payment_id"]]) or payment["settlement_id"] != sid or payment["request_id"] is not None or payment["created_at"] != settlement["committed_at"]:
                    fail()
        claimed, created_resources = set(), set()
        def canonical_tree(tree):
            if not isinstance(tree, list) or not tree or not isinstance(tree[0], str):
                fail()
            tag = tree[0]
            if tag == "null":
                if len(tree) != 1:
                    fail()
                return
            if len(tree) != 2:
                fail()
            payload = tree[1]
            if tag == "bool":
                if type(payload) is not bool:
                    fail()
            elif tag == "string":
                if not isinstance(payload, str):
                    fail()
            elif tag == "number":
                if not isinstance(payload, str) or not re.fullmatch(r"0|-?[1-9][0-9]*e-?[0-9]+", payload):
                    fail()
            elif tag == "array":
                if not isinstance(payload, list):
                    fail()
                for item in payload:
                    canonical_tree(item)
            elif tag == "object":
                if not isinstance(payload, list):
                    fail()
                keys = []
                for pair in payload:
                    if not isinstance(pair, list) or len(pair) != 2 or not isinstance(pair[0], str):
                        fail()
                    keys.append(pair[0])
                    canonical_tree(pair[1])
                if keys != sorted(set(keys)):
                    fail()
            else:
                fail()
        def original_request(record):
            current = state["requests"][record["request_id"]]
            if record.get("status") != "pending" or record.get("payment_id") is not None:
                fail()
            if canonical({k: v for k, v in record.items() if k not in {"status", "payment_id"}}) != canonical({k: v for k, v in current.items() if k not in {"status", "payment_id"}}):
                fail()
        def original_body(tree):
            tag = tree[0]
            if tag == "null":
                return None
            if tag == "number":
                return JSONNumber(tree[1])
            if tag == "array":
                return [original_body(item) for item in tree[1]]
            if tag == "object":
                return {key: original_body(value) for key, value in tree[1]}
            return tree[1]
        for entry in state["idempotency"]:
            identity = (entry["user_id"], entry["method"], entry["path"], entry["key"])
            if identity in claimed or entry["user_id"] not in state["users"] or entry["method"] != "POST" or not isinstance(entry["path"], str) or not isinstance(entry["key"], str) or not 1 <= len(entry["key"]) <= 255:
                fail()
            if not isinstance(entry["body"], list) or entry["body"][0] != "object" or not isinstance(entry["response"], dict):
                fail()
            canonical_tree(entry["body"])
            response, path = entry["response"], entry["path"]
            if path == "/payments" or re.fullmatch(r"/requests/[^/]+/pay", path):
                if canonical(response) != canonical(state["payments"][response["payment_id"]]) or response["from_user_id"] != entry["user_id"]:
                    fail()
                if path != "/payments" and response["request_id"] != path.split("/")[2]:
                    fail()
            elif path == "/requests":
                original_request(response)
                if response["requester_id"] != entry["user_id"]:
                    fail()
            elif path == "/settlements":
                if canonical(response) != canonical(state["settlements"][response["settlement_id"]]):
                    fail()
            elif path == "/splits":
                validate_id(response["split_id"])
                timestamp = dt.datetime.fromisoformat(response["created_at"])
                if timestamp.tzinfo is None or response["currency"] != state["currency"]:
                    fail()
                note(response)
                split_amount = amount(response)
                shares = response["shares"]
                if not isinstance(shares, list) or not shares:
                    fail()
                handles = [share["handle"] for share in shares]
                if len(handles) != len(set(handles)):
                    fail()
                quotient, remainder = divmod(split_amount, len(shares))
                expected_payers = []
                for index, share in enumerate(shares):
                    participant = user_by_handle(state, share["handle"])
                    if integer(share["amount"], 0, 1000000000) != quotient + (index < remainder):
                        fail()
                    if participant["id"] != entry["user_id"]:
                        expected_payers.append(participant["id"])
                if [r["payer_id"] for r in response["requests"]] != expected_payers:
                    fail()
                for record in response["requests"]:
                    original_request(record)
                    if record["requester_id"] != entry["user_id"] or record["created_at"] != response["created_at"] or record["note"] != response["note"]:
                        fail()
            else:
                fail()
            original = original_body(entry["body"])
            if canonical(original) != entry["body"]:
                fail()
            resources = completed_claim(state, entry, original)
            if len(set(resources)) != len(resources) or any(resource in created_resources for resource in resources):
                fail()
            created_resources.update(resources)
            claimed.add(identity)
        # Stored API responses contain only integer numbers. Restore integer-valued
        # exponent/decimal encodings too, without ever rounding fractional input.
        def native(value):
            if isinstance(value, JSONNumber):
                return integer(value, -MAX_BALANCE * max(1, len(state["users"])), MAX_BALANCE * max(1, len(state["users"])))
            if isinstance(value, list):
                return [native(item) for item in value]
            if isinstance(value, dict):
                return {key: native(item) for key, item in value.items()}
            return value
        return native(state)
    except (KeyError, TypeError, ValueError, IndexError, AttributeError, ArithmeticError, RecursionError, APIError):
        fail()


AUTH_STATUSES = {"open", "captured", "voided", "expired"}


def instant(value):
    try:
        result = dt.datetime.fromisoformat(value)
        if result.tzinfo is None:
            fail()
        return result
    except (ValueError, TypeError):
        fail()


def lifetime(value):
    if isinstance(value, bool) or not isinstance(value, (int, JSONNumber)):
        fail(400, "malformed_request")
    number = value if isinstance(value, JSONNumber) else JSONNumber(str(value))
    if number.negative or number.digits == "0" or number.exponent < 0:
        fail()
    return number.identity()


def expiration(timestamp, ttl):
    # RFC3339 uses a four-digit year. Keep very long lifetimes representable;
    # their exact duration remains in the private snapshot.
    start = instant(timestamp)
    ceiling = dt.datetime.max.replace(tzinfo=dt.timezone.utc)
    seconds = int((ceiling - start).total_seconds())
    try:
        duration = JSONNumber(ttl).bounded_integer(1, seconds)
    except APIError:
        return ceiling.isoformat()
    return (start + dt.timedelta(seconds=duration)).isoformat(timespec="microseconds")


def authorization_record(state, sender, receiver, value, memo, scope, deadline, timestamp, aid=None):
    return {"authorization_id": aid or identifier("a_"), "from_user_id": sender["id"],
            "from_handle": sender["handle"], "to_user_id": receiver["id"], "to_handle": receiver["handle"],
            "amount": value, "captured_amount": 0, "currency": state["currency"], "note": memo,
            "visibility": scope, "status": "open", "expires_at": deadline, "payment_id": None,
            "payment_ids": [], "created_at": timestamp, "seeded": False}


def authorization_view(record):
    result = {key: copy.deepcopy(value) for key, value in record.items() if key != "seeded"}
    result["remaining_amount"] = record["amount"] - record["captured_amount"] if record["status"] == "open" else 0
    return result


def expire(state):
    clock = request_clock()
    for record in state["authorizations"].values():
        if record["status"] == "open" and instant(record["expires_at"]) <= clock:
            record["status"] = "expired"


def held(state, uid):
    return sum(a["amount"] - a["captured_amount"] for a in state["authorizations"].values()
               if a["status"] == "open" and a["from_user_id"] == uid)


def available(state, uid):
    return state["users"][uid]["balance"] - held(state, uid)


def decoded(tree):
    if not isinstance(tree, list) or not tree or not isinstance(tree[0], str):
        fail()
    tag = tree[0]
    if tag == "null" and len(tree) == 1:
        return None
    if len(tree) != 2:
        fail()
    payload = tree[1]
    if tag == "bool" and type(payload) is bool or tag == "string" and isinstance(payload, str):
        return payload
    if tag == "number" and isinstance(payload, str) and re.fullmatch(r"0|-?[1-9][0-9]*e-?[0-9]+", payload):
        value = JSONNumber(payload)
        if canonical(value) != tree:
            fail()
        return value
    if tag == "array" and isinstance(payload, list):
        return [decoded(item) for item in payload]
    if tag == "object" and isinstance(payload, list):
        if any(not isinstance(pair, list) or len(pair) != 2 or not isinstance(pair[0], str) for pair in payload):
            fail()
        keys = [pair[0] for pair in payload]
        if keys != sorted(set(keys)):
            fail()
        return {key: decoded(value) for key, value in payload}
    fail()


def capture_final(body):
    value = body.get("final", True)
    if type(value) is not bool:
        fail(400, "malformed_request")
    return value


def validate_snapshot(body):
    """Validate old exports or a full authorization ledger before replacement."""
    try:
        state = body["state"]
        if set(state) == set(legacy_blank_state()):
            result = validate_stage1_snapshot(body)
            result.update(schema=2, authorizations={}, authorization_ttl_seconds="6e2")
            for payment in result["payments"].values():
                payment["authorization_id"] = None
            for settlement in result["settlements"].values():
                for payment in settlement["payments"]:
                    payment["authorization_id"] = None
            return result
        if set(state) != set(blank_state()) or isinstance(state["schema"], bool) or state["schema"] != 2:
            fail()
        ttl = state["authorization_ttl_seconds"]
        if not isinstance(ttl, str) or not re.fullmatch(r"[1-9][0-9]*e[0-9]+", ttl) or lifetime(JSONNumber(ttl)) != ttl:
            fail()
        if not isinstance(state["authorizations"], dict):
            fail()
        ledger_ids, closing = set(), {}
        for aid, record in state["authorizations"].items():
            validate_id(aid)
            if set(record) != set(authorization_record(state, {"id":"", "handle":""}, {"id":"", "handle":""}, 1, "", "public", now(), now())):
                fail()
            sender, receiver = state["users"][record["from_user_id"]], state["users"][record["to_user_id"]]
            if sender is receiver or record["authorization_id"] != aid or record["from_handle"] != sender["handle"] or record["to_handle"] != receiver["handle"] or record["currency"] != state["currency"]:
                fail()
            record["amount"] = amount(record)
            record["captured_amount"] = integer(record["captured_amount"], 0, record["amount"])
            note(record); visibility(record); instant(record["created_at"]); instant(record["expires_at"])
            if type(record["seeded"]) is not bool or record["status"] not in AUTH_STATUSES or not isinstance(record["payment_ids"], list):
                fail()
            if not record["seeded"] and record["expires_at"] != expiration(record["created_at"], ttl):
                fail()
            total, previous_time = 0, None
            for pid in record["payment_ids"]:
                if pid in ledger_ids:
                    fail()
                ledger_ids.add(pid)
                payment = state["payments"][pid]
                if payment["authorization_id"] != aid or payment["request_id"] is not None or payment["settlement_id"] is not None:
                    fail()
                for field in ("from_user_id", "from_handle", "to_user_id", "to_handle", "currency", "note", "visibility"):
                    if payment[field] != record[field]:
                        fail()
                payment["amount"] = integer(payment["amount"], 1, 1000000000)
                total += payment["amount"]
                timestamp = instant(payment["created_at"])
                if timestamp < instant(record["created_at"]) or timestamp >= instant(record["expires_at"]) or previous_time is not None and timestamp < previous_time:
                    fail()
                previous_time = timestamp
            if total != record["captured_amount"] or record["payment_id"] != (record["payment_ids"][-1] if record["payment_ids"] else None):
                fail()
            if record["status"] == "open" and total >= record["amount"]:
                fail()
        for pid, payment in state["payments"].items():
            if "authorization_id" not in payment or (payment["authorization_id"] is not None) != (pid in ledger_ids):
                fail()
        projection = copy.deepcopy(state)
        projection.pop("authorizations"); projection.pop("authorization_ttl_seconds"); projection["schema"] = 1
        def stage1_receipt(value):
            if isinstance(value, dict):
                return {key: stage1_receipt(item) for key, item in value.items() if key != "authorization_id"}
            if isinstance(value, list):
                return [stage1_receipt(item) for item in value]
            return value
        projection["payments"] = stage1_receipt(projection["payments"])
        projection["settlements"] = stage1_receipt(projection["settlements"])
        old_entries, captures, created, identities = [], set(), set(), set()
        for entry in state["idempotency"]:
            identity = (entry["user_id"], entry["method"], entry["path"], entry["key"])
            if identity in identities or entry["user_id"] not in state["users"] or entry["method"] != "POST" or not isinstance(entry["key"], str) or not 1 <= len(entry["key"]) <= 255:
                fail()
            identities.add(identity)
            path, response = entry["path"], entry["response"]
            raw = decoded(entry["body"])
            if not isinstance(raw, dict) or canonical(raw) != entry["body"]:
                fail()
            if path == "/authorizations":
                aid = response["authorization_id"]
                if aid in created:
                    fail()
                created.add(aid)
                record = state["authorizations"][aid]
                if record["seeded"] or record["from_user_id"] != entry["user_id"] or record["to_handle"] != handle_field(raw, "to_handle") or record["amount"] != amount(raw) or record["note"] != note(raw) or record["visibility"] != visibility(raw):
                    fail()
                original = copy.deepcopy(record)
                original.update(status="open", captured_amount=0, payment_id=None, payment_ids=[])
                if canonical(response) != canonical(authorization_view(original)):
                    fail()
            elif isinstance(path, str) and re.fullmatch(r"/authorizations/[^/]+/capture", path):
                aid = path.split("/")[2]
                record = state["authorizations"][aid]
                pid = response["payment_id"]
                if pid in captures or pid not in record["payment_ids"] or record["to_user_id"] != entry["user_id"] or canonical(response) != canonical(state["payments"][pid]):
                    fail()
                captures.add(pid)
                index = record["payment_ids"].index(pid)
                before = record["amount"] - sum(state["payments"][p]["amount"] for p in record["payment_ids"][:index])
                requested = integer(raw["amount"], 1, 1000000000) if "amount" in raw else before
                if requested != response["amount"] or requested > before:
                    fail()
                final = capture_final(raw) or requested == before
                if final and index != len(record["payment_ids"]) - 1:
                    fail()
                if index == len(record["payment_ids"]) - 1:
                    closing[aid] = final
            else:
                def check_receipt(value):
                    if isinstance(value, dict):
                        if "from_user_id" in value and "payment_id" in value:
                            if value.get("authorization_id") is not None or value["payment_id"] in ledger_ids:
                                fail()
                        for item in value.values():
                            check_receipt(item)
                    elif isinstance(value, list):
                        for item in value:
                            check_receipt(item)
                check_receipt(response)
                old_entries.append(stage1_receipt(entry))
        if captures != ledger_ids:
            fail()
        for aid, final in closing.items():
            if (state["authorizations"][aid]["status"] == "captured") != final:
                fail()
        projection["idempotency"] = old_entries
        validate_stage1_snapshot({**body, "state": projection})
        def native(value):
            if isinstance(value, JSONNumber):
                return integer(value, -MAX_BALANCE * max(1, len(state["users"])), MAX_BALANCE * max(1, len(state["users"])))
            if isinstance(value, list):
                return [native(item) for item in value]
            if isinstance(value, dict):
                return {key: native(item) for key, item in value.items()}
            return value
        result = native(state)
        expire(result)
        if any(available(result, uid) < 0 for uid in result["users"]):
            fail()
        return result
    except (KeyError, TypeError, ValueError, IndexError, AttributeError, ArithmeticError, RecursionError, APIError):
        fail()


def pagination(query):
    result = []
    for name, default, low, high in (("limit", "50", 1, 200), ("offset", "0", 0, None)):
        value = query.get(name, [default])[0]
        if not re.fullmatch(r"[0-9]+", value):
            fail()
        # Avoid interpreter limits on hostile but otherwise digit-only values.
        number = int(value.lstrip("0") or "0") if len(value.lstrip("0")) < 100 else 10 ** 100
        if number < low or high is not None and number > high:
            fail()
        result.append(number)
    return result


def transfer(state, sender, receiver, value, memo, scope, request_id=None):
    if available(state, sender["id"]) < value:
        fail(409, "insufficient_funds")
    if receiver["balance"] + value > MAX_BALANCE:
        fail()
    record = payment_record(state, sender, receiver, value, memo, scope, request_id=request_id)
    sender["balance"] -= value
    receiver["balance"] += value
    state["payments"][record["payment_id"]] = record
    return record


def authentication(path, body):
    """Compute password hashes outside the state lock, commit sessions inside it."""
    email, password = string(body, "email"), string(body, "password")
    def session(state, user, status):
        token = secrets.token_urlsafe(32)
        state["tokens"][token] = user["id"]
        return status, {"user_id": user["id"], "display_name": user["display_name"], "token": token}
    if path == "/auth/signup":
        display = string(body, "display_name")
        if not EMAIL.fullmatch(email) or len(password) < 8:
            fail()
        handle = re.sub(r"[^a-z0-9_]", "_", email.split("@", 1)[0].lower())[:20]
        def available(state):
            if any(u["email"] == email for u in state["users"].values()):
                fail(409, "email_taken")
            if any(u["handle"] == handle for u in state["users"].values()):
                fail(409, "handle_taken")
        with LOCK:
            available(STATE)
        hashed = password_hash(password)
        with LOCK:
            state = STATE
            available(state)
            uid = identifier("u_")
            user = {"id": uid, "email": email, "display_name": display, "handle": handle, "balance": 0,
                    "password_hash": hashed}
            state["users"][uid] = user
            return session(state, user, 201)
    while True:
        with LOCK:
            state = STATE
            user = next((u for u in state["users"].values() if u["email"] == email), None)
            if user is None:
                fail(401, "unauthenticated")
            hashed = user["password_hash"]
        matches = password_matches(password, hashed)
        with LOCK:
            # Reset/import may replace credentials while scrypt is running. Recheck
            # the current account before issuing a token into the current state.
            if STATE is not state or state["users"].get(user["id"]) is not user:
                continue
            if not matches:
                fail(401, "unauthenticated")
            return session(state, user, 200)


def stage2_dispatch(method, path, query, body, authorization, key):
    global STATE
    if method == "GET" and path == "/health":
        return 200, {"status": "ok"}
    if method == "POST" and path == "/_test/reset":
        STATE = fixture_state(body)
        return 204, None
    if method == "GET" and path == "/_test/export":
        expire(STATE)
        return 200, {"track": "pocketful", "format_version": 1, "state": copy.deepcopy(STATE)}
    if method == "POST" and path == "/_test/import":
        STATE = validate_snapshot(body)
        return 204, None
    state = STATE
    expire(state)
    match = re.fullmatch(r"Bearer ([^\s]+)", authorization or "", re.IGNORECASE)
    uid = state["tokens"].get(match[1]) if match else None
    if uid is None:
        fail(401, "unauthenticated")
    user = state["users"][uid]
    request_action = re.fullmatch(r"/requests/([^/]+)/(pay|decline|cancel)", path)
    authorization_action = re.fullmatch(r"/authorizations/([^/]+)/(capture|void)", path)
    idempotent = method == "POST" and (path in {"/payments", "/requests", "/splits", "/settlements", "/authorizations"} or request_action and request_action[2] == "pay" or authorization_action and authorization_action[2] == "capture")
    if idempotent:
        if path == "/settlements" and uid not in state["operators"] and not key:
            fail(403, "forbidden")
        if key is None or key == "":
            fail(400, "missing_idempotency_key")
        if len(key) > 255:
            fail()
        body_value = canonical(body)
        for entry in state["idempotency"]:
            if (entry["user_id"], entry["method"], entry["path"], entry["key"]) == (uid, method, path, key):
                if entry["body"] != body_value:
                    fail(409, "idempotency_key_reuse")
                return 200, copy.deepcopy(entry["response"])
    if method == "GET" and path == "/me":
        return 200, {"user_id": uid, "display_name": user["display_name"], "handle": user["handle"],
                     "balance": user["balance"], "total": user["balance"], "available": available(state, uid),
                     "held": held(state, uid), "currency": state["currency"], "minor_units": state["minor_units"]}
    if method == "POST" and path == "/payments":
        handle, value, memo, scope = handle_field(body, "to_handle"), amount(body), note(body), visibility(body)
        if handle == user["handle"]:
            fail(422, "self_payment")
        response = transfer(state, user, user_by_handle(state, handle), value, memo, scope)
    elif method == "POST" and path == "/requests":
        handle, value, memo = handle_field(body, "payer_handle"), amount(body), note(body)
        if handle == user["handle"]:
            fail(422, "self_request")
        response = request_record(state, user, user_by_handle(state, handle), value, memo)
        state["requests"][response["request_id"]] = response
    elif method == "POST" and request_action:
        rid, action = request_action[1], request_action[2]
        record = state["requests"].get(rid)
        if record is None:
            fail(404, "not_found")
        if uid != record["requester_id" if action == "cancel" else "payer_id"]:
            fail(403, "forbidden")
        if action == "pay":
            scope = visibility(body)
            if record["status"] != "pending":
                fail(409, "request_not_pending")
            response = transfer(state, user, state["users"][record["requester_id"]], record["amount"], record["note"], scope, rid)
            record["status"], record["payment_id"] = "paid", response["payment_id"]
        else:
            target = "cancelled" if action == "cancel" else "declined"
            if record["status"] not in {"pending", target}:
                fail(409, "request_not_pending")
            record["status"] = target
            return 200, copy.deepcopy(record)
    elif method == "POST" and path == "/splits":
        value, memo = amount(body), note(body)
        handles = array_field(body, "participant_handles")
        if not handles:
            fail()
        if any(not isinstance(handle, str) for handle in handles):
            fail(400, "malformed_request")
        if len(set(handles)) != len(handles) or any(not HANDLE.fullmatch(handle) for handle in handles):
            fail()
        participants = [user_by_handle(state, handle) for handle in handles]
        quotient, remainder = divmod(value, len(handles))
        shares = [{"handle": handle, "amount": quotient + (index < remainder)} for index, handle in enumerate(handles)]
        timestamp = now()
        requests = [request_record(state, user, participant, share["amount"], memo, timestamp)
                    for participant, share in zip(participants, shares) if participant["id"] != uid]
        for record in requests:
            state["requests"][record["request_id"]] = record
        response = {"split_id": identifier("sp_"), "amount": value, "currency": state["currency"], "note": memo,
                    "shares": shares, "requests": requests, "created_at": timestamp}
    elif method == "POST" and path == "/settlements":
        if uid not in state["operators"]:
            fail(403, "forbidden")
        transfers = body.get("transfers")
        if not isinstance(transfers, list) or not 1 <= len(transfers) <= 32:
            fail()
        prepared, deltas = [], {}
        for raw in transfers:
            if not isinstance(raw, dict):
                fail()
            from_handle, to_handle = handle_field(raw, "from_handle"), handle_field(raw, "to_handle")
            value, memo, scope = amount(raw), note(raw), visibility(raw)
            sender, receiver = user_by_handle(state, from_handle), user_by_handle(state, to_handle)
            if sender is receiver:
                fail(422, "self_payment")
            prepared.append((sender, receiver, value, memo, scope))
            deltas[sender["id"]] = deltas.get(sender["id"], 0) - value
            deltas[receiver["id"]] = deltas.get(receiver["id"], 0) + value
        balances = {wallet: state["users"][wallet]["balance"] + delta for wallet, delta in deltas.items()}
        if any(balance < held(state, wallet) for wallet, balance in balances.items()):
            fail(409, "insufficient_funds")
        if any(balance > MAX_BALANCE for balance in balances.values()):
            fail()
        sid, timestamp = identifier("st_"), now()
        payments = [payment_record(state, *transfer_args, timestamp=timestamp, settlement_id=sid) for transfer_args in prepared]
        for wallet, balance in balances.items():
            state["users"][wallet]["balance"] = balance
        for payment in payments:
            state["payments"][payment["payment_id"]] = payment
        response = {"settlement_id": sid, "committed_at": timestamp, "payments": payments}
        state["settlements"][sid] = response
    elif method == "POST" and path == "/authorizations":
        target = handle_field(body, "to_handle")
        value, memo, scope = amount(body), note(body), visibility(body)
        receiver = user_by_handle(state, target)
        if receiver is user:
            fail(422, "self_payment")
        if available(state, uid) < value:
            fail(409, "insufficient_funds")
        timestamp = now()
        record = authorization_record(state, user, receiver, value, memo, scope,
                                      expiration(timestamp, state["authorization_ttl_seconds"]), timestamp)
        state["authorizations"][record["authorization_id"]] = record
        response = authorization_view(record)
    elif method == "POST" and authorization_action:
        aid, action = authorization_action[1], authorization_action[2]
        record = state["authorizations"].get(aid)
        if record is None:
            fail(404, "not_found")
        if uid != record["to_user_id" if action == "capture" else "from_user_id"]:
            fail(403, "forbidden")
        if action == "void":
            if record["status"] not in {"open", "voided"}:
                fail(409, "authorization_not_open")
            record["status"] = "voided"
            return 200, authorization_view(record)
        if record["status"] == "expired":
            fail(409, "authorization_expired")
        if record["status"] != "open":
            fail(409, "authorization_not_open")
        capture_time = now()
        if instant(record["expires_at"]) <= instant(capture_time):
            record["status"] = "expired"
            fail(409, "authorization_expired")
        remaining = record["amount"] - record["captured_amount"]
        raw = body.get("amount", remaining)
        if isinstance(raw, bool) or not isinstance(raw, (int, JSONNumber)):
            fail()
        number = raw if isinstance(raw, JSONNumber) else JSONNumber(str(raw))
        if number.negative or number.digits == "0" or number.exponent < 0:
            fail()
        try:
            value = number.bounded_integer(1, remaining)
        except APIError:
            fail(422, "capture_exceeds_authorization")
        final = capture_final(body)
        sender = state["users"][record["from_user_id"]]
        if user["balance"] + value > MAX_BALANCE:
            fail()
        payment = payment_record(state, sender, user, value, record["note"], record["visibility"], timestamp=capture_time)
        payment["authorization_id"] = aid
        sender["balance"] -= value
        user["balance"] += value
        record["captured_amount"] += value
        record["payment_ids"].append(payment["payment_id"])
        record["payment_id"] = payment["payment_id"]
        if final or value == remaining:
            record["status"] = "captured"
        state["payments"][payment["payment_id"]] = payment
        response = payment
    elif method == "GET" and path == "/authorizations":
        limit, offset = pagination(query)
        direction, status = query.get("direction", [None])[0], query.get("status", [None])[0]
        if direction not in {None, "incoming", "outgoing"} or status not in AUTH_STATUSES | {None}:
            fail()
        records = [r for r in state["authorizations"].values() if uid in (r["from_user_id"], r["to_user_id"])
                   and (direction != "incoming" or r["to_user_id"] == uid)
                   and (direction != "outgoing" or r["from_user_id"] == uid) and (status is None or r["status"] == status)]
        records.sort(key=lambda record: record["created_at"], reverse=True)
        return 200, {"authorizations": [authorization_view(r) for r in records[offset:offset + limit]], "has_more": offset + limit < len(records)}
    elif method == "GET" and path in {"/requests", "/activity"}:
        limit, offset = pagination(query)
        if path == "/activity":
            records = [p for p in state["payments"].values() if p["visibility"] == "public" or uid in (p["from_user_id"], p["to_user_id"])]
            field = "payments"
        else:
            direction, status = query.get("direction", [None])[0], query.get("status", [None])[0]
            if direction not in {None, "incoming", "outgoing"} or status not in STATUSES | {None}:
                fail()
            records = [r for r in state["requests"].values() if uid in (r["requester_id"], r["payer_id"])
                       and (direction != "incoming" or r["payer_id"] == uid)
                       and (direction != "outgoing" or r["requester_id"] == uid) and (status is None or r["status"] == status)]
            field = "requests"
        records.sort(key=lambda record: record["created_at"], reverse=True)
        return 200, {field: copy.deepcopy(records[offset:offset + limit]), "has_more": offset + limit < len(records)}
    else:
        fail(404, "not_found")
    if idempotent:
        state["idempotency"].append({"user_id": uid, "method": method, "path": path, "key": key,
                                     "body": body_value, "response": copy.deepcopy(response)})
    return 201, copy.deepcopy(response)


# ---------------------------------------------------------------------------
# Stage 3: temporal statements, immutable payment revisions and corrections.
#
# The Stage 2 ledger remains byte-compatible so Stage 1/2 exports continue to
# import through validate_snapshot(). Stage-3-only history is stored in a
# sidecar that is included in our opaque export and restored on import.
# ---------------------------------------------------------------------------

def _stage3_empty():
    return {"revisions": {}, "snapshots": {}, "openings": {},
            "correction_idempotency": [], "auth_closed": {}}


STAGE3_META = _stage3_empty()


def _auth_uid(authorization):
    match = re.fullmatch(r"Bearer ([^\s]+)", authorization or "", re.IGNORECASE)
    uid = STATE["tokens"].get(match[1]) if match else None
    if uid is None:
        fail(401, "unauthenticated")
    return uid


def _parse_instant(value):
    if not isinstance(value, str) or not value:
        fail()
    try:
        parsed = dt.datetime.fromisoformat(value)
    except (TypeError, ValueError):
        fail()
    if parsed.tzinfo is None:
        fail()
    return parsed.astimezone(dt.timezone.utc)


def _strict_after(previous):
    current = dt.datetime.now(dt.timezone.utc)
    if previous is not None:
        prior = _parse_instant(previous)
        if current <= prior:
            current = prior + dt.timedelta(microseconds=1)
    return current.isoformat(timespec="microseconds")


def _revision_one(payment):
    return {"payment_id": payment["payment_id"], "revision": 1,
            "amount": payment["amount"], "effective_at": payment["created_at"],
            "recorded_at": payment["created_at"], "reason": "",
            "correction_batch_id": None}


def _ensure_revisions():
    revisions = STAGE3_META["revisions"]
    for pid, payment in STATE["payments"].items():
        if pid not in revisions:
            revisions[pid] = [_revision_one(payment)]
    for pid in list(revisions):
        if pid not in STATE["payments"]:
            revisions.pop(pid, None)
    for uid in STATE["users"]:
        STAGE3_META["openings"].setdefault(uid, 0)


def _derive_openings():
    openings = {uid: user["balance"] for uid, user in STATE["users"].items()}
    for payment in STATE["payments"].values():
        value = payment["amount"]
        openings[payment["from_user_id"]] += value
        openings[payment["to_user_id"]] -= value
    return openings



def _stage3_prepare_seed_times(body):
    """Validate Stage-3 seeded timestamps before reset mutates live state."""
    changes = {"payments": {}, "authorizations": {}, "closed": {}}
    current = dt.datetime.now(dt.timezone.utc)
    for raw in body.get("payments", []) if isinstance(body.get("payments", []), list) else []:
        if isinstance(raw, dict) and "created_at" in raw:
            parsed = _parse_instant(raw["created_at"])
            if parsed > current:
                fail()
            changes["payments"][raw.get("id")] = raw["created_at"]
    for raw in body.get("authorizations", []) if isinstance(body.get("authorizations", []), list) else []:
        if isinstance(raw, dict) and "created_at" in raw:
            _parse_instant(raw["created_at"])
            changes["authorizations"][raw.get("id")] = raw["created_at"]
        if isinstance(raw, dict) and "closed_at" in raw:
            closed = _parse_instant(raw["closed_at"])
            if closed > current:
                fail()
            changes["closed"][raw.get("id")] = raw["closed_at"]
    return changes


def _stage3_apply_seed_times(changes):
    for pid, timestamp in changes["payments"].items():
        if pid in STATE["payments"]:
            STATE["payments"][pid]["created_at"] = timestamp
    for aid, timestamp in changes["authorizations"].items():
        if aid in STATE["authorizations"]:
            STATE["authorizations"][aid]["created_at"] = timestamp


def _stage3_apply_seed_closed(changes):
    for aid, timestamp in changes.get("closed", {}).items():
        if aid in STATE["authorizations"] and STATE["authorizations"][aid]["status"] != "open":
            STAGE3_META["auth_closed"][aid] = timestamp


def _stage3_reset_meta():
    global STAGE3_META
    STAGE3_META = _stage3_empty()
    STAGE3_META["openings"] = _derive_openings()
    _ensure_revisions()
    reset_clock = request_clock()
    for aid, record in STATE["authorizations"].items():
        status = record["status"]
        if status == "captured":
            if record.get("payment_ids"):
                last = STATE["payments"].get(record["payment_ids"][-1])
                STAGE3_META["auth_closed"][aid] = last["created_at"] if last else record["created_at"]
            else:
                STAGE3_META["auth_closed"][aid] = record["created_at"]
        elif status == "voided":
            if record.get("payment_ids"):
                last = STATE["payments"].get(record["payment_ids"][-1])
                STAGE3_META["auth_closed"][aid] = last["created_at"] if last else record["created_at"]
            else:
                STAGE3_META["auth_closed"][aid] = record["created_at"]
        elif status == "expired":
            expiry = _parse_instant(record["expires_at"])
            created = _parse_instant(record["created_at"])
            if expiry <= reset_clock:
                STAGE3_META["auth_closed"][aid] = record["expires_at"]
            else:
                STAGE3_META["auth_closed"][aid] = record["created_at"]


def _selected_revision(pid, known_at):
    _ensure_revisions()
    chosen = None
    for revision in STAGE3_META["revisions"].get(pid, []):
        if _parse_instant(revision["recorded_at"]) <= known_at:
            chosen = revision
        else:
            break
    return chosen


def _payment_delta(payment, revision, uid):
    value = revision["amount"]
    if payment["from_user_id"] == uid:
        return -value
    if payment["to_user_id"] == uid:
        return value
    return 0


def _historical_total(uid, at, known_at, inclusive=True):
    _ensure_revisions()
    total = STAGE3_META["openings"].get(uid, 0)
    for pid, payment in STATE["payments"].items():
        revision = _selected_revision(pid, known_at)
        if revision is None:
            continue
        effective = _parse_instant(revision["effective_at"])
        if effective < at or inclusive and effective == at:
            total += _payment_delta(payment, revision, uid)
    return total


def _authorization_closed_at(record):
    aid = record["authorization_id"]
    known = STAGE3_META["auth_closed"].get(aid)
    if known is not None:
        return known
    if record["status"] == "expired":
        return record["expires_at"]
    if record["status"] == "captured" and record.get("payment_ids"):
        latest = STATE["payments"].get(record["payment_ids"][-1])
        return latest["created_at"] if latest else None
    return None


def _held_at(uid, at, known_at):
    held_value = 0
    for record in STATE["authorizations"].values():
        if record["from_user_id"] != uid:
            continue
        created = _parse_instant(record["created_at"])
        if created > known_at or created > at:
            continue
        remaining = record["amount"]
        for pid in record.get("payment_ids", []):
            payment = STATE["payments"].get(pid)
            if payment is None:
                continue
            event = _parse_instant(payment["created_at"])
            if event <= known_at and event <= at:
                remaining -= payment["amount"]
        close_text = _authorization_closed_at(record)
        if close_text is not None:
            close = _parse_instant(close_text)
            # Expiry is knowable once the hold is known. Other lifecycle events
            # are known at their server-assigned event time.
            if close_text == record["expires_at"] or close <= known_at:
                if close <= at:
                    remaining = 0
        else:
            expiry = _parse_instant(record["expires_at"])
            if expiry <= at:
                remaining = 0
        if remaining > 0:
            held_value += remaining
    return held_value


def _decorate_authorization(value):
    if isinstance(value, dict) and "authorization_id" in value and "status" in value:
        result = copy.deepcopy(value)
        record = STATE["authorizations"].get(value["authorization_id"])
        result["closed_at"] = _authorization_closed_at(record) if record else None
        return result
    return value


def _historical_money(uid, at, known_at):
    total = _historical_total(uid, at, known_at, inclusive=True)
    hold = _held_at(uid, at, known_at)
    return total, hold, total - hold


def _history_boundaries(extra=None):
    points = set(extra or [])
    _ensure_revisions()
    future = dt.datetime.max.replace(tzinfo=dt.timezone.utc)
    for pid, payment in STATE["payments"].items():
        revision = _selected_revision(pid, future)
        if revision is not None:
            points.add(_parse_instant(revision["effective_at"]))
    for record in STATE["authorizations"].values():
        points.add(_parse_instant(record["created_at"]))
        points.add(_parse_instant(record["expires_at"]))
        closed = _authorization_closed_at(record)
        if closed:
            points.add(_parse_instant(closed))
        for pid in record.get("payment_ids", []):
            if pid in STATE["payments"]:
                points.add(_parse_instant(STATE["payments"][pid]["created_at"]))
    return sorted(points)


def _history_nonnegative(known_at, extra=None):
    for boundary in _history_boundaries(extra):
        for uid in STATE["users"]:
            total = _historical_total(uid, boundary, known_at, inclusive=True)
            if total < 0 or total - _held_at(uid, boundary, known_at) < 0:
                return False
    return True


def _idempotency_lookup(store, uid, path, key, body):
    if key is None or key == "":
        fail(400, "missing_idempotency_key")
    if not isinstance(key, str) or len(key) > 255:
        fail()
    body_value = canonical(body)
    for entry in store:
        if (entry["user_id"], entry["path"], entry["key"]) == (uid, path, key):
            if entry["body"] != body_value:
                fail(409, "idempotency_key_reuse")
            return copy.deepcopy(entry["response"])
    return None


def _idempotency_store(store, uid, path, key, body, response):
    store.append({"user_id": uid, "path": path, "key": key,
                  "body": canonical(body), "response": copy.deepcopy(response)})


def _statement(uid, query):
    _ensure_revisions()
    if "snapshot" in query:
        if any(name in query for name in ("from", "to", "known_at")):
            fail()
        token = query.get("snapshot", [""])[0]
        snap = STAGE3_META["snapshots"].get(token)
        if snap is None or snap["user_id"] != uid:
            fail(404, "not_found")
        limit, offset = pagination(query)
        full = copy.deepcopy(snap["response"])
        entries = full["entries"]
        full["entries"] = entries[offset:offset + limit]
        full["has_more"] = offset + limit < len(entries)
        return full

    read_at = request_clock()
    known_text = query.get("known_at", [None])[0]
    known_at = _parse_instant(known_text) if known_text is not None else read_at
    from_text = query.get("from", [None])[0]
    to_text = query.get("to", [None])[0]
    start = _parse_instant(from_text) if from_text is not None else dt.datetime.min.replace(tzinfo=dt.timezone.utc)
    end = _parse_instant(to_text) if to_text is not None else read_at
    if start > end:
        fail()
    limit, offset = pagination(query)

    opening = _historical_total(uid, start, known_at, inclusive=False)
    closing = _historical_total(uid, end, known_at, inclusive=False)
    selected = []
    for pid, payment in STATE["payments"].items():
        if uid not in (payment["from_user_id"], payment["to_user_id"]):
            continue
        revision = _selected_revision(pid, known_at)
        if revision is None:
            continue
        effective = _parse_instant(revision["effective_at"])
        if start <= effective < end:
            selected.append((effective, pid, payment, revision))
    selected.sort(key=lambda item: (item[0], item[1]))

    running = opening
    entries = []
    for _, _, payment, revision in selected:
        delta = _payment_delta(payment, revision, uid)
        running += delta
        view = copy.deepcopy(payment)
        view["amount"] = revision["amount"]
        entries.append({"payment": view, "delta": delta, "balance_after": running,
                        "revision": revision["revision"], "effective_at": revision["effective_at"],
                        "recorded_at": revision["recorded_at"]})

    token = identifier("snap_")
    response = {"opening_balance": opening, "entries": entries, "closing_balance": closing,
                "has_more": offset + limit < len(entries), "snapshot": token}
    if known_text is not None:
        response["known_at"] = known_text
    STAGE3_META["snapshots"][token] = {"user_id": uid, "response": copy.deepcopy(response)}
    response["entries"] = entries[offset:offset + limit]
    return response


def _correction(uid, path, body, key):
    match = re.fullmatch(r"/payments/([^/]+)/corrections", path)
    if match is None:
        fail(404, "not_found")

    # Idempotency claim resolution precedes body/business validation.
    replay = _idempotency_lookup(STAGE3_META["correction_idempotency"], uid, path, key, body)
    if replay is not None:
        return 200, replay

    # This endpoint specifies validation_failed for all invalid fields/types.
    required = {"expected_revision", "amount", "effective_at", "reason"}
    if not required.issubset(body):
        fail()
    expected = integer(body.get("expected_revision"), 1, 1000000000)
    corrected_amount = integer(body.get("amount"), 0, 1000000000)
    effective_text = body.get("effective_at")
    effective = _parse_instant(effective_text)
    request_now = request_clock()
    if effective > request_now:
        fail()
    reason = body.get("reason")
    if not isinstance(reason, str) or not 1 <= len(reason) <= 200:
        fail()

    payment = STATE["payments"].get(match[1])
    if payment is None:
        fail(404, "not_found")
    if payment["from_user_id"] != uid:
        fail(403, "forbidden")
    if payment.get("settlement_id") is not None or payment.get("authorization_id") is not None or _stage4_is_refund(payment["payment_id"]):
        fail(422, "linked_payment_immutable")

    _ensure_revisions()
    history = STAGE3_META["revisions"][payment["payment_id"]]
    latest = history[-1]
    if expected != latest["revision"]:
        fail(409, "stale_revision")
    if _stage4_refunded_total(payment["payment_id"]) > corrected_amount:
        fail(422, "refund_exceeds_payment")

    difference = corrected_amount - latest["amount"]
    sender = STATE["users"][payment["from_user_id"]]
    receiver = STATE["users"][payment["to_user_id"]]
    if difference > 0:
        if available(STATE, sender["id"]) < difference:
            fail(409, "insufficient_funds")
        if receiver["balance"] + difference > MAX_BALANCE:
            fail()
    elif difference < 0:
        debit = -difference
        if available(STATE, receiver["id"]) < debit:
            fail(409, "insufficient_funds")
        if sender["balance"] + debit > MAX_BALANCE:
            fail()

    recorded = _strict_after(latest["recorded_at"])
    revision = {"payment_id": payment["payment_id"], "revision": latest["revision"] + 1,
                "amount": corrected_amount, "effective_at": effective_text,
                "recorded_at": recorded, "reason": reason, "correction_batch_id": None}
    history.append(revision)
    known_at = _parse_instant(recorded)
    if not _history_nonnegative(known_at, [effective]):
        history.pop()
        fail(409, "historical_overdraft")

    if difference > 0:
        sender["balance"] -= difference
        receiver["balance"] += difference
    elif difference < 0:
        debit = -difference
        receiver["balance"] -= debit
        sender["balance"] += debit

    response = copy.deepcopy(revision)
    _idempotency_store(STAGE3_META["correction_idempotency"], uid, path, key, body, response)
    return 201, response


def _sync_stage3_after(method, path, response):
    _ensure_revisions()
    if method == "POST":
        action = re.fullmatch(r"/authorizations/([^/]+)/(capture|void)", path)
        if action:
            record = STATE["authorizations"].get(action[1])
            if record is not None and record["status"] in {"captured", "voided"}:
                if record["status"] == "captured" and record.get("payment_ids"):
                    last_payment = STATE["payments"].get(record["payment_ids"][-1])
                    closed = last_payment["created_at"] if last_payment else now()
                else:
                    closed = now()
                STAGE3_META["auth_closed"].setdefault(record["authorization_id"], closed)
    if path == "/authorizations":
        if isinstance(response, dict) and "authorizations" in response:
            response = copy.deepcopy(response)
            response["authorizations"] = [_decorate_authorization(item) for item in response["authorizations"]]
        else:
            response = _decorate_authorization(response)
    else:
        action = re.fullmatch(r"/authorizations/([^/]+)/(capture|void)", path)
        if action and isinstance(response, dict) and "authorization_id" in response:
            response = _decorate_authorization(response)
    return response


def stage3_dispatch(method, path, query, body, authorization, key):
    global STATE, STAGE3_META

    if method == "POST" and path == "/_test/reset":
        seed_times = _stage3_prepare_seed_times(body)
        status, response = stage2_dispatch(method, path, query, body, authorization, key)
        _stage3_apply_seed_times(seed_times)
        _stage3_reset_meta()
        _stage3_apply_seed_closed(seed_times)
        return status, response

    if method == "GET" and path == "/_test/export":
        status, response = stage2_dispatch(method, path, query, body, authorization, key)
        response = copy.deepcopy(response)
        response["stage3_meta"] = copy.deepcopy(STAGE3_META)
        return status, response

    if method == "POST" and path == "/_test/import":
        status, response = stage2_dispatch(method, path, query, body, authorization, key)
        meta = body.get("stage3_meta")
        if isinstance(meta, dict) and all(name in meta for name in _stage3_empty()):
            STAGE3_META = copy.deepcopy(meta)
            # Snapshot tokens are intentionally restored for a same-team Stage-3
            # export imported by Stage 4.
            _ensure_revisions()
        else:
            _stage3_reset_meta()
        return status, response

    correction_match = method == "POST" and re.fullmatch(r"/payments/[^/]+/corrections", path)
    if correction_match:
        uid = _auth_uid(authorization)
        return _correction(uid, path, body, key)

    revisions_match = method == "GET" and re.fullmatch(r"/payments/[^/]+/revisions", path)
    if revisions_match:
        uid = _auth_uid(authorization)
        pid = path.split("/")[2]
        payment = STATE["payments"].get(pid)
        if payment is None or uid not in (payment["from_user_id"], payment["to_user_id"]):
            fail(404, "not_found")
        _ensure_revisions()
        return 200, {"revisions": copy.deepcopy(STAGE3_META["revisions"][pid])}

    if method == "GET" and path == "/statement":
        uid = _auth_uid(authorization)
        return 200, _statement(uid, query)

    if method == "GET" and path == "/me" and ("as_of" in query or "known_at" in query):
        uid = _auth_uid(authorization)
        request_at = request_clock()
        as_text = query.get("as_of", [None])[0]
        known_text = query.get("known_at", [None])[0]
        as_of = _parse_instant(as_text) if as_text is not None else request_at
        known_at = _parse_instant(known_text) if known_text is not None else request_at
        user = STATE["users"][uid]
        total, hold, spendable = _historical_money(uid, as_of, known_at)
        result = {"user_id": uid, "display_name": user["display_name"], "handle": user["handle"],
                  "balance": total, "total": total, "available": spendable, "held": hold,
                  "currency": STATE["currency"], "minor_units": STATE["minor_units"]}
        if as_text is not None:
            result["as_of"] = as_text
        if known_text is not None:
            result["known_at"] = known_text
        return 200, result

    status, response = stage2_dispatch(method, path, query, body, authorization, key)
    response = _sync_stage3_after(method, path, response)
    return status, response


# ---------------------------------------------------------------------------
# Stage 4: refunds and atomic correction batches.
# Stage-4-only links/idempotency are kept in a sidecar so Stage-1/2/3 opaque
# exports remain import-compatible without changing the Stage-2 ledger schema.
# ---------------------------------------------------------------------------

def _stage4_empty():
    return {"refund_of": {}, "refund_idempotency": [], "batch_idempotency": [],
            "correction_batches": {}}


STAGE4_META = _stage4_empty()


def _stage4_is_refund(payment_id):
    return payment_id in STAGE4_META["refund_of"]


def _stage4_refunded_total(payment_id):
    total = 0
    for refund_id, target in STAGE4_META["refund_of"].items():
        if target == payment_id and refund_id in STATE["payments"]:
            total += STATE["payments"][refund_id]["amount"]
    return total


def _stage4_current_amount(payment_id):
    _ensure_revisions()
    history = STAGE3_META["revisions"].get(payment_id)
    return history[-1]["amount"] if history else STATE["payments"][payment_id]["amount"]


def _decorate_payment_stage4(value):
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            result[key] = _decorate_payment_stage4(item)
        if "payment_id" in value and "from_user_id" in value and "to_user_id" in value:
            result["refund_of"] = STAGE4_META["refund_of"].get(value["payment_id"])
        return result
    if isinstance(value, list):
        return [_decorate_payment_stage4(item) for item in value]
    return copy.deepcopy(value)


def _stage4_refund(uid, path, body, key):
    match = re.fullmatch(r"/payments/([^/]+)/refunds", path)
    if match is None:
        fail(404, "not_found")

    # Claimed idempotency keys resolve before endpoint validation/business checks.
    replay = _idempotency_lookup(STAGE4_META["refund_idempotency"], uid, path, key, body)
    if replay is not None:
        return 200, _decorate_payment_stage4(replay)

    value = amount(body)
    target_id = match[1]
    target = STATE["payments"].get(target_id)
    if target is None:
        fail(404, "not_found")
    if target["to_user_id"] != uid:
        fail(403, "forbidden")
    if _stage4_is_refund(target_id):
        fail(422, "invalid_refund_target")
    if _stage4_refunded_total(target_id) + value > _stage4_current_amount(target_id):
        fail(422, "refund_exceeds_payment")

    payer = STATE["users"][target["to_user_id"]]
    receiver = STATE["users"][target["from_user_id"]]
    if available(STATE, payer["id"]) < value:
        fail(409, "insufficient_funds")
    if receiver["balance"] + value > MAX_BALANCE:
        fail()

    record = payment_record(STATE, payer, receiver, value, target["note"], target["visibility"],
                            timestamp=now())
    record["request_id"] = None
    record["settlement_id"] = None
    record["authorization_id"] = None

    payer["balance"] -= value
    receiver["balance"] += value
    STATE["payments"][record["payment_id"]] = record
    STAGE4_META["refund_of"][record["payment_id"]] = target_id
    _ensure_revisions()

    response = _decorate_payment_stage4(record)
    _idempotency_store(STAGE4_META["refund_idempotency"], uid, path, key, body, response)
    return 201, response


def _stage4_batch_item(raw):
    if not isinstance(raw, dict):
        fail()
    required = {"payment_id", "expected_revision", "amount", "effective_at", "reason"}
    if not required.issubset(raw):
        fail()

    pid = raw.get("payment_id")
    if not isinstance(pid, str):
        fail()
    expected = integer(raw.get("expected_revision"), 1, 1000000000)
    corrected = integer(raw.get("amount"), 0, 1000000000)
    effective_text = raw.get("effective_at")
    effective = _parse_instant(effective_text)
    if effective > request_clock():
        fail()
    reason = raw.get("reason")
    if not isinstance(reason, str) or not 1 <= len(reason) <= 200:
        fail()

    payment = STATE["payments"].get(pid)
    if payment is None:
        fail(404, "not_found")
    if payment.get("authorization_id") is not None or _stage4_is_refund(pid):
        fail(422, "linked_payment_immutable")

    _ensure_revisions()
    latest = STAGE3_META["revisions"][pid][-1]
    if expected != latest["revision"]:
        fail(409, "stale_revision")
    if _stage4_refunded_total(pid) > corrected:
        fail(422, "refund_exceeds_payment")

    return {"payment": payment, "pid": pid, "latest": latest, "amount": corrected,
            "effective_at": effective_text, "effective": effective, "reason": reason}


def _stage4_batch(uid, body, key):
    if uid not in STATE["operators"]:
        fail(403, "forbidden")

    replay = _idempotency_lookup(STAGE4_META["batch_idempotency"], uid, "/correction-batches", key, body)
    if replay is not None:
        return 200, copy.deepcopy(replay)

    raw_items = body.get("corrections")
    if not isinstance(raw_items, list) or not 1 <= len(raw_items) <= 32:
        fail()
    ids = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            fail()
        ids.append(raw.get("payment_id"))
    if any(not isinstance(pid, str) for pid in ids) or len(set(ids)) != len(ids):
        fail()

    # Per-item validation/error precedence is input order.
    items = [_stage4_batch_item(raw) for raw in raw_items]
    included = set(ids)

    # Settlement completeness and shared effective instant.
    settlements = {}
    for item in items:
        sid = item["payment"].get("settlement_id")
        if sid is not None:
            settlements.setdefault(sid, []).append(item)
    for sid, members in settlements.items():
        settlement = STATE["settlements"].get(sid)
        if settlement is None:
            fail(422, "incomplete_settlement")
        member_ids = {p["payment_id"] for p in settlement["payments"]}
        if not member_ids.issubset(included):
            fail(422, "incomplete_settlement")
        instants = {_parse_instant(item["effective_at"]) for item in members}
        if len(instants) != 1:
            fail()

    # Compute one atomic current-balance change for the whole batch.
    deltas = {}
    for item in items:
        payment, latest = item["payment"], item["latest"]
        diff = item["amount"] - latest["amount"]
        if diff:
            deltas[payment["from_user_id"]] = deltas.get(payment["from_user_id"], 0) - diff
            deltas[payment["to_user_id"]] = deltas.get(payment["to_user_id"], 0) + diff

    proposed_balances = {uid2: user["balance"] + deltas.get(uid2, 0)
                         for uid2, user in STATE["users"].items()}
    for uid2, balance in proposed_balances.items():
        if balance < held(STATE, uid2):
            fail(409, "insufficient_funds")
        if balance > MAX_BALANCE:
            fail()

    # All revisions in one batch share a single recorded_at strictly later than
    # the prior revision of every member.
    recorded_dt = request_clock()
    for item in items:
        prior = _parse_instant(item["latest"]["recorded_at"])
        if recorded_dt <= prior:
            recorded_dt = prior + dt.timedelta(microseconds=1)
    recorded = recorded_dt.isoformat(timespec="microseconds")
    batch_id = identifier("cb_")

    revisions = []
    for item in items:
        latest = item["latest"]
        revision = {"payment_id": item["pid"], "revision": latest["revision"] + 1,
                    "amount": item["amount"], "effective_at": item["effective_at"],
                    "recorded_at": recorded, "reason": item["reason"],
                    "correction_batch_id": batch_id}
        STAGE3_META["revisions"][item["pid"]].append(revision)
        revisions.append(revision)

    if not _history_nonnegative(_parse_instant(recorded), [item["effective"] for item in items]):
        for item in items:
            STAGE3_META["revisions"][item["pid"]].pop()
        fail(409, "historical_overdraft")

    for uid2, balance in proposed_balances.items():
        STATE["users"][uid2]["balance"] = balance

    response = {"correction_batch_id": batch_id, "recorded_at": recorded,
                "revisions": copy.deepcopy(revisions)}
    STAGE4_META["correction_batches"][batch_id] = copy.deepcopy(response)
    _idempotency_store(STAGE4_META["batch_idempotency"], uid, "/correction-batches", key, body, response)
    return 201, response


def dispatch(method, path, query, body, authorization, key):
    global STAGE4_META

    if method == "POST" and path == "/_test/reset":
        status, response = stage3_dispatch(method, path, query, body, authorization, key)
        STAGE4_META = _stage4_empty()
        return status, response

    if method == "GET" and path == "/_test/export":
        status, response = stage3_dispatch(method, path, query, body, authorization, key)
        response = copy.deepcopy(response)
        response["stage4_meta"] = copy.deepcopy(STAGE4_META)
        return status, response

    if method == "POST" and path == "/_test/import":
        status, response = stage3_dispatch(method, path, query, body, authorization, key)
        meta = body.get("stage4_meta")
        if isinstance(meta, dict) and all(name in meta for name in _stage4_empty()):
            STAGE4_META = copy.deepcopy(meta)
        else:
            STAGE4_META = _stage4_empty()
        return status, response

    if method == "POST" and re.fullmatch(r"/payments/[^/]+/refunds", path):
        uid = _auth_uid(authorization)
        return _stage4_refund(uid, path, body, key)

    if method == "POST" and path == "/correction-batches":
        uid = _auth_uid(authorization)
        status, response = _stage4_batch(uid, body, key)
        return status, copy.deepcopy(response)

    status, response = stage3_dispatch(method, path, query, body, authorization, key)
    return status, _decorate_payment_stage4(response)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Do not log bearer tokens, passwords, or private test snapshots.

    def handle_api(self):
        # One monotonic UTC clock read per HTTP request. All timestamps and
        # expiry decisions inside this request derive from this exact instant.
        REQUEST_CLOCK.value = _next_request_clock()
        try:
            path = urlsplit(self.path).path
            if self.command == "GET" and (path in {"/", "/split", "/signup", "/login"} or path in {"/requests", "/authorizations"} and "text/html" in self.headers.get("Accept", "")):
                return self.asset("index.html", "text/html; charset=utf-8")
            if self.command == "GET" and path in {"/assets/app.js", "/assets/style.css"}:
                return self.asset(path.rsplit("/", 1)[1], "text/javascript; charset=utf-8" if path.endswith(".js") else "text/css; charset=utf-8")
            length = self.headers.get("Content-Length", "0")
            if not re.fullmatch(r"[0-9]+", length):
                fail(400, "malformed_request")
            raw = self.rfile.read(int(length))
            body = {}
            if raw:
                try:
                    body = json.loads(raw.decode("utf-8"), parse_float=JSONNumber,
                                      parse_constant=lambda _: fail(400, "malformed_request"))
                except (ValueError, UnicodeError, ArithmeticError, RecursionError):
                    fail(400, "malformed_request")
                object_value(body)
            elif self.command == "POST":
                empty_path = urlsplit(self.path).path
                # Some write contracts use an empty JSON object as a meaningful
                # default body, while Stage 3/4 field-validation endpoints must
                # receive {} so they can return validation_failed rather than a
                # transport-level malformed_request.
                empty_allowed = (
                    re.fullmatch(r"/requests/[^/]+/(pay|decline|cancel)", empty_path)
                    or re.fullmatch(r"/authorizations/[^/]+/(capture|void)", empty_path)
                    or re.fullmatch(r"/payments/[^/]+/(corrections|refunds)", empty_path)
                    or empty_path == "/correction-batches"
                )
                if not empty_allowed:
                    fail(400, "malformed_request")
            url = urlsplit(self.path)
            if self.command == "POST" and url.path in {"/auth/signup", "/auth/login"}:
                status, response = authentication(url.path, body)
            else:
                with LOCK:
                    status, response = dispatch(self.command, url.path, parse_qs(url.query, keep_blank_values=True), body,
                                                self.headers.get("Authorization"), self.headers.get("Idempotency-Key"))
            encoded = b"" if response is None else json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        except APIError as error:
            status = error.status
            encoded = json.dumps({"error": {"code": error.code, "message": error.message}}).encode()
        except (ValueError, TypeError, KeyError, ArithmeticError, RecursionError):
            status = 400
            encoded = b'{"error":{"code":"malformed_request","message":"Invalid request"}}'
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(encoded)

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = do_HEAD = handle_api

    def asset(self, name, content_type):
        encoded = (Path(__file__).parent / "static" / name).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(encoded)

    def send_error(self, code, message=None, explain=None):
        encoded = json.dumps({"error": {"code": "malformed_request", "message": message or "Invalid request"}}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(encoded)


class Server(ThreadingHTTPServer):
    request_queue_size = 128


if __name__ == "__main__":
    server = Server(("0.0.0.0", int(os.environ.get("PORT", "8080"))), Handler)
    server.daemon_threads = True
    server.serve_forever()
