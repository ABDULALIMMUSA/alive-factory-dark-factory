# Architecture and production line

This is a documentation view of the existing implementation and recorded responsibilities. It introduces no new product component or deployment requirement. Each stage is a standalone image; Stage 2 extends a copy of Stage 1, rather than depending on a running Stage 1 server.

## Product boundaries

| Boundary | Existing implementation | Reason and limit |
|---|---|---|
| Container | Digest-pinned Python 3.12 slim base; standard-library service; non-root user; configurable `PORT` | Single self-contained image, no outbound runtime dependency. Memory state clears on restart. |
| HTTP handler | JSON API, validation, authentication, route dispatch; Stage 2 also serves bundled HTML/CSS/JS | Browser/API content negotiation on shared routes. Test controls are for isolated fixtures and portability. |
| State transaction | Process-wide reentrant lock covering committed reads, writes, retry claims and state replacement | No transient partially committed transfer or import is exposed. State work serializes; no unlimited-throughput claim. |
| Exact money and body identity | Integer minor units; compact exact JSON-number representation and tagged canonical bodies | Equivalent numeric bodies can replay without binary rounding. Finite resource limits still apply. |
| Authentication | Salted scrypt outside transaction lock; guarded current-account/session commits | Reduces lock occupancy while guarding reset/import races. Prior timing failures remain unexplained. |
| Completed operations | Caller/method/path-scoped keys and immutable original successful responses | Historical replay does not recompute against mutable balances or terminal resources. Stage 1 has five keyed paths; Stage 2 adds authorize/capture for seven. |
| Portable snapshots | Export/import preserves accounts, hashed credentials, tokens, permissions, resources and retry receipts | Detached validation precedes atomic replacement. Snapshots are credential-bearing private data, not public demo artifacts. |
| Stage 2 reserved funds | Open remaining amounts determine held funds; available = total - held; capture/void/expiry under the state lock | Reservation and money movement share atomic state. Astronomical TTL expiry saturation remains failed/unresolved. |
| Stage 2 browser | Vanilla HTML/CSS/JS, exact decimal parsing via integers/BigInt, per-form operation identities, generation counters and pending-action barriers | Original payment key/body survive same-page uncertainty; stale reads cannot supersede later refreshes; navigation waits for the complete write action. Exhaustive browsers/reload recovery are not claimed. |

A browser write creates or reuses an operation identity, submits the body and key, then refreshes confirmed state. A refused or uncertain result preserves recoverable form state. The backend validates, acquires the state lock, evaluates expiry where relevant, resolves an existing completed claim or commits one atomic operation, and stores its successful original response. Successful HTTP replay returns that original response. Import validates a candidate state before installing it under the same lock.

Stage 1-to-2 upgrade is a portability test: export old state, stop the actual shipped Stage 1 source, import into Stage 2, then exercise the same browser token and original operation key/body. It is not a production database migration service. The independent exact-900 reports describe the executed no-reload proof.

## Factory boundaries

| Handoff | Required output | Receiving responsibility |
|---|---|---|
| Foreman -> Fabricator | Complete scoped job/spec, prerequisites and result path | Build the assigned behavior and primary evidence |
| Fabricator -> Integrator | Exact revision, requirements, commands, results, risks, next action | Independently verify integration and revision identity |
| Integrator -> Test Pilot | Qualified cumulative evidence with retained failures | Independently falsify behavior, races, browser states and recovery |
| Test Pilot -> Inspector | Exact revision and reproducible observations, including unresolved targets | Decide ACCEPT/REJECT/BLOCKED against complete requirements |
| Inspector -> Shipper | Explicit ACCEPT of one exact revision | Clean checkout/build/start and delivery verification only |
| Shipper -> Foreman | Exact accepted revision and release observations | Publish final qualified receipt |
| Any failed check -> Foreman -> responsible seat | Reproducer, expected/actual behavior and preserved log | Scoped repair, new revision and renewed independent verification |

Private execution tasks, shared assignment cards and the durable room plan serve different purposes. Evidence lives in new output directories; accepted source identity is bound by Git and runtime hashes. A room snapshot preserves intent. A shared task becoming Done records completed work, not an acceptance decision.

The production-continuation [plan.md](../plan.md) is preserved. This explanatory document is not a replacement live room plan or a new delivery roadmap. Read [FACTORY.md](../FACTORY.md) for setup and [the timeline](EVIDENCE-TIMELINE.md) for the actual outcomes.
