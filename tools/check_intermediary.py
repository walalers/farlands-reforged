#!/usr/bin/env python3
"""Do Farlands Reforged's mixin targets keep the same *intermediary* names across the 1.21 family?

A Fabric jar is remapped to intermediary at build time, so a jar built for one Minecraft version only
works on another if every class, method and field it references carries the same intermediary name there.
This chains Mojang's official mappings (named -> obfuscated) with Fabric's intermediary tiny files
(obfuscated -> intermediary) and prints the intermediary name of every target, per version.
"""
import os, sys, collections

SP = os.path.dirname(os.path.abspath(__file__))
VERSIONS = ['1.21','1.21.1','1.21.2','1.21.3','1.21.4','1.21.5','1.21.6','1.21.7','1.21.8','1.21.9','1.21.10','1.21.11']

PRIMS = {'int':'I','double':'D','float':'F','long':'J','boolean':'Z','byte':'B','char':'C','short':'S','void':'V'}

# (named class, member signature as it appears in the Mojang mappings)
TARGETS = [
  ('net.minecraft.world.level.levelgen.synth.BlendedNoise', 'm', 'compute', ['net.minecraft.world.level.levelgen.DensityFunction$FunctionContext']),
  ('net.minecraft.world.level.levelgen.synth.PerlinNoise', 'm', 'wrap', ['double']),
  ('net.minecraft.world.level.levelgen.synth.ImprovedNoise', 'm', 'noise', ['double','double','double','double','double']),
  ('net.minecraft.util.Mth', 'm', 'floor', ['double']),
  ('net.minecraft.world.level.levelgen.DensityFunctions$RangeChoice', 'm', 'compute', ['net.minecraft.world.level.levelgen.DensityFunction$FunctionContext']),
  ('net.minecraft.world.level.levelgen.DensityFunctions$RangeChoice', 'm', 'fillArray', ['double[]','net.minecraft.world.level.levelgen.DensityFunction$ContextProvider']),
  ('net.minecraft.world.level.levelgen.DensityFunctions$Noise', 'm', 'compute', ['net.minecraft.world.level.levelgen.DensityFunction$FunctionContext']),
  ('net.minecraft.world.level.levelgen.DensityFunctions$Noise', 'f', 'noise', None),
  ('net.minecraft.world.level.levelgen.SurfaceRules$Context', 'm', 'getMinSurfaceLevel', []),
  ('net.minecraft.world.level.levelgen.SurfaceRules$Context', 'f', 'blockX', None),
  ('net.minecraft.world.level.levelgen.SurfaceRules$Context', 'f', 'blockZ', None),
  ('net.minecraft.world.level.levelgen.SurfaceRules$Context', 'f', 'context', None),
  ('net.minecraft.world.level.levelgen.Aquifer$NoiseBasedAquifer', 'm', 'computeSubstance', ['net.minecraft.world.level.levelgen.DensityFunction$FunctionContext','double']),
  ('net.minecraft.world.level.levelgen.Aquifer$NoiseBasedAquifer', 'f', 'globalFluidPicker', None),
  ('net.minecraft.world.level.levelgen.Aquifer$NoiseBasedAquifer', 'f', 'shouldScheduleFluidUpdate', None),
  ('net.minecraft.world.level.levelgen.WorldGenerationContext', 'm', 'getMinGenY', []),
  ('net.minecraft.world.level.levelgen.feature.UnderwaterMagmaFeature', 'm', 'place', ['net.minecraft.world.level.levelgen.feature.FeaturePlaceContext']),
  ('net.minecraft.commands.Commands', 'f', 'dispatcher', None),
  ('net.minecraft.server.level.ServerPlayer', 'm', 'doTick', []),
  # --- everything the non-mixin code calls, which is remapped the same way ---
  ('net.minecraft.resources.ResourceLocation', 'm', 'fromNamespaceAndPath', ['java.lang.String','java.lang.String']),
  ('net.minecraft.resources.Identifier', 'm', 'fromNamespaceAndPath', ['java.lang.String','java.lang.String']),
  ('net.minecraft.commands.Commands', 'm', 'literal', ['java.lang.String']),
  ('net.minecraft.commands.Commands', 'f', 'LEVEL_GAMEMASTERS', None),
  ('net.minecraft.commands.CommandSourceStack', 'm', 'hasPermission', ['int']),
  ('net.minecraft.commands.CommandSourceStack', 'm', 'getPosition', []),
  ('net.minecraft.commands.CommandSourceStack', 'm', 'sendSystemMessage', ['net.minecraft.network.chat.Component']),
  ('net.minecraft.network.chat.Component', 'm', 'literal', ['java.lang.String']),
  ('net.minecraft.server.MinecraftServer', 'm', 'getAdvancements', []),
  ('net.minecraft.server.ServerAdvancementManager', 'm', 'get', ['net.minecraft.resources.ResourceLocation']),
  ('net.minecraft.server.PlayerAdvancements', 'm', 'getOrStartProgress', ['net.minecraft.advancements.AdvancementHolder']),
  ('net.minecraft.server.PlayerAdvancements', 'm', 'award', ['net.minecraft.advancements.AdvancementHolder','java.lang.String']),
  ('net.minecraft.advancements.AdvancementProgress', 'm', 'isDone', []),
  ('net.minecraft.advancements.AdvancementProgress', 'm', 'getRemainingCriteria', []),
  ('net.minecraft.server.level.ServerPlayer', 'm', 'getAdvancements', []),
  ('net.minecraft.world.entity.Entity', 'm', 'getX', []),
  ('net.minecraft.world.entity.Entity', 'm', 'getZ', []),
  ('net.minecraft.world.level.block.Blocks', 'f', 'WATER', None),
  ('net.minecraft.world.level.block.Blocks', 'f', 'LAVA', None),
  ('net.minecraft.world.level.block.state.BlockBehaviour', 'm', 'defaultBlockState', []),
  ('net.minecraft.world.level.block.state.BlockState', 'm', 'is', ['net.minecraft.world.level.block.Block']),
  ('net.minecraft.world.level.levelgen.Aquifer$FluidPicker', 'm', 'computeFluid', ['int','int','int']),
  ('net.minecraft.world.level.levelgen.Aquifer$FluidStatus', 'm', 'at', ['int']),
  ('net.minecraft.world.level.levelgen.DensityFunction$FunctionContext', 'm', 'blockX', []),
  ('net.minecraft.world.level.levelgen.DensityFunction$FunctionContext', 'm', 'blockY', []),
  ('net.minecraft.world.level.levelgen.DensityFunction$FunctionContext', 'm', 'blockZ', []),
  ('net.minecraft.world.level.levelgen.DensityFunction$ContextProvider', 'm', 'forIndex', ['int']),
  ('net.minecraft.world.level.levelgen.DensityFunction$NoiseHolder', 'm', 'noiseData', []),
  ('net.minecraft.world.level.levelgen.Noises', 'f', 'NOODLE', None),
  ('net.minecraft.world.level.levelgen.feature.FeaturePlaceContext', 'm', 'origin', []),
  ('net.minecraft.core.Vec3i', 'm', 'getX', []),
  ('net.minecraft.core.Vec3i', 'm', 'getZ', []),
]

