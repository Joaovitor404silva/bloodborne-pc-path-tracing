# AgentLink host for bbport (private)

Generic spec: `D:\modding\Game-Crawler\docs\agent\2026-11-11-agent-layer-design.md` (AgentLink v1 ABI).
This file holds the bbport-specific parts. Not for the public Game Crawler repo.

## Facts (from code, 2026-11-11 review)

- No debug socket. Today's channels: rt.cfg hot reload, `BB_PAD_FILE` (polled at most every 20 ms, same-size edits within
  one second are dropped, `src/runtime_pad.c:765-772`), `pad_hold` adds 0.3 s (`tools/bbrt_mcp.py:298`).
- Pad merge point: `sample()` (`src/runtime_pad.c:~890`), called per `scePadRead` on the pad thread; it returns early when
  the overlay captures input (line ~898).
- Camera: `vk_camera_motion.h:94-99` (view, inv_view, proj[4], valid), written on the GPU thread
  (`vk_rasterizer.cpp:2870`); valid only on G-buffer frames and when `BB_UPSCALER` != none (`vk_rasterizer.cpp:291`,
  `vk_camera_motion.cpp:59`).
- RT build presents ~11 fps (docstring `tools/bbrt_mcp.py:178`, may be stale; spike measures).
- No player struct known. Leads: `scripts/patches.py` (Player No Dead, Debug Camera, Enemy Control), `patches/Bloodborne.xml`.
- `cheat_no_death` exists (`scripts/patches.py:54`): use it on every live agent run.
- Capture: `tools/live_vision.py` (dxcam, letterbox at :75-78).

## Host work

1. `src/agentlink_host.c`: create `Local\AgentLink_<pid>`, header, frame block (pad thread is fine as the frame clock).
2. Renderer: write the `camera` block (own seq, GPU thread only) once per finalised frame, viewport rect incl. letterbox.
3. `sample()`: read `command` (ttl), map world `move` to the left stick relative to the camera yaw, buttons by profile
   bits; keep `BB_PAD_FILE` + replay working; decide behaviour when the overlay has input (no injection).
4. Player block: pos/yaw/hp/area from the struct found in spike S3; until then pos = camera pos + profile offset, valid-mask
   flags it as proxy.
5. Profile `bloodborne.json`: buttons (roll=circle, attack=r1, heal=triangle, interact=cross, sprint=hold circle),
   stick calibration, stuck_dist 1.0 m while on proxy.

## Live checks

Invincible (`cheat_no_death`), hot sync where possible, 2 checks per plan: metric task once, kill agentd mid-goto -> stop.

## Built (2026-11-11) - status

- `gpu/shim/bbport_agent.cpp` = the host (lazy `Local\AgentLink_<pid>`, off with `BB_AGENTLINK=0`), host_kind PAD,
  up_axis 1 (Y up), caps STICKS. agentd computes the sticks; there is no world `move` mapping in the host.
- Camera block: `bbgpu_agent_camera` from `CameraMotion::OnConstants` (GPU thread), so only with an upscaler on.
  view = 3x4 rows [R|t], clip = (proj0 x, proj1 y, ., z); image v = 0.5 - 0.5 * ndc_y (checked live with agent_look).
- Player block: `bbgpu_agent_pivot` in `BloodborneCam::Apply` (game thread): pos = camera object +0xD0/D4/D8 (follow
  pivot, about head height), lock-on flag +0x154 == 1.0f, vel from samples. valid = POS|VEL|FLAGS|PROXY; no hp/area yet.
- `SetProbe(true)` keeps the camera-update jump installed without mouse capture (window.cpp `UpdateMouseCamera`, once,
  when `bbgpu_agent_wants_camera_hook()`). SetEnabled(false) keeps the jump while probing.
- Pad merge: `agent_merge()` in `src/runtime_pad.c` `sample()` after the injected sticks; skipped while the overlay
  has input. ttl checked in `bbgpu_agent_command` (stale -> nothing injected). Live: agentd killed -> 0 drift.
- Measured: cam 49 Hz, pad reads 48.5 Hz, pivot 74 Hz, apply ~14 ms, start lag ~210-310 ms, stop overrun 0.6-0.8 m,
  run 3.32 m/s, camera-relative movement, right_sign +1 (strafe checked live), right stick deadzone ~0.38 and
  4/27/49/132 deg/s at 0.4/0.55/0.7/1.0 (profile look_dz 0.38, look_exp 1.4).
- Open: area, entity names/kinds, lock-on flag once read 1 while not locked (re-check).

## Player + entities from memory (2026-11-11)

Address rule: runtime = 0x800000000 + (PS4 VA - 0x400000) + `m_cameraOffset` (patch VAs use eboot base 0x400000;
the community tables quote 0x800000000-based addresses, subtract 0x400000 first). Verified by vtables with a
read-only peek.

| What | Where (PS4 VA / offset) | Check |
|---|---|---|
| WorldChrMan | `[0x593E878]` | vtable 0x57301F0 |
| player ChrIns | `[WCM+0x60]` | vtable 0x578F310 |
| modules | `[P+0x3B0]`; data `[M+0x20]` (vtable 0x5735810), transform `[M+0x68]` | |
| hp / max | data +0xF8 / +0xFC (i32) | matches HUD within 1.2% |
| stamina / max | data +0x134 / +0x138 | |
| position (feet) | transform +0x1E0 float[3] | within 5 m of the camera pivot, else fall back to pivot + PROXY |
| char table | WCM+0x850: ChrSet*[0x3E], count = `[[WCM+8]+0x18]+2`; ChrSet = {u32 cap, entries*}; entry 0x38, ChrIns* at +0 | handle at chr+0x08, alive = hp >= 1 |

Sources: bbhost, LanternEngine, bloodborne-vr, BloodbornePC, Paleblood, stagvant patch decode.
Data +0x158 is not an ASCII name: entities publish `name = "hp <max>"`, `kind = 1`, `id = handle`.

`bbgpu_agent_pivot(camera, image_offset)` reads the player every call and scans the table every 100 ms (nearest 64
alive), all under `sigsetjmp` + `runtime_fault_recover` so a bad pointer cannot crash the game. Publishes
POS|VEL|HP|STAMINA|FLAGS (ALIVE = hp >= 1). Live: hp 763/1325 tracked through damage and heals; the entity reported
at 3.5 m attacked the player; markers project onto the scene.
