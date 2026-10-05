# Test Pilot Stage 2 first independent candidate execution

**Qualified result: API, browser, migration, timing, lifecycle and unchanged supplied Stage 1/2 suites passed after documented external-probe corrections. The astronomical TTL contract remains FAILED/UNRESOLVED. No acceptance or shipping decision is made here.**

## 1. Exact revision and artifact identity

- Full tested HEAD: `900cdcee3a98b8dcaf55dad9618199a0e649e924`, detached LF checkout `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-2-test-pilot\candidate-900cdce-01`. `git status --porcelain` was empty before and after; `git diff --check` was empty. Compared with `6018879f243af527c263c65d8885801052ef7301`, only root `plan.md` changed. The Stage 1 tree has no diff from shipped `65a56da7aa03c6690f12aa24c0dad372f2163437`.
- Independent no-cache Stage 2 image: `sha256:5cafe4981e523c4739d9a59710d7b9cec60fe591ecd3bd8bc3b607f9a04f179e`. Shipped Stage 1 source image independently built: `sha256:120433eee427fa66d03bc92bea39d6ebcde24c72c000d76749ff715cde365c8b`. New stock Linux helper image: `sha256:af84a6ce23f92c9b28452fab3e977f2267c1aee68fbe111dd102400152d5c8b2`.
- Exact committed LF and in-image SHA256: `stage-2/service.py` `866c89057a4d0ca689f305e44e71295e2462d29730974c8365a3153a774a227d`; `static/app.js` `c3de16565e9580806eb98c83e4223ede5e0a3240267f9513520e56db8dd73078`; `static/style.css` `7a935f89e4db83dd016eec45ac67486ae905dcfcaa78267dfb1ba08c4b3afa84`; `static/index.html` `b1eea0d86383dccea345645ecece9b6743552d79f0d633de75bdce5470e21060`. Actual shipped `stage-1/service.py`: `7bb43b5ac5e1bb8930e25f921119b72d7d0bd392aa2c009e8120a3847f45c0a9`. `checkout-final-hashes.txt`, `build.log`, service Docker inspect records corroborate.
- Foreman preservation manifest: all **333** entries match both before and after this run (`preservation-before.json`, `preservation-after.json`). Seven supplied test files have identical before/after hashes. Both specification hashes match the predeclared protocol. No product file, challenge assertion, or original evidence file was edited.
- All artifacts in this report live outside the product at `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-2-test-pilot\run-900cdce-01`. Private tokens and credential-bearing exports remained only in probe memory; logs contain no raw token/export.

## 2. Cumulative coverage and observed results

