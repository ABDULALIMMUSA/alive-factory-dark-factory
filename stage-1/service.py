"""Pocketful: single-process transactional, exact-minor-unit HTTP service."""
import copy
import datetime as dt
from decimal import Decimal
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import re
import secrets
import threading
from urllib.parse import urlsplit, parse_qs

MAX_BALANCE = 2 ** 53
LOCK = threading.RLock()
HANDLE = re.compile(r"[a-z0-9_]{1,20}\Z")
EMAIL = re.compile(r"[^\s@]+@[^\s@]+\Z")
STATUSES = {"pending", "paid", "declined", "cancelled"}


class APIError(Exception):
    def __init__(self, status=422, code="validation_failed", message="Invalid request"):
        self.status, self.code, self.message = status, code, message


def fail(status=422, code="validation_failed", message="Invalid request"):
    raise APIError(status, code, message)


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")


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
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        fail()
    if isinstance(value, Decimal) and (not value.is_finite() or value != value.to_integral_value()):
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
    if isinstance(value, (int, Decimal)):
        number = Decimal(value)
        sign, digits, exponent = number.as_tuple()
        digits = list(digits)
        if not any(digits):
            return ["number", "0"]
        while digits[-1] == 0:
            digits.pop()
            exponent += 1
        return ["number", ("-" if sign else "") + "".join(map(str, digits)) + "e" + str(exponent)]
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


def blank_state():
    return {"schema": 1, "currency": "EUR", "minor_units": 2, "seeded_total": 0,
            "users": {}, "tokens": {}, "payments": {}, "requests": {},
            "settlements": {}, "operators": [], "idempotency": []}


STATE = blank_state()


