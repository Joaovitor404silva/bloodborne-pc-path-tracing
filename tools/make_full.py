#!/usr/bin/env python3
"""Builds the full download: SuperMedo's Bloodborne-Windows.zip of the base version with the path tracing
engine files and the fork's launcher (frozen from the fork branch: out/pyi-dist/Bloodborne) in place.

    py -3.14 tools/make_full.py UPSTREAM_ZIP FORK_REPO PAYLOAD_BIN OUT_ZIP

UPSTREAM_ZIP  SuperMedo's Bloodborne-Windows.zip (github.com/Supermedo/bloodborne_pc releases)
FORK_REPO     the fork's source tree, with out/pyi-dist/Bloodborne frozen from it
PAYLOAD_BIN   the 4 path tracing files (bb-probe.exe, bbport_dlss.dll, nvngx_dlssd.dll, libc++.dll)
OUT_ZIP       the package, same layout as SuperMedo's (bbport-windows/...), so the launcher's updater takes it
"""
import json
import shutil
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOP = 'bbport-windows'
PAYLOAD = ('bb-probe.exe', 'bbport_dlss.dll', 'nvngx_dlssd.dll', 'libc++.dll')


def main(upstream_zip, fork_repo, payload_bin, out_zip):
    upstream_zip, fork_repo, payload_bin, out_zip = map(Path, (upstream_zip, fork_repo, payload_bin, out_zip))
    stage = out_zip.parent / (out_zip.stem + '-stage')
    if stage.exists():
        shutil.rmtree(stage)
    with zipfile.ZipFile(upstream_zip) as z:
        z.extractall(stage)
    port = stage / TOP
    old = json.loads((port / 'bbport-files.json').read_text(encoding='utf-8'))
    # The fork's launcher replaces his (Bloodborne.exe + _internal).
    frozen = fork_repo / 'out' / 'pyi-dist' / 'Bloodborne'
    shutil.rmtree(port / '_internal')
    shutil.copytree(frozen / '_internal', port / '_internal')
    shutil.copy2(frozen / 'Bloodborne.exe', port / 'Bloodborne.exe')
    for name in PAYLOAD:
        shutil.copy2(payload_bin / name, port / 'bin' / name)
    # Credits and notes beside his README.
    shutil.copy2(HERE.parent / 'installer' / 'full' / 'README-PathTracing.txt', port / 'README-PathTracing.txt')
    # The program file list, as package.sh writes it (run.py and Help check mixed versions with it).
    sys.path.insert(0, str(fork_repo / 'scripts'))
    import package_files
    count = package_files.write(port, old['version'])
    if out_zip.exists():
        out_zip.unlink()
    shutil.make_archive(str(out_zip.with_suffix('')), 'zip', stage)
    shutil.rmtree(stage)
    print(f'{out_zip}: {out_zip.stat().st_size} bytes, {count} program files, version {old["version"]}')


if __name__ == '__main__':
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
