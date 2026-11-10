# Bloodborne PC Path Tracing installer

Adds real-time path tracing to [SuperMedo's Bloodborne PC port](https://github.com/Supermedo/bloodborne_pc):
moonlight and bounce light, traced shadows and reflections, water and puddle mirrors, traced glass.

> **Alpha.** This is an early build and work is ongoing: light sources are being remade, along
> with effects such as fire, fog and glows, water and the overall look. Expect bugs, places that
> look wrong, and big changes between versions.

![Moonlit walk to the statues](docs/media/moonlit-walk.gif)

![Cainhurst: a ghost on the stairs](docs/media/cainhurst-ghost.gif)

![Flooded street: lamp light mirrored in the water](docs/media/flooded-street.jpg)

![Forbidden Woods: lantern and shrine light](docs/media/forbidden-woods.jpg)

## Download

**[Download the latest release](https://github.com/Joaovitor404silva/bloodborne-pc-path-tracing/releases/latest)**
(`Bloodborne-PC-Path-Tracing-pt2.1.zip`).

## Needs

- Bloodborne PC **1.9.7** (SuperMedo), installed and working:
  [windows-v1.9.7](https://github.com/Supermedo/bloodborne_pc/releases/tag/windows-v1.9.7)
- A ray tracing GPU: GeForce RTX or Radeon RX 6000 and newer.
- Your own copy of the game. No game files are included.

## What the mod is

Three files on top of SuperMedo's port; everything else stays his:

| File | What it is |
|---|---|
| `bin/bb-probe.exe` | The port's game engine, built from his source with the path tracer added |
| `bin/bbport_dlss.dll` | The DLSS bridge, with Ray Reconstruction added |
| `bin/nvngx_dlssd.dll` | NVIDIA's DLSS Ray Reconstruction (new file) |

Path tracing is switched on by a line of variables in his launcher: Advanced > Diagnostics >
Extra variables. The installer writes it for you.

## Install

1. Close the game and the launcher.
2. Unzip the release anywhere (inside the Bloodborne PC folder is easiest).
3. Run `Install Path Tracing.bat`. It finds the game folder, or asks for it.
4. Start `Bloodborne.exe` as usual.

In game, press **F9** to turn path tracing off and on and compare with the stock lighting.
Give it about 3 seconds after each press while the exposure adjusts.

The installer checks the folder is 1.9.7, backs up the 2 files it replaces to `rt-backup`,
copies the 3 files and checks each by SHA-256. It adds the path tracing variables to the
launcher's Extra variables and keeps any you already had.

In a protected folder such as Program Files, Windows asks for administrator rights. If a copy
fails (a file in use by the game or an antivirus), the installer puts every file back, leaves the
folder as it was, and says what failed.

**Upscaler:** pt2 does not start path tracing under FSR 4.1, which is the launcher's
automatic pick. In that case the installer sets DLSS on NVIDIA cards and FSR 3.1 on others.
Keep DLSS or FSR 3.1.

**Launcher updates:** an update of Bloodborne PC replaces `bb-probe.exe`, and path tracing is
gone. Run the installer again after updating only if this mod supports that version.

## Known issue (pt2)

Path tracing can stay off after the game starts, so the lighting looks like stock. Its memory
fills during loading and is never freed.

| Setting | Our tests |
|---|---|
| DLSS, frame generation off | works |
| FSR 3.1, frame generation off | works |
| FSR 4.1 | stuck |
| DLSS + DLSS frame generation | stuck |

If it happens, turn frame generation off and restart the game. A fix is planned.

## Uninstall

Run `Uninstall Path Tracing.bat`. It restores the 2 backed-up files, removes NVIDIA's Ray
Reconstruction DLL, takes the variables out of Extra variables and puts your old upscaler back.

## Source

`source/` holds only our work; SuperMedo's code is in his repository.

- Files we wrote are there as they are: the path tracer
  (`source/gpu/shadps4/video_core/renderer_vulkan/rt/`), its shaders
  (`source/gpu/shadps4/video_core/host_shaders/rt_*.comp`), tests and tools.
- Our changes to his files are one patch: `source/supermedo-1.9.7.patch`.

Rebuild the exact pt2 tree:

```
git clone --recursive --branch windows-v1.9.7 https://github.com/Supermedo/bloodborne_pc
git clone https://github.com/Joaovitor404silva/bloodborne-pc-path-tracing
cp -r bloodborne-pc-path-tracing/source/. bloodborne_pc/
cd bloodborne_pc && git apply supermedo-1.9.7.patch
```

Then build on Windows (MSYS2 CLANG64) as in his `packaging/windows/README.md`: `bash build.sh`
gives `out/bb-probe.exe`; `packaging/windows/build_dlss.sh` gives `out/bbport_dlss.dll` (needs
the NVIDIA DLSS SDK, see `docs/PATH_TRACING.md`, "Fetching the DLL and SDK").

Tweaks without rebuilding: the `BB_RT_*` variables in
`source/gpu/shadps4/video_core/renderer_vulkan/rt/vk_ray_tracing.cpp` go in Extra variables,
for example `BB_RT_GI_STRENGTH=1.3 BB_RT_REFLECT_STRENGTH=0.8`. The design notes and every A/B
behind the defaults: `source/docs/PATH_TRACING.md`.

## Build the release

```
python tools/make_payload.py <stock 1.9.7 folder> <path tracing build folder> dist/Bloodborne-PC-Path-Tracing-pt2.1 1.9.7 pt2.1
cp installer/* dist/Bloodborne-PC-Path-Tracing-pt2.1/
python tools/make_source.py <bloodborne_pc repo> windows-v1.9.7 rt-v1.9.7-pt2 source
```

## License

The path tracer and this installer are GPL-2.0, like the port. NVIDIA's DLSS DLL ships under
the NVIDIA DLSS SDK licence (it is in the port's `licenses` folder).

Path tracing by Joao vitor alves on top of SuperMedo's Bloodborne PC.
