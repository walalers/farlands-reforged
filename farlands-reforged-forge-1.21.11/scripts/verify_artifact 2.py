"""Sanity-check a built Farlands Reforged Forge jar (1.21.11).

Forge 61 runs on Mojang's official names, not SRG - ForgeGradle 7 does no reobfuscation and emits no
refmap, which is why this project mirrors farlands-reforged-forge-26.2 rather than the SRG-based
farlands-reforged-forge-1.21. So the check here is the mirror image of that project's: assert that the
mod's calls into Minecraft and its @Shadow field are still spelled the way the sources spell them. An
SRG name appearing in this jar would mean the mixins are looking for members the runtime does not have.

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
required_entries = {
    'META-INF/mods.toml',
    f"{props['mod_id']}.mixins.json",
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

# ForgeGradle 7 leaves the jar in official names. Prove it, in both places a stray SRG name would show up:
# the compiled classes (which would mean a reobf step ran that should not have) and the mixin config.
srg = re.compile(r'\b(?:[mf]_\d+_|C_\d+_)\b')
with zipfile.ZipFile(jar) as zf:
    for name in sorted(n for n in zf.namelist() if n.endswith('.class')):
        body = zf.read(name).decode('latin-1')
        if srg.search(body):
            raise SystemExit(f'{name} contains SRG names; this project must stay on official names, '
                             'as Forge 61 does not run on SRG.')
    commands_mixin = zf.read('com/shigeo/farlandsreforged/mixin/CommandsMixin.class')
if b'dispatcher' not in commands_mixin:
    raise SystemExit('CommandsMixin no longer shadows "dispatcher" under its official name.')
if f"{props['mod_id']}.refmap.json" in names:
    raise SystemExit('A refmap was generated. Forge 61 runs on official names, so a refmap here means the '
                     'mixins were remapped to names the runtime does not use.')

print(f'OK: {jar.name} targets Minecraft {props["minecraft_version"]} ({props["minecraft_version_range"]}) '
      f'on Forge {props["forge_version"]}, Java {props["java_version"]}, all {len(MIXINS)} mixins present '
      f'and every class still in official names, with no refmap.')
