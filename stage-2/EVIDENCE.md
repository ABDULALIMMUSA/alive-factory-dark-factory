# Stage 2 Fabricator evidence

Executed source revision: `8b9b564ed3538ebf3e29be20a2242dd52983d555`.
The evidence commit is a documentation child with unchanged runtime bytes.
Starting revision was Foreman's plan-only `05e39c0ea8e19ba02c88e2e99787119572ef85ab`,
above shipped Stage1 `65a56da7aa03c6690f12aa24c0dad372f2163437`.
Both complete authoritative specifications and the published Stage2 production
plan were read. Implementation and evidence changes are confined to stage-2.
This is a build-seat handoff, not an acceptance decision.

## Cumulative coverage

| Requirement | Implementation and exercised evidence |
|---|---|
| Stage1 §§1–4: scope, deployment, model, fixtures | Exact integer ledger, single unprivileged bundled image, configurable/default port, reset replacement and rollback, seeded history ignored unknown fields; existing Stage1 bytes preserved. |
| §5: validation and errors | Omission/type/value distinctions, endpoint amount/note/visibility exceptions, digit-only queries, malformed JSON, preserved R1/R3 guards; failure claims no key or state mutation. |
| §6: authentication | scrypt hashes, multiple bearer sessions, signup/handle collision, reset/import race recheck outside the money lock, imported hashes and tokens. |
| §7: retries | All seven caller/method/path-scoped paths; exact arbitrary numeric JSON identity, ordered arrays and defaults, replay before current validation/status, original immutable receipt, concurrent one201/rest200, reusable failed keys. |
| §§8–9: transfers, requests, splits, feed | Immediate transfers/request pay; lifecycle permissions and races; privacy and filtering; Unicode notes; ordered remainder/zero-share/caller-only splits; exact seeded conservation. |
| §10: portable state | Atomic validated replacement, native Stage2 and actual shipped Stage1 migration, sessions/hashes/operator permissions/original bodies and receipts, no process/address dependency, corrupt body/receipt/resource/actor/link/order/finality rejection. |
| §11: settlements | Input-order errors, operator-only access, atomic net affordability after incoming/outgoing effects, available-funds constraint under holds, original ordered batch receipts and links. |
| Stage2 browser screens and visual direction | Six routes; negotiated shared HTML/JSON routes; consistent calm visual system, available headline and total/held secondary, labels/focus styling, empty/loading/success/refused/uncertain feedback,375/1440px layouts. |
| Decimal forms and split preview | Integer decimal parsing for EUR/JPY/BHD without rounding, exact formatted/testid amounts, ordered shares and zero shares; successful actions refresh state. |
| Competing clients and uncertainty | Stable unchanged body/key after success or lost committed response, input preservation, changed fields new operation, refusal refresh, stale cancelled-request removal, latest wallet/feed/available/held refresh wins. |
| Existing signed-in browser after upgrade | Lost committed payment on actual shipped Stage1 retries after import without reload; old browser token/form/key remain, old pending request is payable. |
| Holds, TTL, expiry and API | Derived available=total-held; immediate paths use available; receiver-only capture/payer-only void; seeded absolute expiry/default TTL, remainder release; list directions/status/pagination and feed visibility. |
| Extended captures and concurrency | Partial/nonfinal/final/full remaining closes, cumulative/ordered/latest payment links, replay after closure/expiry, partial void/expiry release, bodyless/repeated void,50-worker holds/capture retries/reserve overspend/capture-versus-void. |

## Executed commands and observations

Full serial command arguments, exits and logs are under the local evidence root
`C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-fabricator-stage-2`.
The external runner is `C:\Users\DELL\Documents\ALIVE FACTORY\pocketful-fabricator-stage2-run.py`;
its final-v2/commands.json records the actual commands. Representative commands:

```sh
docker --context desktop-linux build -t pocketful-fabricator:stage2 ./stage-2
docker --context desktop-linux exec pocketful-fabricator-s2-client python /src/checks.py http://pocketful-fabricator-s2-source:18886 http://pocketful-fabricator-s2-destination:18887 http://pocketful-fabricator-s2-old:18888
docker --context desktop-linux exec pocketful-fabricator-s2-client python /src/numeric_checks.py http://pocketful-fabricator-s2-source:18886 http://pocketful-fabricator-s2-destination:18887
docker --context desktop-linux exec pocketful-fabricator-s2-client python /src/semantic_checks.py --source http://pocketful-fabricator-s2-source:18886 --destination http://pocketful-fabricator-s2-destination:18887 --revision 8b9b564ed3538ebf3e29be20a2242dd52983d555
```

