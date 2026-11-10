import os
import re
import subprocess
import sys

if len(sys.argv) < 3:
    sys.exit('usage: sync-live-shaders.py <build dir with build.ninja> <BB_RT_SHADER_DIR>')
build, dst = sys.argv[1], sys.argv[2]
text = open(os.path.join(build, 'build.ninja'), encoding='utf-8', errors='replace').read()
rules = {}
for m in re.finditer(r'(\S*glslang\.exe) (.*?) -o \S+/host_shaders/(\w+)\.h --vn \w+ (.*?)(\S+\.(?:comp|glsl|frag|vert)) &&', text):
    exe, pre, name, defs, src = m.groups()
    rules[name] = (exe, pre.split(), defs.split(), src)
names = sorted(f[:-4] for f in os.listdir(dst) if f.endswith('.spv'))
done = 0
for n in names:
    if n not in rules:
        print(f'sync-live-shaders: no build rule for {n}, left as is')
        continue
    exe, pre, defs, src = rules[n]
    tmp = os.path.join(dst, n + '.spv.tmp')
    r = subprocess.run([exe, *pre, '-o', tmp, *defs, src], capture_output=True, text=True)
    if r.returncode:
        print(f'sync-live-shaders: {n} failed\n{r.stdout[-800:]}{r.stderr[-800:]}')
        if os.path.exists(tmp):
            os.remove(tmp)
        continue
    new = open(tmp, 'rb').read()
    path = os.path.join(dst, n + '.spv')
    if os.path.exists(path) and open(path, 'rb').read() == new:
        os.remove(tmp)
    else:
        os.replace(tmp, path)
        done += 1
print(f'sync-live-shaders: {done} of {len(names)} shaders updated from {build}')
