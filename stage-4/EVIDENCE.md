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

## Repair #15: navigation waits for the complete write action

Rejected independent baseline: `8a1498528daa41d188860b9eaa3b8027c839ab79`.
Tested final runtime/test revision: `41c7162444f2d512f8ef326c196a08b71d4453da`.
This evidence is a documentation child; runtime bytes remain those tested.
Read the complete independent report, corrected navigation probe/results/log,
both complete authoritative specs and production plan. The peer probe remains
unchanged (SHA256 b57de3ba6cfe6f985eca03f5a7f9ee0637f1f54134876b67bb1e408021ccb7bd).

The original probe independently reproduced premature GET /requests?limit=200
while POST /payments was withheld, exit1, with correct900 post-success balance.
Repair tracks pending mutations and complete browser action refreshes. Route,
history and logout navigation waits, and only the latest queued destination
proceeds after confirmed success. Refused/uncertain actions discard their queued
navigation, leaving feedback/forms and original retry identity available. A later
explicit navigation remains usable. Logout clears its session after the write.
Existing wallet/list read generations still enforce latest refresh wins.

Stage1 §§1–11 and Stage2 monetary/authorization/snapshot behavior are inherited
unchanged: service.py/Dockerfile/CSS/HTML Git blobs did not change in this repair.
The browser preserves decimal parsing/formatting, all six routes, status/privacy,
split ordering/zeros, seven-path original receipt semantics, competing-client
refusal refresh, lost-response recovery and signed-in Stage1 migration.
Auth hashing, resource limits and5s/10s transport constraints are unchanged.

Exact command argv/exits/timings, topology, hashes and retained failures:
`C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-fabricator-stage2-repair15`.
Executed `python ...\run.py baseline`, `repaired`, `repaired-v2`, and `final-lf`;
each uses a new evidence directory and retains earlier outputs. The runner builds
with Docker desktop-linux --no-cache, source/default8080 and destination8098 on
an internal network, each2CPU/2GiB/no mounts. Separate client shares only the
source network namespace, outside its quota, enabling localhost Chromium.
Actual shipped Stage1 runs at8099; its source hash remains7bb43b5...f45c0a9.
`expanded.py` verifies literal committed runtime bytes and original probe identity.
`close.py` records final clean HEAD, runtime identity,333 preservation hashes and
owned-container cleanup. No credentials or snapshots are written to these logs.

Final exact-LF observations (final-lf/commands.json and corresponding logs):

| Check | Result |
|---|---|
| Unchanged corrected peer navigation probe |PASS, no GET before withheld write success, post-success900. |
| Fabricator navigation matrix |14 groups PASS: wallet pay/request/authorize/split, request pay/decline/cancel, capture/void, refused/uncertain same-key retry, latest destination, history and logout. |
| Retained independent authored browser matrix, executed by Fabricator |9 groups PASS, no page errors or unexpected asset origins; this is not independent acceptance. |
| Existing Fabricator browser faults/viewport matrix |7 groups PASS, six375/1440 routes and migration/retry/latest-refresh/capture/release retained; screenshots preserved. |
| Retained independent API matrix, executed by Fabricator |15 groups/737 calls PASS, maximum0.219s. |
| Fabricator cumulative HTTP |327 calls PASS, maximum0.121s, including actual shipped old export/token/request/retry continuity. |
| Seven-path numeric HTTP |963 calls PASS, maximum0.166s. |
| Unchanged supplied Stage1 |147 passed in48.13s, one readonly cache warning. |
| Unchanged supplied Stage2 |35 passed in64.13s, same cache warning. |
| Preservation |All333 hashes match; Stage1/root plan/evidence unchanged. |

Final image: sha256:bb64c24e1a6497c7e37e226f0df1147e5b42aee33e67241de3c0d70e7266b296.
Literal committed LF/image hashes: service.py866c89057a4d0ca689f305e44e71295e2462d29730974c8365a3153a774a227d;
app.jsc3de16565e9580806eb98c83e4223ede5e0a3240267f9513520e56db8dd73078;
style.css7a935f89e4db83dd016eec45ac67486ae905dcfcaa78267dfb1ba08c4b3afa84.
Service logs in the final repair run were empty. Pending-write desktop and mobile
wallet screenshots were visually reviewed; controls/loading/available hierarchy
remain clear. Runtime assets are bundled; no new runtime dependencies.

Retained repair history: the first network-only barrier passed the original probe
but an added latest-destination check found stale1000 on Reservations after a
confirmed100 transfer (expected900). repaired/navigation-outcomes.log is retained.
Holding the complete action refresh fixed this, and all assertions remain.
Git archive on this host converted files to CRLF under core.autocrlf=true;
repaired-v2 passed but raw hashes differed. Final-lf restores each archived file
from exact Git blob bytes, rebuilds and reruns the full selected checks. The earlier
converted runs and identity distinction remain; final raw hashes now match Git.

**D2 remains unresolved:** the independent original external-client cold50-login
TimeoutError,48 BrokenPipeError response-write records and incomplete failed-wave
final assertions are preserved at the Integrator evidence root. Two predeclared
fresh cold waves passed50/50 but do not prove cause or erase the failure. Reviewed
their phase/final-state/cgroup evidence and the frozen diagnostic; there is no
measured root cause supporting a hash/timeout/resource change. No new cold auth
workload or speculative authentication repair was performed in #15.

**D3 remains unresolved:** TTL1e12 independently produces datetime.max, not exact
created_at+TTL. Saturation is not claimed compliant; no undocumented maximum or
calendar repair was introduced. Inspector/Foreman adjudication remains necessary.
Finite schedules/Chromium checks do not prove every interleaving/browser. Original
Stage1 and Stage2 failure histories remain intact. No self-acceptance or shipping.

Next: Foreman routes the exact final documentation-child SHA for renewed
independent Integrator navigation/retry/freshness and cumulative review, then
Test Pilot and Inspector with D2/D3 evidence visible. Source stops at handoff.
