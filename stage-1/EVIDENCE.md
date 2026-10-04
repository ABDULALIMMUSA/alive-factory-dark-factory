# Fabricator implementation evidence

Date: 2026-10-04. This is implementation evidence for independent verification;
it is not an acceptance decision. The exact handoff commit is supplied in the
room message. The prior implementation commit is `6dfd858`; no history was amended
or squashed. Foreman's existing `plan.md` remains intact.

The complete authoritative specification at
`C:\Users\DELL\Documents\ALIVE FACTORY\challenge\pocketful\spec\stage-1.md`
was read again before completion. No source code, API documentation, or schemas
from existing payment products were used.

| Spec section | Implementation and observed coverage |
| --- | --- |
| 1 Scope/invariants | All required HTTP operations; lock serializes state observation and mutations. Fifty distinct payment keys competing for 300 units produced exactly 30 successful ten-unit payments and 20 insufficient-funds errors, with 30 records/claims and balances 0/300/0. |
| 2 Delivery | Self-contained standard-library service, digest-pinned Python image, Dockerfile and RUN.md; non-root UID/GID 65534. Both test configurations used 2 CPUs and 2 GiB. Full checks passed with network disabled. |
| 3 Runtime | Default 8080 and configured 8091/18777, 0.0.0.0 listening, health, repeated atomic reset, JSON UTF-8 responses and offset-bearing timestamps. Final default-port cold start reached healthy in 2.011 seconds including Docker command overhead; fresh state was empty. |
| 4 Model | Exact Decimal input parsing and integer monetary arithmetic; derived handles and zero-balance signup; seed receipts do not debit balances again; over-balance pending requests; visibility limited to public or payment parties. All three currencies and the 2^53 balance boundary checked. |
| 5 Errors | Error envelope and required codes; malformed JSON/types, missing fields, amount/note/visibility exceptions, key length and decimal-only pagination checked. No 5xx or container error logs observed. |
| 6 Authentication | Salted scrypt hashes, login/signup validation, email/handle collision, multiple tokens; 50 simultaneous logins issued distinct valid sessions within ordinary five-second request timeouts. Import preserved passwords and tokens; reset invalidated both. |
| 7 Idempotency | Tagged canonical JSON values preserve exact number equality, key-order independence and omitted/default distinctions. Caller/method/path scoping; claimed-key precedence; immutable original receipts; failed-key reuse. For each of all five write paths, 50 simultaneous identical calls gave one 201 and 49 identical 200 responses. |
| 8 API | /me, payments, requests and pay/decline/cancel, filtered request lists, splits and activity; role authorization and competing terminal-state operations checked. Unicode note preserved verbatim; private payments seen by both parties and hidden from third party. |
| 9 Rounding | Quotient/remainder ordered shares, sum conservation, zeros that create and pay requests, caller-only splits and reordered participants tested. |
| 10 Export/import | Detached atomic snapshots; validated detached replacement; checks for structural, balance, password, token, canonical-body, cached-response and request/payment-link corruption. Invalid imports and negative resets left snapshots unchanged. Two independent containers preserved identity/timestamps, hashes, tokens, balances, all five original retry responses, operator permission and settlement membership; repeated import replaced rather than merged. |
| 11 Settlements | Operator-only batches, input-order entry errors before funds, net affordability including an outgoing entry from a zero-balance wallet funded by a later incoming entry; full rollback and reusable failed keys; member ordering, shared timestamps, null request_id and settlement_id links; replay/import preservation checked. |

## Commands and results

Run from `C:\Users\DELL\Documents\ALIVE FACTORY\pocketful-result`:

```sh
python -m py_compile stage-1/service.py stage-1/checks.py
docker --context desktop-linux build -t pocketful-stage-1 ./stage-1
docker --context desktop-linux run -d --name pocketful-fabricator-source -e PORT=8080 -p 18080:8080 --cpus=2 --memory=2g pocketful-stage-1
docker --context desktop-linux run -d --name pocketful-fabricator-destination -e PORT=8091 -p 18091:8091 --cpus=2 --memory=2g pocketful-stage-1
python stage-1/checks.py http://127.0.0.1:18080 http://127.0.0.1:18091
docker --context desktop-linux run -d --network none --name pocketful-fabricator-offline -e PORT=18777 --cpus=2 --memory=2g pocketful-stage-1
docker --context desktop-linux cp stage-1/checks.py pocketful-fabricator-offline:/tmp/checks.py
docker --context desktop-linux exec pocketful-fabricator-offline python /tmp/checks.py http://127.0.0.1:18777
git diff --check
```

Compilation, Docker build and whitespace check passed. Each final behavioral run
printed `PASS: 607 HTTP checks`, covering all five concurrent retry paths, competing
writes, request state races, settlements, portable snapshots and exact balance
boundaries. Ordinary HTTP requests use a five-second timeout and control requests
use ten seconds. Tests include assertions beyond the reported HTTP-check counter.
Final built image: `sha256:369ef9ce9361eebd0123e55a712ad45897026779963131d620af48f26889ee2e`.
Inspection confirmed all three containers used this image and the stated resource
limits; the offline container had network mode `none`. Container logs were empty.

A separate default-port cold start (no `-e PORT`) with host mapping 18080:8080
returned health in 2.011 seconds. Restart of the previous candidate also reached
health in 5.673 seconds and had empty state. Private export responses stayed in
test-process memory, with no snapshot files or room attachments. All Fabricator
test containers were removed at completion.

Early harness runs hit the service before it was ready; the harness now polls
health up to the permitted 60 seconds. Two auxiliary restart assertions had
PowerShell quoting/empty-property-count mistakes; corrected native JSON counts
verified users=0, tokens=0 and retries=0. These were check-invocation defects, and
no remaining product defect was observed in the final runs.

## Limits and next verification

State is intentionally ephemeral. The global lock serializes transactions and
password work; unbounded dataset sizes and sustained load beyond these checks are
not benchmarked. The checks are implementation-authored and do not replace an
independent specification review or the isolated judging harness. No acceptance
is claimed.

Foreman's next action is to route the exact handoff SHA to Integrator for independent
Docker lifecycle, concurrency, atomicity and portable-state verification. Repairs
and later seat packets remain routed by Foreman.
