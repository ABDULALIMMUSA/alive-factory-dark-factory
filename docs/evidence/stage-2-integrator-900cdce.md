# Continued Stage2 independent integration packet — exact900

**Qualified verification packet complete for Test Pilot; no acceptance or shipping authorization.** New affected checks and the fixed authentication protocol pass. The unchanged TTL contract remains failed/unresolved, and the original external cold timeout's cause remains unproved. Human CONTINUE did not select a TTL policy.

## 1. Exact revision and runtime correspondence

Executed **900cdcee3a98b8dcaf55dad9618199a0e649e924** from a clean detached LF checkout:
`C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-integrator-stage2-900cdce\candidate`.
It changes only root plan.md from6018879f243af527c263c65d8885801052ef7301.601 is the evidence-only child of41c7162444f2d512f8ef326c196a08b71d4453da, whose UI runtime was repaired at7d97da19473ec5b325770391461b60b793c8b472. No Integrator product edits or commits.

New independent no-cache image: **sha256:eb0fe2108f6b582f9597ac6eb35bbc412d3d58180192c1015869af7b015600da**.

| Runtime file | Exact LF/Git/image SHA256 |
|---|---|
| service.py |866c89057a4d0ca689f305e44e71295e2462d29730974c8365a3153a774a227d |
| static/app.js |c3de16565e9580806eb98c83e4223ede5e0a3240267f9513520e56db8dd73078 |
| static/style.css |7a935f89e4db83dd016eec45ac67486ae905dcfcaa78267dfb1ba08c4b3afa84 |
| static/index.html |b1eea0d86383dccea345645ecece9b6743552d79f0d633de75bdce5470e21060 |
| Actual shipped Stage1 service.py |7bb43b5ac5e1bb8930e25f921119b72d7d0bd392aa2c009e8120a3847f45c0a9 |

`continuity.json` compares each file's raw bytes with full-test revision8a1498528daa41d188860b9eaa3b8027c839ab79 and bounded41c. All runtime files match41c; only app.js differs from8a. service.py, Dockerfile, .dockerignore, HTML/CSS and Stage1 service match8a exactly. The pinned Python3.12 base and first five filesystem layers match across old8a image164d7f...,41c image276dcc..., and new900 imageeb0fe.... Their full image IDs differ and are not claimed identical. Current actual image hashes are recorded in `runtime-hashes.log`; `observations.json` contains image IDs, layers, command/user/environment correspondence.

Both complete specs were previously read; renewed continuity checks retain unchanged hashes: Stage1 `65497dea09a8b432598c71662320cf66c3550e183cfd76e2d7f97318e0d30aa4`, Stage2 `39aaf9d7743c6fd831663e5b8363866f7d70795e5efb9000c2803f471397b13f`. Read the active immutable Continuation Plan and prior full/bounded/primary reports. Complete source review is carried forward by exact unchanged-byte correspondence, including the inspected action-refresh navigation repair; no hidden service change is inferred.

## 2. Complete cumulative coverage, reused evidence and new work

Reused independent backend executions are **actual8a14985 results, not new900 runs**. Full evidence remains at `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-integrator-stage2-8a14985\report.md`, with actual command manifests and image164d7f... identity. Exact unchanged backend/Docker/base correspondence above supports reuse as authorized:

| Cumulative requirement | Preserved actual8a execution |
|---|---|
| Stage1 §§1–6 deployment/fixtures/types/auth/privacy; §7 retry; §§8–9 money/requests/splits/feed; §11 settlements |771 independent integration +668 legacy +682 repair calls; R1/R2 semantic233 cases/516calls; seeded17/68 and29/119 |
| 50-inflight holds/captures/void/expiry/payments/net settlements, conservation and read histories |15 independent groups/737calls with retained redacted timing histories; primary327HTTP independently executed |
| Seven retry paths, exact numeric bodies, semantic import/rollback, old receipts and seeded history |963 numeric;41 additional semantic cases; full legacy R1/R2; original Inspector48 numeric and R1/R2 zero failures |
| Network-none runtime, default/custom ports, ephemeral restart/reset tokens/state/retries |Offline309/963; mapped startup5.953s/restart6.594s; lifecycle-result.json |
| Supplied unchanged cumulative assertions |Separate147 Stage1 /35 Stage2 pass on8a; original tests and read-only transport unchanged. These counts are not relabeled as900 results. |
| Authentication/control races |Prior cold16-case run's first50-login failure retained; other15 and fixed warm16-case pass, including signup/login versus reset/import. New unresolved timing protocol below supplements this evidence. |

