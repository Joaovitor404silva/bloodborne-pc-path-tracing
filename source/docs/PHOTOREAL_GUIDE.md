# Photoreal guide: Bloodborne path tracing

Companion to `docs/LOOK_GUIDE.md`. LOOK_GUIDE sets the art (dark gothic, more dramatic than stock,
stock art kept); this guide sets the **physics** that makes a frame read as real instead of CG.
Where the two disagree, **LOOK_GUIDE wins** (see section 4). Measure with `tools/look_check.py`
(stats, diff, sheet) on half-res shots, always next to the F9 stock shot of the same frame.

Tags: **[src]** from the sources in section 5, **[start]** a starting value by judgement, to tune.
"Linear" ratios below use `(luma/255)^2.2` as a rough inverse; the game's tonemap bends this, so
compare ours against stock of the same frame rather than against the absolute number.

## 1. Rules

1. **One slow exposure, scene ratios kept.** Exposure is one global scale that moves at most about
   1 EV per second and never lifts a backlit subject to front-lit level. A dark interior stays
   darker than the moonlit street outside it after adaptation settles. *Check:* turn 90 deg from
   the moon side to the lit side; p50 settles in 1-3 s with no overshoot above the final value;
   doorway test: interior p50 below exterior p50. *Why:* eyes and cameras adapt slowly and only
   partly; per-view instant exposure makes every place the same brightness, a video-game tell.
   [src: Filament / Frostbite physical camera, EV100]

2. **Highlights roll off toward white, small and few.** Brightening a coloured source drives it
   toward white (path to white), not to a clipped saturated patch. A flame or lamp core is
   near-white; its halo and the wall it lights keep the hue. *Check:* pixels with luma > 235 near a
   lamp have mean C* < 25; pixels with one channel at 255 and another below 128 are under 0.1% of
   the frame; LOOK_GUIDE rule 12 (> 250 luma under 0.5%). *Why:* film and every filmic curve
   (Hable, ACES, AgX) desaturate the shoulder; hard per-channel clipping gives the "neon orange
   blob" and hue skew of CG. [src: Hable, Hill/Narkowicz ACES fits, Sobotka AgX]

3. **Albedo stays in the physical range.** Real non-metals have linear albedo of about 0.03-0.85
   (sRGB about 50-240): charcoal 0.04, wet dark earth 0.08, grass 0.1-0.25, weathered stone
   0.2-0.4, plaster 0.6-0.8, fresh snow 0.8-0.9. Nothing natural is below 0.02 or above 0.9.
   *Check:* `BB_RT_GI_DEBUG=3` (albedo as used): linear p1 >= 0.02 and p99 <= 0.9 over geometry.
   *Why:* albedo near 1 makes multi-bounce GI gain energy (interiors glow, colour bleeding goes
   neon); near 0 makes holes. Stock textures may carry baked light, so clamp only the albedo the
   **bounce** uses; the displayed surface keeps stock albedo (LOOK rule 14). [src: Filament,
   physicallybased.info, PBS course]

4. **Lit to shadow ratio follows moon and sky.** Skylight is moonlight scattered by the same air,
   so on a clear night direct moon to sky on flat ground is about 5-10 : 1, as in daylight. A cast
   shadow in the open on the same material is 4-10x darker in linear, about 2-3x in luma [start].
   Under mist or overcast the ratio falls toward 2 : 1. *Check:* luma inside / outside a wall
   shadow on the same cobbles in an open street. *Why:* a shadow that is too light is fake
   ambient; a black shadow in the open means the sky is missing. Fits LOOK rule 3 (p90/p20 5.5-8).
   [src: Wikipedia Daylight / Moonlight lux tables, Frostbite light units]

5. **Lamps dominate their near field and fall off as 1/d^2.** A gas lamp gives tens of lux at 2 m
   against about 0.25 lux of full moon, so the pool around a lamp is several stops brighter than
   the moonlit ground. *Check:* lamp pool p90 >= 1.5x moonlit ground p90 in the same frame;
   linear luma along the ground at 2 m vs 4 m from the lamp is 3-5x (1/d^2 is 4x); no visible
   edge or ring where the light's range ends. *Why:* linear or windowed falloff and hard range
   circles read as game lights; inverse square makes small hot pools. [src: Frostbite light units;
   Mullen: day-for-night fails when other sources must expose realistically]

