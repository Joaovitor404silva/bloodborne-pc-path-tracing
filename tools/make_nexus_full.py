"""Nexus companion zip of the full download: Nexus blocks .exe, so it holds the READ ME FIRST (pointing to the
GitHub Bloodborne-Windows.zip) and the payload's non-.exe files.

usage: make_nexus_full.py PAYLOAD_BIN RT BASE OUT_ZIP
"""
import os
import sys
import zipfile

payload, rt, base, out = sys.argv[1:5]
root = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(root, 'templates', 'nexus_readme_full.txt'), encoding='utf-8') as f:
    readme = f.read().format(rt=rt, base=base).replace('\n', '\r\n')
names = sorted(n for n in os.listdir(payload) if not n.lower().endswith('.exe'))
if os.path.exists(out):
    os.remove(out)
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr(f'Path Tracing {rt} - READ ME FIRST.txt', readme)
    for name in names:
        z.write(os.path.join(payload, name), f'bin/{name}')
with zipfile.ZipFile(out) as z:
    listed = z.namelist()
assert not any(n.lower().endswith('.exe') for n in listed), listed
print(out, os.path.getsize(out), 'bytes:', ', '.join(listed))
