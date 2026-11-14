"""MCP server for the render-look skill: see and drive the running RT game (bb-probe).

Tools: live vision (measure flicker/motion, grab frames, frame strips, motion maps), F9 stock A/B,
rt.cfg knobs (get, set, interleaved knob A/B that restores the file), the pad file (free camera),
per-frame light statistics and log search. Run with the vision venv (out/vision-venv, which has
dxcam, numpy, opencv-python-headless and mcp 2.x); registered in .mcp.json as "bbrt".
"""
import glob
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from mcp.server.mcpserver import Image, MCPServer

sys.path.insert(0, str(Path(__file__).resolve().parent))
import live_vision as lv  # noqa: E402

LIVE = Path(r"D:\modding\bbport-rt\out\rt-live")
CFG = LIVE / "rt.cfg"
PAD = LIVE / "pad"
WINDRIVE_GLOB = os.path.expanduser(
    r"~\.claude\plugins\cache\universal-modder\universal-modder\*\um\ps1\WinDrive.ps1")

mcp = MCPServer("bbrt")


# --------------------------------------------------------------------------- helpers

def _game_pid():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq bb-probe.exe", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    m = re.search(r'"bb-probe\.exe","(\d+)"', out)
    return int(m.group(1)) if m else None


def _need_game():
    if not _game_pid():
        raise RuntimeError("bb-probe is not running")


def _latest_log():
    logs = sorted(LIVE.glob("*.log"), key=lambda p: p.stat().st_mtime)
    if not logs:
        raise RuntimeError(f"no *.log in {LIVE}")
    return logs[-1]


def _read_from(path, offset):
    with open(path, "rb") as f:
        f.seek(offset)
        return f.read().decode("utf-8", "replace")


def _cfg_text():
    return CFG.read_text(encoding="ascii", errors="replace")


def _cfg_write(text):
    # ASCII, LF, invariant numbers: the game re-reads the file on change.
    CFG.write_bytes(text.replace("\r\n", "\n").encode("ascii"))


def _cfg_with(base, values):
    """base text with KEY=value lines replaced or appended (value None removes the key)."""
    lines = [l for l in base.split("\n") if l.strip()]
    for k, v in values.items():
        lines = [l for l in lines if not l.startswith(k + "=")]
        if v is not None:
            lines.append(f"{k}={v}")
    return "\n".join(lines) + "\n"


def _parse_set(s):
    """'A=1;B=2' -> {A: '1', B: '2'}"""
    out = {}
    for part in filter(None, (p.strip() for p in s.split(";"))):
        k, v = part.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _windrive(*lines):
    scripts = sorted(glob.glob(WINDRIVE_GLOB), key=os.path.getmtime)
    if not scripts:
        raise RuntimeError("WinDrive.ps1 (universal-modder plugin) not found")
    p = subprocess.Popen(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                          scripts[-1], "-Proc", "bb-probe"], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, text=True, bufsize=1)
    replies = [p.stdout.readline().strip()]
    for line in lines:
        p.stdin.write(line + "\n")
        p.stdin.flush()
        replies.append(p.stdout.readline().strip())
    p.stdin.close()
    p.wait(10)
    return replies


def _toggle_stock():
    # BB_RT_PAUSE in rt.cfg is the same switch as F9, without focusing the game window or
    # sending keys (the user keeps the mouse and focus).
    base = _cfg_text()
    paused = any(l.strip() == "BB_RT_PAUSE=1" for l in base.split("\n"))
    _cfg_write(_cfg_with(base, {"BB_RT_PAUSE": "0" if paused else "1"}))


def _regions(regions):
    if not regions:
        return {"frame": [0.0, 0.0, 1.0, 1.0]}
    out = {}
    for k, box in regions.items():
        if len(box) != 4 or not all(0.0 <= v <= 1.0 for v in box):
            raise ValueError(f"region {k}: need [x0, y0, x1, y1] fractions 0..1")
        out[k] = [float(v) for v in box]
    return out


def _measure(regions, sec):
    cap = lv.Capture()
    try:
        return lv.report(*lv.series(cap, regions, sec))
    finally:
        cap.stop()


def _frames(box, n, gap):
    cap = lv.Capture()
    try:
        out = []
        for _ in range(n):
            out.append(lv.crop(cap.frame(), box) if box else cap.frame())
            if gap > 0:
                time.sleep(gap)
        return out
    finally:
        cap.stop()


def _png(rgb, max_w=1600):
    if rgb.shape[1] > max_w:
        s = max_w / rgb.shape[1]
        rgb = cv2.resize(rgb, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".png", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    return Image(data=buf.tobytes(), format="png")


def _sheet(tiles, cols):
    h = min(t.shape[0] for t in tiles)
    w = min(t.shape[1] for t in tiles)
    tiles = [t[:h, :w] for t in tiles]
    while len(tiles) % cols:
        tiles.append(np.zeros_like(tiles[0]))
    return np.vstack([np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)])