6. **Night colour is lighting, not a filter.** Moonlight is about 4100 K (slightly warmer than
   sun) yet looks neutral to cool because of the Purkinje shift; the sky-lit shadow side is a
   little cooler than the moon-lit side. *Check:* LOOK rules 4-5, plus b*(shadow side) minus
   b*(lit side) of the same material is -1 to -5; lamps, faces and blood keep their hue. *Why:*
   real moonlit landscapes look like a lowered, slightly cooled, desaturated day; a global blue
   LUT is the cliche. [src: Wikipedia Moonlight, Patry 2021, In Depth Cine, Mullen on day-for-night]

7. **Penumbra matches the source size.** Penumbra width = occluder-to-receiver distance x source
   angular diameter. Moon: 0.53 deg, so x0.0093: a 3 m post gives a 3 cm soft edge at its tip,
   0 at its base. *Check:* every shadow sharpens toward its contact point (contact hardening);
   measured 10-90% edge width within 2x of the prediction. *Why:* uniform blur on all shadows is
   the shadow-map tell; real shadows are sharp at contact and soften with distance. [src: PBS
   course, Unreal path tracer source radius]

8. **Local sources cast shadows from the visible flame.** Candle flame 1-3 cm, torch 10-30 cm,
   lamp glass 15-30 cm. A 0.5-1 m source gives softbox shadows that no candle makes. *Check:* an
   arm or chair leg 0.5 m from a torch casts a shadow with a sharp core; candle-lit statues show
   crisp shadow edges near contact. *Why:* hard little shadows from fire are what make firelight
   read as fire. The intensity size (`BB_RT_EMITTER_FLAME`, near-field falloff) and the shadow
   sampling size should be separate. [src: Frostbite area lights, Cyberpunk Overdrive ReSTIR DI]

9. **Every contact is grounded.** Props, feet and walls meet the floor with a dark contact line and
   no gap of light. *Check:* zoomed crops of boots, barrels, crates, coffin bases: no line of
   brighter pixels between the object and its shadow (peter-panning); crease luma below both
   neighbouring faces. *Why:* floating objects are the strongest CG tell after noise.

10. **AO is not a second shadow.** With traced GI, AO applies only to light that is not traced
    (the stock ambient), never to the moon or lamp terms, with a small radius (0.2-0.5 m), and it
    weakens on bright albedo (multi-bounce). *Check:* GI on, AO on vs off: open-ground luma moves
    < 5%; no dark halo wider than 2 px around a character standing near a wall; bright stone
    crevices darker than open stone by at most 2x. *Why:* double-counted AO gives the dirty,
    outlined "SSAO look". [src: Jimenez 2016 GTAO, Lumen docs]

11. **Bounce light is real and bounded.** GI colour = incoming light x albedo, so a lit red cloth
    tints a pale wall within about 1 m, weaker each bounce; moonlit areas do not turn green from
    grass. *Check:* wall C* within 0.5 m of a lit coloured surface > wall C* 3 m away, and never
    above the source surface's C*; `BB_RT_GI_STRENGTH` stays 1 (other values break energy
    conservation); A/B `BB_RT_GI_CLAMP` 4 vs 64 in a lamp-lit room changes mean luma < 10%.
    *Why:* missing bleeding looks flat; GI gain above 1 makes everything glow. [src: Lumen,
    Metro Exodus EE RTGI, Portal RTX]

12. **Fresnel on every surface.** Dielectric F0 is 0.02-0.05 (water 0.02); reflectance rises to
    near 1 at grazing angles. Specular only where a source can be seen. *Check:* a puddle seen
    along the street (grazing) reflects lamps >= 3x brighter than the same puddle seen from
    above; no glints inside a moon shadow except from lamps (specular occlusion). *Why:* mirrors
    that are equally strong head-on look like chrome; real wet ground mirrors only at a distance.
    [src: Filament, PBS course]

