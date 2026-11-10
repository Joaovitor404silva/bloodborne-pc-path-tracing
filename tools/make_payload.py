"""Build the installer folder from a stock Bloodborne PC release and a path tracing build.

usage: make_payload.py STOCK_DIR RT_DIR OUT_DIR BASE_VERSION RT_VERSION
Copies the mod's own files (SHIP) from RT_DIR into OUT_DIR/payload and writes
OUT_DIR/manifest.json with the stock and RT sha256 of each one. Every other file of
the port stays SuperMedo's: the build's other differences (MSYS2 DLL versions, the
launcher, line endings) are not needed, measured on a stock 1.9.7 (2026-11-10).
"""
import hashlib
import json
import os
import shutil
import sys


def tree(root):
    out = {}
    for d, _, fs in os.walk(root):
        for f in fs:
            p = os.path.join(d, f)
            with open(p, "rb") as fh:
                out[os.path.relpath(p, root).replace("\\", "/")] = hashlib.sha256(fh.read()).hexdigest()
    return out


# The path tracing renderer, our DLSS bridge (Ray Reconstruction) and NVIDIA's Ray Reconstruction DLL.
SHIP = ("bin/bb-probe.exe", "bin/bbport_dlss.dll", "bin/nvngx_dlssd.dll")

stock_dir, rt_dir, out_dir, base, rt_version = sys.argv[1:6]
stock, rt = tree(stock_dir), tree(rt_dir)
files = {}
for rel in SHIP:
    h = rt[rel]
    if stock.get(rel) == h:
        sys.exit(f"{rel} is the same as stock: not a path tracing build?")
    dst = os.path.join(out_dir, "payload", rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(os.path.join(rt_dir, rel), dst)
    files[rel] = {"stock": stock.get(rel), "rt": h}
manifest = {"base_version": base, "rt_version": rt_version, "files": files}
with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8", newline="\n") as fh:
    json.dump(manifest, fh, indent=1)
print(len(files), "files,", sum(1 for f in files.values() if f["stock"] is None), "new")
