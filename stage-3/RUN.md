# Pocketful Stage 3

Stage 3 is cumulative: it includes every Stage 1 and Stage 2 behavior plus temporal statements and payment corrections.

## Build and run

From the repository root:

```sh
docker build -t pocketful-stage-3 ./stage-3
docker run --rm --name pocketful-stage-3 --cpus=2 --memory=2g -e PORT=8080 -p 8080:8080 pocketful-stage-3
```

Verify:

```sh
curl http://localhost:8080/health
```

Expected:

```json
{"status":"ok"}
```

The browser UI remains available at `http://localhost:8080/`. API behavior from Stages 1 and 2 remains cumulative.

## Stage 3 additions

Stage 3 adds:

- payment `created_at` history;
- `GET /me?as_of=...&known_at=...`;
- `GET /statement` with stable snapshot pagination;
- immutable payment revision history;
- `POST /payments/{payment_id}/corrections`;
- `GET /payments/{payment_id}/revisions`;
- historical total/available/held views;
- migration of Stage 1 and Stage 2 exports into the Stage 3 service.

The service keeps Stage-3-only history in an opaque export sidecar while retaining the Stage 2 ledger shape, so older same-team exports remain importable.

## Official directional harness

Using the pinned event challenge package:

```sh
python -m harness run --track pocketful --repo /path/to/alive-factory-dark-factory --stage 3 --mode isolated --out /tmp/pocketful-s3
```

A successful Stage 3 run should show Stages 1, 2 and 3 passing and the Stage 4 overshoot suite failing, with `claimed stage: 3`.

The released harness is directional only; hidden judging covers additional specification boundaries.
