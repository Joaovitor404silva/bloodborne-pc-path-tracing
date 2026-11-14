Bloodborne PC - Path Tracing ({rt}) - READ ME FIRST
====================================================

GET THE FULL DOWNLOAD ON GITHUB (one unzip, nothing to install):
https://github.com/Joaovitor404silva/bloodborne-pc-path-tracing/releases/latest
File: Bloodborne-Windows.zip

That download is SuperMedo's whole Bloodborne PC {base} with path tracing built in.
All credit for the port goes to SuperMedo: https://github.com/Supermedo/bloodborne_pc

This Nexus zip is NOT the full download. Nexus blocks .exe files, and both the
launcher (Bloodborne.exe) and the path tracing engine (bin\bb-probe.exe) are .exe.
This zip holds only 2 of the mod's files (NVIDIA's Ray Reconstruction DLL,
bin\nvngx_dlssd.dll, is in the GitHub download):
- bin\bbport_dlss.dll   DLSS bridge with Ray Reconstruction
- bin\libc++.dll        newer C++ runtime the engine needs

INSTALL
1. Download Bloodborne-Windows.zip from the GitHub link above.
2. Unzip it into a new folder (not over another Bloodborne PC folder).
3. Start Bloodborne.exe and set the game up as in SuperMedo's port.
Path tracing is on by default. In game, F9 switches it off and on to compare
(about 3 seconds while the exposure adjusts).

SETTINGS
Launcher > Picture & performance > Path tracing: the switch, then bounce light,
reflections and shadows, each Auto (recommended), Low, Medium, High or Custom.
DLSS, FSR 3.1 and FSR 4.1 all work, with frame generation too.

NEEDS
- A ray tracing GPU (GeForce RTX, Radeon RX 6000 or newer).
- Your own copy of the game. No game files are included.

ALPHA: early build, work ongoing. Report path tracing problems on the GitHub or
Nexus page, not to SuperMedo.