def validate_id(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 64:
        fail()
    return value


def currency_fields(body):
    currency = string(body, "currency")
    units = integer(body.get("minor_units"), 0, 3)
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
    return {"payment_id": payment_id or identifier("p_"), "from_user_id": sender["id"],
            "from_handle": sender["handle"], "to_user_id": receiver["id"], "to_handle": receiver["handle"],
            "amount": value, "currency": state["currency"], "note": memo, "visibility": scope,
            "request_id": request_id, "settlement_id": settlement_id, "created_at": timestamp or now()}


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
        uid = validate_id(raw.get("id"))
        email, handle = string(raw, "email"), handle_field(raw, "handle")
        if not EMAIL.fullmatch(email) or uid in state["users"] or email in emails or handle in handles:
            fail()
        user = {"id": uid, "email": email, "display_name": string(raw, "display_name"), "handle": handle,
                "balance": integer(raw.get("balance"), 0, MAX_BALANCE), "password_hash": password_hash(string(raw, "password"))}
        state["users"][uid] = user
        emails.add(email)
        handles.add(handle)
    state["seeded_total"] = sum(user["balance"] for user in state["users"].values())
    state["operators"] = array_field(body, "settlement_operator_ids", [])
    if any(not isinstance(uid, str) or uid not in state["users"] for uid in state["operators"]):
        fail()
    timestamp = now()
    for raw in array_field(body, "payments", []):
        raw = object_value(raw)
        pid = validate_id(raw.get("id"))
        sender, receiver = state["users"].get(raw.get("from_user_id")), state["users"].get(raw.get("to_user_id"))
        if sender is None or receiver is None or sender is receiver or pid in state["payments"]:
            fail()
        state["payments"][pid] = payment_record(state, sender, receiver, amount(raw), note(raw), visibility(raw),
                                               timestamp, payment_id=pid)
    for raw in array_field(body, "requests", []):
        raw = object_value(raw)
        rid = validate_id(raw.get("id"))
        requester, payer = state["users"].get(raw.get("requester_id")), state["users"].get(raw.get("payer_id"))
        status = string(raw, "status")
        if requester is None or payer is None or requester is payer or rid in state["requests"] or status not in STATUSES:
            fail()
        record = request_record(state, requester, payer, integer(raw.get("amount"), 0, 1000000000), note(raw), timestamp, rid)
        record["status"] = status
        record["payment_id"] = raw.get("payment_id")
        state["requests"][rid] = record
    return state


def validate_snapshot(body):
    """Validate into a detached candidate; never alter live state during import."""
    try:
        if body.get("track") != "pocketful" or type(body.get("format_version")) is bool or body.get("format_version") != 1:
            fail()
        state = body["state"]
        if not isinstance(state, dict) or set(state) != set(blank_state()) or isinstance(state["schema"], bool) or state["schema"] != 1:
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
                if payment != state["payments"][payment["payment_id"]] or payment["settlement_id"] != sid or payment["request_id"] is not None or payment["created_at"] != settlement["committed_at"]:
                    fail()
        claimed = set()
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
            if {k: v for k, v in record.items() if k not in {"status", "payment_id"}} != {k: v for k, v in current.items() if k not in {"status", "payment_id"}}:
                fail()
        for entry in state["idempotency"]:
            identity = (entry["user_id"], entry["method"], entry["path"], entry["key"])
            if identity in claimed or entry["user_id"] not in state["users"] or entry["method"] != "POST" or not isinstance(entry["path"], str) or not isinstance(entry["key"], str) or not 1 <= len(entry["key"]) <= 255:
                fail()
            if not isinstance(entry["body"], list) or entry["body"][0] != "object" or not isinstance(entry["response"], dict):
                fail()
            canonical_tree(entry["body"])
            response, path = entry["response"], entry["path"]
            if path == "/payments" or re.fullmatch(r"/requests/[^/]+/pay", path):
                if response != state["payments"][response["payment_id"]] or response["from_user_id"] != entry["user_id"]:
                    fail()
                if path != "/payments" and response["request_id"] != path.split("/")[2]:
                    fail()
            elif path == "/requests":
                original_request(response)
                if response["requester_id"] != entry["user_id"]:
                    fail()
            elif path == "/settlements":
                if response != state["settlements"][response["settlement_id"]]:
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
            claimed.add(identity)
        # Stored API responses contain only integer numbers. Restore integer-valued
        # exponent/decimal encodings too, without ever rounding fractional input.
        def native(value):
            if isinstance(value, Decimal):
                return integer(value, -MAX_BALANCE * max(1, len(state["users"])), MAX_BALANCE * max(1, len(state["users"])))
            if isinstance(value, list):
                return [native(item) for item in value]
            if isinstance(value, dict):
                return {key: native(item) for key, item in value.items()}
            return value
        return native(state)
    except (KeyError, TypeError, ValueError, IndexError, AttributeError, OverflowError, APIError):
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
    if sender["balance"] < value:
        fail(409, "insufficient_funds")
    if receiver["balance"] + value > MAX_BALANCE:
        fail()
    record = payment_record(state, sender, receiver, value, memo, scope, request_id=request_id)
    sender["balance"] -= value
    receiver["balance"] += value
    state["payments"][record["payment_id"]] = record
    return record


def dispatch(method, path, query, body, authorization, key):
    global STATE
    if method == "GET" and path == "/health":
        return 200, {"status": "ok"}
    if method == "POST" and path == "/_test/reset":
        STATE = fixture_state(body)
        return 204, None
    if method == "GET" and path == "/_test/export":
        return 200, {"track": "pocketful", "format_version": 1, "state": copy.deepcopy(STATE)}
    if method == "POST" and path == "/_test/import":
        STATE = validate_snapshot(body)
        return 204, None
    state = STATE
    if method == "POST" and path in {"/auth/signup", "/auth/login"}:
        email, password = string(body, "email"), string(body, "password")
        user = next((u for u in state["users"].values() if u["email"] == email), None)
        if path == "/auth/signup":
            display = string(body, "display_name")
            if not EMAIL.fullmatch(email) or len(password) < 8:
                fail()
            if user is not None:
                fail(409, "email_taken")
            handle = re.sub(r"[^a-z0-9_]", "_", email.split("@", 1)[0].lower())[:20]
            if any(u["handle"] == handle for u in state["users"].values()):
                fail(409, "handle_taken")
            uid = identifier("u_")
            user = {"id": uid, "email": email, "display_name": display, "handle": handle, "balance": 0,
                    "password_hash": password_hash(password)}
            state["users"][uid] = user
            status = 201
        else:
            if user is None or not password_matches(password, user["password_hash"]):
                fail(401, "unauthenticated")
            status = 200
        token = secrets.token_urlsafe(32)
        state["tokens"][token] = user["id"]
        return status, {"user_id": user["id"], "display_name": user["display_name"], "token": token}
    match = re.fullmatch(r"Bearer ([^\s]+)", authorization or "", re.IGNORECASE)
    uid = state["tokens"].get(match[1]) if match else None
    if uid is None:
        fail(401, "unauthenticated")
    user = state["users"][uid]
    request_action = re.fullmatch(r"/requests/([^/]+)/(pay|decline|cancel)", path)
    idempotent = method == "POST" and (path in {"/payments", "/requests", "/splits", "/settlements"} or request_action and request_action[2] == "pay")
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
                     "balance": user["balance"], "currency": state["currency"], "minor_units": state["minor_units"]}
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
        if any(balance < 0 for balance in balances.values()):
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


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Do not log bearer tokens, passwords, or private test snapshots.

    def handle_api(self):
        try:
            length = self.headers.get("Content-Length", "0")
            if not re.fullmatch(r"[0-9]+", length):
                fail(400, "malformed_request")
            raw = self.rfile.read(int(length))
            body = {}
            if raw:
                try:
                    body = json.loads(raw.decode("utf-8"), parse_float=Decimal,
                                      parse_constant=lambda _: fail(400, "malformed_request"))
                except (ValueError, UnicodeError, RecursionError):
                    fail(400, "malformed_request")
                object_value(body)
            elif self.command == "POST" and not re.fullmatch(r"/requests/[^/]+/(decline|cancel)", urlsplit(self.path).path):
                fail(400, "malformed_request")
            url = urlsplit(self.path)
            with LOCK:
                status, response = dispatch(self.command, url.path, parse_qs(url.query, keep_blank_values=True), body,
                                            self.headers.get("Authorization"), self.headers.get("Idempotency-Key"))
            encoded = b"" if response is None else json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        except APIError as error:
            status = error.status
            encoded = json.dumps({"error": {"code": error.code, "message": error.message}}).encode()
        except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
            status = 400
            encoded = b'{"error":{"code":"malformed_request","message":"Invalid request"}}'
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(encoded)

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = do_HEAD = handle_api

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
