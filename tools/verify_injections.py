#!/usr/bin/env python3
"""Verify every Farlands Reforged mixin injection point against a *named* (Mojang-mapped) Minecraft jar.

The Java compiler never sees mixin targets, so a project can build fine and then fail at runtime with
"@Redirect target not found". This disassembles the real classes and checks each target method exists
and, for the two @Redirects, that the redirected INVOKE is actually inside it.

    python verify_injections.py <named-minecraft.jar>
"""
import re, subprocess, sys, zipfile, tempfile, os, shutil

JAR = sys.argv[1]
JAVAP = shutil.which('javap') or '/usr/bin/javap'

# class -> {'methods': [...], 'fields': [...], 'invokes': {method: [needle, ...]}}
CHECKS = {
    'net/minecraft/world/level/levelgen/synth/BlendedNoise': {
        'methods': ['double compute(net.minecraft.world.level.levelgen.DensityFunction$FunctionContext)'],
        'invokes': {'compute': ['synth/PerlinNoise.wrap:(D)D']},
    },
    'net/minecraft/world/level/levelgen/synth/ImprovedNoise': {
        'methods': ['double noise(double, double, double, double, double)'],
        'invokes': {'noise': ['util/Mth.floor:(D)I']},
    },
    'net/minecraft/world/level/levelgen/DensityFunctions$RangeChoice': {
        'methods': ['double compute(', 'void fillArray(double[],',
                    'input()', 'minInclusive()', 'maxExclusive()', 'whenInRange()', 'whenOutOfRange()'],
    },
    'net/minecraft/world/level/levelgen/DensityFunctions$Noise': {
        'methods': ['double compute('],
        'fields': ['DensityFunction$NoiseHolder noise'],
    },
    'net/minecraft/world/level/levelgen/SurfaceRules$Context': {
        'methods': ['int getMinSurfaceLevel()'],
        'fields': ['WorldGenerationContext context', 'int blockX', 'int blockZ'],
    },
    'net/minecraft/world/level/levelgen/Aquifer$NoiseBasedAquifer': {
        'methods': ['computeSubstance('],
        'fields': ['Aquifer$FluidPicker globalFluidPicker', 'boolean shouldScheduleFluidUpdate'],
    },
    'net/minecraft/world/level/levelgen/feature/UnderwaterMagmaFeature': {
        'methods': ['boolean place(net.minecraft.world.level.levelgen.feature.FeaturePlaceContext<'],
    },
    'net/minecraft/commands/Commands': {
        'methods': ['Commands(net.minecraft.commands.Commands$CommandSelection, net.minecraft.commands.CommandBuildContext)'],
        'fields': ['CommandDispatcher<net.minecraft.commands.CommandSourceStack> dispatcher'],
    },
    'net/minecraft/server/level/ServerPlayer': {
        'methods': ['void doTick()'],
    },
    'net/minecraft/world/level/levelgen/WorldGenerationContext': {
        'methods': ['int getMinGenY()'],
    },
}

# Minecraft 1.18.2 predates two shapes the checks above assume: DensityFunction.NoiseHolder arrived in 1.19
# (before it, DensityFunctions$Noise holds the noise key itself), and so did CommandBuildContext. The
# 1.18.2 projects are written against these instead. The version comes from Loom's cache directory name
# ("<version>-loom.mappings...").
_version = re.match(r'(\d+(?:\.\d+)*)', os.path.basename(os.path.dirname(os.path.abspath(JAR))))
if _version and tuple(int(p) for p in _version.group(1).split('.')) < (1, 19):
    CHECKS['net/minecraft/world/level/levelgen/DensityFunctions$Noise']['fields'] = ['net.minecraft.core.Holder<net.minecraft.world.level.levelgen.synth.NormalNoise$NoiseParameters> noiseData']
    CHECKS['net/minecraft/commands/Commands']['methods'] = ['Commands(net.minecraft.commands.Commands$CommandSelection)']

tmp = tempfile.mkdtemp()
with zipfile.ZipFile(JAR) as zf:
    names = zf.namelist()
    for cls in CHECKS:
        entry = cls + '.class'
        if entry not in names:
            print(f'FAIL  {cls}: class not in jar'); continue
        zf.extract(entry, tmp)

failures = 0
for cls, spec in CHECKS.items():
    path = os.path.join(tmp, cls + '.class')
    if not os.path.exists(path):
        failures += 1
        continue
    out = subprocess.run([JAVAP, '-p', '-c', path], capture_output=True, text=True).stdout
    # split into per-method chunks for the invoke checks
    for needle in spec.get('methods', []):
        ok = needle in out
        print(f"{'ok  ' if ok else 'FAIL'}  {cls.split('/')[-1]}#{needle}")
        failures += 0 if ok else 1
    for needle in spec.get('fields', []):
        ok = needle in out
        print(f"{'ok  ' if ok else 'FAIL'}  {cls.split('/')[-1]} field {needle}")
        failures += 0 if ok else 1
    for method, needles in spec.get('invokes', {}).items():
        # grab the bytecode of the named method only
        chunks = re.split(r'\n(?=  [\w<])', out)
        body = '\n'.join(c for c in chunks if re.search(rf'\b{re.escape(method)}\(', c.split('\n')[0]))
        for needle in needles:
            ok = needle.replace(':', ':') in body.replace('. ', '.')
            # javap prints e.g. "Method net/minecraft/util/Mth.floor:(D)I"
            ok = needle in body
            print(f"{'ok  ' if ok else 'FAIL'}  {cls.split('/')[-1]}#{method} invokes {needle}")
            failures += 0 if ok else 1

shutil.rmtree(tmp, ignore_errors=True)
print()
print('ALL INJECTION POINTS PRESENT' if failures == 0 else f'{failures} PROBLEM(S)')
sys.exit(1 if failures else 0)
