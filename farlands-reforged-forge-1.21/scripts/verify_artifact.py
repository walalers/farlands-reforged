"""Sanity-check a built Farlands Reforged Forge jar.

Beyond the usual metadata checks this verifies the thing that makes the Forge build different from every
other project here: Forge runs on SRG names across the whole 1.21 family, so the jar must carry a refmap
that maps each mixin target to its SRG name. Without it the mod loads and then silently fails to find a
single injection point.

    python scripts/verify_artifact.py [jar]
"""
import json
import re
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
refmap_name = f"{props['mod_id']}.refmap.json"
required_entries = {
    'META-INF/mods.toml',
    f"{props['mod_id']}.mixins.json",
    refmap_name,
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
    mods_toml = zf.read('META-INF/mods.toml').decode('utf-8')
    mixins = zf.read(f"{props['mod_id']}.mixins.json").decode('utf-8')
    refmap = json.loads(zf.read(refmap_name).decode('utf-8'))
    advancement = zf.read('data/farlandsreforged/advancement/farlands/where_am_i.json').decode('utf-8')
    lang = zf.read('assets/farlandsreforged/lang/en_us.json').decode('utf-8')

expected = [
    f'modId="{props["mod_id"]}"',
    f'version="{mod_version}"',
    f'versionRange="{props["minecraft_version_range"]}"',
    f'JAVA_{props["java_version"]}',
    '"trigger": "minecraft:impossible"',
    '"...where am I?"',
    'Inspired by AdyTech99',
] + MIXINS
combined = '\n'.join([mods_toml, mixins, advancement, lang])
miss = [e for e in expected if e not in combined]
if miss:
    raise SystemExit('Missing expected metadata/data text: ' + ', '.join(miss))
if '${' in combined:
    raise SystemExit('Unexpanded placeholder found in jar metadata/resources')

# The refmap is the whole point of this project. Every mixin that targets a Minecraft class must appear
# in it, and its entries must actually be SRG (m_123456_ / f_123456_) rather than the names we wrote.
mappings = refmap.get('mappings', {})
srg = re.compile(r'\b[mf]_\d+_\b')
described, unmapped = [], []
for name in MIXINS:
    key = f'com/shigeo/farlandsreforged/mixin/{name}'
    entries = mappings.get(key)
    if not entries:
        unmapped.append(name)
        continue
    if not any(srg.search(str(v)) for v in entries.values()):
        described.append(name)
if unmapped:
    raise SystemExit('No refmap entries for: ' + ', '.join(unmapped)
                     + ' -- these mixins would find nothing at runtime.')
if described:
    raise SystemExit('Refmap entries for ' + ', '.join(described)
                     + ' are not SRG names; remapping did not happen.')

print(f'OK: {jar.name} targets Minecraft {props["minecraft_version"]} ({props["minecraft_version_range"]}) '
      f'on Forge {props["forge_version"]}, Java {props["java_version"]}, all {len(MIXINS)} mixins present '
      f'and every one of them remapped to SRG in {refmap_name}.')
