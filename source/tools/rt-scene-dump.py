import io
import re
import sys

log = sys.argv[1]
lines = [l.rstrip("\r\n") for l in io.open(log, encoding="utf-8", errors="replace") if l.startswith("Scene ")]
out = []
for i, l in enumerate(lines):
    if l.startswith("Scene dispatch"):
        m = re.match(r"Scene dispatch cs 0*([0-9a-f]+) (\S+)", l)
        out.append("%3d  CS %s %s" % (i, m.group(1), m.group(2)))
        continue
    if l.startswith("Scene native read"):
        out.append("%3d  READ %s" % (i, l[len("Scene native read: "):]))
        continue
    m = re.match(r"Scene pass: reduced (\d) pass vs ([0-9a-f]+) ps ([0-9a-f]+) mrt (\S+) samples (\d+) raster_scaling (\w+):(.*)", l)
    if not m:
        out.append("%3d  ?? %s" % (i, l[:120]))
        continue
    tgts = re.findall(r"\[(\w+) (\d+x\d+) eligible[^\]]*\]", m.group(7))
    depth = re.search(r"depth \[(\w+) (\d+x\d+)", m.group(7))
    t = " ".join("%s@%s" % (f, s) for f, s in tgts[: len(tgts) - (1 if depth else 0)])
    d = (" D:%s@%s" % (depth.group(1), depth.group(2))) if depth else ""
    out.append("%3d  PASS vs %s ps %s mrt %s %s%s" % (i, m.group(2), m.group(3), m.group(4), t, d))

skip = re.compile(r"@(128x128|64x64|32x32|16x16|4096x4096)\b")
compact = []
run = 0
for o in out:
    if skip.search(o):
        run += 1
        continue
    if run:
        compact.append("     ... %d probe/shadow lines" % run)
        run = 0
    compact.append(o)
if run:
    compact.append("     ... %d probe/shadow lines" % run)
print("\n".join(compact))
