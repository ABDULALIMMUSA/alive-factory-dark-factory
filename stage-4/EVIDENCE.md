# Pocketful Stage 4 — post-submit evidence

> **Provenance:** This Stage 4 implementation was completed after the hackathon submission without BAND. It lives on the separate `post-submit/stages-2-4` branch. It does not rewrite the submitted BAND production record or imply that the original six-seat room produced Stages 3–4.

## Candidate verified

- Branch: `post-submit/stages-2-4`
- Isolated verification revision: `56f679906e0dd9b2884d3dc2c099b6bf051f0556`
- Pinned challenge source: `band-ai/dark-factory-wearedevs@803560d2a678ace1414465c098eb0ab5380ffade`
- GitHub Actions run: `37519748129`
- Official run id: `b6c144613ae54fb3a151e72175821ce8`
- Mode: official harness `isolated`

## Released-harness result

The pinned official cumulative Stage 4 harness reported:

| Suite | Collected | Passed | Failed |
| --- | ---: | ---: | ---: |
| Stage 1 | 147 | 147 | 0 |
| Stage 2 | 35 | 35 | 0 |
| Stage 3 | 6 | 6 | 0 |
| Stage 4 | 5 | 5 | 0 |

Harness disposition:

- **highest contiguous stage: 4**
- **claimed stage: 4 on the shipped checks**
- overshoot: none

## Implemented Stage 4 surfaces

- `POST /payments/{payment_id}/refunds`
- refund payments in the reverse direction with `refund_of`
- cumulative refund ceilings against the latest corrected amount
- refund idempotency and original-body replay
- refund affordability against available funds
- immutable captures and refund payments
- correction floor at already-refunded total
- `POST /correction-batches`
- settlement-operator authorization
- 1..32 distinct corrections
- settlement completeness and common effective instant
- combined atomic affordability
- historical total / available validation
- one shared strictly-increasing batch `recorded_at`
- `correction_batch_id` on batch-written revisions
- idempotent batch replay
- Stage 1–3 export/import compatibility, including revision history and statement snapshots

## Extra post-submit probes

After the official harness, the same CI job built the Stage 4 Docker image and ran `stage-4/postsubmit_checks.py`.

Result:

```text
postsubmit Stage 4 probes: PASS
```

Those probes additionally exercise:

- historical `as_of` opening balances;
- corrections and correction replay;
- revision history;
- `known_at` before a later correction;
- snapshot stability after a later write;
- refunds and refund replay;
- `refund_of` direction/linkage;
- refusing a correction below the refunded total;
- correction batches and batch replay;
- non-operator batch rejection;
- invalid naive temporal values;
- seeded payment `created_at` history.

## Stage 2 inheritance / known specification boundary

Stage 4 remains cumulative over the Stage 2 authorization implementation. Released Stage 2 checks pass. The previously disclosed mathematical edge remains: an unrestricted positive authorization TTL can exceed the representable four-digit RFC 3339 year range. The implementation does not present that impossible boundary as resolved; this evidence is intentionally explicit about it.

## Limit of this evidence

The released challenge harness itself warns that its public checks are directional and cover only part of the full tests used before judging. The results above are therefore exact claims about the tests that actually ran, not a fabricated guarantee about unseen tests.
