# Pocketful Stage 1 production plan

Authoritative specification: `C:\Users\DELL\Documents\ALIVE FACTORY\challenge\pocketful\spec\stage-1.md`.
Submission: `C:\Users\DELL\Documents\ALIVE FACTORY\pocketful-result\stage-1`.

## Production packets

1. Foreman verifies workspace, Git, Docker, readable complete specification, absence of stale Toy code, and all-seat participation. Passed: clean unborn main; stage-1 absent; Docker server 29.8.1; every seat visibly confirmed local access and readiness.
2. Fabricator implements the complete specification in stage-1 with meaningful commits, a self-contained Dockerfile, RUN.md and implementation evidence. Primary packet #1 and repair packets #6/#7 are completed; the latest source commit is `a5741a7d7b9f32f06b06315b2638467f73111912` and still requires renewed independent verification.
3. Integrator independently inspects the exact Fabricator revision against the whole specification and runs Docker lifecycle, concurrency, atomicity and portable-state checks. Shared task #2.
4. Test Pilot independently attempts specification-derived falsification and runs the supplied isolated harness. Shared task #3. Preparation can proceed before the candidate, with artifacts outside the product tree.
5. Inspector independently issues evidence-backed ACCEPT or REJECT for the exact tested revision. Shared task #4. Rejection routes through Foreman for repair and renewed independent verification.
6. Shipper follows RUN.md from a clean checkout/build of the exact Inspector-accepted revision and verifies the runtime contract. Shared task #5. Any source change invalidates acceptance.
7. Foreman records the exact delivered revision and evidence in a final SHIPPED or BLOCKED Factory Receipt. Foreman neither implements nor accepts product work.

## Coverage required at the gates

- Container portability, configurable listening port, health, resource/time limits and no runtime outbound dependencies.
- Authentication, derived handles, multiple tokens and password hashing.
- Exact minor-unit monetary arithmetic, conservation, nonnegative balances and atomic changes under concurrency.
- Payments, legal over-balance requests, request terminal states, payer/requester authorization and once-only payment.
- All five idempotent paths: per-user and per-method/path scope, JSON-value bodies, replay precedence, original response preservation and reusable failed keys.
- Exact ordered split rounding including zero shares and caller-only splits; feed/request privacy, filters and pagination.
- Correct type/validation errors, optional defaults, unknown fields, note round trips and timestamps.
- Atomic reset and portable export/import preserving hashes, tokens, identities, timestamps, money, requests, operator permissions, settlement membership and successful retry records. Failed controls must preserve prior state.
- Atomic net settlements: ordered entry errors, cyclic affordability, full-batch commit or rollback, shared timestamps and ordinary feed visibility.

## Evidence continuity

Every substantive handoff names the exact Git revision, specification coverage, commands executed, observed results, defects or unresolved risks, and explicit next-seat action. Receiving seats visibly reply using their real room handles. Credential-bearing exports remain private and outside Git and room messages. Failed verification is routed through Foreman; repaired revisions are independently re-tested and re-inspected. Supplied checks alone are insufficient evidence.

## Preserved repair history and current structure

- Integrator rejected `e6df7a668de6c0c051116507e4d6c30bf03d2a40` for missing required split/reset arrays returning 400 rather than 422. Fabricator repair `998dc1ae32db14f7be18ce3369393fa17e59c7f0` independently passed Integrator's renewed checks and Test Pilot's independent groups and 147 supplied tests.
- Inspector then rejected that revision for reset scalar/ID type errors and contradictory imported completed retry bodies. Fabricator repair #7 validates omission/type/value distinctions and completed body/receipt/resource/path/actor/permission semantics across all five paths. Original rejection evidence remains outside the product repository.
- Fabricator also observed concurrent login timeouts. Password hashing now runs outside the transaction lock; account/session commits remain guarded against reset/import replacement. Monetary changes, request transitions, receipts, snapshots and state replacement retain atomic synchronization. Integrator, Test Pilot and Inspector must independently reassess this changed concurrency structure.
- The stock isolated harness on Windows passed a backslash suite path to Linux and collected zero tests. The preserved POSIX-path transport run executed unchanged supplied Stage 1 tests/plugin on an internal Docker network: 147 passed. This is separate from a stock CLI scoring claim; subsequent exact-revision evidence must retain the distinction.
- Current next gate: complete source/diff inspection and full independent regression runs on the repaired candidate, including authentication/control races and semantic import corruption. Acceptance and shipping remain pending; no source change is allowed after acceptance without renewed checks.
