"""Sanity-check a built Farlands Reforged NeoForge jar.

Unlike the 26.x projects this one is built for a whole family of Minecraft versions, so the expected
metadata is read from gradle.properties instead of being hardcoded.

    python scripts/verify_artifact.py [jar]
"""
import sys
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parent.parent
props = {}
for line in (root / 'gradle.properties').read_text().splitlines():
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        key, _, value = line.partition('=')
        props[key.strip()] = value.strip()

mod_version = props['mod_version']
jar = Path(sys.argv[1]) if len(sys.argv) > 1 else root / 'build' / 'libs' / f"{props['mod_id']}-{mod_version}.jar"
# ModDevGradle has named this jar differently over the years (minecraft-patched-<ver>.jar on the 26.x
# projects, neoforge-<ver>.jar here), so find it rather than spell it out.
mc_artifact = next((p for p in sorted((root / 'build' / 'moddev' / 'artifacts').glob('*.jar'))
                    if 'client-extra' not in p.name and 'sources' not in p.name),
                   root / 'build' / 'moddev' / 'artifacts' / 'missing.jar')

MIXINS = [
    'BlendedNoiseMixin',
    'ImprovedNoiseMixin',
    'RangeChoiceMixin',
    'SurfaceRulesContextMixin',
    'NoiseBasedAquiferMixin',
    'UnderwaterMagmaFeatureMixin',
    'NoodleCavesMixin',
]
required_entries = {
    'META-INF/neoforge.mods.toml',
    'farlandsreforged.mixins.json',
    'data/farlandsreforged/advancement/farlands/where_am_i.json',
    'assets/farlandsreforged/lang/en_us.json',
}
for name in ['FarlandsReforged', 'FarlandsConfig', 'FarlandsCommands', 'FarlandsEvents', 'FarlandsRegion']:
    required_entries.add(f'com/shigeo/farlandsreforged/{name}.class')
for name in MIXINS:
    required_entries.add(f'com/shigeo/farlandsreforged/mixin/{name}.class')
if not jar.exists():
    raise SystemExit(f'Artifact missing: {jar}')

with zipfile.ZipFile(jar) as zf:
    names = set(zf.namelist())
    missing = sorted(required_entries - names)
    if missing:
        raise SystemExit('Missing required jar entries: ' + ', '.join(missing))
    if 'pack.mcmeta' in names:
        raise SystemExit('Runtime jar should not include pack.mcmeta; this code/data-only mod does not need a resource pack.')
    mods_toml = zf.read('META-INF/neoforge.mods.toml').decode('utf-8')
    mixins = zf.read('farlandsreforged.mixins.json').decode('utf-8')
    advancement = zf.read('data/farlandsreforged/advancement/farlands/where_am_i.json').decode('utf-8')
    lang = zf.read('assets/farlandsreforged/lang/en_us.json').decode('utf-8')

expected_text = [
    f'modId = "{props["mod_id"]}"',
    f'version = "{mod_version}"',
    f'versionRange = "{props["minecraft_version_range"]}"',
    f'versionRange = "{props["neoforge_version_range"]}"',
    f'JAVA_{props["java_version"]}',
    'Inspired by AdyTech99',
    'config = "farlandsreforged.mixins.json"',
    '"trigger": "minecraft:impossible"',
    '"...where am I?"',
    'Farlands Reforged restores classic Far Lands-style terrain generation',
] + MIXINS
combined = mods_toml + '\n' + mixins + '\n' + advancement + '\n' + lang
missing_text = [t for t in expected_text if t not in combined]
if missing_text:
    raise SystemExit('Missing expected metadata/data text: ' + ', '.join(missing_text))

if mc_artifact.exists():
    # Every class the terrain mixins hook, with a member each one relies on.
    mixin_targets = {
        'net/minecraft/world/level/levelgen/synth/BlendedNoise.class': [b'wrap', b'compute'],
        'net/minecraft/world/level/levelgen/synth/ImprovedNoise.class': [b'floor', b'noise'],
        'net/minecraft/world/level/levelgen/DensityFunctions$RangeChoice.class': [b'whenInRange', b'fillArray'],
        'net/minecraft/world/level/levelgen/SurfaceRules$Context.class': [b'getMinSurfaceLevel', b'blockX'],
        'net/minecraft/world/level/levelgen/Aquifer$NoiseBasedAquifer.class': [b'computeSubstance', b'globalFluidPicker'],
    }
    with zipfile.ZipFile(mc_artifact) as zf:
        for cls_name, members in mixin_targets.items():
            try:
                cls = zf.read(cls_name)
            except KeyError:
                raise SystemExit(f'Minecraft no longer ships {cls_name}; mixin target needs remapping.')
            for member in members:
                if member not in cls:
                    raise SystemExit(f'{cls_name} no longer references {member.decode()}; mixin target needs remapping.')

print(f'OK: {jar.name} targets Minecraft {props["minecraft_version"]} ({props["minecraft_version_range"]}) '
      f'on NeoForge {props["neoforge_version"]}, Java {props["java_version"]}, all {len(MIXINS)} mixins, '
      f'advancement and lang present'
      + (', and every terrain mixin target still exists in the patched Minecraft jar.' if mc_artifact.exists()
         else '. (Build the project to also check the mixin targets against Minecraft.)'))
