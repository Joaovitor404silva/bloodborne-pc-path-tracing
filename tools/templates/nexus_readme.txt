Bloodborne PC - Path Tracing mod ({rt}) - READ ME FIRST
========================================================

GET THE FULL MOD ON GITHUB (one-click auto installer):
https://github.com/Joaovitor404silva/bloodborne-pc-path-tracing/releases/latest

This Nexus download is NOT the full mod. Nexus blocks .exe files, and the path
tracing engine is one: bin\bb-probe.exe (SuperMedo's game engine rebuilt with the
path tracer). It is only in the GitHub download. This zip holds the mod's other
3 files:
- bin\bbport_dlss.dll   DLSS bridge with Ray Reconstruction
- bin\nvngx_dlssd.dll   NVIDIA DLSS Ray Reconstruction
- bin\libc++.dll        newer C++ runtime the engine needs (the port's other
                        programs work with it too)

NEEDS
- Bloodborne PC {base} (SuperMedo), installed and working:
  https://github.com/Supermedo/bloodborne_pc/releases/tag/windows-v{base}
- A ray tracing GPU (GeForce RTX, Radeon RX 6000 or newer). Use DLSS or FSR 3.1.

INSTALL (recommended)
Download Bloodborne-PC-Path-Tracing-{rt}.zip from the GitHub link above, unzip it
and double-click "Install Path Tracing.bat". It backs up the files it replaces,
checks every file, sets up the launcher and can uninstall cleanly.

MANUAL INSTALL
1. Close the game and the launcher. Back up bin\bb-probe.exe, bin\bbport_dlss.dll
   and bin\libc++.dll.
2. From the GitHub zip, copy payload\bin\bb-probe.exe into the game's bin folder
   (this Nexus zip has the other 3 files: extract it over the game folder).
3. Launcher > Advanced > Diagnostics > Extra variables, add this line:
{rt_env}
4. Set the upscaler to DLSS or FSR 3.1 (not FSR 4.1 or automatic).
5. Start Bloodborne.exe. In game, F9 turns path tracing off and on.

UNINSTALL (manual)
Put back your backup of the 3 files, delete bin\nvngx_dlssd.dll and remove the line
from Extra variables.

ALPHA: early build, work ongoing.

Source code: https://github.com/Joaovitor404silva/bloodborne-pc-path-tracing
