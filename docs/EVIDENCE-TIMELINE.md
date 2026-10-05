# Evidence timeline

Dates below use UTC. Commit times establish source chronology, not the time an independent decision or shipment occurred. The copied reports retain author attribution and original revision labels. Full room provenance still requires the production session export.

## Stage 1: discovery, rejection, repair, independent re-verification, shipment

| Recorded event | Evidence/revision | Outcome |
|---|---|---|
| 2026-10-04 13:52–14:09: initial plan, implementation and portability validation | `9de7d78`, `6dfd858`, `e6df7a6` | Complete API candidate and primary evidence; no self-acceptance |
| Required split/reset arrays omitted produced 400 instead of 422 | Integration discovery; repair `998dc1a` at 14:34:54 | Absence/type distinction repaired; independent regressions reran |
| Inspector rejected wrong-type fixture scalars and inconsistent imported completed retry | Rejected `998dc1a`; repair `a5741a7` at 16:42:34 | Body amount 9 paired with amount-1 original receipt had been accepted. Typed fixture validation and five-path consistency repaired |
| Concurrent authentication checks exposed five-second timeouts | R7 evidence and retained timing logs | Scrypt moved outside transaction lock with guarded state commits. Later external-client checks passed; earlier failures were retained |
| Integrator rejected undocumented fixture request linkage handling | Rejected `7d72f80`; repair `16eda9c` at 17:09:59 | Unknown fixture field ignored across value shapes/statuses; legitimate API linkage/import behavior retained |
| Inspector rejected exact-number boundaries | Rejected `437b56d`; repair `1da4777` at 18:20:57 | Equivalent 4,301/5,000-digit retries, oversized amount classification and huge exponent disconnect repaired using exact compact number representation |
| Final documentation children preserved tested runtime | `d1030f3`, final `65a56da` at 18:28:07 | No squash/amend; repair histories remained visible |
| Integrator and Test Pilot independently reverified final revision | Final reports summarized in [factory receipt](evidence/stage-1-factory-receipt.md) | Raw numeric, import/rollback, races, privacy, auth/state replacement, source-unavailable restoration and unchanged 147 supplied tests passed |
| Inspector independently ACCEPTed final exact revision | [Decision](evidence/stage-1-inspector-accept.md), `65a56da7aa03c6690f12aa24c0dad372f2163437` | Acceptance bounded by explicit finite-load/timing/transport limits |
| Shipper verified accepted SHA from clean LF checkout/no-cache build | [Shipping report](evidence/stage-1-shipping.md) | Default/custom port, network-none health and documented behavior passed; Foreman final state SHIPPED |

Stage 1 service SHA256: `7bb43b5ac5e1bb8930e25f921119b72d7d0bd392aa2c009e8120a3847f45c0a9`. Shipper image: `sha256:c131b68d2e95735be17a1cf4cded5d68e5f799c0ed0e490ef0b063b33d3ff394`. The existing Stage 1 directory and its original EVIDENCE.md remain unchanged.

## Stage 2: candidate checks, repair and a retained blocker

