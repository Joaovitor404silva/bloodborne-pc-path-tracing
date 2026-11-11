Bloodborne PC - Path Tracing mod (pt2.2)
========================================

Real-time path tracing for SuperMedo's Bloodborne PC port: moonlight, bounce light,
shadows, reflections, water and puddle mirrors, traced glass.

ALPHA: this is an early build and work is ongoing. Light sources are being remade,
along with effects (fire, fog, glows), water and the overall look. Expect bugs, places
that look wrong, and big changes between versions.

NEEDS
- Bloodborne PC 1.9.8.4 (SuperMedo), already installed and working:
  https://github.com/Supermedo/bloodborne_pc/releases/tag/windows-v1.9.8.4
- A ray tracing GPU (GeForce RTX, Radeon RX 6000 or newer). Use DLSS or FSR.

INSTALL
1. Close the game and the launcher.
2. Unzip this folder anywhere (inside the Bloodborne PC folder is easiest).
3. Double-click "Install Path Tracing.bat". If it does not find the game folder,
   it asks for it (the folder with Bloodborne.exe).
4. Start Bloodborne.exe as usual.

In game, press F9 to turn path tracing off and on and compare with the stock
lighting. Give it about 3 seconds after each press while the exposure adjusts.

The mod is 4 files: bin\bb-probe.exe (the port's engine with the path tracer),
bin\bbport_dlss.dll (DLSS bridge with Ray Reconstruction), NVIDIA's
bin\nvngx_dlssd.dll and bin\libc++.dll (a newer C++ runtime the engine needs; the
port's other programs work with it too). The 3 files it replaces go to "rt-backup"
in the game folder.
It checks every copied file. Path tracing is switched on by variables the installer
adds to the launcher: Advanced > Diagnostics > Extra variables.

If the game is in a protected folder (Program Files, for example), Windows asks for
administrator rights. If something goes wrong (a file in use by the game or an
antivirus), the installer puts every file back and says what failed.

UNINSTALL
Double-click "Uninstall Path Tracing.bat": the backup goes back, the Ray Reconstruction
DLL and the launcher variables are removed, and the folder is stock 1.9.8.4 again.

UPSCALER
Path tracing was not tested with FSR 4.1 (the launcher's automatic pick). If your
upscaler is FSR 4.1 or automatic, the installer sets DLSS on NVIDIA cards, else FSR 3.1.
Keep DLSS or FSR 3.1. Uninstall puts your old setting back.

FIXED IN pt2.2
Path tracing no longer stays off after the game starts (earlier versions could keep
the stock lighting for the whole session: loading filled its memory and never freed it).
FSR 4.1 and frame generation are not tested again yet: keep DLSS or FSR 3.1.

NOTES
- A Bloodborne PC update replaces bin\bb-probe.exe and removes path tracing. Install
  the mod version made for the new Bloodborne PC; do not run the old uninstaller.
- Path tracing works in normal play. Seamless co-op runs its own engine
  (bb-probe-seamless.exe) without path tracing.
- Without a ray tracing GPU the game keeps its own lighting.
- No game files are included. You need your own copy of the game.
- Source code: https://github.com/Joaovitor404silva/bloodborne-pc-path-tracing
