# Pocketful Stage 1

From the repository root, build and start the self-contained HTTP service:

```sh
docker build -t pocketful-stage-1 ./stage-1 && docker run --rm --name pocketful-stage-1 -e PORT=8080 -p 8080:8080 --cpus=2 --memory=2g pocketful-stage-1
```

On PowerShell, execute the two commands separately if `&&` is unavailable.
Health is `GET http://localhost:8080/health`. The image also supports any other
`PORT` with a matching port mapping. No runtime network access or manual setup is
needed. Stop the foreground container with Ctrl+C.

The implementation uses Python's standard library only. State is in memory and is
ephemeral. A process-wide transaction lock covers reads, writes, idempotency claims,
and control operations, making committed states observable atomically. Passwords
use salted scrypt. JSON decimal/exponent amounts are parsed exactly, and balances
use integer arithmetic. Idempotency compares a tagged canonical JSON value tree,
scoped by caller, HTTP method and path; successful responses are stored separately
from mutable records.

Unauthenticated `POST /_test/reset` loads the specified fixture. `GET /_test/export`
returns a portable private snapshot; `POST /_test/import` validates and replaces
state atomically. Snapshots include hashes and tokens: keep them outside Git and
shared room artifacts. Reset invalidates all earlier credentials and retries.

Run the behavioral checks against a running container (these replace its data):

```sh
python stage-1/checks.py http://localhost:8080
```

For migration checks, start a second container and pass both addresses:

```sh
docker run --rm --name pocketful-stage-1-destination -e PORT=8091 -p 8091:8091 --cpus=2 --memory=2g pocketful-stage-1
python stage-1/checks.py http://localhost:8080 http://localhost:8091
```
