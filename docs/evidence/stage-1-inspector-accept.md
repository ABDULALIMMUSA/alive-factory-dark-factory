# Inspector decision: ACCEPT

## 1. Exact accepted revision and evidence identity

**ACCEPT 65a56da7aa03c6690f12aa24c0dad372f2163437** for Pocketful Stage 1, on the evidence and limits below. No remaining blocking product defect was found. This accepts only the examined revision; Shipper's independent delivery verification remains required.

Repository: `C:\Users\DELL\Documents\ALIVE FACTORY\pocketful-result`.
Product: `C:\Users\DELL\Documents\ALIVE FACTORY\pocketful-result\stage-1`.
Specification: `C:\Users\DELL\Documents\ALIVE FACTORY\challenge\pocketful\spec\stage-1.md`, SHA-256 `65497dea09a8b432598c71662320cf66c3550e183cfd76e2d7f97318e0d30aa4`.
Accepted service.py SHA-256: **`7bb43b5ac5e1bb8930e25f921119b72d7d0bd392aa2c009e8120a3847f45c0a9`**.

Source/test/RUN parent is `1da47776db111836d944f976c2d8f6e47688b9ea`; subsequent d1030f3/65a56da children change only EVIDENCE.md. I verified the parent-to-candidate diff and clean exact HEAD. Inspector made no product edits or commits.

Decision and Inspector artifacts are outside the result repository at `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-1-inspector`:

- `decision-65a56da.md`: this decision.
- `numeric-on-65a56da.log`: unchanged R3 probe execution, 48/48 passed.
- `original-on-65a56da.log`: unchanged original R1/R2 probe, zero failures.
- `oracle-65a56da.py` and `oracle-65a56da.log`: additional independent exact-value HTTP oracle, 375 calls passed. Script SHA-256 `bfee5c510c86bb670df74bb4e69de496ec53b72a88f847b1af3e0191e8465ceb`.

Original `decision-998dc1a.md`, `decision-437b56d.md`, their reproducers/failure logs, intermediate seeded-field failures and authentication timing failures remain preserved. This decision does not amend their results.

## 2. Complete specification/source assessment and defect closure

I reread the complete authoritative specification and all 830 lines of current service.py, examined the exact repair diff, new numeric_checks.py and RUN/EVIDENCE changes, and reviewed the complete Fabricator repair-9, Integrator final and Test Pilot final reports. Foreman's final Test Pilot packet arrived and was read before this acceptance. Mandatory visible receipt/finding handoffs and exact candidate continuity were retained.

| Spec sections | Reviewed behavior and supporting evidence |
| --- | --- |
| 1, 4, 9 | Integer balances and bounded numeric conversion preserve minor-unit values; seed payments are history and are not reapplied. Direct debit/credit and net settlements share transactional locking. Ordered quotient/remainder splits preserve totals, including zero-share requests. Independent concurrency/exact-money/split checks and source review support conservation, no overdrafts and once-only request payment. |
| 2, 3 | Standard-library standalone container, pinned Python image, no service dependencies or mounts, non-root process, 0.0.0.0/default and custom PORT. Independent no-cache builds, no-outbound configurations and normal-bridge mapped-port lifecycle checks support delivery. Reset/import replace detached validated state under the lock; health and JSON conventions reviewed. |
| 5 | Fixture-specific helpers now distinguish missing fields, wrong JSON types and invalid numeric values. Amount/note/visibility special errors remain intact. Parsing and conversion handle repaired numeric boundaries; malformed controls retain 400. Prior required-array, scalar/ID and new numeric regressions all pass. |
| 6 | Salted scrypt password storage, multiple valid bearer tokens, derived handles and zero-balance signup retained. Hash work is outside the state lock; signup rechecks availability and login rechecks state/account identity before session commit. Fixed auth/control races exercise replacement with the same ID and changed credentials. |
| 7 | Canonical JSON includes unknown fields for retry identity, separates booleans, normalizes exact numeric values and preserves array order. Scope is caller/method/path. Successful receipt copies survive resource changes/import; failed keys remain reusable. Claimed-key resolution precedes field/resource validation. Five-path retry/concurrency and semantic import evidence reviewed. |
| 8 | Required payments/requests/pay/decline/cancel/split/list endpoints and receipts remain implemented. Payer/requester permissions, above-balance request creation, terminal-state rules, note preservation, private/public feed membership and pagination reviewed and exercised by independent suites. |
| 10 | Export is a detached snapshot; import reconstructs state without historical transfers or ID/timestamp regeneration. Completed claim validation ties bodies to receipts/resources/path/actor/permissions. Separate-container tests preserve tokens, hashed login, original receipts and permissions and remove destination state. A source-stopped test demonstrates destination independence. |
| 11 | Settlement entries validate in order before net affordability. Wallet deltas are aggregated before final balances are installed; no intermediate negative debit is applied. The batch, member receipts and retry claim commit under the same lock. Cyclic netting, ordered errors, rollback, concurrency, visibility and portable membership evidence are sufficient. |

