"""Move the path tracing mod to a new Bloodborne PC (SuperMedo) release and ship it.

usage: python tools/port_update.py STEP [--base X.Y.Z] [--rt ptN] [--yes]

Steps, in order (each one stops on the first problem and says what to do):
  check    newest windows-v* release of SuperMedo's port vs the version we ship (tools/port.json)
  merge    new worktree <repo>/../bbport-rt-<base> on his tag, our last release (rt_ref) merged in.
           Conflicts stop here: resolve them in that worktree, `git commit`, run `build`.
  build    build.sh in MSYS2 CLANG64, strip bb-probe.exe; the DLSS bridge is rebuilt only when its
           source changed since rt_ref (else the last release's DLLs are reused); import check.
  package  stock zip of <base>, installer folder + GitHub zip + Nexus zip in dist/, source/ for
           the new base, version strings in the READMEs, release notes in work/.
  test     tools/test_installer.ps1 on the stock folder (no game needed).
  release  tag rt-v<base>-<rt> in the bloodborne_pc repo, commit this repo, push, GitHub release.
           Only with --yes; without it, prints what it would do.
Live game test (between test and release) is by hand: install the dist folder into a copy of the
stock folder, play, press F9. Nexus upload is by hand: dist/*-nexus.zip, its readme names the version.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONF = os.path.join(ROOT, "tools", "port.json")
WORK = os.path.join(ROOT, "work")
UPSTREAM = "Supermedo/bloodborne_pc"
OUR_REPO = "Joaovitor404silva/bloodborne-pc-path-tracing"
SUBMODULES = ("gpu/third_party/fsr-vulkan", "gpu/third_party/imgui", "gpu/third_party/magic_enum",
              "gpu/third_party/miniz", "gpu/third_party/xbyak", "third_party/LibAtrac9")


def die(msg, code=1):
    print("STOP:", msg)
    sys.exit(code)


def run(cmd, cwd=None, check=True, env=None):
    print("+", " ".join(cmd) if isinstance(cmd, list) else cmd)
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode:
        die(f"failed ({r.returncode}):\n{(r.stdout + r.stderr)[-3000:]}")
    return r


def git(repo, *args, check=True):
    return run(["git", "-C", repo, *args], check=check).stdout.strip()


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def conf():
    with open(CONF, encoding="utf-8") as f:
        return json.load(f)


def worktree(c, base):
    return os.path.join(os.path.dirname(c["repo"]), f"bbport-rt-{base}")


def dist_name(rt):
    return f"Bloodborne-PC-Path-Tracing-{rt}"


def posix(path):
    p = os.path.abspath(path).replace("\\", "/")
    return f"/{p[0].lower()}{p[2:]}" if re.match(r"^[A-Za-z]:", p) else p


def msys(c, script, cwd):
    env = dict(os.environ, MSYSTEM="CLANG64", CHERE_INVOKING="1")
    return run([os.path.join(c["msys2"], "usr", "bin", "bash.exe"), "-lc", f"cd '{posix(cwd)}' && {script}"], env=env)


def latest_upstream():
    out = run(["gh", "release", "list", "-R", UPSTREAM, "-L", "20", "--json", "tagName,isLatest"]).stdout
    tags = [r["tagName"] for r in json.loads(out) if r["tagName"].startswith("windows-v")]
    latest = [r["tagName"] for r in json.loads(out) if r["isLatest"]]
    tag = latest[0] if latest and latest[0].startswith("windows-v") else tags[0]
    return tag[len("windows-v"):]


def stock_dir(base):
    """SuperMedo's release zip of <base>, unpacked once into work/stock-<base>."""
    d = os.path.join(WORK, f"stock-{base}")
    folder = os.path.join(d, "x", "bbport-windows")
    if not os.path.isdir(folder):
        os.makedirs(d, exist_ok=True)
        run(["gh", "release", "download", f"windows-v{base}", "-R", UPSTREAM, "-p", "Bloodborne-Windows.zip", "-D", d, "--clobber"])
        with zipfile.ZipFile(os.path.join(d, "Bloodborne-Windows.zip")) as z:
            z.extractall(os.path.join(d, "x"))
        os.remove(os.path.join(d, "Bloodborne-Windows.zip"))
    with open(os.path.join(folder, "bbport-files.json"), encoding="utf-8") as f:
        if json.load(f)["version"] != base:
            die(f"{folder} is not Bloodborne PC {base}")
    return folder


