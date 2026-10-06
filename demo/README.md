# ALIVE FACTORY — Interactive 3D Demo

Live demo: https://alive-factory-demo-production.up.railway.app

This directory contains the browser source for the judge-facing **ALIVE FACTORY 3D evidence world**. It is a procedural WebGL experience built with Three.js; the factory environment, robots, conveyors, reactor, drones, crates, lighting, evidence spine and replay transitions are rendered as actual 3D geometry rather than a background image.

## What the demo communicates

The six production seats are represented as distinct 3D worker agents:

- Foreman — orchestration and exact-revision routing
- Fabricator — implementation and repair
- Integrator — independent system verification
- Test Pilot — falsification and adversarial checks
- Inspector — independent acceptance
- Shipper — release verification

The **Replay Stage 1** control visualizes the recorded production loop:

`BUILD → CHALLENGE → REJECT → REPAIR → PROVE → SHIP`

When the recorded validation failure is reached, the production line visibly stops and turns red. The repair is routed back to the Fabricator, the repaired revision is independently re-tested, the Inspector opens the release gate, and the Shipper completes the runtime-verification sequence.

The replay is a visualization of evidence preserved in the repository and production `room.json`; it does **not** claim the six agents are executing live in the visitor's browser.

## Accuracy

- Stage 1: independently accepted and shipped; 147/147 supplied checks passed.
- Stage 2: released cumulative checks passed (147/147 + 35/35), but ALIVE FACTORY withheld internal acceptance over the disclosed extreme-TTL contract boundary.

Core principle: **Never trust the build. Trust the evidence.**