Numeric repair inspection: JSONNumber stores normalized sign, coefficient digits and an arbitrary integer exponent. Zero canonicalizes identically regardless of signed/exponent representation. A negative exponent after trailing-zero normalization denotes a nonintegral value; monetary size/integrality checks occur before power-of-ten expansion. Plain integer token parsing no longer has the interpreter's 4,300-digit cap. Canonical reconstruction on import uses the same representation and rejects noncanonical or semantically contradictory stored claims. No new product amount/offset cap or floating-point rounding was introduced.

Original rejection closure was reproduced directly by Inspector: fourteen reset wrong-type cases now return 400 with state unchanged; omitted controls return 422; contradictory imported amount/body state returns 422 with destination unchanged. All four R3 failures now return their specified replay/error responses, and all 24 original long-query controls still pass. R8 seeded unknown-field closure is supported by independently executed 17/29-case Integrator and 28 positive Test Pilot controls, with normal API linkage preserved.

## 3. Inspector executions and review observations

Executed from the result repository, as separate PowerShell commands:

```text
git rev-parse HEAD
git status --short
git diff 437b56d2deb96646a55360b4f8caaa5938985b70 65a56da7aa03c6690f12aa24c0dad372f2163437 -- stage-1/service.py stage-1/numeric_checks.py stage-1/RUN.md stage-1/EVIDENCE.md
git diff 1da47776db111836d944f976c2d8f6e47688b9ea 65a56da7aa03c6690f12aa24c0dad372f2163437 --stat
docker --context desktop-linux build -t pocketful-inspector:65a56da ./stage-1
docker --context desktop-linux run -d --name pocketful-inspector-65a56da --network none --cpus=2 --memory=2g -e PORT=18879 pocketful-inspector:65a56da
docker --context desktop-linux cp 'C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-1-inspector\numeric-437b56d.py' pocketful-inspector-65a56da:/tmp/numeric.py
docker --context desktop-linux cp 'C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-1-inspector\probe-998dc1a.py' pocketful-inspector-65a56da:/tmp/original.py
docker --context desktop-linux exec pocketful-inspector-65a56da python /tmp/numeric.py 18879
docker --context desktop-linux exec pocketful-inspector-65a56da python /tmp/original.py 18879
docker --context desktop-linux cp 'C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-1-inspector\oracle-65a56da.py' pocketful-inspector-65a56da:/tmp/oracle.py
docker --context desktop-linux exec pocketful-inspector-65a56da python /tmp/oracle.py 18879
docker --context desktop-linux exec pocketful-inspector-65a56da sha256sum /app/service.py
docker --context desktop-linux inspect --format '{{.Image}} cpus={{.HostConfig.NanoCpus}} memory={{.HostConfig.Memory}} network={{.HostConfig.NetworkMode}} mounts={{json .Mounts}}' pocketful-inspector-65a56da
docker --context desktop-linux logs pocketful-inspector-65a56da
Get-FileHash -LiteralPath stage-1/service.py -Algorithm SHA256
git status --porcelain=v1
git diff --check
```

All three probes exited 0. Original R3: 48/48 passed. Original R1/R2: zero failed contract cases. Additional oracle: **375 HTTP calls, maximum 0.094612 seconds**, all assertions passed. Its fixed-seed 80-case rational Fraction oracle independently classified seven valid integral amounts and 73 invalid amounts; each invalid request left state unchanged and its key reusable. Additional checks cover 6,000-digit coefficient/exponent cancellation into small valid amounts, signed huge-exponent equivalence/conflict across all five paths, 15 original receipts after equivalent-version/schema import, and five invalid canonical-tree encodings rejected with rollback. The oracle imports no product source.

Inspector build reused cache; image ID `sha256:c76df5867d4c7579bd7d679f9c8497d457fc4cd33be8621ace28a2e2988c0139`. Host/image source hash matched. Container inspection: 2,000,000,000 NanoCPUs, 2,147,483,648 memory bytes, network none, mounts empty. Service logs were empty. These are sequential Inspector probes, not additional auth stress claims. Ordinary/control timeouts were 5/10 seconds. Exports, credentials and tokens remained only in process memory.

## 4. Independent gate evidence and reproducibility