| Scope | Fresh exact900 observation |
|---|---|
| Stage 1 adversarial | Seven unchanged specification-derived groups PASS: validation, requests, auth/privacy, settlements, exact money, 50-inflight races and portable import (`legacy-adversarial.log`). |
| Stage 1 R3 numeric | 244 checks PASS, including huge raw JSON values, all five idempotent paths, portable replay, range and query controls (`legacy-numeric.log`). |
| Stage 1 R1/R2 and auth replacement | 216 reset/import/receipt checks PASS (`legacy-repair.log`); 26 login/signup versus reset/import and token-state race checks PASS (`legacy-auth-replacement.log`). |
| Stage 2 API | 420 checks PASS after one corrected external fixture oracle: partial/final captures, void/expiry, seeded holds and atomic reset, seven-path portable import/replay/corruption, currencies, validation (`api-oracle-fix.log`). Maximum recorded HTTP response 0.195177s. |
| Stage 2 concurrency | Nine predeclared waves PASS, up to 50 in flight: identical/distinct authorize/capture, capture versus void, payment/request-pay/net-settlement versus holds, interleaved snapshots. No exceptions; wave maxima 0.021–0.140s (`races.log`). |
| External cold/warm auth | Corrected fresh service: exactly one cold and two warm 50-login waves, each resetting the one-user fixture first. Every wave therefore starts with zero tokens, ends with 50 unique exported tokens, and all 50 returned tokens are visible through `/me`. Status 200 for all 150 requests, no exceptions. Maxima 1.452108s cold, 0.897633s warm 1, 1.169264s warm 2, original 5s end-to-end deadline (`cold-auth-corrected-01/cold-auth.log`). The earlier aborted helper execution is not counted. |
| Real browser | Corrected external probe: 11 groups PASS, Chromium at 375/1280 CSS pixels; no horizontal overflow on wallet/requests/split/reservations; visually reviewed `375-home.png`, `375-authorizations.png`, `1280-home.png`. EUR/JPY/BHD and zero-share preview, labels/focus, offline asset origins, competing-client refusal/cancel, lost post-commit response, original key/body retry and latest refresh wins (`browser-oracle-fix/browser-observations.json`, screenshots). |
| Navigation/order | Three controlled withheld-write outcomes and two same-page recovery cases PASS; zero premature GETs before mutation completion, success navigates and refused/uncertain retain recoverable form/key (`navigation/navigation-summary.json`, screenshots). |
| Live Stage 1 upgrade | Corrected external display-wait oracle: six checks PASS. Actual browser login token and successful lost-response payment/key/body originated in shipped Stage 1. Stage 1 export remained private in process; host stopped old source before Stage 2 import. Same live browser/page replayed exact key/body, moved money once, paid old pending request (`upgrade-oracle-fix/ready-for-stage1-stop.json`, stop signal, `upgrade-observations.json`). |
| Supplied cumulative suites | Original plugin/tests, read-only POSIX challenge mount, separate invocations: Stage 1 **147/147**, Stage 2 **35/35**; zero failed/errors/skipped/deselected. One read-only pytest cache warning each (`supplied-stage1/2.log`, `supplied-stage1/2-counts.json`). |
| Stock Linux judging CLI | Unmodified CLI from new helper and pinned checkout, isolated mode: Stage 1 147/147 PASS, Stage 2 35/35 PASS, highest contiguous/claimed stage **2**, share 1.0. It attempted Stage 3 overshoot and failed on a Stage 3 `as_of` feature (1 failed, 2 passed); this is not a Stage 2 failure. `stock-900cdce-01/report.json` SHA256 `e63b0e9a879971b68c267f0087b702b14a7f3386e5357afeffb660d8e91c2783`; its `revision` and upgrade-source revision fields are blank because the helper lacks Git. Exact host-pinned HEAD, clean status, source/image hashes and before/after test hashes externally bind the result; the report's provenance limitation remains explicit. |
| Deployment/lifecycle | Internal network `.Internal=true`, services 2 CPU/2 GiB, no mounts, no outbound service path; external client is outside service cgroup. Default mapped health 2.463s; restart health 4.951s and state cleared; custom PORT=8098 mapped health 1.777s; HTML/JS/CSS 200 (`lifecycle-corrected.json`, Docker inspect/logs). Owned containers and network were removed after capture. |

## 3. Executed commands, topology and preserved corrections

The preparation scripts and fixed protocol are in the parent Test Pilot directory. Exact representative commands below ran in PowerShell; all logs and detached checkout have new Stage 2 names:

```powershell
git clone -c core.autocrlf=false --no-hardlinks -n 'C:\Users\DELL\Documents\ALIVE FACTORY\pocketful-result' 'C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-2-test-pilot\candidate-900cdce-01'
git -C 'C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-2-test-pilot\candidate-900cdce-01' checkout --detach 900cdcee3a98b8dcaf55dad9618199a0e649e924
docker --context desktop-linux build --no-cache --progress=plain -t pocketful-pilot:s2-900cdce-01 'C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-2-test-pilot\candidate-900cdce-01\stage-2'
docker --context desktop-linux build --no-cache -t pocketful-pilot:s1-900cdce-01 'C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-2-test-pilot\candidate-900cdce-01\stage-1'
docker --context desktop-linux network create --internal pf-pilot-s2-900-01
docker --context desktop-linux run -d --name pf-pilot-s2-900-02 --network pf-pilot-s2-900-01 --cpus 2 --memory 2g --memory-swap 2g pocketful-pilot:s2-900cdce-01
docker --context desktop-linux run -d --name pf-pilot-s2-dest-900-01 --network pf-pilot-s2-900-01 --cpus 2 --memory 2g --memory-swap 2g pocketful-pilot:s2-900cdce-01
```