13. **Wet stone darkens and sharpens.** Wet porous stone gets darker (about 0.5-0.8x albedo) and
    smoother; pooled water is roughness 0.05-0.2 on top of it. Lamp reflections on wet cobbles are
    vertical streaks stretched toward the viewer. *Check:* lamp reflection streak length/width >= 3
    on a wet street; no seam where reflections switch from traced to stock at
    `BB_RT_REFLECT_MAX_ROUGH`. *Why:* round, sharp blobs on rough wet ground are the CG version;
    streaks are what a camera sees. Small patches only (LOOK rule 12). [src: Lagarde wet surfaces]

14. **Fog extinguishes and scatters.** Distance lowers contrast exponentially; shafts appear when
    looking toward the light (forward scattering, Henyey-Greenstein g about 0.3-0.7 for mist
    [start]); lamps get a halo that grows with fog density; fog in a shadowed alley is darker than
    fog in the open. *Check:* p90-p10 of geometry at 50 m <= 0.5x that at 5 m in misty areas;
    shaft contrast facing the moon >= 2x facing away; halo visible round every lamp in mist.
    *Why:* uniformly lit fog is a flat overlay; directional, shadowed fog reads as air. Strength
    stays inside LOOK rule 10. [src: Hillaire 2015 Frostbite volumetrics, Alan Wake 2 GDC]

15. **Clean but not smeared.** Light reacts at once; no ghost trails; no boiling; texture
    survives. *Check:* (a) a flame flicker or door opening changes the lit area within 4 frames;
    (b) a torch carried past a wall leaves no trail longer than 0.1 s; (c) on a still frame pair,
    `look_check diff` in dark bands < 1.5 luma (no boiling, no crawling); (d) Laplacian variance
    of a shadowed wall crop >= 0.8x stock (no oil-paint smear); (e) no 10-50 px blotches in
    corners. *Why:* denoiser lag, smear and blotches are the signature of real-time path tracing.
    [src: Cyberpunk / Alan Wake 2 talks, DLSS Ray Reconstruction coverage]

16. **Camera effects come from stock only.** Bloom, depth of field, grain and vignette stay the
    game's own. Our HDR must feed stock bloom so that only emitters and the moon disc glow.
    *Check:* moonlit stone (<= 135 luma) has no glow; bloom radius round a lamp within +/-25% of
    stock. *Why:* bloom on non-emitters and added lens effects read as filters. (LOOK rule 14.)

## 2. Rule to knob map

