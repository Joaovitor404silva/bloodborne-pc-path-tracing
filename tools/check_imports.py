"""Check that every function an exe imports from a non-system DLL is exported by that DLL in a folder.

usage: check_imports.py EXE DLL_DIR [OBJDUMP]
Prints each missing DLL/function and exits 1 when anything is missing (Windows would refuse to start
the exe with 0xC0000139, entry point not found).
"""
import os
import re
import subprocess
import sys


def dump(path, objdump):
    return subprocess.run([objdump, "-p", path], capture_output=True, text=True, errors="replace", check=True).stdout


def imports(path, objdump):
    """{dll name: [imported function names]}"""
    out, cur = {}, None
    for line in dump(path, objdump).splitlines():
        m = re.match(r"\s*DLL Name: (\S+)", line)
        if m:
            cur = out.setdefault(m.group(1), [])
            continue
        m = re.match(r"\s+\d+\s+(\S+)\s*$", line)  # "    hint  name" rows of the import table
        if cur is not None and m and not line.strip().startswith(("vma", "Hint")):
            cur.append(m.group(1))
    return out


def exports(path, objdump):
    names, on = set(), False
    for line in dump(path, objdump).splitlines():
        if line.startswith("Export Table:"):
            on = True
        elif on:
            m = re.match(r"\s+\d+\s+0x[0-9a-f]+\s+(\S+)", line)
            if m:
                names.add(m.group(1))
    return names


def missing(exe, dll_dir, objdump, only=None):
    """{dll: [functions exe imports that the dll in dll_dir lacks]}; DLLs not in dll_dir are skipped."""
    out = {}
    for dll, funcs in sorted(imports(exe, objdump).items()):
        path = os.path.join(dll_dir, dll)
        if (only and dll.lower() != only.lower()) or not os.path.exists(path):
            continue
        have = exports(path, objdump)
        out[dll] = [f for f in funcs if f not in have]
    return out


if __name__ == "__main__":
    exe, dll_dir = sys.argv[1:3]
    objdump = sys.argv[3] if len(sys.argv) > 3 else "llvm-objdump"
    bad = 0
    for dll, miss in missing(exe, dll_dir, objdump).items():
        n = len(imports(exe, objdump)[dll])
        print(f"{dll}: {n} imports, {len(miss)} missing")
        for f in miss[:15]:
            print("   ", f)
        bad += len(miss)
    sys.exit(1 if bad else 0)
