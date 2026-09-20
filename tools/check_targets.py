#!/usr/bin/env python3
"""Check every class/member Farlands Reforged mixes into against Mojang's official mappings."""
import os, re, sys, collections

SP = os.path.dirname(os.path.abspath(__file__))
MAP = os.path.join(SP, 'mappings')
VERSIONS = ['1.21','1.21.1','1.21.2','1.21.3','1.21.4','1.21.5','1.21.6','1.21.7','1.21.8','1.21.9','1.21.10','1.21.11']

# class -> list of members to look for. A member is (kind, name, matcher)
TARGETS = {
 'net.minecraft.world.level.levelgen.synth.BlendedNoise': ['double compute(net.minecraft.world.level.levelgen.DensityFunction$FunctionContext)'],
 'net.minecraft.world.level.levelgen.synth.PerlinNoise': ['double wrap(double)'],
 'net.minecraft.world.level.levelgen.synth.ImprovedNoise': ['double noise(double,double,double,double,double)'],
 'net.minecraft.util.Mth': ['int floor(double)'],
 'net.minecraft.world.level.levelgen.DensityFunctions$RangeChoice': ['compute(','fillArray(','input()','minInclusive()','maxExclusive()','whenInRange()','whenOutOfRange()'],
 'net.minecraft.world.level.levelgen.DensityFunctions$Noise': ['compute(','NoiseHolder noise'],
 'net.minecraft.world.level.levelgen.SurfaceRules$Context': ['getMinSurfaceLevel(','WorldGenerationContext context','int blockX','int blockZ'],
 'net.minecraft.world.level.levelgen.Aquifer$NoiseBasedAquifer': ['computeSubstance(','FluidPicker globalFluidPicker','boolean shouldScheduleFluidUpdate'],
 'net.minecraft.world.level.levelgen.WorldGenerationContext': ['getMinGenY('],
 'net.minecraft.world.level.levelgen.feature.UnderwaterMagmaFeature': ['boolean place(net.minecraft.world.level.levelgen.feature.FeaturePlaceContext)'],
 'net.minecraft.world.level.levelgen.Noises': ['NOODLE'],
 'net.minecraft.commands.Commands': ['<init>','LEVEL_GAMEMASTERS','dispatcher','literal(','argument('],
 'net.minecraft.server.level.ServerPlayer': ['void doTick()'],
 'net.minecraft.resources.ResourceLocation': ['fromNamespaceAndPath('],
 'net.minecraft.resources.Identifier': ['fromNamespaceAndPath('],
 'net.minecraft.advancements.AdvancementHolder': [],
 'net.minecraft.advancements.AdvancementProgress': ['isDone()','getRemainingCriteria('],
 'net.minecraft.server.PlayerAdvancements': ['getOrStartProgress(','award('],
 'net.minecraft.commands.CommandSourceStack': ['hasPermission(','sendSystemMessage(','sendSuccess(','getPosition('],
 'net.minecraft.world.level.levelgen.DensityFunction$NoiseHolder': ['noiseData('],
 'net.minecraft.server.ServerAdvancementManager': ['get('],
}

def parse(path, wanted):
    """Return {class: {'obf':..., 'members':[raw lines]}} for the wanted classes."""
    out = {}
    cur = None
    wanted = set(wanted)
    with open(path) as fh:
        for line in fh:
            if line.lstrip().startswith('#'):
                continue
            if not line.startswith('    '):
                # class line: "a.b.C -> x:"
                m = line.split(' -> ')
                if len(m) == 2:
                    name = m[0].strip()
                    cur = name if name in wanted else None
                    if cur:
                        out[cur] = {'obf': m[1].strip().rstrip(':'), 'members': []}
                else:
                    cur = None
            elif cur:
                out[cur]['members'].append(line.strip())
    return out

rows = {}
for v in VERSIONS:
    rows[v] = parse(os.path.join(MAP, f'{v}.txt'), TARGETS)

def find(members, needle):
    hits = [m for m in members if needle in m]
    return hits

print(f"{'target':<78} " + ' '.join(f'{v:>7}' for v in VERSIONS))
print('-' * (78 + 8*len(VERSIONS)))
sigs = collections.defaultdict(dict)
for cls, mems in TARGETS.items():
    short = cls.replace('net.minecraft.', '')
    line = f'{short:<78} '
    cells = []
    for v in VERSIONS:
        cells.append('  yes  ' if cls in rows[v] else '   -   ')
    print(line + ' '.join(cells))
    for mem in mems:
        line = f'  .{mem:<75} '
        cells = []
        for v in VERSIONS:
            if cls not in rows[v]:
                cells.append('   .   '); continue
            hits = find(rows[v][cls]['members'], mem)
            cells.append(f'{len(hits):>4}   ' if hits else '  MISS ')
            sigs[(cls, mem)][v] = tuple(sorted(re.sub(r'^\d+:\d+:', '', h).split(' -> ')[0] for h in hits))
        print(line + ' '.join(cells))

print()
print('=== signature changes across the family ===')
for key, per in sigs.items():
    vals = list(per.values())
    if len(set(vals)) > 1:
        print(f'\n{key[0].replace("net.minecraft.","")}.{key[1]}')
        last = None
        for v in VERSIONS:
            cur = per.get(v)
            if cur != last:
                print(f'   {v:>8}: ' + ('\n             '.join(cur) if cur else '(absent)'))
                last = cur
