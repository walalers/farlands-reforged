#!/usr/bin/env python3
"""Group built jars by whether their compiled classes are actually identical.

    python tools/compare_jars.py path/to/*.jar

Mapping tables tell you whether the names a mod references still exist. They do not tell you what the
compiler emitted: a covariant override, for instance, silently changes the call site. `ServerPlayer.level()`
returns `Level` on 1.21 and `ServerLevel` on 1.21.10, so jars built against the two call different methods
even though every name the mod mentions is unchanged.

So compare the real thing. Two jars whose class entries hash the same are interchangeable, and their
Minecraft version range can safely cover both. Non-class entries (the manifest, fabric.mod.json) carry the
version string and build timestamp, so they are reported separately rather than counted as a difference.
"""
import hashlib, sys, zipfile
from collections import OrderedDict
from pathlib import Path

jars = [Path(p) for p in sys.argv[1:]]
if len(jars) < 2:
    raise SystemExit(__doc__)

def fingerprint(path):
    classes, others = {}, {}
    with zipfile.ZipFile(path) as zf:
        for name in sorted(zf.namelist()):
            if name.endswith('/'):
                continue
            digest = hashlib.sha256(zf.read(name)).hexdigest()
            (classes if name.endswith('.class') else others)[name] = digest
    return classes, others

prints = {jar: fingerprint(jar) for jar in jars}

groups = OrderedDict()
for jar, (classes, _) in prints.items():
    key = tuple(sorted(classes.items()))
    groups.setdefault(key, []).append(jar)

print(f'{len(jars)} jars -> {len(groups)} distinct sets of compiled classes\n')
for i, (_, members) in enumerate(groups.items(), 1):
    print(f'  group {i}: ' + ', '.join(m.name for m in members))

if len(groups) > 1:
    print('\nWhat differs between the groups:')
    reps = [members[0] for members in groups.values()]
    base_classes = prints[reps[0]][0]
    for rep in reps[1:]:
        other = prints[rep][0]
        changed = sorted(n for n in set(base_classes) | set(other)
                         if base_classes.get(n) != other.get(n))
        print(f'  {reps[0].name} vs {rep.name}: ' + ', '.join(changed))
    print('\n  Disassemble a differing class in both to see the call that moved:')
    print('    unzip -p <jar> <class> > /tmp/a.class && javap -p -c /tmp/a.class')

names = set()
for _, others in prints.values():
    names |= set(others)
print('\nNon-class entries (expected to differ, they carry the version and build time):')
print('  ' + ', '.join(sorted(names)))
