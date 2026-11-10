"""Write source/ with only our path tracing work, local paths scrubbed (GPL-2.0 corresponding source).

usage: make_source.py REPO BASE_TAG RT_TAG OUT_DIR

REPO is the bloodborne_pc checkout with both tags (BASE_TAG = SuperMedo's windows-v1.9.7).
- Files we added go to OUT_DIR at their paths, as they are.
- Our edits to SuperMedo's files go to OUT_DIR/supermedo-<version>.patch, one diff against BASE_TAG.
SuperMedo's own files are not copied. Left out: the launcher change (the mod no longer replaces
the launcher) and the upstream README.
"""
import os
import re
import shutil
import subprocess
import sys

repo, base, rt, out = sys.argv[1:5]
SKIP = ("launcher/", "README.md", "tests/test_fsr412_launcher.py")
private = re.compile(rb"C:[\\/]+Users[\\/]+[^\\/\s)\"']+")


def git(*args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True).stdout


def scrub(data):
    return private.subn(rb"C:\\Users\\<user>", data)


if os.path.exists(out):
    shutil.rmtree(out)
os.makedirs(out)
added, modified = [], []
for line in git("diff", "--name-status", "--no-renames", base, rt).decode().splitlines():
    status, path = line.split("\t", 1)
    if path.startswith(SKIP):
        continue
    if status == "A":
        added.append(path)
    elif status == "M":
        modified.append(path)
    else:
        sys.exit(f"unexpected {status} {path}")

n = 0
for path in added:
    body, k = scrub(git("show", f"{rt}:{path}"))
    n += k
    dst = os.path.join(out, path)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "wb") as fh:
        fh.write(body)

patch, k = scrub(git("diff", "--binary", "--no-renames", base, rt, "--", *modified))
n += k
name = f"supermedo-{base.removeprefix('windows-v')}.patch"
with open(os.path.join(out, name), "wb") as fh:
    fh.write(patch)
print(f"{len(added)} added files, {len(modified)} patched files in {name}, {n} paths scrubbed")
