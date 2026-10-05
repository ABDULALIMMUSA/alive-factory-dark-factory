# Factory: six seats with separate build and acceptance ownership

Prepared by the Fabricator agent for the entrant's editorial review. This describes the recorded factory and a reusable setup procedure. It does not certify submission eligibility, human authorship or uninterrupted autonomy.

The factory's main design choice is to make a build handoff an inspectable claim. The implementing seat supplies a revision and evidence. Other seats independently try to break it, check its requirements and decide whether that exact revision can proceed. The release seat then verifies delivery from a clean checkout. Completing an assignment or freezing source never substitutes for acceptance.

## Seats and setup

| Band seat | Mandate file | Owns | Does not own |
|---|---|---|---|
| Foreman | [foreman.md](mandates/foreman.md) | Scope, work packets, routing, durable outcomes | Product implementation or its acceptance |
| Fabricator | [fabricator.md](mandates/fabricator.md) | Implementation, primary checks, scoped repairs | Independent acceptance |
| Integrator | [integrator.md](mandates/integrator.md) | Whole-system integration and revision correspondence | Silent product repairs |
| Test Pilot | [test-pilot.md](mandates/test-pilot.md) | Independent behavioral falsification | Release authorization |
| Inspector | [inspector.md](mandates/inspector.md) | Requirements/evidence review and exact-revision decision | Repairing and accepting its own build |
| Shipper | [shipper.md](mandates/shipper.md) | Clean delivery verification of an accepted revision | Substituting an unaccepted newer revision |

The mandate files were assembled during submission closeout from the seats' role briefings and recorded responsibilities. They are reusable instructions, not claimed byte-identical copies of the original production prompts. Named harness/model declarations belong at the start of each mandate. All six current headers are verified; [declaration evidence](docs/MANDATE-DECLARATIONS.md) records the closeout-only scope. A family name or list of available models cannot establish a more specific selected ID. Historical production selection is a disclosed evidence limitation, not an additional eligibility gate or a reason to invent values.

To reproduce the factory on a different problem:

1. Configure six distinct Band seat identities with the linked generic mandates and provider access. Record each actual harness and model. Three seats is the challenge minimum; this factory uses six to separate implementation, integration, falsification, acceptance and delivery.
2. Give all local seats the same absolute result checkout and a separate location for checks. Prepare Git, Docker and browser tooling; keep credentials outside both the product and public evidence. Remote seats need shared artifacts they can open.
3. Open a production room, add the seats, and verify addressed messages and replies in both directions. A listed but non-serving participant cannot receive work.
4. Dispatch the complete job and specification once. The Foreman decomposes packets on the shared Work board and publishes the room plan. Track private execution steps separately. Each handoff carries the complete requirements, not just a reference to another message.
5. Build and verify in the sequence below. New check outputs use new directories so first failures survive. Export the full production session at the end and retain unsquashed Git history.

Setup permissions are chosen before the run so routine checks can proceed. During a submitted dark run, the guide permits only the initial human dispatch for each stage: unresolved requirements must produce an evidenced blocker. This recorded run includes a later human CONTINUE; no claim of strict dark-run autonomy is made.

## Production line and handoff contract

`Foreman -> Fabricator -> Integrator -> Test Pilot -> Inspector -> Shipper -> Foreman receipt`

Foreman routes rejected work back to the responsible seat. Fabricator reproduces the named defect, repairs its scope and returns a new revision. Affected independent checks and inspection run again. Every product edit after acceptance invalidates that acceptance.

Each packet includes six fields:

1. Full revision and source/image correspondence.
2. Requirements covered, including inherited requirements.
3. Commands, topology, limits and deadlines actually used.
4. Observed results and links to preserved logs.
5. Defects, uncertainty, reused evidence and unexecuted work.
6. Explicit next-seat verification or decision.

Primary executions of a peer-authored probe remain primary evidence. Independent authorship and independent execution are separate facts. Reused results keep their original tested revision; unchanged byte correspondence can justify reuse but cannot turn an old execution into a fresh one. Inspectable local handoffs include absolute paths; remote handoffs require shared content.

The shared board is for cross-seat assignments. Historical Stage 1 production/repair cards finished through the final receipt. Stage 2 had separate build, integration, falsification, inspection, release and navigation-repair assignments. An investigation marked complete means its packet is complete, even when its result is BLOCKED. It does not mean the product passed.

## Why this design, and what it costs