def step_check(c, a):
    new = latest_upstream()
    print(f"we ship {c['rt_version']} for Bloodborne PC {c['base']}; newest Bloodborne PC is {new}")
    if new == c["base"]:
        print("up to date")
        return
    print(f"next: python tools/port_update.py merge --base {new}")
    sys.exit(10)


def step_merge(c, a):
    repo, wt = c["repo"], worktree(c, a.base)
    git(repo, "fetch", "origin", "--tags", "--force")
    if not os.path.isdir(wt):
        git(repo, "worktree", "add", "-b", f"rt-v{a.base}", wt, f"windows-v{a.base}")
    for s in SUBMODULES:  # same files as the repo's own checkout when the pinned commit is the same
        if git(repo, "rev-parse", f"windows-v{a.base}:{s}") != git(repo, "rev-parse", f"{c['rt_ref']}:{s}"):
            die(f"{s} moved upstream: run `git submodule update --init {s}` in {wt}, then build")
        src, dst = os.path.join(repo, s), os.path.join(wt, s)
        if not (os.path.isdir(dst) and os.listdir(dst)):
            shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git"))
    if run(["git", "-C", wt, "merge-base", "--is-ancestor", c["rt_ref"], "HEAD"], check=False).returncode == 0:
        print("already merged")
        return
    r = run(["git", "-C", wt, "-c", "user.name=Joao vitor alves",
             "-c", "user.email=177051894+Joaovitor404silva@users.noreply.github.com",
             "merge", "--no-ff", "-m", f"Merge {c['rt_ref']} into windows-v{a.base}", c["rt_ref"]], check=False)
    if r.returncode:
        files = git(wt, "diff", "--name-only", "--diff-filter=U")
        print(f"Conflicts in {wt}:\n{files}")
        print("The launcher is not shipped: take 1.9.x's side for launcher/ and README.md "
              "(git checkout --ours -- <file>). Resolve the rest, git commit, then run build.")
        sys.exit(2)
    print(f"merged in {wt}; next: build --base {a.base}")


def step_build(c, a):
    wt = worktree(c, a.base)
    if git(wt, "diff", "--name-only", "--diff-filter=U"):
        die("unresolved conflicts in the worktree")
    if git(wt, "status", "--porcelain", "--untracked-files=no"):
        die(f"uncommitted changes in {wt}: commit them first (the source zip is made from the commit)")
    msys(c, "bash build.sh", wt)
    out = os.path.join(WORK, f"rt-{a.base}", "bin")
    os.makedirs(out, exist_ok=True)
    strip = os.path.join(c["msys2"], "clang64", "bin", "llvm-strip.exe")
    run([strip, "--strip-debug", "-o", os.path.join(out, "bb-probe.exe"), os.path.join(wt, "out", "bb-probe.exe")])
    if run(["git", "-C", wt, "diff", "--quiet", c["rt_ref"], "HEAD", "--", "gpu/dlss_bridge"], check=False).returncode:
        msys(c, f"DLSS_SDK_ROOT='{posix(c['dlss_sdk'])}' bash packaging/windows/build_dlss.sh", wt)
        src = os.path.join(wt, "out")
    else:
        src = os.path.join(ROOT, "dist", dist_name(c["rt_version"]), "payload", "bin")
        print(f"DLSS bridge unchanged since {c['rt_ref']}: reusing {src}")
    for dll in ("bbport_dlss.dll", "nvngx_dlssd.dll"):
        shutil.copy2(os.path.join(src, dll), out)
    # Every DLL the exe imports must be in the stock bin folder or be Windows' own.
    stock_bin = os.path.join(stock_dir(a.base), "bin")
    objdump = os.path.join(c["msys2"], "clang64", "bin", "llvm-objdump.exe")
    dlls = re.findall(r"DLL Name: (\S+)", run([objdump, "-p", os.path.join(out, "bb-probe.exe")]).stdout)
    system = re.compile(r"^(api-ms-win-|kernel32|user32|advapi32|shell32|ws2_32|bcrypt|crypt32|ntdll|pdh|iphlpapi|dxgi|d3d12|vulkan-1|ole32|gdi32|winmm|dbghelp|version|setupapi|imm32|oleaut32|cfgmgr32|hid|dwmapi|uxtheme|shlwapi|secur32|winhttp|dnsapi|mswsock|userenv|psapi|powrprof)", re.I)
    absent = [d for d in dlls if not system.match(d) and not os.path.exists(os.path.join(stock_bin, d))]
    if absent:
        die(f"bb-probe.exe needs DLLs stock {a.base} does not ship: {absent}")
    # Every function too: when his DLL is older than our MSYS2 one (1.9.8.4's libc++.dll), ship ours,
    # but only if all his programs and DLLs that use it still find their functions in ours.
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import check_imports as ci
    msys_bin = os.path.join(c["msys2"], "clang64", "bin")
    for dll, miss in ci.missing(os.path.join(out, "bb-probe.exe"), stock_bin, objdump).items():
        if not miss:
            continue
        ours = os.path.join(msys_bin, dll)
        if not os.path.exists(ours) or ci.missing(os.path.join(out, "bb-probe.exe"), msys_bin, objdump, dll)[dll]:
            die(f"stock {dll} lacks {miss[:5]} and MSYS2 has no {dll} that fixes it")
        n = 0
        for d, _, fs in os.walk(stock_dir(a.base)):
            for f in fs:
                if f.lower().endswith((".exe", ".dll", ".pyd")):
                    user = ci.missing(os.path.join(d, f), msys_bin, objdump, dll)
                    if user.get(dll):
                        die(f"stock {f} needs {user[dll][:5]} that MSYS2's {dll} lacks: can't replace it")
                    n += dll in user
        shutil.copy2(ours, out)
        print(f"stock {dll} lacks {len(miss)} functions bb-probe.exe uses: shipping MSYS2's ({n} stock users checked)")
    print(f"built {out}: {len(dlls)} DLLs, every imported function present")


