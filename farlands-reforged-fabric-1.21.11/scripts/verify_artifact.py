"""Sanity-check a built Farlands Reforged Fabric jar.

Unlike the 26.x projects this one is built for a whole family of Minecraft versions, so the expected
metadata is read from gradle.properties (or from -P overrides passed here) instead of being hardcoded.

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

MIXINS = [
    'BlendedNoiseMixin',
    'ImprovedNoiseMixin',
    'RangeChoiceMixin',
    'SurfaceRulesContextMixin',
    'NoiseBasedAquiferMixin',
    'UnderwaterMagmaFeatureMixin',
    'NoodleCavesMixin',
    'CommandsMixin',
    'ServerPlayerMixin',
]
required_entries = {
    'fabric.mod.json',
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
    fabric = zf.read('fabric.mod.json').decode('utf-8')
    mixins = zf.read('farlandsreforged.mixins.json').decode('utf-8')
    advancement = zf.read('data/farlandsreforged/advancement/farlands/where_am_i.json').decode('utf-8')
    lang = zf.read('assets/farlandsreforged/lang/en_us.json').decode('utf-8')

expected = [
    f'"id": "{props["mod_id"]}"',
    f'"version": "{mod_version}"',
    f'"minecraft": "{props["minecraft_version_range"]}"',
    f'"java": ">={props["java_version"]}"',
    f'JAVA_{props["java_version"]}',
    '"trigger": "minecraft:impossible"',
    '"...where am I?"',
    'Inspired by AdyTech99',
] + MIXINS
combined = '\n'.join([fabric, mixins, advancement, lang])
miss = [e for e in expected if e not in combined]
if miss:
    raise SystemExit('Missing expected metadata/data text: ' + ', '.join(miss))
if '${' in combined:
    raise SystemExit('Unexpanded placeholder found in jar metadata/resources')
print(f'OK: {jar.name} targets Minecraft {props["minecraft_version"]} '
      f'({props["minecraft_version_range"]}), Java {props["java_version"]}, '
      f'all {len(MIXINS)} mixins, advancement and lang present.')
