# Pocketful Stage 2

From the repository root, build and start the cumulative browser and HTTP API:

```sh
docker build -t pocketful-stage-2 ./stage-2
docker run --rm --name pocketful-stage-2 --cpus=2 --memory=2g -e PORT=18886 -p 18886:18886 pocketful-stage-2
```

Open http://localhost:18886 in a browser. Health is GET /health. Default PORT is
8080; choose any unused port and map it to the matching container PORT. The
example avoids an existing host8080 service. Stop the foreground container with
Ctrl+C. All assets and dependencies are bundled; runtime needs no outbound access.
The image is self-contained, standard-library Python and vanilla HTML/CSS/JS,
running as an unprivileged user. State is intentionally ephemeral on restart.

API requests to /requests and /authorizations return JSON by default. Browser
navigation with Accept: text/html receives the app. All required screens are
directly reachable. Sign up to create a zero-balance account; the test reset API
can seed balances and existing history. No deposit/top-up endpoint is provided.

Wallet totals move only through immediate payments, request payments, settlements
and captures. Open authorization remainders reserve funds; available is total
minus held. Reads and writes evaluate deadline expiry under the same transaction
lock used for money, captures, receipts and snapshots. Password verification runs
outside that lock, rechecking the current account before committing a session.
JSON numeric identity is exact across integral/fraction/exponent forms.

Seven write paths use caller/method/path-scoped keys and immutable original
responses. Browser payment retries retain the submitted body/key after success
or uncertainty; changed inputs start a new operation. A read generation prevents
older wallet refreshes from replacing a newer result. Decimal form parsing uses
integer arithmetic and rejects excess decimal places instead of rounding.

GET /_test/export and POST /_test/import support both this service's snapshots
and shipped Stage1 exports. Migration preserves accounts, hashes, tokens,
permissions and original receipts; old cached receipt shapes stay original.
Snapshots include private credentials. Keep them out of Git and shared logs.

HTTP checks replace isolated service data; pass a second service for portability,
and optionally a shipped Stage1 service to exercise old exports:

```sh
python stage-2/checks.py http://localhost:18886 http://localhost:18887 http://localhost:18888
```

Exact numeric identity and portable retry regressions cover all seven paths:

```sh
python stage-2/numeric_checks.py http://localhost:18886 http://localhost:18887
```

For browser fault/viewport checks, a development environment with Playwright and
Chromium can run `browser_checks.py` with the Stage2 URL, shipped Stage1 URL and
a screenshot output directory. These testing dependencies are not runtime dependencies.

The final evidence document records actual executed tests, browser screenshots,
resource/asset checks and exact revision. Acceptance belongs to independent seats.
