Bloodborne PC - Path Tracing mod (pt2)
======================================

Real-time path tracing for SuperMedo's Bloodborne PC port: moonlight, bounce light,
shadows, reflections, water and puddle mirrors, traced glass.

NEEDS
- Bloodborne PC 1.9.7 (SuperMedo), already installed and working:
  https://github.com/Supermedo/bloodborne_pc/releases/tag/windows-v1.9.7
- A ray tracing GPU (GeForce RTX, Radeon RX 6000 or newer). Use DLSS or FSR.

INSTALL
1. Close the game and the launcher.
2. Unzip this folder anywhere (inside the Bloodborne PC folder is easiest).
3. Double-click "Install Path Tracing.bat". If it does not find the game folder,
   it asks for it (the folder with Bloodborne.exe).
4. Start Bloodborne.exe as usual. Settings: Graphics page > Path tracing.

The installer replaces 85 files of the port (launcher, renderer and its DLLs) and adds
NVIDIA's DLSS Ray Reconstruction DLL. The files it replaces go to "rt-backup" in the
game folder. It checks every copied file.

UNINSTALL
Double-click "Uninstall Path Tracing.bat": the backup goes back and the folder is stock
1.9.7 again.

UPSCALER
Path tracing pt2 does not start with FSR 4.1 (the launcher's automatic pick). If your
upscaler is FSR 4.1 or automatic, the installer sets DLSS on NVIDIA cards, else FSR 3.1.
Keep DLSS or FSR 3.1. Uninstall puts your old setting back.

NOTES
- Update checks are off in this build: the upstream update has no path tracing.
  Installing a newer Bloodborne PC update replaces the mod.
- Without a ray tracing GPU the game keeps its own lighting.
- No game files are included. You need your own copy of the game.
