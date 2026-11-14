---
name: render-look
description: MUST load before touching anything visible in the bbport/Bloodborne path tracer or answering a complaint about how it looks. Triggers on any look report or request, e.g. "fake light", "light here", "too dark/bright", "foggy", "milky", "blob", "puddle", "water", "reflection", "mirror", "shadow", "fog", "mist", "glow", "flicker", "colour/color", "orange/green/magenta", "exposure", "fire", "lamp", "moon", "sky", "looks fake/CG/wrong", or a screenshot of the game. Rules: docs/LOOK_GUIDE.md (dark gothic, more dramatic than stock, stock art kept) and docs/PHOTOREAL_GUIDE.md (physically believable). Covers rt.cfg live knobs, shader hot sync, F9 stock A/B, live_vision measure/grab, the free camera and look_check.py numbers.
---

# Render look

Goal for the whole game: **dark gothic, more dramatic than stock, stock art kept** (palette,
grading, fog colour, mood). `docs/LOOK_GUIDE.md` holds the 14 rules, the numeric targets and the
rule-to-knob map. Read it before a change; quote the rule a change serves.

Never assume: every change gets RT shots, the stock (F9) shot of the same frame and numbers from
`look_check.py`. A knob that "loaded" is not proof; the shot and the numbers are.

## Targets (from LOOK_GUIDE, check every shot)

| What | Target |
|---|---|
| moonlit pale surfaces (petals, stone tops), low top 10% luma | 115-135 |
| shadow floor p5 | 14-23, pixels under 5 below 0.5% |
| contrast p90/p20 | 5.5-8 |
| moon-lit highlight tint (Lab) | a -3..+2, b -4..+2 (neutral, no olive) |
| warm hues | fire, lamps and blood only |
| saturation | falls as luminance rises |
| overall exposure log level | -5.2..-5.6 (BB_RT_EXPOSURE_KEY, -5.5 now) |

## Realism (docs/PHOTOREAL_GUIDE.md)

Gothic sets the **mood**; physics makes the frame read as **real**. PHOTOREAL_GUIDE has 16
measurable rules, the rule-to-knob map and a "CG tells" checklist; **LOOK_GUIDE wins a conflict**
(level, tonemap, post chain, stock albedo). Run the CG-tells list on every sheet. The checks
that come up most:

- **Shadow in the open is not black.** Sky fill keeps a moon shadow about 2-3x darker in luma
  than lit ground of the same material, never crushed (rule 4 with the LOOK floor).
- **Contact hardening.** The moon penumbra is about 0.0093 x the occluder distance; shadows are
  sharp at contact. Fire shadows come from the flame size (rules 7-8).
- **Grounded contacts.** No light gap under feet or props. AO acts only on stock ambient and
  never darkens moon or lamp light (rules 9-10).
- **Bounded bounce.** GI_STRENGTH stays 1. Bounce colour is local, so no green moonlit petals
  (rule 11).
- **Fresnel.** Puddles mirror at grazing angles, not head-on (rule 12; WATER_F0 0.02). Wet ground
  under water is darker than dry (rule 13, `BB_RT_PUDDLE_WET`).
- **Clean, not smeared.** No trails, no boiling (still-pair `diff` in dark bands under 1.5),
  and shadowed texture keeps at least 0.8x stock detail (rule 15).
- **Highlights roll toward white.** Lamp cores are near-white; there are no clipped orange blobs
  (rule 2).

## Hot-reload loop (no restart)

- **Knobs:** edit `D:\modding\bbport-rt\out\rt-live\rt.cfg` (`KEY=value` lines). The file is
  re-read on change. The look knobs are live: EXPOSURE*, MOON*, GI_STRENGTH, GI_DEBUG,
  THIN_TRANSMIT, REFLECT_STRENGTH, FX_FOG*, FILL_*, EMITTER_*, AO_*, HALO*, SKY_*, FOG_STOCK,
  BOUNCES. These are read once at boot and need a restart: SHADOWS, SKY, FX_SMOKE, WATER_SHEET,
  GBUF_NORMAL, GI_SER, DLSS_RR*, OMM, PTLAS, EXCLUDE, SHADOW_SPEC, FX_CAP. Write the file
  with ASCII and invariant numbers (no "0,5" locale commas).