| Final source check | Observed result |
|---|---|
| Fabricator cumulative HTTP |327 checks pass, max0.150s, including actual shipped old export migration. |
| Seven-path numeric identity and rollback |963 checks pass, max0.148s; long coefficients/exponents, equivalent/reordered ignored numbers, conflicts, failed-key reuse and portable replays. |
| Retained legacy checks.py |668 pass, including five50-worker retries. |
| Retained legacy repair_checks.py |653 calls pass, max0.206s, R1/R2/unknown fixture and auth/reset controls. |
| Retained Integrator HTTP probe, executed by Fabricator |771 checks/nine groups pass, max0.182s. This rerun is not independent verification. |
| Fabricator-derived schema2 semantic probe |233 cases/516 calls pass, max0.124s. Original peer probe unchanged; only format guard adapted. |
| Retained external-client authentication probe |16 cases/1177 calls pass, max1.517s, client outside service2CPU quota. |
| Network-none cumulative HTTP/numeric |309/963 checks pass, max0.191/0.222s; no mounts or outbound access. |
| Retained Inspector R1/R2 and R3 probes, offline |Zero R1/R2 failures; all48 numeric checks pass. |
| Unchanged supplied Stage1 suite |147 passed in39.77s; one readonly pytest-cache warning. |
| Unchanged supplied Stage2 suite |35 passed in58.22s; same harmless cache warning. |
| Playwright browser faults/layout |Seven groups pass;11 screenshots; all six routes at375/1440 without horizontal overflow. Visually reviewed mobile routes, desktop wallet, partial/final capture and refusal/uncertainty. |
| Separate default8080/mapped18890 startup/restart |Start-to-health3.187s; restart health0.437s; six HTML routes/two assets, JSON negotiation and empty restarted state pass. |
| Preservation and scope |All333 Foreman preservation hashes match; git diff from starting revision changes only stage-2. Host8080 incumbent untouched. |

Service source/destination/offline images have2CPU/2GiB limits and no mounts.
The client runs in a separate container outside the service quota. Internal
network and network-none runs establish no outbound dependency. The mapped
lifecycle uses bridge solely for host reachability. Runtime logs were empty.
Python syntax parsing covered all five Python files; browser execution exercised
the bundled JavaScript. Default and environment-override ports were exercised.

Image: `sha256:8077c0993e0af9384a038644f5732ce32d112ccbaddb403300b2800c02fc6b5f`.
Actual shipped Stage1 source in the migration container matched
`7bb43b5ac5e1bb8930e25f921119b72d7d0bd392aa2c009e8120a3847f45c0a9`.
Final host/image runtime hashes:

| File | SHA256 |
|---|---|
| service.py |866c89057a4d0ca689f305e44e71295e2462d29730974c8365a3153a774a227d |
| static/app.js |5a19614f219fd83ab37cec3947ade453b66a82284115dfe53c8650d1c53e6922 |
| static/style.css |f747ed10f9a5f44245b936ac95fca073444194053301a5dbde61cfc3f6fd0095 |

## Retained failures, limits and next action

Initial combined supplied-suite collection failed on duplicate test_sample module
names before executing tests. The unchanged suites were then run separately.
The first final runner stopped at the old probe's explicit schema1 guard before
semantic cases ran. The schema2 adapter is labeled derived, not a passing
unchanged peer script. Preliminary migration used a pre-R3 image; final migration
rebuilt the unchanged shipped Stage1 directory and verified its source hash.

Final-v2's trailing host localhost18886 restart probe failed after60s because
the internal network published no usable host port (requested binding present,
NetworkSettings.Ports empty). This failure remains in host-restart-observed.txt.
The internal-client health/empty-state check passed after that restart. A separate
properly mapped default-port lifecycle passed. The failed host probe is not counted
as passing, and earlier logs/results were not overwritten.

No observed functional failure remains in the executed suites. Tests cover finite
data and schedules; browser tests use Chromium and cannot prove every browser or
interleaving. For TTLs beyond the four-digit RFC3339 calendar, expiration currently
saturates at datetime.max while retaining exact private TTL; this calendar edge
needs independent adjudication. No unbounded load benchmark is claimed. State is
ephemeral by contract. Old Stage1 timing/rejection and harness evidence remains
unchanged; bounded external-client results do not erase it or establish a universal
timing guarantee. Credential-bearing snapshots/tokens remained in process memory,
not Git or shared logs.

Next: Foreman routes the exact documentation-child revision for Integrator's
independent cumulative lifecycle/concurrency/migration review, then Test Pilot's
independent browser/API falsification, then Inspector's exact-SHA decision.
Shipper remains gated. Fabricator does not accept this candidate.
