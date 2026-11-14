"""Measure screenshots against docs/LOOK_GUIDE.md.

  look_check.py stats  A.png [B.png ...]   luma percentiles, dark floor, p90/p20, Lab tint
  look_check.py diff   A.png B.png         mean abs luma difference (camera/scene moved?)
  look_check.py sheet  OUT.png A.png ...   2-column contact sheet
  look_check.py mask   OUT.png A.png [L]   paint pixels under luma L (default: the p5) magenta

The HUD band (top 1/8) is cropped. "low" is the lower 55% (ground, petals, walls).
Needs Pillow (clang64 python has it).
"""
import sys
from PIL import Image, ImageChops, ImageStat


def flat(im):
    return list(getattr(im, "get_flattened_data", im.getdata)())


def body(im):
    # drop pillarbox bars (pure black columns) and the HUD band (top 1/8)
    w, h = im.size
    im = im.crop((0, h // 8, w, h))  # the FPS overlay sits in the bar, so trim below it
    box = im.convert("L").point(lambda v: 255 if v > 2 else 0).getbbox()
    return im.crop((box[0], 0, box[2], im.size[1])) if box else im


def pct(hist, p):
    tot, c = sum(hist), 0
    for i, v in enumerate(hist):
        c += v
        if c >= tot * p:
            return i
    return 255


def band_tint(rgb, lo, hi):
    px = sorted(zip(flat(rgb.convert("L")), flat(rgb.convert("LAB"))))
    sel = px[int(len(px) * lo):max(int(len(px) * hi), int(len(px) * lo) + 1)]
    n = len(sel)
    return (sum(t[0] for t in sel) / n, sum(t[1][1] - 128 for t in sel) / n,
            sum(t[1][2] - 128 for t in sel) / n)


def stats(paths):
    print("guide: pale lit 115-135 | floor p5 14-23, <5 under 0.5% | p90/p20 5.5-8 | "
          "top10% a -3..+2 b -4..+2")
    for p in paths:
        rgb = body(Image.open(p).convert("RGB"))
        hist = rgb.convert("L").histogram()
        tot = sum(hist)
        p5, p20, p50, p90, p95 = (pct(hist, q) for q in (0.05, 0.2, 0.5, 0.9, 0.95))
        black = 100.0 * sum(hist[:5]) / tot
        mean = ImageStat.Stat(rgb.convert("L")).mean[0]
        w, h = rgb.size
        low = rgb.crop((0, int(h * 0.45), w, h))
        tl, ta, tb = band_tint(low, 0.9, 1.0)
        ml, ma, mb = band_tint(low, 0.4, 0.6)
        print(f"{p}\n  mean {mean:5.1f} p5 {p5} p20 {p20} p50 {p50} p90 {p90} p95 {p95} "
              f"<5 {black:.2f}% p90/p20 {p90 / max(p20, 1):.1f}\n"
              f"  low top10% luma {tl:5.1f} a {ta:+.1f} b {tb:+.1f} | mid luma {ml:5.1f} "
              f"a {ma:+.1f} b {mb:+.1f}")


def diff(a, b):
    x = Image.open(a).convert("L")
    y = Image.open(b).convert("L").resize(x.size)
    print(f"diff {ImageStat.Stat(ImageChops.difference(x, y)).mean[0]:.1f}")


def sheet(out, paths):
    ims = [Image.open(p).convert("RGB") for p in paths]
    w, h = ims[0].size
    s = Image.new("RGB", (w * 2, h * ((len(ims) + 1) // 2)))
    for i, im in enumerate(ims):
        s.paste(im.resize((w, h)), ((i % 2) * w, (i // 2) * h))
    s.save(out)
    print(out)


def mask(out, path, level=None):
    # where the dark floor is: ground shadow (a fault) or silhouettes against the sky (fine)
    rgb = body(Image.open(path).convert("RGB"))
    lum = rgb.convert("L")
    level = float(level) if level else pct(lum.histogram(), 0.05) + 0.5
    hot = lum.point(lambda v: 255 if v < level else 0)
    rgb.paste((255, 0, 255), mask=hot)
    rgb.save(out)
    print(f"{out}: under {level:.1f}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "stats":
        stats(args)
    elif cmd == "diff":
        diff(*args[:2])
    elif cmd == "mask":
        mask(*args[:3])
    elif cmd == "sheet":
        sheet(args[0], args[1:])
    else:
        sys.exit(__doc__)