Integrator final report: `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-integrator-65a56da\report.md`.
I inspected its command manifest: **41 commands, zero nonzero exits**, all tied to the final SHA. Its clean LF detached checkout and no-cache image match the accepted source. Independent numeric **199 cases/1,988 calls**, full **771**, R1/R2 **233/516**, seeded **17/68 plus 29/119**, arrays **63**, and unchanged Inspector probes passed in separate-container and network-none configurations. Product-authored 668/653/711-check suites were separately identified reruns, not mislabeled independent designs. Fixed external auth cold/warm each passed 16 cases, maxima 1.829/2.206 seconds. Supplied tests: 147/147; all 23 harness/test file hash entries match before/after.

Final Test Pilot report: `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-1-test-pilot\verification-65a56da-01\report.md`.
Its independent no-cache image is `sha256:1db01dfc315c8ee7a47a03532559e361bcbf60fc8055f28e13f51c934cc3d0fa`, same service hash. Numeric **244/244**, focused repair **216/216**, full **7/7 groups**, boundary **16/16**, and original Inspector probes passed. I inspected protocol, final counts, auth summary, resource manifests, lifecycle JSON, source-unavailable script/log, and supplied-file hashes. All 42 supplied before/after entries match; counts are **147 collected/passed, zero failures/errors/skips/deselections/xfails**.

Test Pilot's predeclared cold/warm/warm auth sequence completed **26 checks and nine waves per run**, no failures/exceptions, maxima **2.298909193 / 1.706064142 / 2.394996381 seconds**. Service manifests show 2 CPUs/2 GiB/no mounts; external client has its own quota. At most 50 requests were in flight, using original 5-second ordinary/10-second control timeouts. No pass-based retry was used.

Portability evidence goes beyond running two live services: after an unchanged export/import, the source was stopped and became unavailable; seven assertions passed for destination tokens, exact balances, original receipt, password login, operator settlement and conservation (final 94+6=100). I verified source_unavailable.py SHA-256 as `9ec049ed5b7dbebf7581395ad840bd67b31c770d09245f71f2127dcb04b7e6a2`, resolving the printed-hash whitespace concern against the actual file.

Default mapped-port health/restart were 2.950/5.616 seconds for Test Pilot and 3.032/5.828 for Integrator, with seeded state cleared on restart. This is separate from no-outbound internal/network-none evidence. Test Pilot final service logs are empty. The final packet and source-stopped proof satisfy the earlier outstanding gate.

## 5. Preserved limitations and risk adjudication

No unresolved blocking defect remains within the complete source review and reproducible evidence. Acceptance does not assert exhaustive proof for all input lengths, schedules, unbounded data growth or sustained global-lock throughput. Arbitrary numeric representation is exact, but CPU/memory remain finite. State is intentionally ephemeral, as allowed.

Prior colocated-client auth failures remain real observations: 5.083-second login and approximately 5.0–5.2-second timeouts/broken pipes. Their cause is not established. My previous adjudication stands: the service's 2-CPU/2-GiB contract does not require a load generator to share that quota. Fixed separate-client runs are the relevant bounded deployment evidence; they do not erase failures or prove universal timing. No new contrary evidence was found.

Setup/transport failures also remain: internal-network host mapping exhausted 60 seconds while localhost/external-client health was 200; actual bridge mapping then passed. Shell quoting/invocation errors, an omitted test argument and pre-ready probes remain in their reports. Test Pilot's host execution policy blocked one lifecycle script before execution; the unchanged script subsequently ran under a process-local policy. These are distinguished from product failures, and were not used to hide failed semantic assertions.

The **stock Windows harness CLI scoring path remains broken** by Windows-to-Linux backslash transport. Passing unchanged read-only tests through the supplied isolated runner/plugin with a POSIX suite path is accepted behavioral evidence, not a successful stock CLI score claim. The numeric control timeout correction to 10 seconds follows specification section 10; ordinary requests remained at 5 seconds.

Existing-product provenance relies partly on Fabricator's explicit declaration that no domain-product source/docs/schemas were used. Inspector performed acceptance review only, never repaired the implementation and never accepted its own product work.

## 6. Next seat and release scope

**Shipper: verify exactly 65a56da7aa03c6690f12aa24c0dad372f2163437 from a clean checkout/build following RUN.md.** Confirm the accepted source hash, standalone image, default/custom listening behavior and delivery artifacts, and report the full SHA and bounded evidence. Do not modify source or substitute a newer revision. Any product change or reproducible delivery defect returns to Foreman for repair and renewed independent verification/review.

Foreman should route this explicit ACCEPT and report path to Shipper and record the exact accepted SHA. Shared task #4 may be completed with this decision/evidence path. This is permission to proceed to the exact-revision shipping gate, not a claim that shipping has already occurred.