def load_mojang(path):
    classes = {}           # named -> obf
    members = collections.defaultdict(list)  # named class -> [(kind, ret, name, params, obf)]
    cur = None
    with open(path) as fh:
        for line in fh:
            if line.lstrip().startswith('#'):
                continue
            if not line.startswith('    '):
                if ' -> ' in line:
                    named, obf = line.strip().rstrip(':').split(' -> ')
                    classes[named] = obf
                    cur = named
                else:
                    cur = None
            elif cur:
                body, obf = line.strip().rsplit(' -> ', 1)
                # strip "12:34:" line numbers
                while body[:1].isdigit() and ':' in body:
                    body = body.split(':', 1)[1]
                ret, rest = body.split(' ', 1)
                if '(' in rest:
                    name, params = rest.split('(', 1)
                    params = params.rstrip(')')
                    params = [p for p in params.split(',') if p]
                    members[cur].append(('m', ret, name, params, obf))
                else:
                    members[cur].append(('f', ret, rest, None, obf))
    return classes, members

def desc(t, classes):
    arr = 0
    while t.endswith('[]'):
        arr += 1; t = t[:-2]
    if t in PRIMS:
        d = PRIMS[t]
    else:
        d = 'L' + classes.get(t, t).replace('.', '/') + ';'
    return '[' * arr + d

