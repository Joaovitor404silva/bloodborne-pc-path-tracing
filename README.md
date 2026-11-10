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
(`Bloodborne-PC-Path-Tracing-pt2.zip`).

## Needs

- Bloodborne PC **1.9.7** (SuperMedo), installed and working:
  [windows-v1.9.7](https://github.com/Supermedo/bloodborne_pc/releases/tag/windows-v1.9.7)
- A ray tracing GPU: GeForce RTX or Radeon RX 6000 and newer.
- Your own copy of the game. No game files are included.

## Install

1. Close the game and the launcher.
2. Unzip the release anywhere (inside the Bloodborne PC folder is easiest).
3. Run `Install Path Tracing.bat`. It finds the game folder, or asks for it.
4. Start `Bloodborne.exe` as usual. Settings: Graphics page > Path tracing.

The installer checks the folder is 1.9.7 and backs up the 84 files it replaces to `rt-backup`.
It then copies the new files, including NVIDIA's DLSS Ray Reconstruction DLL, and checks
every copied file by SHA-256.

**Upscaler:** pt2 does not start path tracing under FSR 4.1, which is the launcher's
automatic pick. In that case the installer sets DLSS on NVIDIA cards and FSR 3.1 on others.
Keep DLSS or FSR 3.1.

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

Run `Uninstall Path Tracing.bat`. It restores the backup and your old upscaler setting.
The folder is then byte-identical to stock 1.9.7.

## Make your own tweaks

`source/` is the exact pt2 source tree (tag `rt-v1.9.7-pt2`), with its submodules pinned at
the same commits. Get everything with:

```
git clone --recursive https://github.com/Joaovitor404silva/bloodborne-pc-path-tracing
```

Where to look:

- Path tracing shaders: `source/gpu/shadps4/video_core/host_shaders/rt_*.comp` (GI,
  reflections, water and glass are in `rt_gi.comp`).
- Look knobs, with defaults and ranges: the `BB_RT_*` variables in
  `source/gpu/shadps4/video_core/renderer_vulkan/rt/vk_ray_tracing.cpp`. To try values
  without rebuilding, put them in the launcher under Advanced > Extra variables, for
  example `BB_RT_GI_STRENGTH=1.3 BB_RT_REFLECT_STRENGTH=0.8`.
- The design notes and every A/B behind the defaults: `source/docs/PATH_TRACING.md`.

Build (Windows, MSYS2 CLANG64): see
[source/packaging/windows/README.md](source/packaging/windows/README.md) (`bash build.sh`).
Then copy `out/bb-probe.exe` over `bin/bb-probe.exe` in your game folder. The DLSS SDK is not
in the tree; `source/docs/PATH_TRACING.md` explains how to fetch it, under "Fetching the DLL
and SDK".

## Build the release

```
python tools/make_payload.py <stock 1.9.7 folder> <path tracing build folder> dist/Bloodborne-PC-Path-Tracing-pt2 1.9.7 pt2
cp installer/* dist/Bloodborne-PC-Path-Tracing-pt2/
python tools/make_source.py <bloodborne_pc repo> rt-v1.9.7-pt2 dist/bloodborne_pc-rt-v1.9.7-pt2-source.zip
```

## License and source

The port and the path tracer are GPL-2.0, and this installer is GPL-2.0 as well.
The source that matches the shipped binaries is in `source/`, and is also attached to the
release as `bloodborne_pc-rt-v1.9.7-pt2-source.zip`.

Third-party licences, including NVIDIA DLSS, AMD FSR and Microsoft Agility, ship in the
port's `licenses` folder.

Path tracing by Joao vitor alves on top of SuperMedo's Bloodborne PC.
