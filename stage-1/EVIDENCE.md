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

## Repair #6: missing required arrays

This addendum preserves the original evidence above and supersedes its
"no remaining product defect observed" statement for the rejected candidate
`e6df7a668de6c0c051116507e4d6c30bf03d2a40`. Integrator independently identified two
manifestations of the required-array validation defect. Fabricator reproduced
them before editing source:

| Request | Rejected candidate observed | Required/repaired response |
| --- | --- | --- |
| Authenticated POST /splits, valid key, body `{"amount":1}` | 400 malformed_request | 422 validation_failed |
| Unauthenticated POST /_test/reset, body `{"currency":"EUR","minor_units":2}` | 400 malformed_request | 422 validation_failed |

Both failure reproductions left exported state unchanged. Root cause:
`array_field` treated an absent required field like a present field of the wrong
type. The scoped source repair adds an absence check before type validation.
Explicit null, boolean, number, string or object values still produce 400
malformed_request. Optional fixture payments, requests and settlement_operator_ids
still default to empty when omitted. No other product source changed.

Integrator's unchanged independent harness was read and executed from
`C:\Users\DELL\Documents\ALIVE FACTORY\pocketful-integrator-checks.py`.
Its original evidence remains at
`C:\Users\DELL\Documents\ALIVE FACTORY\pocketful-integrator-e6df7a6-evidence.md`;
Fabricator did not edit either file. The local checks.py adds HTTP regressions for
both omissions, five present wrong-type values on required and optional arrays,
unchanged snapshots after each error, reusable failed split keys and optional
fixture defaults, followed by snapshot restoration and the existing full suite.

Before the repair, these commands reproduced Integrator's two failing groups
(771 HTTP checks, exit 1, maximum measured request 0.107 seconds):

```sh
docker --context desktop-linux build -t pocketful-fabricator:repair-repro ./stage-1
docker --context desktop-linux run -d --name pocketful-fabricator-repair-repro --network none --cpus=2 --memory=2g -e PORT=18778 pocketful-fabricator:repair-repro
docker --context desktop-linux cp 'C:\Users\DELL\Documents\ALIVE FACTORY\pocketful-integrator-checks.py' pocketful-fabricator-repair-repro:/tmp/integration.py
docker --context desktop-linux exec pocketful-fabricator-repair-repro python /tmp/integration.py http://127.0.0.1:18778 http://127.0.0.1:18778
```

After the repair, compilation/build/whitespace checks passed. The following
commands passed on the repaired service (all test runs exited 0):

```sh
python -m py_compile stage-1/service.py stage-1/checks.py
git diff --check
docker --context desktop-linux build -t pocketful-fabricator:repair ./stage-1
docker --context desktop-linux run -d --name pocketful-fabricator-repair --network none --cpus=2 --memory=2g -e PORT=18778 pocketful-fabricator:repair
docker --context desktop-linux cp 'C:\Users\DELL\Documents\ALIVE FACTORY\pocketful-integrator-checks.py' pocketful-fabricator-repair:/tmp/integration.py
docker --context desktop-linux exec pocketful-fabricator-repair python /tmp/integration.py http://127.0.0.1:18778 http://127.0.0.1:18778
docker --context desktop-linux cp stage-1/checks.py pocketful-fabricator-repair:/tmp/checks.py
docker --context desktop-linux exec pocketful-fabricator-repair python /tmp/checks.py http://127.0.0.1:18778
docker --context desktop-linux run -d --name pocketful-fabricator-repair-source -p 18280:8080 --cpus=2 --memory=2g pocketful-fabricator:repair
docker --context desktop-linux run -d --name pocketful-fabricator-repair-destination -p 18291:8091 -e PORT=8091 --cpus=2 --memory=2g pocketful-fabricator:repair
python stage-1/checks.py http://127.0.0.1:18280 http://127.0.0.1:18291
python 'C:\Users\DELL\Documents\ALIVE FACTORY\pocketful-integrator-checks.py' http://127.0.0.1:18280 http://127.0.0.1:18291
```

Observed repaired results:

- Integrator's supplied suite: 771 checks, all nine groups passed, zero failed
  groups in each configuration. Maximum measured request 0.164 seconds offline
  and 0.172 seconds across separate mapped containers.
