Bloodborne PC - Path Tracing edition (1.9.8.6 + pt2.3)
======================================================

This is SuperMedo's Bloodborne PC port with real-time path tracing built in:
moonlight, bounce light, shadows, reflections, water and puddle mirrors, traced glass.

CREDITS
- Bloodborne PC (the Windows port, launcher, DLSS/FSR, online, everything except
  path tracing): SuperMedo and the port's contributors.
  https://github.com/Supermedo/bloodborne_pc   (all credit for the port is his)
- Path tracing: Joao (this fork).
  https://github.com/Joaovitor404silva/bloodborne-pc-path-tracing
- Based on shadPS4 (GPL-2.0). Licences of every part are in the licenses folder.
Please report path tracing problems to the fork, not to SuperMedo.

ALPHA: early build, work is ongoing. Light sources, fire, fog, glows, water and the
overall look are being remade. Expect bugs and big changes between versions.

NEEDS
- A ray tracing GPU (GeForce RTX, Radeon RX 6000 or newer).
- Your own copy of the game. No game files are included.

INSTALL
1. Unzip anywhere (a new folder; do not unzip over another Bloodborne PC folder).
2. Start Bloodborne.exe and set the game up as in SuperMedo's port.
That is all: path tracing is on by default.

In game, press F9 to turn path tracing off and on and compare with the stock
lighting. Give it about 3 seconds after each press while the exposure adjusts.

WHAT IS DIFFERENT FROM SUPERMEDO'S 1.9.8.6
- bin\bb-probe.exe: the engine with the path tracer. bin\bbport_dlss.dll: the DLSS
  bridge with Ray Reconstruction; bin\nvngx_dlssd.dll: NVIDIA's Ray Reconstruction;
  bin\libc++.dll: a newer C++ runtime the engine needs.
- The launcher: a Path tracing section (Picture & performance) with the switch
  and the bounce light, reflection and shadow presets; its updates come from the
  path tracing fork (so an update never removes path tracing).

SETTINGS
- Picture & performance > Path tracing: on/off, then bounce light, reflections and
  shadows, each Auto (recommended), Low, Medium, High or Custom (the slider).
- More tweaks: BB_RT_* variables in Advanced > Diagnostics > Extra variables.
- Upscalers: DLSS, FSR 3.1 and FSR 4.1 work, with frame generation too.
- Seamless co-op runs its own engine (bb-probe-seamless.exe) without path tracing.

SOURCE
https://github.com/Joaovitor404silva/bloodborne-pc-path-tracing (path tracer and the
patch on SuperMedo's code) and https://github.com/Supermedo/bloodborne_pc
