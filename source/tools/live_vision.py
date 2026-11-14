"""Real-time vision of the running game (bb-probe) for the render-look skill.

Captures the game window with DXGI desktop duplication (dxcam) at the display rate instead of
single screenshots, so effects in time (flame flicker, wobble, boiling, adaptation) are measured.

Run with the project venv (out/vision-venv: dxcam numpy opencv-python-headless):
  py -m venv out/vision-venv; out/vision-venv/Scripts/python -m pip install dxcam numpy opencv-python-headless

Regions are name=x0,y0,x1,y1 as fractions (0..1) of the game image (black side bars removed).

  live_vision.py measure --sec 5 wall=0.81,0.42,0.98,0.78 fire=0.55,0.57,0.71,0.78
      per region: mean luma, flicker sd % and peak-to-peak %, dominant frequency (Hz),
      frame-to-frame change, optical-flow motion (px/frame at 1/4 res = wobble)
  live_vision.py fps [--sec 3]                raw capture rate (no processing)
  live_vision.py stream --sec 60 wall=...     one line per second (for the Monitor tool)
  live_vision.py grab OUT.png [--scale 0.5]   one frame, game image only
"""
import ctypes
import ctypes.wintypes as wt
import sys
import time

import cv2
import dxcam
import numpy as np

PROC = "bb-probe.exe"


def game_rect():
    """Client rect of the largest visible bb-probe window, in screen pixels."""
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    found = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        h = kernel32.OpenProcess(0x1000, False, pid.value)
        if h:
            buf = ctypes.create_unicode_buffer(512)
            n = wt.DWORD(512)
            if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)) and \
                    buf.value.lower().endswith(PROC):
                r = wt.RECT()
                user32.GetClientRect(hwnd, ctypes.byref(r))
                p = wt.POINT(0, 0)
                user32.ClientToScreen(hwnd, ctypes.byref(p))
                found.append((r.right * r.bottom, (p.x, p.y, p.x + r.right, p.y + r.bottom)))
            kernel32.CloseHandle(h)
        return True

    user32.EnumWindows(cb, 0)
    if not found:
        raise RuntimeError(f"{PROC} window not found")
    return max(found)[1]


def luma(rgb):
    return rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722


class Capture:
    def __init__(self):
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        x0, y0, x1, y1 = game_rect()
        self.cam = dxcam.create(output_color="RGB")
        w, h = self.cam.width, self.cam.height
        self.region = (max(x0, 0), max(y0, 0), min(x1, w), min(y1, h))
        self.cam.start(region=self.region, target_fps=240, video_mode=False)
        first = self.next()
        # The RT build letterboxes the game inside the window: drop the black side columns.
        cols = first.max(axis=(0, 2))
        lit = np.nonzero(cols > 6)[0]
        self.x0, self.x1 = (int(lit[0]), int(lit[-1]) + 1) if len(lit) else (0, first.shape[1])

    def next(self):
        f = None
        while f is None:
            f = self.cam.get_latest_frame()
        return f

    def frame(self):
        return self.next()[:, self.x0:self.x1]

    def stop(self):
        self.cam.stop()


def parse_regions(args):
    regions = {}
    for a in args:
        name, box = a.split("=")
        regions[name] = [float(v) for v in box.split(",")]
    return regions or {"frame": [0.0, 0.0, 1.0, 1.0]}


def crop(img, box):
    h, w = img.shape[:2]
    return img[int(box[1] * h):int(box[3] * h), int(box[0] * w):int(box[2] * w)]


def series(cap, regions, sec):
    t0 = time.perf_counter()
    times, means, small_prev = [], {k: [] for k in regions}, {}
    flow = {k: [] for k in regions}
    step = {k: [] for k in regions}
    while time.perf_counter() - t0 < sec:
        img = cap.frame()
        times.append(time.perf_counter() - t0)
        # half size once: region means are the same, the per-region work 4x cheaper
        img = cv2.resize(img, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        for k, box in regions.items():
            c = crop(img, box).astype(np.float32)
            means[k].append(float(luma(c).mean()))
            g = cv2.resize(luma(c), None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
            if k in small_prev:
                p = small_prev[k]
                step[k].append(float(np.abs(g - p).mean()))
                f = cv2.calcOpticalFlowFarneback(p.astype(np.uint8), g.astype(np.uint8), None,
                                                 0.5, 2, 9, 2, 5, 1.1, 0)
                flow[k].append(float(np.linalg.norm(f, axis=2).mean()))
            small_prev[k] = g
    return np.array(times), means, step, flow


def report(times, means, step, flow):
    n = len(times)
    fps = (n - 1) / (times[-1] - times[0]) if n > 1 else 0.0
    out = [f"{n} frames, {fps:.0f} fps"]
    for k in means:
        m = np.array(means[k])
        avg = m.mean()
        sd = 100 * m.std() / avg if avg > 0 else 0.0
        p2p = 100 * (m.max() - m.min()) / avg if avg > 0 else 0.0
        hz = 0.0
        if n > 8 and fps > 0:
            # resample to even steps, then the strongest non-DC frequency
            t = np.linspace(times[0], times[-1], n)
            u = np.interp(t, times, m) - avg
            spec = np.abs(np.fft.rfft(u * np.hanning(n)))
            freqs = np.fft.rfftfreq(n, (times[-1] - times[0]) / (n - 1))
            if len(spec) > 2:
                hz = float(freqs[1 + int(np.argmax(spec[1:]))])
        st = np.mean(step[k]) if step[k] else 0.0
        fl = np.mean(flow[k]) if flow[k] else 0.0
        out.append(f"  {k:12s} mean {avg:6.1f}  flicker sd {sd:4.1f}% p2p {p2p:5.1f}%  "
                   f"main {hz:4.1f} Hz  step {st:5.2f}  motion {fl:5.3f} px/f")
    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd, args = sys.argv[1], sys.argv[2:]
    opts = {}
    rest = []
    i = 0
    while i < len(args):
        if args[i].startswith("--"):
            opts[args[i][2:]] = args[i + 1]
            i += 2
        else:
            rest.append(args[i])
            i += 1
    cap = Capture()
    try:
        if cmd == "grab":
            img = cap.frame()
            s = float(opts.get("scale", 1.0))
            if s != 1.0:
                img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
            cv2.imwrite(rest[0], cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            print(f"{rest[0]}: {img.shape[1]}x{img.shape[0]}")
        elif cmd == "fps":
            t0, n = time.perf_counter(), 0
            while time.perf_counter() - t0 < float(opts.get("sec", 3)):
                cap.next()
                n += 1
            print(f"capture {n / (time.perf_counter() - t0):.0f} fps, game image "
                  f"{cap.x1 - cap.x0}x{cap.region[3] - cap.region[1]}")
        elif cmd == "measure":
            print(report(*series(cap, parse_regions(rest), float(opts.get("sec", 5)))), flush=True)
        elif cmd == "stream":
            end = time.perf_counter() + float(opts.get("sec", 60))
            regions = parse_regions(rest)
            while time.perf_counter() < end:
                r = report(*series(cap, regions, 1.0))
                print(time.strftime("%H:%M:%S ") + r.replace("\n", " |"), flush=True)
        else:
            sys.exit(__doc__)
    finally:
        cap.stop()


if __name__ == "__main__":
    main()