| Rule | Knob(s), or change needed |
|---|---|
| 1 Slow exposure | `BB_RT_EXPOSURE_RATE` (0.03), `BB_RT_EXPOSURE_MAX` (1.5 EV), `BB_RT_EXPOSURE_KEY` |
| 2 Roll-off | `BB_RT_EXPOSURE_WHITE`; path to white: **shader change in `rt_exposure.comp`** (luminance-based shoulder that desaturates the top stop; the game tonemap itself stays) |
| 3 Albedo range | `BB_RT_GI_DEBUG=3` to measure; clamp: **shader change in `rt_gi.comp`** (bounce albedo only) |
| 4 Moon/sky ratio | `BB_RT_GI_FILL_SKY`, `BB_RT_SKY`, `BB_RT_MOON_MIN`, `BB_RT_FILL_ENCLOSED`, `BB_RT_AMBIENT_CUT` |
| 5 Lamp falloff | `BB_RT_LAMP_SOURCE`, `BB_RT_LAMP_RANGE`, `BB_RT_EMITTER_RANGE`, `BB_RT_EMITTER_PEAK`, `BB_RT_GLOW_RANGE`; smooth end of range: check `EmitterFalloff` in `rt_direct.comp` |
| 6 Night colour | `BB_RT_AMBIENT_COOL`, `BB_RT_LAMP_HUE`; night shift: **new code in `rt_exposure.comp`** (LOOK map rule 5) |
| 7 Moon penumbra | `BB_RT_MOON_ANGLE` (3 = real moon), `BB_RT_MOON_HALF` |
| 8 Flame shadows | `BB_RT_EMITTER_FLAME`, `BB_RT_GLOW_FLAME`, `BB_RT_CANDLE_SOURCE`; separate shadow radius: **shader change in `rt_direct.comp`** |
| 9 Contact | `BB_RT_SHADOW_BIAS`, `BB_RT_SHADOW_TMIN`, `BB_RT_SHADOW_GAP` (local lights only), `BB_RT_GBUF_NORMAL` (boot) |
| 10 AO | `BB_RT_AO`, `BB_RT_AO_RADIUS`, `BB_RT_AO_FALLOFF`, `BB_RT_GAME_AO`, `BB_RT_AMBIENT_KEEP_*`; multi-bounce AO: **shader change in `rt_ao.comp`** |
| 11 Bounce | `BB_RT_GI_STRENGTH` (keep 1), `BB_RT_GI_CLAMP`, `BB_RT_BOUNCES`, `BB_RT_GI_LAST_BOUNCE_CACHE` |
| 12 Fresnel | `BB_RT_REFLECT_STRENGTH` (keep 1), `BB_RT_WATER_F0` (0.02, physical), `BB_RT_PUDDLE_EDGE`, `BB_RT_PUDDLE_WET` (wet bed 0.6), `BB_RT_WATER_SHEET_F0`, `BB_RT_AMBIENT_SPEC_CUT`, `BB_RT_SHADOW_SPEC` (boot) |
| 13 Wet stone | `BB_RT_WATER_ROUGH`, `BB_RT_REFLECT_MAX_ROUGH`, `BB_RT_WATER_RIPPLE`; wet darkening and streaks: **shader change in the reflection pass (`rt_gi.comp`)** |
| 14 Fog | `BB_RT_FX_FOG_G`, `BB_RT_FX_FOG_SHAFT`, `BB_RT_FX_FOG_STRENGTH`, `BB_RT_FX_FOG_DIST`, `BB_RT_FX_FOG_STEPS`, `BB_RT_HALO*`, `BB_RT_MIST*`, `BB_RT_HAZE_*` |
| 15 Denoise | `BB_RT_GI_DENOISE`, `BB_RT_GI_HISTORY` (boot), `BB_RT_RESTIR_GI_M`, `BB_RT_RESTIR_GI_AGE`, `BB_RT_RESTIR_GI_RADIUS`, `BB_RT_RESTIR_*`, `BB_RT_DIRECT_KEEP`, `BB_RT_AO_HISTORY`, `BB_RT_DLSS_RR` (boot) |
| 16 Camera | None by design; check `BB_RT_HALO` does not add glow to non-emitters |

## 3. CG tells checklist

- [ ] Same exposure in every place; caves as bright as streets.
- [ ] Saturated orange or red clipped blobs at lamps and flames, no white core.
- [ ] Shadows equally soft everywhere; no contact hardening; candle shadows like a softbox.
- [ ] Light gap under feet, props or wall bases (peter-panning).
- [ ] Dark AO outlines round characters and wall edges; dirt in every crease.
- [ ] Everything glows faintly in shadow (flat ambient, GI gain above 1, albedo above 0.9).
- [ ] Neon colour bleeding, or green moonlit petals from grass bounce.
- [ ] Chrome-like puddles seen from above; glints inside shadow with no source.
- [ ] Round, sharp lamp reflections on rough wet stone instead of streaks.
- [ ] Hard circle where a lamp's range ends; linear falloff.
- [ ] Fog as an even veil: no shafts toward the moon, no halo round lamps, lit in shadow.
- [ ] Global blue tint over lamps, faces and blood.
- [ ] Ghost trails behind torches or enemies; lighting lagging a flicker.
- [ ] Boiling or crawling noise in dark corners; 10-50 px blotches.
- [ ] Oil-paint smear: shadowed stone loses its texture against stock.
- [ ] Bloom or glow on moonlit stone; added grain, vignette or lens dirt.

