Real-time path tracing for [SuperMedo's Bloodborne PC port](https://github.com/Supermedo/bloodborne_pc) {base}: moonlight, bounce light, traced shadows and reflections, water and puddle mirrors, traced glass. **Alpha.**

## Download

**`Bloodborne-PC-Path-Tracing-{rt}.zip`** below: unzip, double-click `Install Path Tracing.bat`, start `Bloodborne.exe`. In game, **F9** turns path tracing off and on.

## What changed since {prev_rt}

- Updated for Bloodborne PC **{base}** (was {prev_base}).
{changes}
## Needs

- Bloodborne PC {base} (SuperMedo), installed and working: [windows-v{base}](https://github.com/Supermedo/bloodborne_pc/releases/tag/windows-v{base})
- A ray tracing GPU (GeForce RTX, Radeon RX 6000 or newer). Upscaler DLSS or FSR 3.1.

Updated Bloodborne PC since you installed path tracing? Just run this installer: it sees the update and installs fresh. Do not run the old version's uninstaller after updating Bloodborne PC.

The mod is 4 files: `bin/bb-probe.exe` (the port's engine with the path tracer), `bin/bbport_dlss.dll` (DLSS bridge with Ray Reconstruction), NVIDIA's `bin/nvngx_dlssd.dll` and `bin/libc++.dll` (a newer C++ runtime the engine needs; every other program and DLL of the port was checked to work with it). Path tracing works in normal play; the launcher's Seamless co-op mode runs its own engine (`bb-probe-seamless.exe`) without it.

## Upscaler

Keep DLSS or FSR 3.1; the installer switches FSR 4.1 (the launcher's automatic pick) to one of them.

## VirusTotal scan

{virustotal}

No game files are included. GPL-2.0.
