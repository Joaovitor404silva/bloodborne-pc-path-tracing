"""Glass masks for meshes that mix glass and metal (BB_RT_GLASS_MASK_DUMP, RayTracing::GlassMaskSlots).

Run with the vision venv (out/vision-venv, needs texture2ddecoder numpy opencv).

  glass_mask.py decode DUMP.raw OUT.png
      decode a dumped albedo (<hash>_<w>x<h>_<vk format>.raw, BC1-BC7 or RGBA8/BGRA8) to PNG
  glass_mask.py pgm PAINT.png OUT.pgm
      white (> 127) pixels of a painted image become glass in an 8-bit P5 mask
      (OUT must be <dir of BB_RT_CFG>/glass_masks/<hash>.pgm; any size, it is sampled by UV)
"""
import pathlib
import re
import sys

import cv2
import numpy as np
import texture2ddecoder as t2d

BC = {131: "bc1", 132: "bc1", 133: "bc1", 134: "bc1", 135: None, 136: None, 137: "bc3",
      138: "bc3", 139: "bc4", 140: "bc4", 141: "bc5", 142: "bc5", 143: "bc6", 144: "bc6",
      145: "bc7", 146: "bc7"}


def decode(raw, out):
    m = re.search(r"_(\d+)x(\d+)_(\d+)\.raw$", raw)
    if not m:
        sys.exit("name must end in _<w>x<h>_<vk format>.raw")
    w, h, fmt = (int(v) for v in m.groups())
    data = pathlib.Path(raw).read_bytes()
    if fmt in BC:
        if not BC[fmt]:
            sys.exit(f"BC2 (format {fmt}) not supported")
        bgra = getattr(t2d, "decode_" + BC[fmt])(data, w, h)
        img = np.frombuffer(bgra, np.uint8).reshape(h, w, 4)
    elif 37 <= fmt <= 50:
        img = np.frombuffer(data, np.uint8)[:w * h * 4].reshape(h, w, 4)
        if fmt <= 43:  # RGBA -> BGRA for OpenCV
            img = img[..., [2, 1, 0, 3]]
    else:
        sys.exit(f"format {fmt} not supported")
    cv2.imwrite(out, img)
    print(f"{out}: {w}x{h} format {fmt}")


def pgm(paint, out):
    img = cv2.imread(paint, cv2.IMREAD_GRAYSCALE)
    if img is None:
        sys.exit(f"cannot read {paint}")
    mask = np.where(img > 127, 255, 0).astype(np.uint8)
    h, w = mask.shape
    pathlib.Path(out).write_bytes(f"P5\n{w} {h}\n255\n".encode() + mask.tobytes())
    print(f"{out}: {w}x{h}, glass {100 * (mask > 0).mean():.1f}%")


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ("decode", "pgm"):
        sys.exit(__doc__)
    (decode if sys.argv[1] == "decode" else pgm)(sys.argv[2], sys.argv[3])


if __name__ == "__main__":
    main()
