"""Per-pixel temporal noise of the running game (shadow speckle / boiling), per region.

Region-mean flicker (live_vision measure) is dominated by global exposure drift. This captures
N frames at full resolution, divides each region by its own mean (removes adaptation drift),
and reports the per-pixel temporal sd in luma levels: median and p90 over the region's pixels,
plus "speckle": the sd of the time-averaged image minus its 3x3 blur (frozen spatial noise;
texture detail adds to it too, so compare only the same view).
Static camera required.

  pixel_noise.py --frames 40 name=x0,y0,x1,y1 ...
"""
import argparse
import sys

import cv2
import numpy as np

sys.path.insert(0, __file__.rsplit("\\", 1)[0].rsplit("/", 1)[0])
from live_vision import Capture, crop, luma, parse_regions  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=40)
    ap.add_argument("--label", default="")
    ap.add_argument("regions", nargs="*")
    a = ap.parse_args()
    regions = parse_regions(a.regions)
    cap = Capture()
    stacks = {k: [] for k in regions}
    prev = None
    try:
        while len(next(iter(stacks.values()))) < a.frames:
            img = cap.frame()
            if prev is not None and np.array_equal(img[::37, ::37], prev):
                continue  # duplicate capture of the same game frame
            prev = img[::37, ::37].copy()
            for k, box in regions.items():
                stacks[k].append(luma(crop(img, box).astype(np.float32)))
    finally:
        cap.stop()
    out = []
    for k, s in stacks.items():
        s = np.stack(s)
        m = s.mean(axis=(1, 2), keepdims=True)
        s = s / np.maximum(m, 1e-3) * m.mean()
        sd = s.std(axis=0)
        # spatial speckle: frozen (static seed) noise is invisible to the temporal sd
        mean_img = s.mean(axis=0)
        hp = mean_img - cv2.blur(mean_img, (3, 3))
        out.append(f"{k} mean {s.mean():6.1f} sd med {np.median(sd):5.2f} p90 {np.percentile(sd, 90):5.2f}"
                   f" speckle {hp.std():5.2f}")
    print(a.label, " | ".join(out))


if __name__ == "__main__":
    main()