New900 executions cover the complete affected browser/action-refresh/navigation/retry/freshness surface: independent nine groups (EUR/JPY/BHD decimals, form persistence/key changes, split zero shares, signup/login/logout, refusal refresh, stale requests, holds/captures, latest refresh, upgrade); original navigation reproducer; eight independent controlled outcomes; primary-authored14 navigation and seven browser groups independently executed and labeled; actual shipped Stage1 source-unavailable no-reload migration. New50-login telemetry supplements rather than replaces the old failure. Known TTL conflict is explicitly carried forward failed/unresolved by identical service bytes.

## 3. Executed commands and resource protocol

New output root: **C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-integrator-stage2-900cdce**.

`run.py` and `commands.json` record exact argv/exits/durations and distinct logs. Representative executed commands:

```text
docker --context desktop-linux build --no-cache -t pocketful-integrator:s2-900cdce <detached900>/stage-2
docker --context desktop-linux exec pi2-900-client python /out/auth-wave.py auth-cold 0
docker --context desktop-linux exec pi2-900-client python /out/auth-wave.py auth-warm1 1
docker --context desktop-linux exec pi2-900-client python /out/auth-wave.py auth-warm2 2
docker --context desktop-linux exec pi2-900-client python /out/navigation-corrected.py
docker --context desktop-linux exec pi2-900-client python /out/outcomes-known-oracle-corrected.py
docker --context desktop-linux exec pi2-900-client python /prepared/browser.py --base http://127.0.0.1:8080 --stage1 http://pi2-900-old:8099 --revision 900cdcee3a98b8dcaf55dad9618199a0e649e924 --output /out/browser
docker --context desktop-linux exec pi2-900-client python /product/navigation_checks.py
docker --context desktop-linux exec pi2-900-client python /product/browser_checks.py http://127.0.0.1:8080 http://pi2-900-old:8099 /out/primary-browser
docker --context desktop-linux exec pi2-900-client python /out/migration-source-unavailable.py
```

Fresh service and rebuilt actual shipped Stage1 each2CPU/2GiB, no mounts, internal network/no outbound. Default8080 and oldPORT8099. Client image188162cb..., separate unlimited cgroup sharing only service network namespace for localhost secure browser context; no insecure-origin flag for independent browser. Primary browser retains its original flag although localhost is already secure. `resources.log` records exact image/cgroup/network/mount settings. Old-source image8c6f6807... and service hash independently captured. All owned containers/network removed after logs; host8080 incumbent untouched.

**Authentication protocol predeclared visibly before execution:** exactly one cold then two warm50-login waves on the same fresh service, before browser work, with no reset between warm waves and no result-dependent repeats. One fixture user shared/same, balance7. Each request records connect/send/response-header/body completion phases, status/exception and elapsed. Ordinary auth total deadline5s; reset10s. Between waves: received tokens checked, correct and wrong credentials checked, export token counts/ledger/health verified. No private tokens or snapshots saved. Raw cgroup cpu.stat/memory.events before/after each wave, Docker stats and cumulative logs saved as `auth-*-cgroup-*.log`, `auth-*-stats.log`, `auth-*-service-logs.log`.

Independent HTTP/browser outcome assertions use5s ordinary waits and10s reset/control transport; the original navigation probe retains its10s release safety guard. Primary browser source remains unchanged and has its original10s development waits/HTTP helper; those passes are functional evidence, not an independent5s service performance measurement. The phase-instrumented authentication waves use the original5s limit and cannot be extended by those waits.

## 4. Newly observed900 results

