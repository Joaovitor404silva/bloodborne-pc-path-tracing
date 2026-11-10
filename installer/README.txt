Bloodborne PC - Path Tracing mod (pt2)
======================================

Real-time path tracing for SuperMedo's Bloodborne PC port: moonlight, bounce light,
shadows, reflections, water and puddle mirrors, traced glass.

ALPHA: this is an early build and work is ongoing. Light sources are being remade,
along with effects (fire, fog, glows), water and the overall look. Expect bugs, places
that look wrong, and big changes between versions.

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

The installer replaces 84 files of the port (launcher, renderer and its DLLs) and adds
NVIDIA's DLSS Ray Reconstruction DLL. The files it replaces go to "rt-backup" in the
game folder. It checks every copied file.

If the game is in a protected folder (Program Files, for example), Windows asks for
administrator rights. If something goes wrong (a file in use by the game or an
antivirus), the installer puts every file back and says what failed.

UNINSTALL
Double-click "Uninstall Path Tracing.bat": the backup goes back and the folder is stock
1.9.7 again.

UPSCALER
Path tracing pt2 does not start with FSR 4.1 (the launcher's automatic pick). If your
upscaler is FSR 4.1 or automatic, the installer sets DLSS on NVIDIA cards, else FSR 3.1.
Keep DLSS or FSR 3.1. Uninstall puts your old setting back.

KNOWN ISSUE (pt2)
Path tracing can stay off after the game starts (the lighting looks like stock): its
memory fills during loading and is never freed. In our tests it worked with DLSS or
FSR 3.1 and frame generation off; it got stuck with FSR 4.1 and with DLSS frame
generation. If it happens, turn frame generation off and restart the game.

NOTES
- Update checks are off in this build: the upstream update has no path tracing.
  Installing a newer Bloodborne PC update replaces the mod.
- Without a ray tracing GPU the game keeps its own lighting.
- No game files are included. You need your own copy of the game.
