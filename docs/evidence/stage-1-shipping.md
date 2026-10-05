# Pocketful Stage 1 — Shipper Release Verification

## 1. Gate and accepted revision

- Inspector decision: `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-stage-1-inspector\decision-65a56da.md` — explicit **ACCEPT** for `65a56da7aa03c6690f12aa24c0dad372f2163437`.
- Scope: this report verifies that revision only. No product or documentation edits were made.
- Final disposition: **DELIVERY PASS / SHIPPED** for the accepted SHA, with the host-port mapping note in field 6.

## 2. Clean checkout and source identity

- Product repository: `C:\Users\DELL\Documents\ALIVE FACTORY\pocketful-result`.
- Fresh checkout: `C:\Users\DELL\Documents\ALIVE FACTORY\checks\pocketful-shipper-65a56da`.
- Checkout command: `git clone --no-hardlinks --no-checkout --config core.autocrlf=false --config core.eol=lf <product-repository> <fresh-checkout>`, then `git config core.autocrlf false`, `git config core.eol lf`, and `git checkout --detach 65a56da7aa03c6690f12aa24c0dad372f2163437`.
- `git rev-parse HEAD`: `65a56da7aa03c6690f12aa24c0dad372f2163437`; `git status --porcelain=v1`: empty after checks and evidence log moved outside checkout.
- Accepted `stage-1/service.py` SHA-256: `7bb43b5ac5e1bb8930e25f921119b72d7d0bd392aa2c009e8120a3847f45c0a9`; checkout and running container hashes matched.
- `stage-1/RUN.md` SHA-256: `e15539c3ba3fc5b2e7a2ca1b8f381d68d5afd5f1634aed7c90744f1e1d421627`.
- Authoritative spec SHA-256: `65497dea09a8b432598c71662320cf66c3550e183cfd76e2d7f97318e0d30aa4`.

## 3. Build and image identity

- Docker context/version: `desktop-linux`; client/server `29.8.1`.
- Build command from the fresh checkout root: `docker --context desktop-linux build --no-cache -t pocketful-shipper:65a56da ./stage-1` — exit 0.
- Build used pinned base `python:3.12-slim@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`.
- Image tag: `pocketful-shipper:65a56da`; image ID and local repo digest: `sha256:c131b68d2e95735be17a1cf4cded5d68e5f799c0ed0e490ef0b063b33d3ff394` (`linux/amd64`).
- Image config: user `65534:65534`; command `python /app/service.py`.

## 4. Runtime, health, limits, and ports

- Network isolation command: `docker --context desktop-linux run -d --name pocketful-shipper-none-65a56da --network none --cpus=2 --memory=2g -e PORT=18879 pocketful-shipper:65a56da` — started successfully. In-container `GET http://127.0.0.1:18879/health` returned `200 {"status":"ok"}` within the 60-second bound. `/app/service.py` SHA-256 matched the accepted source hash. Inspect showed `network=none`, 2,000,000,000 NanoCPUs, 2,147,483,648 memory bytes, no mounts.
- Default PORT bridge command: `docker --context desktop-linux run -d --name pocketful-shipper-default-65a56da -e PORT=8080 -p 18080:8080 --cpus=2 --memory=2g pocketful-shipper:65a56da` — `GET http://127.0.0.1:18080/health` returned `200 {"status":"ok"}` in 0.502s. Inspect confirmed target container port 8080, bridge network, same image, limits above, and no mounts.
- Custom PORT bridge command: `docker --context desktop-linux run -d --name pocketful-shipper-custom-65a56da -e PORT=18091 -p 18091:18091 --cpus=2 --memory=2g pocketful-shipper:65a56da` — `GET http://127.0.0.1:18091/health` returned `200 {"status":"ok"}` in 0.637s. Inspect confirmed target container port 18091, bridge network, same image, limits above, and no mounts.
- Both mapped health requests reached the app, confirming it listens for the default and custom `PORT` values across the container interface.

## 5. Documented behavior and delivery checks

Executed from the fresh checkout with host Python `3.12.10`; command outputs are preserved in the adjacent `shipper-delivery.log`.

- `python stage-1/checks.py http://localhost:18080` — **PASS**, 668 HTTP checks; covers 50-way retries on all five write paths, competing writes, state races, atomic settlements, portable snapshots, and exact balance boundary.
- `python stage-1/checks.py http://localhost:18080 http://localhost:18091` — **PASS**, 668 HTTP checks including two-container migration.
- `python stage-1/repair_checks.py http://localhost:18080 http://localhost:18091` — **PASS**, 661 HTTP checks; reset type/value/rollback cases, imported retry consistency and atomic rejection, concurrent password checks versus reset, and portable import behavior.
- `python stage-1/numeric_checks.py http://localhost:18080 http://localhost:18091` — **PASS**, 711 HTTP checks; exact numeric identity/conflict, portable receipts, rollback, failed-key reuse, and settlements.
- All services used the same independently built image; tests completed with exit code 0. No product files were modified.

## 6. Risks, environment notes, and final disposition

- Host port 8080 was occupied by an existing container `stage-1-counter-1` before Shipper started. I left it untouched and mapped container default PORT 8080 to host 18080; the custom PORT 18091 used matching host/container ports. The app's documented internal PORT behavior and host reachability passed. To use the literal `-p 8080:8080` on this host, the incumbent listener must first be moved or stopped by its owner.
- The no-outbound check was performed with Docker network mode `none`; it proves startup and health without network access. Functional API suites ran on bridge-mapped localhost ports.
- Inspector's accepted limitations remain: finite checks do not prove every input length/schedule, unbounded state growth, or sustained-load throughput; earlier colocated auth timing failures remain with cause unproven. The stock Windows harness scoring transport remains broken for Linux backslash paths; this verification ran the documented Python scripts directly.
- No reproducible blocking delivery defect found. **Independent delivery PASS; SHIPPED receipt issued for `65a56da7aa03c6690f12aa24c0dad372f2163437` only.**

### Log format

shipper-delivery-raw.log is a UTF-16LE archive of the captured command/results; use Get-Content -Encoding Unicode to read it without NUL characters. eport.md remains the readable summary. The command/result text was retained when creating the UTF-8 readable log and the UTF-16LE archive.
