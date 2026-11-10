"""Build the installer folder from a stock Bloodborne PC release and a path tracing build.

usage: make_payload.py STOCK_DIR RT_DIR OUT_DIR BASE_VERSION RT_VERSION
Copies every file that is new or different in RT_DIR into OUT_DIR/payload and writes
OUT_DIR/manifest.json with the stock and RT sha256 of each one. Files only the stock
release has are left alone by the installer.
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


stock_dir, rt_dir, out_dir, base, rt_version = sys.argv[1:6]
stock, rt = tree(stock_dir), tree(rt_dir)
files = {}
for rel, h in sorted(rt.items()):
    if stock.get(rel) == h:
        continue
    dst = os.path.join(out_dir, "payload", rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(os.path.join(rt_dir, rel), dst)
    files[rel] = {"stock": stock.get(rel), "rt": h}
manifest = {"base_version": base, "rt_version": rt_version, "files": files}
with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8", newline="\n") as fh:
    json.dump(manifest, fh, indent=1)
print(len(files), "files,", sum(1 for f in files.values() if f["stock"] is None), "new")