| Recorded event | Evidence/revision | Outcome |
|---|---|---|
| 2026-10-04 21:19:57: cumulative Stage 2 plan | `05e39c0` | Stage 1 preservation and gated independent verification defined |
| 21:41–22:04: browser/API implementation and primary evidence | `316ca28` through `8a14985` | Holds/captures, bundled UI, seven keyed paths and actual old-state upgrade exercised |
| Independent integration found premature navigation reads, cold-login timeout and saturated TTL | [Historical blocked receipt](evidence/stage-2-blocked-receipt.md), exact `8a14985` | Supplied 147/35 passed, yet candidate blocked. First external 50-login wave timed out; 48 broken pipes recorded, cause unproved |
| 22:36–22:40: navigation repair sequence | `6f89001`, `7d97da1`, `41c7162` | First barrier passed original probe but a new check found stale balance 1000 instead of 900. Complete action-refresh gating repaired it |
| 22:49:19: repair evidence-only checkpoint | `6018879` | Primary exact-LF suites passed; qualified independent narrow navigation evidence followed. No ACCEPT |
| 2026-10-05: human CONTINUE and continuation plan | `900cdce` at 01:14:08; preserved [plan.md](../plan.md) | Resumed independent work. This human intervention is disclosed, not described as an untouched autonomous run. No TTL policy amendment |
| Renewed independent Integrator on exact `900cdce` | [Report](evidence/stage-2-integrator-900cdce.md) | New browser/navigation/source-stopped migration passed. One cold plus two warm 50-login waves passed at 2.251233/1.305286/1.051655s. Backend evidence reused from `8a14985` only with unchanged-byte correspondence |
| Test Pilot's first independent exact-900 candidate execution | [Report](evidence/stage-2-pilot-900cdce.md) | 420 API checks, nine race waves, 11 browser groups, navigation/recovery, live old-source-stopped upgrade and 147/35 unchanged supplied suites passed after preserved external-probe corrections |
| Fixed Pilot external auth protocol | Same Pilot report | Fresh corrected service; fixture reset before each cold/warm/warm 50-login wave; maxima 1.452108/0.897633/1.169264s. Earlier helper abort has unknown committed count |
| Stock Linux isolated judging CLI | Pilot report and original report hash therein | Claimed stage 2; 147/35 pass. Stage 3 overshoot fails on an unimplemented historical-view feature (1 failed, 2 passed). Report revision fields blank; host-pinned checkout/source/image hashes bind the result externally |
| TTL target independently reproduced on exact900 | Pilot astronomical `10^30` case and Inspector's earlier boundary analysis | Positive TTL accepted, but expiry saturates at year 9999; exact addition fails. Calendar-boundary rounding/OverflowError robustness findings remain applicable |
| 2026-10-05 22:16–22:17: final Windows stock Stage 1 attempt | [Final packet](evidence/stage-final-pilot-20261005.md), [error report](evidence/stage-1-final-windows-error-report.json) | Zero collected tests, error and no stage claim; Windows suite path failed in Linux pytest. Retained transport failure, not a service pass |
| 22:26–22:32: final stock Linux isolated runs | [Stage 1 report](evidence/stage-1-final-linux-report.json), [Stage 2 worktree report](evidence/stage-2-final-worktree-report.json) | Claimed stage 1 with 147/147 and stage 2 with 147/147 plus 35/35; elapsed about 109.17s/179.61s. Worktree CSS line-ending difference explicitly retained |
| 22:34–22:36: exact committed LF Stage 2 stock rerun | [Exact-LF report](evidence/stage-2-final-lf-report.json), [binding packet](evidence/stage-final-pilot-20261005.md) | Clean detached900 and runtime byte correspondence; 147/147 plus 35/35, claimed stage 2, about129.62s. Blank helper revisions externally bound; no ACCEPT |
| Final TTL and offline packaging checks | [Final Pilot packet](evidence/stage-final-pilot-20261005.md) | TTL exact-addition target fails again. Offline check recognizes uncommitted docs and finds only authentic room.json missing; historical declarations/authorship remain separate obligations |
| Documentation/package closeout | Documentation-only additions after exact900 | Product source remains frozen. Freeze and packaging are not acceptance or shipment; Stage 2 remains unaccepted |

Integrator's newer warm waves retain cumulative state without resets; Pilot's warm waves reset the fixture. These are different predeclared protocols. Passing either cannot explain the original cold failure. Original failed logs, corrected external probes and new output directories remain distinguished. No product or supplied-test change accompanied those external-probe corrections.

## Claims deliberately bounded by the evidence

- Stage 1 is shipped; Stage 2 is a checked candidate with an unresolved failure. Stages 3/4 are absent.
- Earlier Windows-to-Linux stock harness path failure remains a historical fact. The later Linux Stage 2 stock run is a separate success with explicit provenance limits.
- Separate unchanged supplied suites are directional evidence, never a hidden-test or all-input proof.
- Checks covered finite schedules and Chromium viewports; no universal timing, all-browser accessibility, sustained throughput or unbounded-state claim is made.
- Snapshots/tokens remained private in test processes. These public textual copies do not include exported state or raw credentials.
- Entrant editorial review, exact configured model declarations, production `room.json`, final package checks and public delivery artifacts must be verified separately.