Six seats increase handoff latency and duplicate some checks. They also give different failure-finding methods a place in the line: integration traces, adversarial inputs, source/evidence review and clean deployment. Most product construction remained Fabricator work; the other seats contributed verification, discovery and release evidence. We do not claim equal code volume or use message count as teamwork evidence.

The service uses a single transaction lock, integer monetary arithmetic, exact JSON numeric identity and immutable successful retry receipts. This makes atomicity and replay behavior inspectable, at the cost of serialized state work and in-memory growth. Authentication hashing runs outside the transaction lock with guarded state commits. Stage 2 bundles its browser assets and adds read generations and write-action navigation barriers. [Architecture](docs/ARCHITECTURE.md) describes these boundaries. No sustained-load or unbounded-growth benchmark was established.

Recorded elapsed times are wall-clock spans between Git commits, not provider compute time or final shipment duration:

| Measurement | Observed value | Source |
|---|---|---|
| Stage 1 initial implementation to final shipped-source commit | 4h 26m 38s, 2026-10-04 14:01:29–18:28:07 UTC | Git commits `6dfd858` -> `65a56da` |
| Stage 2 plan to navigation-repair evidence checkpoint | 1h 29m 22s, 2026-10-04 21:19:57–22:49:19 UTC | Git commits `05e39c0` -> `6018879` |
| Stage 1 Shipper mapped default/custom health | 0.502s / 0.637s | [Shipping report](docs/evidence/stage-1-shipping.md) |
| Stage 2 Pilot default/restart/custom health | 2.463s / 4.951s / 1.777s | [Pilot report](docs/evidence/stage-2-pilot-900cdce.md) |
| Final stock Linux isolated Stage 1 / exact-LF Stage 2 elapsed | About 109.17s / 129.62s, including harness work | [Final Pilot packet](docs/evidence/stage-final-pilot-20261005.md), copied report timestamps |
| Token totals, model spend and provider bill | Not available in inspected evidence | No zero-cost claim or estimate invented |

Stage 2 independent continuation occurred later and is outside the initial 1h29 span. A useful cost report would preserve production-session usage per seat, pricing/date, measured total tokens, elapsed time and any unpriced usage. Missing measurements remain missing.

## A bad result the factory caught

Inspector rejected `998dc1a` after reset type errors and a snapshot that paired a retry body for amount 9 with the original amount-1 receipt. Fabricator reproduced the contradiction, repaired imported body/receipt/resource validation and fixture classifications, and added focused checks. Integrator then found a separate undocumented fixture-field regression. Later Inspector rejected `437b56d` for huge exact JSON-number failures. Each repair returned through independent checks before Inspector accepted `65a56da`; Shipper clean-built that accepted SHA. The [timeline](docs/EVIDENCE-TIMELINE.md) retains all loops.

Stage 2 integration discovered navigation reads racing a withheld payment. A first fix passed the original reproducer but exposed a stale-balance case; the completed action-refresh barrier repaired it. Renewed independent navigation, browser and migration checks passed. The independent reviewers still withheld acceptance over the TTL target. Stopping with a qualified blocker is part of the factory's outcome, not a completed stage claim.

## Final recorded limits

Stage 1 is SHIPPED at `65a56da7aa03c6690f12aa24c0dad372f2163437`. Stage 2 exact `900cdcee3a98b8dcaf55dad9618199a0e649e924` has passing supplied and specification-derived observations, but no ACCEPT or shipment. The unrestricted-positive-TTL/exact-expiry/RFC3339 conflict remains failed/unresolved; floating calendar-boundary robustness findings remain visible. Original external cold-login timeouts and broken pipes have no established root cause. Later bounded passes do not erase them.

Tests cover finite inputs, schedules and Chromium viewports. State is intentionally ephemeral. The final Windows stock invocation recorded zero collected tests and no stage claim. Later Linux stock runs claimed stage 1 and stage 2; the final Stage 2 run used clean detached committed LF bytes. Their blank revision fields are externally bound by the [final Pilot packet](docs/evidence/stage-final-pilot-20261005.md). A repeated TTL probe still failed. None of these results proves hidden-test success or grants Stage 2 acceptance.

[plan.md](plan.md) is retained historical continuation intent, not final completion evidence. Portable textual [evidence copies](docs/evidence/README.md) preserve independent authors and exact scopes. Current model declarations are verified; their historical scope remains explicitly limited. Authorized agent drafting is disclosed, without treating it as an additional eligibility failure. The production room export, final package compliance, public repository, slides and video remain packaging obligations until independently verified. This document never substitutes for the production log.