def load_tiny(path):
    cls = {}     # obf class -> intermediary
    mem = {}     # (obf class, kind, obf name, obf desc) -> intermediary
    cur = None
    with open(path) as fh:
        next(fh)
        for line in fh:
            p = line.rstrip('\n').split('\t')
            if p[0] == 'c':
                cur = p[1]; cls[p[1]] = p[2]
            elif cur and p and p[0] == '' and len(p) >= 5 and p[1] in ('m', 'f'):
                mem[(cur, p[1], p[3], p[2])] = p[4]
    return cls, mem

results = collections.defaultdict(dict)
for v in VERSIONS:
    classes, members = load_mojang(os.path.join(SP, 'mappings', f'{v}.txt'))
    tcls, tmem = load_tiny(os.path.join(SP, 'intermediary', f'{v}.tiny'))
    for named_cls, kind, name, params in TARGETS:
        key = (named_cls, kind, name)
        obf_cls = classes.get(named_cls)
        if obf_cls is not None:
            # Mojang leaves a handful of classes unobfuscated (MinecraftServer, ...); those keep their
            # dotted package name here while the tiny files use slashes throughout.
            obf_cls = obf_cls.replace('.', '/')
        if obf_cls is None:
            results[key][v] = 'CLASS-MISSING'; continue
        inter_cls = tcls.get(obf_cls, obf_cls)
        hit = None
        for m in members.get(named_cls, []):
            if m[0] != kind or m[2] != name:
                continue
            if kind == 'm':
                if [p.strip() for p in m[3]] != params:
                    continue
                d = '(' + ''.join(desc(p, classes) for p in m[3]) + ')' + desc(m[1], classes)
            else:
                d = desc(m[1], classes)
            hit = tmem.get((obf_cls, kind, m[4], d))
            if hit is None:
                # Intermediary leaves a member unmapped when it does not need a stable name (overrides of
                # library methods, and anything Mojang already ships unobfuscated). Flag it so a silent
                # lookup miss can never be mistaken for a stable name.
                hit = f'{m[4]}(unmapped)'
            break
        results[key][v] = f'{inter_cls}.{hit}' if hit else 'MEMBER-MISSING'

changes = 0
print(f"{'target':<62} " + ' '.join(f'{v:>8}' for v in VERSIONS))
print('-' * (62 + 9 * len(VERSIONS)))
for key, per in results.items():
    short = key[0].split('.')[-1] + ('#' if key[1] == 'm' else '.') + key[2]
    vals = [per[v] for v in VERSIONS]
    uniq = {}
    tags = []
    for val in vals:
        if val not in uniq:
            uniq[val] = chr(ord('A') + len(uniq))
        tags.append(uniq[val])
    if len(uniq) > 1:
        changes += 1
    print(f'{short:<62} ' + ' '.join(f'{t:>8}' for t in tags) + ('   <-- CHANGES' if len(uniq) > 1 else ''))

print()
print('Letters are per-row identities: the same letter means the same intermediary name.')
print(f'{changes} of {len(results)} targets change intermediary name somewhere in the family.')

# group versions by the full fingerprint of all targets
fp = collections.OrderedDict()
for v in VERSIONS:
    key = tuple(results[k][v] for k in results if all(results[k][w] not in ('CLASS-MISSING','MEMBER-MISSING') for w in VERSIONS))
    fp.setdefault(key, []).append(v)
print()
print('Versions sharing an identical set of intermediary names (one jar can serve a whole group):')
for i, (_, vs) in enumerate(fp.items(), 1):
    print(f'  group {i}: ' + ', '.join(vs))
