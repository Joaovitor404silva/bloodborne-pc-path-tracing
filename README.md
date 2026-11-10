# Bloodborne PC Path Tracing installer

Adds real-time path tracing to [SuperMedo's Bloodborne PC port](https://github.com/Supermedo/bloodborne_pc):
moonlight and bounce light, traced shadows and reflections, water and puddle mirrors, traced glass.

## Download

Get `Bloodborne-PC-Path-Tracing-pt2.zip` from [Releases](../../releases).

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

## Uninstall

Run `Uninstall Path Tracing.bat`. It restores the backup and your old upscaler setting.
The folder is then byte-identical to stock 1.9.7.

## Build the release

```
python tools/make_payload.py <stock 1.9.7 folder> <path tracing build folder> dist/Bloodborne-PC-Path-Tracing-pt2 1.9.7 pt2
cp installer/* dist/Bloodborne-PC-Path-Tracing-pt2/
python tools/make_source.py <bloodborne_pc repo> rt-v1.9.7-pt2 dist/bloodborne_pc-rt-v1.9.7-pt2-source.zip
```

## License and source

The port and the path tracer are GPL-2.0, and this installer is GPL-2.0 as well.
The source that matches the shipped binaries is attached to each release as
`bloodborne_pc-rt-v1.9.7-pt2-source.zip`.

Third-party licences, including NVIDIA DLSS, AMD FSR and Microsoft Agility, ship in the
port's `licenses` folder.

Path tracing by Joao vitor alves on top of SuperMedo's Bloodborne PC.
