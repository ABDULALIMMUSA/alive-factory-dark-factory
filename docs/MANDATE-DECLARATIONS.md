# Mandate declaration evidence

Mandate bodies were assembled during submission closeout from role briefings and recorded responsibilities. Their headers must state actual configurations. Available-model lists and model-family descriptions do not prove the selected model.

| Seat | Harness | Exact active model | Verification scope/source |
|---|---|---|---|
| Fabricator | Codex | `gpt-6.1-sol` | Own native current-session metadata and turn context, 2026-10-05 22:14:07.035 UTC; session `01a10e21-87ba-7023-b79d-74cc2ca76058`; originator `jam`, provider `openai`, result-repository cwd |
| Integrator | Codex | `gpt-6-astra` | [Selected metadata](evidence/model-integrator-closeout.md): matching environment/session IDs and three turn-context model records; CURRENT CLOSEOUT AUDIT ONLY, historical production model unverified |
| Inspector | Codex | `gpt-6-astra` | Inspector reconfirmed own-session selected-model metadata in reviews `e4a60b0d-2c56-4dfd-94ad-de040819c5fb` and `cfcc889d-b936-4546-b2ee-46cec3d44403`: native thread `01a10e21-5df4-7771-8ff8-eaa7a9717fc4`, turn contexts 2026-10-05 22:13:57.712–22:23:46.617 UTC. CURRENT CLOSEOUT ONLY; historical selection not established |
| Foreman | Codex | `gpt-6.1-sol` | [Selected metadata](evidence/model-foreman-closeout.md): both environment IDs and native session metadata match `01a10e20-05e1-76e0-8167-2c85ea0bec2e`; turn context at 2026-10-05 22:12:36.178 UTC. CURRENT CLOSEOUT ONLY; supersedes family-only declaration |
| Test Pilot | Codex | `gpt-6-sol` | [Final Pilot packet](evidence/stage-final-pilot-20261005.md): native session `01a10e21-498e-7790-bd35-5a6291202e05` matches both environment IDs; turn context at 2026-10-05 22:13:52.577 UTC. CURRENT CLOSEOUT ONLY; historical model unverified |
| Shipper | Codex | `gpt-6-luna` | Selected metadata in closeout message `5de38c15-eed8-4853-ad1c-aa52600f1ad3`: both environment IDs and session metadata match `01a10e21-6a50-79c1-bdc6-fd0b7bed01a7`; latest turn context at 2026-10-05 22:33:07.781 UTC. CURRENT CLOSEOUT ONLY; historical model unverified |

Fabricator's source is its matching local native session file under `C:\Users\DELL\.codex\sessions\2026\10\05\rollout-2026-10-05T23-14-01-01a10e21-87ba-7023-b79d-74cc2ca76058.jsonl`. Only session identity/provider and turn-context model/cwd/timestamp fields were extracted. Raw prompts and credentials were not copied. Current active-session verification does not by itself prove every historical production turn used the same model.

All six current headers now have verified named harness/model declarations. These prove current closeout configuration; they do not establish which models implemented or historically tested the product. That historical distinction is disclosed as an evidence limitation, not an additional operator eligibility gate. The full production room export remains the collaboration provenance. A nonempty header's offline syntax result alone cannot prove configuration, and unknown values must never be replaced with guesses.