- **Shaders:** `ninja -C out\gpu bb-probe` rebuilds the SPIR-V, then
  `"C:/msys64/clang64/bin/python.exe" tools/sync-live-shaders.py D:/modding/bbport-rt-perfall/out/gpu D:/modding/bbport-rt/out/rt-live/shaders`
  hot-swaps them. The rt_gi.comp moon code lives in `rt_sky_layer_comp`. Only C++ changes need
  a game restart. Kill bb-probe before linking it; `rt-gi-test` builds while the game runs.
- **Stock A/B:** `BB_RT_PAUSE=1` in rt.cfg is the same switch as F9 (RT off; remove it for on).
  Never focus the game window or send OS keys/mouse (user rule). Shoot both sides of the same frame. Wait about 1 s after a toggle or knob change; exposure adapts.
- **Launch** (PowerShell tool, run in background): `D:\modding\bbport-rt\out\rt-live\run-hot.ps1`
  with `-Name viewN -Exe D:\modding\bbport-rt-perfall\out\gpu\bb-probe.exe` and
  `-Extra @{ BB_UPSCALER='dlss'; BB_RT_MOON_CACHE='...\rt_moon.txt'; BB_RT_SKY_CACHE='...\rt_sky' }`.
  Run `um` only from the PowerShell tool.

## Screenshots and numbers

```powershell
um win shot --exe bb-probe.exe X.png --scale 0.5        # writes X.png and X_small.png
& "C:/msys64/clang64/bin/python.exe" tools\look_check.py stats rt_small.png stock_small.png
& "C:/msys64/clang64/bin/python.exe" tools\look_check.py diff a_small.png b_small.png
& "C:/msys64/clang64/bin/python.exe" tools\look_check.py sheet out.png a_small.png b_small.png
```

- `stats` prints mean, p5/p20/p50/p90/p95, the share under 5, p90/p20, and the Lab tint of the
  low frame's top 10% and mid band.
- `diff` shows whether the view moved: about 10-20 when only the player moved, 40+ when the
  camera moved. Below 5 means nothing changed.
- `sheet` builds a contact sheet. Read the image yourself; numbers alone never prove a look.
- `mask OUT.png A.png [L]` paints the pixels under the p5 (or luma L) magenta. Run it before
  chasing a low p5: canopy and trunks backlit by the sky go near black by physics and are fine.
  Only crushed ground, walls or faces are faults.
- Eye adaptation pulls the mean back, so judge the percentiles and tints, not the mean. A global
  lift (more sky, more GI) is mostly undone by adaptation; it changes ratios, not levels.
- Fires drift: a burning area moves 15-25 luma over minutes. Compare A/B only inside one run,
  interleaved (base, X, base, X, base) with 2-3 shots each, never against an older base:
  `tools\look_ab.ps1 -Sets '','BB_RT_X=1','','BB_RT_X=1','' -N 2 -Stock` (restores rt.cfg).
- Keep shots in the scratchpad. Never put a shot that shows the chat or desktop in front of the
  user.

## Live vision (effects in time)

Flicker, sway, boiling and adaptation need frames in time, not single shots.
`tools\live_vision.py` captures the game window with DXGI duplication (venv
`out\vision-venv`, run with its `Scripts\python.exe`). Regions are `name=x0,y0,x1,y1` fractions
of the game image.

- `measure --sec 6 fire=0.80,0.58,0.95,0.85 mantel=...` per region: mean, flicker sd %, p2p,
  main Hz, frame step, optical-flow motion. Run it on RT, set BB_RT_PAUSE=1, wait 3 s, run it on stock.
- `tools\pixel_noise.py --frames 40 name=...` per-pixel temporal sd (speckle, boiling) with the
  exposure drift divided out; static camera. Moving cloth and fire read high by nature.
- `stream --sec 60 ...` one line per second; `fps` raw capture rate; `grab OUT.png`.
- The RT capture reaches only 11 fps at 3172x1328 (stock 88): the copy waits behind the RT GPU
  work. The sd and p2p are still right; Hz above ~5 and motion are not comparable across modes.
- Light timing from the game itself: `BB_RT_DIRECT_LIST_LOG=2` logs every light, every frame
  (`=1` every 30 frames), with `RT dlist raw` rows of the game's draws within 6 m.

**MCP server `bbrt`** (`tools\bbrt_mcp.py`, registered in `.mcp.json` here and in
`C:\Games\Bloodborne`): the same loop as tools, images returned inline. Prefer it when loaded.
`game_status`, `vision_measure` / `vision_grab` / `vision_strip` (each with `stock_ab`),
`vision_motion_map` (where the image changes), `stock_toggle`, `knobs_get` / `knobs_set`,
`knob_ab` (interleaved sets, restores rt.cfg), `pad_hold` / `freecam_cycle`, `lights`
(per-light game vs RT flicker), `log_grep`.