- Expanded Fabricator suite: 668 checks passed in each configuration, including
  the new required/optional array HTTP regressions and all original endpoint,
  concurrency, state continuity and arithmetic checks.
- Both exact missing-field reproductions now returned 422 validation_failed.
- Image `sha256:c89ce0fa67f21b20e3ebc082608dca8ea48752ae62427602ef6003fbb883c337`
  was used by all repaired containers. Inspection confirmed 2 CPU/2 GiB limits
  and the offline container's network mode none. Service logs were empty.
- All four Fabricator repair/repro containers were removed. No private snapshot
  or token artifacts were written to Git or the room.

Coverage delta is specification section 5's missing-field/type distinction, used
by section 8's split participant list and sections 3/4's reset users fixture.
All original sections 1–11 remain implemented; the unchanged Integrator suite
and expanded local suite were fully rerun. No additional product defect was
observed in these runs. Existing global-lock/ephemeral-state and unbounded-load
limitations remain. These executions by Fabricator are repair evidence, not a
new independent acceptance decision.

Next action: Foreman supplies the exact new repair SHA to Integrator for renewed
independent verification, then routes Test Pilot and Inspector on that tested
revision. No self-acceptance is claimed.

## Repair #7: Inspector R1/R2 and observed login timing

Rejected predecessor: `998dc1ae32db14f7be18ce3369393fa17e59c7f0`. Inspector's
unchanged decision/probe/log remain at
`C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-1-inspector`.
Fabricator read the decision and executable probe, reproduced before editing,
and read the complete authoritative spec again. The first probe invocation
preceded container readiness and refused the connection; its ready-container
rerun reproduced all 15 cases, exit 1: fourteen reset type misclassifications and
one contradictory imported payment retry body. The malformed reset candidates
left state unchanged; the contradictory import returned 204 and changed state,
then the altered amount-9 retry returned the original amount-1 receipt.

R1 repair introduces fixture-specific numeric and ID field validators, keeping
omission (422), present wrong type (400), and correct-type invalid value (422)
separate. This applies to minor_units, user balances/IDs, payment/request IDs and
user references, and operator array members. Fixture object/array/string fields
retain their type checks; amount/note/visibility retain their 422 exceptions.
Linked seeded paid requests validate and bind their referenced payment so the
service's own resulting export remains importable. Every failed reset builds a
detached candidate and leaves live state unchanged.

R2 repair decodes each canonical successful request body and validates its
operation-specific meaning against its original receipt and current immutable
resource fields: direct payments, request creation, request pay, splits and
settlements. It checks path, actor, operator permission, recipient/payer, amount,
note, visibility, input order, defaults, exact shares, generated requests/payments,
and absence of duplicate creation claims. Original pending receipts remain valid
after requests become terminal. Current balances and request-pending status are
not re-executed for historical operations. Canonical JSON comparisons distinguish
booleans from numbers in receipts while preserving numeric equivalence and
ignored unknown request fields. Invalid imported state remains 422 with rollback.

The full checks also exposed two initial five-second timeouts in 50 concurrent
logins, followed by an isolated successful rerun. Old containers logged broken
pipes from the clients that timed out. This was not omitted as a passing check.
The repair moves login/signup scrypt work outside the transaction lock without
weakening its parameters. Account/session commits remain locked; login retries
credential verification if reset/import replaced its state/account during scrypt,
preventing stale session installation. Final suites include 50 concurrent logins
and 49 password checks racing one reset, with no stale users/tokens afterward.

New HTTP-only `repair_checks.py` tests the broad scalar/ID/reference/array-member
omission/type/value matrix and full-state rollback. It corrupts canonical bodies,
receipts, associated resources, path, method, actor, permission and duplicate
creation claims across all five successful paths. Positive controls preserve
unchanged portable exports, numeric forms, unknown fractional fields, optional
defaults, array ordering, terminal request original receipts and zero-share pay.

Final source SHA-256, identical on host and in the tested image:
`b042e6e93f4ee510f59b03284af8fe1b35252e58559e50a50620fc2af486ac05`.
Final image: `sha256:cf2504d7795ce1b4526fbc913672d93c0617aef97c5cae6c0ae474ab4fa0030b`.

Commands were separate PowerShell commands from the repository root:

```text
python -m py_compile stage-1/service.py stage-1/checks.py stage-1/repair_checks.py
git diff --check
docker --context desktop-linux build -t pocketful-fabricator:r7-repro ./stage-1
docker --context desktop-linux run -d --name pocketful-fabricator-r7-repro --network none --cpus=2 --memory=2g -e PORT=18879 pocketful-fabricator:r7-repro
docker --context desktop-linux cp 'C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-1-inspector\probe-998dc1a.py' pocketful-fabricator-r7-repro:/tmp/inspector.py
docker --context desktop-linux exec pocketful-fabricator-r7-repro python /tmp/inspector.py 18879
docker --context desktop-linux build -t pocketful-fabricator:r7 ./stage-1
docker --context desktop-linux run -d --name pocketful-fabricator-r7 --network none --cpus=2 --memory=2g -e PORT=18879 pocketful-fabricator:r7
docker --context desktop-linux cp stage-1/checks.py pocketful-fabricator-r7:/tmp/checks.py
docker --context desktop-linux cp stage-1/repair_checks.py pocketful-fabricator-r7:/tmp/repair_checks.py
docker --context desktop-linux cp 'C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-1-inspector\probe-998dc1a.py' pocketful-fabricator-r7:/tmp/inspector.py
docker --context desktop-linux cp 'C:\Users\DELL\Documents\ALIVE FACTORY\pocketful-integrator-checks.py' pocketful-fabricator-r7:/tmp/integration.py
docker --context desktop-linux exec pocketful-fabricator-r7 python /tmp/checks.py http://127.0.0.1:18879
docker --context desktop-linux exec pocketful-fabricator-r7 python /tmp/repair_checks.py http://127.0.0.1:18879
docker --context desktop-linux exec pocketful-fabricator-r7 python /tmp/inspector.py 18879
docker --context desktop-linux exec pocketful-fabricator-r7 python /tmp/integration.py http://127.0.0.1:18879 http://127.0.0.1:18879
docker --context desktop-linux run -d --name pocketful-fabricator-r7-source -p 18380:8080 --cpus=2 --memory=2g pocketful-fabricator:r7
docker --context desktop-linux run -d --name pocketful-fabricator-r7-destination -e PORT=8091 -p 18391:8091 --cpus=2 --memory=2g pocketful-fabricator:r7
python stage-1/checks.py http://127.0.0.1:18380 http://127.0.0.1:18391
python stage-1/repair_checks.py http://127.0.0.1:18380 http://127.0.0.1:18391
python 'C:\Users\DELL\Documents\ALIVE FACTORY\pocketful-integrator-checks.py' http://127.0.0.1:18380 http://127.0.0.1:18391
Get-FileHash stage-1/service.py -Algorithm SHA256
docker --context desktop-linux exec pocketful-fabricator-r7 sha256sum /app/service.py
```

Final observed results (after the authentication timing repair):

| Suite | Network none | Separate mapped containers |
| --- | --- | --- |
| Unchanged Inspector probe | 0 failed cases, missing-field and unchanged-import controls passed, exit 0 | Not rerun here; renewed independent gate remains required |
| Unchanged Integrator harness, executed by Fabricator | 771 checks, 9 groups passed, max request 0.730 seconds | 771 checks, 9 groups passed, max request 0.265 seconds |
| Existing Fabricator checks | 668 checks passed, including 50 concurrent logins | 668 checks passed, including 50 concurrent logins |
| New repair boundary suite | 535 checks passed, max request 0.645 seconds | 535 checks passed, max request 1.485 seconds |

Compilation, build and whitespace checks passed. All final runs exited 0; final
container logs were empty. Resource inspection confirmed 2,000,000,000 NanoCPUs,
2,147,483,648 bytes memory, no mounts, and network none for the offline container.
All four Fabricator R7 containers were removed. Private snapshots, hashes and
tokens remained in test-process memory and were never written/shared.

Coverage delta: §§3/4/5 fixture/reset validation; §§7/8/9/10/11 imported completed
operation semantics and portable continuity; §§2/6 concurrency timing and
authentication/control races. Original §§1–11 behavior was exercised by the full
reruns. No remaining defect observed in final checks. Unbounded data growth and
sustained load remain unbenchmarked; transaction work is still serialized and
state remains ephemeral. Authentication hash work is now outside that lock.
The stock judging CLI issue noted by Inspector is not claimed repaired or scored
here. Executing peer probes is Fabricator repair evidence, not independent
verification or acceptance.