def bump(path, pairs):
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    for old, new in pairs:
        text = text.replace(old, new)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def rt_env_line():
    with open(os.path.join(ROOT, "installer", "install.ps1"), encoding="ascii") as f:
        block = re.search(r"\$rtEnv = @\((.*?)\)", f.read(), re.S).group(1)
    return " ".join(re.findall(r"'([^']+)'", block))


def step_package(c, a):
    if a.rt == c["rt_version"]:
        die("--rt must be the new mod version (port.json has the last released one)")
    wt, stock = worktree(c, a.base), stock_dir(a.base)
    rt_dir = os.path.join(WORK, f"rt-{a.base}")
    name = dist_name(a.rt)
    dist = os.path.join(ROOT, "dist", name)
    if os.path.exists(dist):
        shutil.rmtree(dist)
    run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_payload.py"), stock, rt_dir, dist, a.base, a.rt])
    with open(os.path.join(dist, "manifest.json"), encoding="utf-8") as f:
        shipped = list(json.load(f)["files"])
    for f in os.listdir(os.path.join(ROOT, "installer")):
        shutil.copy2(os.path.join(ROOT, "installer", f), dist)
    # Versions in the READMEs before they are copied into the zips.
    pairs = [(c["rt_ref"], f"rt-v{a.base}-{a.rt}"), (f"supermedo-{c['base']}.patch", f"supermedo-{a.base}.patch"),
             (c["base"], a.base), (c["rt_version"], a.rt)]
    for f in ("README.md", os.path.join("installer", "README.txt")):
        bump(os.path.join(ROOT, f), pairs)
    shutil.copy2(os.path.join(ROOT, "installer", "README.txt"), dist)
    zpath = os.path.join(ROOT, "dist", name + ".zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for d, _, fs in os.walk(dist):
            for f in sorted(fs):
                p = os.path.join(d, f)
                z.write(p, os.path.relpath(p, os.path.dirname(dist)))
    with open(os.path.join(ROOT, "tools", "templates", "nexus_readme.txt"), encoding="utf-8") as f:
        readme = f.read().format(rt=a.rt, base=a.base, rt_env=rt_env_line()).replace("\n", "\r\n")
    with zipfile.ZipFile(os.path.join(ROOT, "dist", name + "-nexus.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"Path Tracing {a.rt} - READ ME FIRST.txt", readme.encode("ascii"))
        for rel in shipped:
            if rel != "bin/bb-probe.exe":
                z.write(os.path.join(dist, "payload", rel), rel)
    # Source: only our work against his new tag, from the merged commit.
    run([sys.executable, "-I", os.path.join(ROOT, "tools", "make_source.py"), wt, f"windows-v{a.base}", "HEAD",
         os.path.join(ROOT, "source")])
    hashes = {rel: sha(os.path.join(dist, "payload", rel)) for rel in shipped}
    hashes[name + ".zip"] = sha(zpath)
    # Results column: fill in after the uploads (VirusTotal does not unpack zips over 3 MB).
    vt = "| File | Result |\n|---|---|\n" + "\n".join(
        f"| [`{k}`](https://www.virustotal.com/gui/file/{v}) | RESULT |" for k, v in hashes.items())
    with open(os.path.join(ROOT, "tools", "templates", "release_notes.md"), encoding="utf-8") as f:
        notes = f.read().format(base=a.base, rt=a.rt, prev_rt=c["rt_version"], prev_base=c["base"],
                                changes="".join(f"- {line}\n" for line in a.change),
                                virustotal=vt)
    os.makedirs(WORK, exist_ok=True)
    with open(os.path.join(WORK, f"release-notes-{a.rt}.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(notes)
    print(f"packaged dist/{name}.zip, dist/{name}-nexus.zip, source/, work/release-notes-{a.rt}.md")
    print(f"Upload the {len(hashes)} files to VirusTotal and put each result next to its link in the notes.")


def step_test(c, a):
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                        os.path.join(ROOT, "tools", "test_installer.ps1"), "-Package",
                        os.path.join(ROOT, "dist", dist_name(a.rt)), "-Stock", stock_dir(a.base),
                        "-Work", os.path.join(WORK, "installer-test")])
    if r.returncode:
        die("installer test failed")


def step_release(c, a):
    tag = f"rt-v{a.base}-{a.rt}"
    name = dist_name(a.rt)
    notes = os.path.join(WORK, f"release-notes-{a.rt}.md")
    plan = [f"tag {tag} at the merged commit in {worktree(c, a.base)}",
            f"commit README, installer, tools, source in {ROOT}; port.json -> base {a.base}, rt {a.rt}",
            "git push origin main",
            f"gh release create {a.rt} dist/{name}.zip --notes-file {notes} (Latest)"]
    if not a.yes:
        print("Would:\n  " + "\n  ".join(plan) + "\nRun again with --yes to do it.")
        return
    if not os.path.exists(notes):
        die("no release notes: run package first")
    git(worktree(c, a.base), "tag", "-f", tag, "HEAD")
    c.update(base=a.base, rt_ref=tag, rt_version=a.rt)
    with open(CONF, "w", encoding="utf-8", newline="\n") as f:
        json.dump(c, f, indent=1)
        f.write("\n")
    git(ROOT, "add", "-A", "README.md", "installer", "tools", "source", ".gitattributes")
    msg = os.path.join(WORK, "commit-msg.txt")
    with open(msg, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"{a.rt}: Bloodborne PC {a.base}\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                + (f"Claude-Session: {os.environ['CLAUDE_SESSION']}\n" if os.environ.get("CLAUDE_SESSION") else ""))
    run(["git", "-C", ROOT, "-c", "user.name=Joao vitor alves",
         "-c", "user.email=177051894+Joaovitor404silva@users.noreply.github.com", "commit", "-q", "-F", msg])
    os.remove(msg)
    git(ROOT, "push", "origin", "main")
    run(["gh", "release", "create", a.rt, os.path.join(ROOT, "dist", name + ".zip"), "-R", OUR_REPO,
         "--target", "main", "--title", f"Bloodborne PC Path Tracing {a.rt} (alpha)", "--notes-file", notes, "--latest"])
    print(f"released {a.rt}. Nexus: upload dist/{name}-nexus.zip as an update of the main file.")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("step", choices=["check", "merge", "build", "package", "test", "release"])
    p.add_argument("--base", help="Bloodborne PC version, e.g. 1.9.8.4 (default: newest)")
    p.add_argument("--rt", help="new mod version, e.g. pt2.2 (package, test, release)")
    p.add_argument("--yes", action="store_true", help="release: really push and publish")
    p.add_argument("--change", action="append", default=[],
                   help="package: one more line for the notes' 'What changed' list (repeatable)")
    a = p.parse_args()
    c = conf()
    if a.step != "check" and not a.base:
        a.base = latest_upstream()
    if a.step in ("package", "test", "release") and not a.rt:
        die("--rt is needed (the new mod version, e.g. pt2.2)")
    globals()[f"step_{a.step}"](c, a)


if __name__ == "__main__":
    main()