# --------------------------------------------------------------------------- tools

@mcp.tool()
def game_status() -> str:
    """Is bb-probe running, which log it writes, and the extra knobs in rt.cfg."""
    pid = _game_pid()
    log = _latest_log()
    return (f"bb-probe pid {pid}\nlog {log} ({log.stat().st_size // 1024} KB, "
            f"{time.time() - log.stat().st_mtime:.0f} s since last write)\nrt.cfg:\n{_cfg_text()}"
            if pid else f"bb-probe not running; last log {log}")


@mcp.tool()
def vision_measure(regions: dict[str, list[float]] | None = None, sec: float = 6.0,
                   stock_ab: bool = False) -> str:
    """Live capture of the game image for `sec` seconds. Per region ([x0, y0, x1, y1] fractions
    of the game image, black bars removed): mean luma, flicker sd % and p2p %, main Hz, frame
    step, optical-flow motion px/frame (wobble; ~0.015-0.025 is the noise floor).
    stock_ab: then press F9, wait 3 s, measure stock the same way and toggle back.
    RT captures at ~11 fps (stock ~90): sd/p2p compare, Hz above ~5 does not."""
    _need_game()
    r = _regions(regions)
    out = "== RT\n" + _measure(r, sec)
    if stock_ab:
        _toggle_stock()
        time.sleep(3)
        try:
            out += "\n== stock\n" + _measure(r, sec)
        finally:
            _toggle_stock()
    return out


@mcp.tool()
def vision_grab(scale: float = 0.5, region: list[float] | None = None,
                stock_ab: bool = False) -> Image:
    """One frame of the game image (optionally a [x0, y0, x1, y1] crop), scaled. stock_ab: the RT
    frame on top, the F9 stock frame of the same view below."""
    _need_game()
    box = _regions({"r": region})["r"] if region else None
    imgs = _frames(box, 1, 0)
    if stock_ab:
        _toggle_stock()
        time.sleep(3)
        try:
            imgs += _frames(box, 1, 0)
        finally:
            _toggle_stock()
    img = np.vstack([i[:min(x.shape[0] for x in imgs), :min(x.shape[1] for x in imgs)]
                     for i in imgs])
    if scale != 1.0:
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return _png(img, max_w=2400)


@mcp.tool()
def vision_strip(region: list[float], frames: int = 8, gap: float = 0.15,
                 stock_ab: bool = False) -> Image:
    """A contact sheet of `frames` consecutive crops (gap seconds apart, 4 per row) to see a flame,
    a flicker or a moving shadow change over time. stock_ab adds the stock rows below."""
    _need_game()
    box = _regions({"r": region})["r"]
    tiles = _frames(box, frames, gap)
    if stock_ab:
        _toggle_stock()
        time.sleep(3)
        try:
            tiles += _frames(box, frames, gap)
        finally:
            _toggle_stock()
    return _png(_sheet(tiles, 4))


@mcp.tool()
def vision_motion_map(region: list[float] | None = None, frames: int = 12) -> Image:
    """Mean frame (left) and per-pixel temporal sd heat map (right) over consecutive frames: shows
    WHERE the image changes (flicker, boiling, a moving light) rather than how much."""
    _need_game()
    box = _regions({"r": region})["r"] if region else None
    st = np.stack([f.astype(np.float32) for f in _frames(box, frames, 0)])
    sd = st.std(axis=0).mean(axis=2)
    heat = cv2.cvtColor(cv2.applyColorMap(np.clip(sd * 6, 0, 255).astype(np.uint8),
                                          cv2.COLORMAP_INFERNO), cv2.COLOR_BGR2RGB)
    return _png(np.hstack([st.mean(axis=0).astype(np.uint8), heat]))


@mcp.tool()
def stock_toggle() -> str:
    """Press F9: RT off/on (stock renderer). Wait ~3 s before judging; exposure adapts."""
    _need_game()
    _toggle_stock()
    return "ok"


@mcp.tool()
def knobs_get(pattern: str = "") -> str:
    """rt.cfg lines (live knobs) matching the regex pattern (all when empty)."""
    lines = [l for l in _cfg_text().split("\n") if l.strip()]
    return "\n".join(l for l in lines if re.search(pattern, l)) or "(none)"


@mcp.tool()
def knobs_set(values: dict[str, str | None]) -> str:
    """Set (or with null remove) rt.cfg knobs, e.g. {"BB_RT_FIXED_SWAY": "0.02"}. Persistent: the
    game re-reads the file at once. Knob defaults belong in code only with the user's approval."""
    _cfg_write(_cfg_with(_cfg_text(), values))
    return knobs_get("|".join(re.escape(k) for k in values) or "^$")