## Free camera (debug camera)

Needs `debug_camera=1` in `C:\Games\Bloodborne\bbport-windows\bbport.ini` at boot. It is kept
on, so no restart is needed. Drive it with `tools\freecam.ps1`, which writes the live pad file
`D:\modding\bbport-rt\out\rt-live\pad` (src/runtime_pad.c; tokens cross circle square triangle
l1 r1 l2 r2 l3 r3 options up down left right, sticks `lx= ly= rx= ry=` 0..255, 128 = centre).

| Command | Effect |
|---|---|
| `freecam.ps1 cycle` | hold Cross + click L3: normal -> **fly** -> **fixed** -> normal |
| fly: `hold -Tokens 'ly=0' -Ms 800` | forward (ly=255 back, lx strafe) |
| fly: `rx=` / `ry=` | turn / pitch |
| fly: `r2` / `l2` | up / down (fast; use short holds) |
| fixed: `ly=0` etc. | camera stays put, the **player walks** inside the view |

**Wide view with the player in it:** from normal mode run `cycle` (fly), back off
(`ly=255` 700 ms), rise (`r2` 500 ms), pitch down (`ry=255` short), run `cycle` (fixed), walk the
player into frame, shoot. Then run `cycle` again to return to normal.

- Never send r2/l2 in normal mode; they attack and fire.
- Flying past the map edge shows a white void, which is not a render bug.
- `diff` between shots confirms which mode you are in. The fly camera starts where it last
  flew, not at the player, so check the mode before trusting a count of cycles.

**Bring the player first.** Streaming and level of detail follow the **player**, not the camera.
A spot the camera flies to while the player stands far away shows low-detail meshes and blurry
textures. Walk the player there (normal mode, or fixed mode with the camera parked), then fly the
camera around the player.

**Fly like a player, not a drone.** Far objects use low-detail meshes and textures (LOD), and
the RT capture only has what the G-buffer drew, so distance hides or fakes problems. Judge
materials, contact, shadows and fire light from **player distance (2-10 m, eye height
1.5-3 m)**. Fly through the area along the paths a player walks: doors, stairs, under trees, next
to lamps and fires. Keep high, wide shots only for the overall mood and the shape of the light.
Steer in short steps: move 300-700 ms, take a 0.25-scale shot, look, adjust. 700 ms of `rx` is
about 45 degrees. Take an F9 stock shot at each stop you judge.

## Change procedure

1. Pick the LOOK_GUIDE (mood) or PHOTOREAL_GUIDE (realism) rule and shoot a baseline: RT and stock, `stats`, a sheet. For wide
   areas, use a free-camera view and the close normal view.
2. Change one knob in rt.cfg, or one shader with a sync. Shoot again with the same view and
   wait for adaptation.
3. Keep the change only if the numbers move toward the target, nothing else leaves its band, and
   the sheet looks more gothic with the stock palette kept. Otherwise revert it.
4. Check at least two areas (a field and an interior or lamp-lit area) before you propose a
   default. A knob default changes in code only after the user approves; log it in
   docs/PATH_TRACING.md.
5. Clean up: delete scratch shots and restore rt.cfg to the agreed set.

## Don'ts

- No new art style, no colour grading of our own, no blanket saturation or contrast boost.
- No per-area hacks when a game-wide rule would work.
- No fake lights unless strictly necessary. Every light has a source: the moon, sky, a lamp or
  a fire. A dark area is fixed by its real source (sky, bounce, emitter reach), never by turning
  `BB_RT_FILL_VIS` off or raising `FILL_FLOOR`/`FILL_SKY_KEEP`; those bring back the game's
  designer fills. If no real source can do it, ask the user, use the minimum, and log why in
  docs/PATH_TRACING.md.
- **Magic is the exception** (user rule, 2026-11-09): light from something magical and not real
  (the messengers' bath, insight and arcane glows, ghostly or eldritch effects) may be "fake":
  keep the game's light for it even with no physical fixture. Ordinary scenes still need a
  real source.
- No warm cast on moonlit surfaces. Fog stays the stock pale mist colour.
- Do not deploy to `C:\Games\Bloodborne\bbport-pathtracing` without asking the user.
