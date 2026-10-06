# Pocketful Stage 4

Stage 4 is the cumulative Pocketful service: all Stage 1–3 behavior plus refunds and atomic correction batches.

## Build and run

From the repository root:

```sh
docker build -t pocketful-stage-4 ./stage-4
docker run --rm --name pocketful-stage-4 --cpus=2 --memory=2g -e PORT=8080 -p 8080:8080 pocketful-stage-4
```

Verify:

```sh
curl http://localhost:8080/health
```

Expected:

```json
{"status":"ok"}
```

The browser UI remains available at `http://localhost:8080/`.

## Stage 4 additions

Stage 4 adds:

- `POST /payments/{payment_id}/refunds`;
- cumulative refund limits against the payment's current corrected amount;
- immutable refund payments linked through `refund_of`;
- `POST /correction-batches` for settlement operators;
- settlement-completeness checks;
- atomic combined affordability and historical-overdraft checks;
- shared batch `recorded_at` and `correction_batch_id`;
- idempotent replay for refunds and correction batches;
- Stage 1–3 export/import compatibility, including statement snapshots and revision history.

## Official directional harness

Using the pinned event challenge package:

```sh
python -m harness run --track pocketful --repo /path/to/alive-factory-dark-factory --stage 4 --mode isolated --out /tmp/pocketful-s4
```

A successful Stage 4 run should show Stages 1 through 4 passing with `highest contiguous stage: 4` and `claimed stage: 4`.

The released harness is directional only; hidden judging covers additional specification boundaries.