The executed external client invocations all used `docker --context desktop-linux run --rm --network container:pf-pilot-s2-900-02`, a read-only mount of the external probe directory at `/probe`, a new writable evidence mount at `/out`, `PYTHONDONTWRITEBYTECODE=1`, and `df-harness-runner`. Exact program/arguments and exits:

```text
python /out/stage2_cold_auth_transport_fix.py --source http://127.0.0.1:8080                  exit 0; first original /probe/stage2_cold_auth.py exit 1
python /out/stage2_api_probe_oracle_fix.py --source http://127.0.0.1:8080 --destination http://pf-pilot-s2-dest-900-01:8080  exit 0; original /probe/stage2_api_probe.py exit 1
python /probe/stage2_races.py --source http://127.0.0.1:8080                             exit 0
python /probe/stage2_ttl_edge.py --source http://127.0.0.1:8080 --destination http://pf-pilot-s2-dest-900-01:8080  exit 2 (known contract issue)
python /out/stage2_browser_probe_refresh_oracle.py --base http://127.0.0.1:8080 --out /out/browser-oracle-fix  exit 0; original /probe/stage2_browser_probe.py exit 1
python /probe/stage2_navigation_order.py --base http://127.0.0.1:8080 --out /out/navigation  exit 0
python /out/stage1_browser_upgrade_refresh_oracle.py --stage1 http://pf-pilot-s1-900-02:8099 --stage2 http://127.0.0.1:8080 --out /out/upgrade-oracle-fix  exit 0; original /probe/stage1_browser_upgrade.py exit 1
python /legacy/adversarial.py --url http://127.0.0.1:8080 --dest-url http://pf-pilot-s2-dest-900-01:8080  exit 0
python /legacy/numeric_regressions.py 8080 8080 (POCKETFUL_DEST_HOST=pf-pilot-s2-dest-900-01)  exit 0
python /legacy/repair_regressions.py 8080                                      exit 0
python /legacy/auth_replacement_races.py 8080                                  exit 0
```

Direct supplied suite command shape (executed separately, not combined):

```powershell
docker --context desktop-linux run --rm --network container:pf-pilot-s2-900-02 -v 'C:\Users\DELL\Documents\ALIVE FACTORY\challenge:/work:ro' -v 'C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-2-test-pilot\run-900cdce-01:/out' -e PYTHONDONTWRITEBYTECODE=1 -e PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 -w /work df-harness-runner python -m pytest pocketful/test/stage_1 --base-url http://127.0.0.1:8080 -p harness.plugin --rootdir pocketful/test -q --harness-summary /out/supplied-stage1-counts.json
docker --context desktop-linux run --rm --network container:pf-pilot-s2-900-02 -v 'C:\Users\DELL\Documents\ALIVE FACTORY\challenge:/work:ro' -v 'C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-2-test-pilot\run-900cdce-01:/out' -e PYTHONDONTWRITEBYTECODE=1 -e PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 -w /work df-harness-runner python -m pytest pocketful/test/stage_2 --base-url http://127.0.0.1:8080 --previous-base-url http://pf-pilot-s1-900-03:8099 -p harness.plugin --rootdir pocketful/test -q --harness-summary /out/supplied-stage2-counts.json
```

Stock helper path/socket preflight found checkout/spec files visible and Docker Desktop daemon `29.8.1` reachable. Executed stock command:

