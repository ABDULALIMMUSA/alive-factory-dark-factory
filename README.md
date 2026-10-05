# Pocketful: the result of a six-seat software factory

Owner: ABDULALIM MUSA. Track: **Pocketful**, the Dark Factory challenge's wallet and payments service. Six Band coding-agent seats built, challenged, repaired and reviewed the work in a shared production room.

**Stage 1 is independently accepted and shipped. Stage 2 is a buildable, tested candidate with an unresolved contract failure; it is not accepted or shipped.** Stage 3 and Stage 4 were not implemented. Submission packaging is separate from product acceptance.

| Output | Recorded outcome | Exact revision |
|---|---|---|
| `stage-1/` | Inspector ACCEPT, then independent Shipper delivery PASS | `65a56da7aa03c6690f12aa24c0dad372f2163437` |
| `stage-2/` | Independent integration/Pilot evidence; supplied checks pass; TTL target failed/unresolved | `900cdcee3a98b8dcaf55dad9618199a0e649e924` |

The Stage 1 directory remains unchanged from its shipped revision. Stage 2 inherits Stage 1 and adds a browser product, reserved funds and partial captures. The [final independent Pilot packet](docs/evidence/stage-final-pilot-20261005.md) records stock Linux isolated claims of stage 1 (147/147) and stage 2 (147/147 plus 35/35), including a clean detached exact-LF Stage 2 run. The helper reports have blank revision fields; the packet binds them externally to the checkout and runtime hashes. These directional results do not establish full specification conformance: a repeated astronomical-TTL probe still fails exact expiry addition. Earlier external cold-login timing failures remain real and unexplained. Read the [judge summary](docs/JUDGE-SUMMARY.md) for the exact qualifications.

## Run the outputs

Use a running Linux Docker daemon. From this repository root, run each command separately:

```sh
docker build -t pocketful-stage-1 ./stage-1
docker run --rm --name pocketful-stage-1 --cpus=2 --memory=2g -e PORT=18080 -p 18080:18080 pocketful-stage-1
```

Stage 1 health: `http://localhost:18080/health`. It provides the JSON API. For the browser candidate, use a separate terminal:

```sh
docker build -t pocketful-stage-2 ./stage-2
docker run --rm --name pocketful-stage-2 --cpus=2 --memory=2g -e PORT=18886 -p 18886:18886 pocketful-stage-2
```

Open `http://localhost:18886`. Both images default to container port 8080; these examples use explicit alternate ports. Choose unused host ports. [Stage 1 RUN.md](stage-1/RUN.md) and [Stage 2 RUN.md](stage-2/RUN.md) contain the original procedures and behavioral-check commands. The alternate port mappings above are instructions, not a claim of an additional executed release verification.

Runtime dependencies and browser assets are bundled. State is in memory and clears on restart. Signup creates a zero-balance account; isolated test fixtures can seed money. There are no top-ups or bank integrations. Exported snapshots contain credentials and must remain private.

## Read the submission

- [FACTORY.md](FACTORY.md): seat ownership, setup, handoffs, rejection gates, costs and reuse.
- [mandates/](mandates/): six generic seat instructions; [declaration evidence](docs/MANDATE-DECLARATIONS.md) distinguishes verified configuration from missing proof.
- [Architecture and production line](docs/ARCHITECTURE.md): system boundaries and responsibility flow.
- [Evidence timeline](docs/EVIDENCE-TIMELINE.md): discovery, rejection, repairs, independent re-verification and shipment.
- [Evidence copies](docs/evidence/README.md): portable textual receipts and reports with hashes and disclosed formatting adjustments to the shipping report and Windows error report.
- [Judge summary](docs/JUDGE-SUMMARY.md), [90-second demo script](docs/DEMO-90-SECONDS.md) and [presentation outline](docs/PRESENTATION-OUTLINE.md).
- [plan.md](plan.md): preserved historical Stage 2 continuation plan. Its future-tense checks describe the dispatch at that checkpoint; later reports record what was actually executed. It provides no Stage 2 shipping authority.

## Submission status and provenance

These README/FACTORY texts were prepared by the Fabricator agent under the authorized documentation assignment. The entrant owns the final editorial choices; the drafting origin remains disclosed. Authorized agent drafting is not presented as a separate eligibility failure. The recorded human CONTINUE during Stage 2 is disclosed in the timeline, so this run is not described as a strictly uninterrupted autonomous run.

Packaging must include the full **production** room download as `room.json`, actual configured harness/model declarations, a public cloneable Git repository, the presentation and a video showing the factory operating. A closeout-room export cannot replace production provenance. Pilot's later offline check recognized the uncommitted documentation and found only `room.json` missing; it must be rerun on the final packaging revision. All six current declarations are now verified; historical model selection is transparently limited and is not an additional eligibility gate. Until the required submission artifacts and final checks are independently verified, this checkout is not described as submission-ready. Preserve the original Git history and failures; do not squash away the repair trail.