@mcp.tool()
def knob_ab(sets: list[str], regions: dict[str, list[float]] | None = None, sec: float = 6.0,
            settle: float = 2.0) -> str:
    """Interleaved knob A/B on the live image: for each set ('' = base, 'A=1;B=2') write it on
    top of rt.cfg, wait `settle` s, run vision_measure. rt.cfg is restored after. Interleave
    (['', 'X=1', '', 'X=1']): fires and adaptation drift over minutes."""
    _need_game()
    r = _regions(regions)
    orig = _cfg_text()
    out = []
    try:
        for s in sets:
            _cfg_write(_cfg_with(orig, _parse_set(s)))
            time.sleep(settle)
            out.append(f"== {s or 'base'}\n" + _measure(r, sec))
    finally:
        _cfg_write(orig)
    return "\n".join(out)


@mcp.tool()
def pad_hold(tokens: str, ms: int = 500) -> str:
    """Hold pad tokens for ms, then release (live pad file). Tokens: cross circle square triangle
    l1 r1 l2 r2 l3 r3 options up down left right, sticks lx= ly= rx= ry= 0..255 (128 centre).
    Normal mode: rx turns (~1300 ms = 45 deg), ly walks; never r2/l2 (attack). Fly mode: ly/lx
    move, rx/ry look, r2/l2 up/down."""
    _need_game()
    PAD.write_text(tokens, encoding="ascii")
    time.sleep(max(ms, 0) / 1000)
    PAD.write_text("", encoding="ascii")
    time.sleep(0.3)
    return "ok"


@mcp.tool()
def freecam_cycle() -> str:
    """Debug camera mode: normal -> fly -> fixed -> normal (Cross + L3). Cross near the
    workbench opens the Workshop menu (close with pad_hold('circle', 200))."""
    _need_game()
    for t, ms in (("cross", 300), ("cross l3", 250), ("cross", 150), ("", 1200)):
        PAD.write_text(t, encoding="ascii")
        time.sleep(ms / 1000)
    return "ok"


_DL = re.compile(r"RT dlist frame (\d+) #\d+ id (\d+) (\S+) world \(([^)]*)\) game r ([\d.]+) .*? "
                 r"lum ([\d.]+) emitter (\d) lamp (\d).*? track colour \(([\d.]+) ([\d.]+) "
                 r"([\d.]+)\) cam ([\d.]+)")


@mcp.tool()
def lights(sec: float = 5.0, max_cam: float = 12.0) -> str:
    """Per-frame direct-light statistics for `sec` seconds (BB_RT_DIRECT_LIST_LOG=2, restored
    after): per tracked light within max_cam m: shader, world, game radius, emitter/lamp, the
    game's own colour sum and its flicker sd %, and the RT light after our flicker (lum, sd %)."""
    _need_game()
    log = _latest_log()
    orig = _cfg_text()
    n = log.stat().st_size
    try:
        _cfg_write(_cfg_with(orig, {"BB_RT_DIRECT_LIST_LOG": "2"}))
        time.sleep(sec)
    finally:
        _cfg_write(orig)
    time.sleep(0.5)
    rows = {}
    for m in _DL.finditer(_read_from(log, n)):
        if float(m.group(12)) > max_cam:
            continue
        r = rows.setdefault(m.group(2), {"name": m.group(3), "w": m.group(4), "r": m.group(5),
                                         "em": m.group(7), "lamp": m.group(8),
                                         "cam": m.group(12), "lum": [], "game": []})
        r["lum"].append(float(m.group(6)))
        r["game"].append(sum(float(m.group(i)) for i in (9, 10, 11)))

    def sd(v):
        a = np.array(v)
        return 100 * a.std() / a.mean() if a.mean() > 0 else 0.0

    out = [f"{len(rows)} lights, log {log.name}"]
    for k, r in sorted(rows.items(), key=lambda kv: float(kv[1]["cam"])):
        out.append(f"id {k:4} {r['name']:27} w ({r['w']}) r {r['r']} em {r['em']} lamp "
                   f"{r['lamp']} cam {r['cam']} n {len(r['lum'])}: game {np.mean(r['game']):.3f} "
                   f"sd {sd(r['game']):.1f}%  RT lum {np.mean(r['lum']):.3f} sd {sd(r['lum']):.1f}%")
    return "\n".join(out)


@mcp.tool()
def log_grep(pattern: str, last_kb: int = 2000, max_lines: int = 60) -> str:
    """Regex search over the last `last_kb` KB of the current game log; the last max_lines hits."""
    log = _latest_log()
    size = log.stat().st_size
    text = _read_from(log, max(0, size - last_kb * 1024))
    hits = [l for l in text.split("\n") if re.search(pattern, l)]
    return f"{len(hits)} hits in {log.name}\n" + "\n".join(hits[-max_lines:])


if __name__ == "__main__":
    mcp.run()
