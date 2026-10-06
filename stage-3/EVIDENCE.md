# Pocketful Stage 3 — post-submit evidence

> **Provenance:** This Stage 3 implementation was completed after the hackathon submission without BAND. It is a technical continuation on the `post-submit/stages-2-4` branch and must not be represented as output from the original BAND production room. The submitted `main`, original `room.json`, and Stage 1 shipment evidence remain preserved.

## Candidate verified

- Branch: `post-submit/stages-2-4`
- Isolated verification revision: `56f679906e0dd9b2884d3dc2c099b6bf051f0556`
- Pinned challenge source: `band-ai/dark-factory-wearedevs@803560d2a678ace1414465c098eb0ab5380ffade`
- GitHub Actions run: `37519748129`
- Mode: official harness `isolated`

## Released-harness result

The pinned official harness reported Stage 3 as the highest contiguous stage for the Stage 3 image:

| Suite | Result |
| --- | --- |
| Stage 1 | PASS — 147 / 147 |
| Stage 2 | PASS — 35 / 35 |
| Stage 3 | PASS — 6 / 6 |
| Stage 4 overshoot | FAIL as intended for the Stage 3 image |

Harness disposition: **claimed stage 3**.

## Implemented Stage 3 surfaces

- payment timestamps and seeded `created_at`
- `GET /me?as_of=&known_at=`
- historical total / available / held
- `GET /statement`
- oldest-first statement ordering and stable `balance_after`
- opaque statement snapshot pagination
- immutable payment revision histories
- `POST /payments/{payment_id}/corrections`
- correction idempotency and stale-revision protection
- effective-time vs recorded-time semantics
- historical overdraft checks
- authorization `closed_at` and historical hold reconstruction
- Stage 1 / Stage 2 export migration

## Additional hardening

The post-submit branch also adds:

- one monotonic request clock for server-assigned timestamps and expiry decisions;
- endpoint-specific empty-body semantics;
- grouped historical-overdraft event sweeps so same-instant movements are evaluated atomically without quadratic rescans on large histories.

## Limit of this evidence

The event harness explicitly states that the released suite is directional and only covers part of the full contract used in judging. PASS here is therefore evidence that the released cumulative Stage 1–3 suites pass; it is **not** a claim that unknown hidden tests are proven in advance.