The exact repaired Git SHA and six-field handoff are also recorded at
`C:\Users\DELL\Documents\ALIVE FACTORY\pocketful-fabricator-repair-7-evidence.md`
and shared task #7. Foreman next routes that SHA through renewed Integrator and
Test Pilot checks, then Inspector. Shipper remains gated until independent
acceptance. No self-acceptance is claimed.

## Repair #8: documented reset schema and ignored request linkage

Blocked predecessor: `7d72f8054d19e8bfe3d91c5c8f28fcbaeae115fe`, Foreman's
documentation-only child of R7. Full independent report read:
`C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-integrator-7d72f80\report.md`.
Unchanged HTTP seeded reproducer and adapter:
`C:\Users\DELL\Documents\ALIVE FACTORY\pocketful-integrator-seeded-roundtrip.py`
and `C:\Users\DELL\Documents\ALIVE FACTORY\pocketful-integrator-r1-r2.py`.

Before edits, Fabricator reproduced twelve reset failures out of seventeen cases
in a 2 CPU/2 GiB, network-none container: string/bool/object unknown payment_id
members were rejected for each legal request status. Five positive controls
passed; 32 HTTP calls, exit1. These were reset acceptance failures, not observed
import failures: rejected cases never reached import.

Correction removes reading/validation of the undocumented fixture request
payment_id. Reset ignores this member regardless of value/status. Seeded request
response linkage remains null; API-created links and opaque export/import keep
their existing validation. The R7 text describing seeded-link validation records
old behavior and is superseded by this correction. No import/authentication or
transaction logic changed.

Meaningful source/test repair commit: `16eda9cd810ff3c595a0e976a10d06f62c539b8f`.
Host/image service SHA-256 matched:
`63d85c0239eb61c3fd614dc4b251581e08095e49c7ec873a9a3e2b9134de0a38`.
Image: `sha256:35293759ccc51e98ee3140427852c17651cc791a66c99858810524606c2bd147`.
This evidence update changes documentation only.

Initial repaired offline observation: unchanged seeded script passed17 cases /
68 calls; every case reset204 and unchanged-import204. Expanded repair suite
passed653 calls, max0.206s. It checks seven ignored linkage values across all four
statuses, other unknown response/link fields, unchanged net balances, seeded
portable round trips, and API-created links/replay after import. Existing R1/R2
guards and auth/control races remain. Call counts can vary with token-race timing.

Commands (scripts copied unchanged into /tmp as r1r2.py, seeded.py, repair.py):

```text
docker --context desktop-linux build -t pocketful-fabricator:r8-repro ./stage-1
docker --context desktop-linux run -d --name pocketful-fabricator-r8-repro --network none --cpus=2 --memory=2g -e PORT=18882 pocketful-fabricator:r8-repro
docker --context desktop-linux exec pocketful-fabricator-r8-repro python /tmp/seeded.py --source http://127.0.0.1:18882 --destination http://127.0.0.1:18882
python -m py_compile stage-1/service.py stage-1/repair_checks.py
git diff --check
docker --context desktop-linux build -t pocketful-fabricator:r8 ./stage-1
docker --context desktop-linux run -d --name pocketful-fabricator-r8-offline --network none --cpus=2 --memory=2g -e PORT=18882 pocketful-fabricator:r8
docker --context desktop-linux exec pocketful-fabricator-r8-offline python /tmp/seeded.py --source http://127.0.0.1:18882 --destination http://127.0.0.1:18882
docker --context desktop-linux exec pocketful-fabricator-r8-offline python /tmp/repair.py http://127.0.0.1:18882
```

Final exact SHA, full separate-container/offline rerun results, commands and
risks are retained in the six-field report at
`C:\Users\DELL\Documents\ALIVE FACTORY\pocketful-fabricator-repair-8-evidence.md`,
also linked in #8 and Foreman's visible handoff. Private snapshots remain in RAM.
Foreman next routes the repaired exact SHA through renewed Integrator/Test Pilot
checks and then Inspector. No acceptance is claimed.
