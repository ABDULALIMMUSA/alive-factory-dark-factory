# 3D visual system

The judge-facing ALIVE FACTORY demo is intentionally a **procedural 3D factory**, not a rendered background.

## Visual metaphor

Software is represented as physical glowing artifacts moving through a factory:

1. **Build** — the Fabricator assembles a candidate.
2. **Challenge** — the candidate enters independent verification.
3. **Reject** — evidence can stop the conveyor and turn the line red.
4. **Repair** — failure evidence routes back to the builder.
5. **Prove** — the repaired revision goes through falsification again.
6. **Ship** — acceptance opens the release gate and the line accelerates into shipping.

This turns the abstract Dark Factory protocol into a visual causal system: **bad evidence physically prevents downstream motion**.

## Procedural 3D elements

The browser constructs the environment at runtime with Three.js:

- six glossy toy-like autonomous worker robots;
- central glowing build reactor and sparks;
- articulated robotic arms and overhead crane;
- ground, upper curved and helical conveyors;
- software-package cubes with generated code/check/integration icons;
- holographic status panels generated with CanvasTexture;
- autonomous AGV carts and inspection drones;
- agent station halos and point-light beacons;
- an evidence spine with moving evidence pulses;
- build / verify / accept gates;
- factory windows, catwalks, pipes, lamps and staging crates;
- cinematic bloom and tone mapping;
- orbit/zoom camera and scripted camera choreography.

No reference image is used as a runtime background. The demo source itself generates the world.

## Evidence integrity

The Stage 1 replay is a visual retelling of the recorded production evidence. It is not a claim that the original six BAND agents are executing live in the browser.

- Stage 1: accepted/shipped, 147/147 supplied checks.
- Stage 2: released cumulative checks passed, but internal acceptance remained withheld over the disclosed extreme-TTL boundary.

Live demo: https://alive-factory-demo-production.up.railway.app
