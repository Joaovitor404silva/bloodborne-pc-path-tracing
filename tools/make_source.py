"""Corresponding source zip of a path tracing build (GPL-2.0), local paths scrubbed.

usage: make_source.py REPO TAG OUT_ZIP
"""
import io
import re
import subprocess
import sys
import zipfile

repo, tag, out = sys.argv[1:4]
data = subprocess.run(["git", "-C", repo, "archive", "--format=zip", f"--prefix=bloodborne_pc-{tag}/", tag],
                      check=True, capture_output=True).stdout
private = re.compile(rb"C:[\\/]+Users[\\/]+[^\\/\s)]+")
n = 0
with zipfile.ZipFile(io.BytesIO(data)) as src, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
    for info in src.infolist():
        body = src.read(info)
        body, k = private.subn(rb"C:\\Users\\<user>", body)
        n += k
        dst.writestr(info, body)
print("scrubbed", n, "paths")