| Check | Observed result |
|---|---|
| Cold50-login |50/50 HTTP200,0 exceptions, max2.251233s;50 unique received tokens all visible |
| Warm1 50-login |50/50 HTTP200,0 exceptions, max1.305286s |
| Warm2 50-login |50/50 HTTP200,0 exceptions, max1.051655s |
| Original unchanged navigation probe |PASS; no premature navigation read; post-success900 |
| Independent controlled outcomes |8/8 PASS: success/refused/uncertain/latest/history/logout/request-pay/void;0 page errors |
| Independent complete browser matrix |9/9 PASS;0 page errors and0 unexpected asset origins |
| Independently executed primary navigation |14/14 PASS including all resource actions and queued outcomes |
| Independently executed primary browser |7/7 PASS including partial/final captures, delayed refresh, migration and responsive routes |
| Actual stopped-Stage1 no-reload migration |PASS source unavailable before import, browser/session/form/body/key retained, original payment once, pending request paid, finalbalance870 |
| Preservation |333 baseline hashes unchanged;187 prior8a/41c evidence files byte-identical; Stage1 tree unchanged; clean exact900 checkout |

The waves begin with0/51/102 tokens, end their50 requests with50/101/152 tokens, and finish positive credential checks with51/102/153. The extra three tokens are the declared credential verification logins. Wrong password401, current credentials valid, health200 after every wave. One user and ledger total7 remain; payments/holds/idempotency tables empty. Per-request artifacts: `auth-cold-results.json`, `auth-warm1-results.json`, `auth-warm2-results.json`; maxima and final states summarized in `observations.json`. No new BrokenPipeError or other service logs in this execution.

Source-unavailable migration exports private state in client RAM, emits only a readiness marker, then host stops actual old container before import. The client verifies old source unreachable, imports, retries with same key/body, pays old pending request, and returns to Wallet without reloading the browser. See `migration-results.json`, `source-unavailable-migration.log`, stop command and screenshot. Only old-service hostname is adapted externally from the previously corrected migration probe; original remains untouched.

The independent outcome probe applies the already established empty-fixture oracle correction before the new run, preserving all original ordering/deadline/money assertions. Earlier7/8 run and corrected single-case history remain unchanged; this900 run independently executes all eight corrected groups. No result-dependent test repetition here.

Inspected newly generated desktop wallet/hold hierarchy, uncertain feedback, partial capture and375px wallet/split screenshots; presentation remains coherent with readable labels, distinct states and no observed horizontal overflow. `browser/` and `primary-browser/` contain19 new route/state screenshots, plus navigation/migration captures. Chromium/finite viewport observations are not an exhaustive accessibility acceptance.

## 5. Failures, unresolved risks and qualification

**TTL remains FAILED/UNRESOLVED, not waived:** unrestricted positive integer TTL, exact expires_at addition and RFC3339 representation cannot all hold for the known1e12 example. The same service bytes still implement saturation. Inspector's report at `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-2-inspector\ttl-adjudication-8a14985.md` also retains floating total_seconds boundary rounding/OverflowError classification findings. No cap, saturation permission, expanded-year schema or altered error policy was chosen by CONTINUE. Known calendar inputs were not rerun merely to repeat unchanged evidence; the historical failure is explicitly reused as unresolved.

**D2 original cold timeout remains real and unexplained:** actual8a external first50-login wave timed out and produced48 late-write BrokenPipeError traces. Its per-request failed-wave phase/final visibility was not recorded. Previous diagnostic passes and these three new instrumented passes establish only the observed schedules; they do not retroactively recover missing original data, prove root cause or establish a universal timing guarantee. All old logs/hash identities remain intact.

No new product failure observed in this run. One metadata-only summarizer exited1 on omitted optional Docker Config.Entrypoint; `.get()` correction reran only metadata aggregation. `summary-first-error.txt` preserves the failure. No product test assertion was weakened and no completed product suite was repeated because of that error.

Reused backend results retain their8a executed revision/image and known failures. Browser change is covered by new900 executions; this is not a claim that every old backend test was freshly run on900. Finite schedules, one browser engine, unbounded datasets/load and all possible in-flight combinations remain limits. State is ephemeral by contract. No source mutation, acceptance or shipping action occurred.

## 6. Explicit next-seat action

Foreman should route **exact900cdcee3a98b8dcaf55dad9618199a0e649e924** with this qualified packet to **Test Pilot's first independent candidate execution**, as the Continuation Plan directs. Pilot independently falsifies cumulative API/races/seven-path import/browser visuals/TTL, performs fixed external timing and actual source-unavailable upgrade, runs unchanged supplied stages separately and the bounded stock Linux CLI attempt. Inspector then decides on the same exact source and all evidence. Known TTL remains a specification-authority block; human continuation is not policy authorization. Shipper remains gated. Shared#11 records completed investigation/handoff, which is not a passing acceptance decision.