```powershell
docker --context desktop-linux run --rm -v '/mnt/host/c/Users/DELL/Documents/ALIVE FACTORY:/mnt/host/c/Users/DELL/Documents/ALIVE FACTORY:rw' -v /run/host-services/docker.proxy.sock:/var/run/docker.sock -w '/mnt/host/c/Users/DELL/Documents/ALIVE FACTORY/challenge' pocketful-pilot-harness-linux:s2-900cdce-01 python -m harness run --track pocketful --repo '/mnt/host/c/Users/DELL/Documents/ALIVE FACTORY/checks/pocketful-stage-2-test-pilot/candidate-900cdce-01' --stage 2 --mode isolated --out '/mnt/host/c/Users/DELL/Documents/ALIVE FACTORY/checks/pocketful-stage-2-test-pilot/run-900cdce-01/stock-900cdce-01'
```

The original auth probe stopped in Python's `HTTPConnection` instrumentation after response headers because `connection.sock` was `None` for HTTP/1.0 close. `cold-auth.log` and empty service log are preserved. **The number of auth requests that reached or committed before this abort is unknown:** no per-request rows or export snapshot had yet been emitted, and that service was removed. The corrected private copy sets the response stream's active socket timeout to the same remaining five-second total deadline, with no assertion or worker-count change. It ran once on a **fresh** service and distinct `cold-auth-corrected-01` output. Each of its three waves resets the fixture and thus has an independent zero-token baseline, not cumulative 0/50/100.

The original API probe stopped after 90 passing partial-capture checks on a false oracle: after a fresh 10,000-unit reset and an expired unspent hold, it expected 9,300 available. The corrected external copy expects 10,000, retaining held=0 and all other assertions; original `api.log` remains. The first browser and first upgrade probes demanded displayed balance 8,500 immediately on uncertainty-marker removal, before the success refresh completed. Their corrected external copies use the existing bounded 50×0.1s refresh wait and retain the exact 8,500 amount, once-only payment, key/body and import assertions. Original `browser.log` and `upgrade.log` remain; the first upgrade reached stopped-source/import before this display assertion. The successful upgrade used a fresh old source and new output directory. No product or supplied test was changed.

The first lifecycle wrapper was blocked by local PowerShell script execution policy and made no request. The next lifecycle attempt used a wrong guessed `/static` asset path and failed after default health; original `lifecycle.log` remains. `lifecycle-stage2-corrected.ps1` uses the actual HTML-referenced `/assets` paths and new service/output names; it passed without changing product behavior or acceptance criteria. The stock Stage 3 overshoot is preserved in `stage-3.log` and excluded from the Stage 2 counts.

## 4. Defects, risks and explicit next action

`ttl.log` exits 2 with one adjudication issue: a positive `10^30`-second TTL is accepted (201), holds 100 units, but `expires_at` saturates at `9999-12-31T23:59:59.999999+00:00` and does **not** equal `created_at + TTL`. The 200-billion-second representable case is exact, invalid type/range controls reject as expected, and the fixed eight-second partial-capture expiry/replay case passes. This is the same unresolved conflict between unrestricted positive TTL, exact addition and four-digit RFC3339 identified by Inspector; no policy amendment exists. It remains a failed/unresolved contract target, not an accepted limitation or silent pass. Inspector's separate near-calendar rounding/OverflowError robustness finding remains applicable because the service bytes are unchanged.

Integrator's original external cold50 timeout and 48 broken pipes on rejected revision `8a1498528daa41d188860b9eaa3b8027c839ab79` remain real, with cause unproved. The fresh exact900 timing results cover these declared schedules only. Finite races, Chromium-only visual review, bounded datasets and client placement do not prove all interleavings or sustained-load timing. The initially aborted auth-probe committed count is unknown, as recorded above.

**Next seat:** Foreman forwards this complete exact-SHA packet and preserved first-failure logs to Inspector for independent final decision on the same `900cdcee3a98b8dcaf55dad9618199a0e649e924`. TTL conflict must remain explicit in that decision; Test Pilot issues no acceptance. Shipper remains gated. All Test Pilot-owned service/destination/old-source/default/custom containers and internal network were removed after logs/inspect were saved; unrelated host 8080 was untouched.