## 4. Conflicts with LOOK_GUIDE (art direction wins)

- **Absolute level.** Real full-moon scenes are about EV100 -2 to -3, far darker than any game
  shows. Realism keeps only the ratios (rules 4, 5); the level follows stock (LOOK rule 13).
- **Purkinje.** A full scotopic model greys the whole frame. Only LOOK rules 4-5's light shift.
- **Shaft strength.** Dense forward-scattering mist can give strong shafts; LOOK rule 10 keeps
  them quiet (5-15 luma above the mist).
- **Lamp vs moon range.** Physically lamps are 5+ stops above moonlight; stock compresses this.
  Keep the order (lamp pools brighter, rule 5) at stock's levels and LOOK rule 6's short reach.
- **Tone mapping and camera.** Realism practice would pick AgX or ACES and might add grain to mask
  denoiser noise. LOOK rule 14 keeps the game's tonemap and post chain; nothing is added after it.
- **Albedo.** Realism would re-author out-of-range textures; LOOK rule 14 keeps stock albedo, so
  only the bounce albedo is clamped.
- Settled 2026-11-10: `BB_RT_WATER_F0` is the physical 0.02 (it was 0.5); the sewer is sheet
  water with its own `BB_RT_WATER_SHEET_F0`.

## 5. Sources

Shading, units, tone mapping
- https://google.github.io/filament/Filament.html
- https://blog.selfshadow.com/publications/s2013-shading-course/ (PBS course)
- https://blog.selfshadow.com/publications/s2014-shading-course/ (Moving Frostbite to PBR: light units, EV, area lights)
- https://www.ea.com/frostbite/news/physically-based-unified-volumetric-rendering-in-frostbite (Hillaire 2015)
- https://physicallybased.info
- http://filmicworlds.com/blog/filmic-tonemapping-with-piecewise-power-curves/ (Hable)
- https://github.com/TheRealMJP/BakingLab (Hill ACES fit)
- https://knarkowicz.wordpress.com/2016/01/06/aces-filmic-tone-mapping-curve/
- https://github.com/sobotka/AgX
- https://therealmjp.github.io/posts/a-closer-look-at-tone-mapping
- https://www.activision.com/cdn/research/Practical_Real_Time_Strategies_for_Accurate_Indirect_Occlusion_NEW%20VERSION_COLOR.pdf (GTAO)
- https://www.fxguide.com/?p=43362 (Lagarde, physically based wet surfaces)

Path-traced games and engines
- https://www.nvidia.com/en-us/geforce/news/cyberpunk-2077-ray-tracing-overdrive-update-launches-april-11/
- https://www.nvidia.cn/on-demand/session/gdc24-gdc1002 (Cyberpunk Overdrive, GDC 2024)
- https://www.nvidia.cn/on-demand/session/gdc24-gdc1003 (Alan Wake 2 path tracing, GDC 2024)
- https://www.remedygames.com/article/gdc2024
- https://www.nvidia.com/en-us/geforce/news/metro-exodus-pc-enhanced-edition-ray-tracing-dlss/
- https://blogs.nvidia.com/blog/portal-prelude-rtx-remix-studio-driver/
- https://dev.epicgames.com/documentation/en-us/unreal-engine/path-tracer-in-unreal-engine
- https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-technical-details-in-unreal-engine
- https://hothardware.com/news/nvidia-debuts-dlss-45-ray-reconstruction (denoiser artefacts)

Night, perception, cinematography
- https://en.wikipedia.org/wiki/Daylight (lux table: full moon about 0.25 lux)
- https://en.wikipedia.org/wiki/Moonlight (about 4100 K)
- https://advances.realtimerendering.com/s2021/jpatry_advances2021/index.html (Purkinje shift)
- https://www.indepthcine.com/videos/moonlight-lighting
- https://www.rogerdeakins.com/?p=219226 (Mullen on day-for-night)
- https://sony-cinematography.com/articles/night-lighting---part-1---tackling-large-night-exteriors/
