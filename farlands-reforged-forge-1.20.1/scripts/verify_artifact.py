"""Sanity-check a built Farlands Reforged Forge jar.

Beyond the usual metadata checks this guards the things a successful build happily gets wrong:

  * Forge 1.20 - 1.20.4 runs on **SRG** names - the opposite of 1.20.6 and later. Its installer renames
    Minecraft with MERGED_MAPPINGS (obfuscated -> SRG). So the refmap must be there with SRG targets for
    every injecting mixin, and reobfJar must have rewritten the mod's own calls and @Shadow fields.
  * The mod class must have a **no-arg** constructor. Forge 51 calls getDeclaredConstructor() with no
    arguments, so an FMLJavaModLoadingContext constructor is never found and loading fails.
  * pack.mcmeta must use the old **pack_format** schema. The 26.x/1.21.11 min_format/max_format keys do
    not parse before 1.21.11, and the failure is silent: the mod's data pack is dropped, the advancement
    never registers, and the server still boots and generates terrain perfectly.

    python scripts/verify_artifact.py [jar]
"""
import json
import re
import subprocess
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
    'pack.mcmeta',
    'data/farlandsreforged/advancements/farlands/where_am_i.json',
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
    if refmap_name not in names:
        raise SystemExit(f'{refmap_name} is missing; Forge 1.20.x runs on SRG and the mixins would find '
                         'nothing to inject into.')
    refmap = json.loads(zf.read(refmap_name))
    mods_toml = zf.read('META-INF/mods.toml').decode('utf-8')
    mixins = zf.read(f"{props['mod_id']}.mixins.json").decode('utf-8')
    pack_mcmeta = json.loads(zf.read('pack.mcmeta').decode('utf-8'))
    mod_class = zf.read('com/shigeo/farlandsreforged/FarlandsReforged.class')
    classes = {n: zf.read(n) for n in names if n.endswith('.class')}
    advancement = zf.read('data/farlandsreforged/advancements/farlands/where_am_i.json').decode('utf-8')
    lang = zf.read('assets/farlandsreforged/lang/en_us.json').decode('utf-8')

expected = [
    f'modId="{props["mod_id"]}"',
    f'version="{mod_version}"',
    f'versionRange="{props["minecraft_version_range"]}"',
    # Not JAVA_{java_version}: every Forge 1.20.6 build bundles Mixin 0.8.5, whose CompatibilityLevel
    # stops at JAVA_17, and a JAVA_21 config kills the server during bootstrap.
    '"compatibilityLevel": "JAVA_17"',
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

# 1. Every injecting mixin needs refmap entries, and they must be SRG (m_123456_ / f_123456_) rather than
#    the official names the sources are written in. CommandsMixin has none: it injects into <init>,
#    which is never remapped, and its other Minecraft reference is a @Shadow field (check 2).
srg = re.compile(r'\b[mf]_\d+_\b')
if json.loads(mixins).get('refmap') != refmap_name:
    raise SystemExit(f'The mixin config does not point at {refmap_name}, so Mixin never loads it.')
mappings = refmap.get('mappings', {})
for name in MIXINS:
    if name == 'CommandsMixin':
        continue
    entries = mappings.get(f'com/shigeo/farlandsreforged/mixin/{name}')
    if not entries:
        raise SystemExit(f'No refmap entries for {name}; it would find nothing at runtime.')
    if not any(srg.search(str(v)) for v in entries.values()):
        raise SystemExit(f'Refmap entries for {name} are not SRG names; remapping did not happen.')

# 2. reobfJar rewrites @Shadow fields and the mod's own calls in place. If it silently stopped running,
#    CommandsMixin would shadow "dispatcher", find nothing on an SRG server, and /farlands would never
#    register - with the jar still building fine.
commands_mixin = classes['com/shigeo/farlandsreforged/mixin/CommandsMixin.class']
if b'dispatcher' in commands_mixin or not srg.search(commands_mixin.decode('latin-1')):
    raise SystemExit('CommandsMixin still shadows "dispatcher" by its official name; reobfJar did not run.')

# 3. The mod class must not ask for FMLJavaModLoadingContext: Forge 51 only ever looks for a no-arg
#    constructor, and Forge 52+ falls back to one, so no-arg is the only signature that works range-wide.
if b'FMLJavaModLoadingContext' in mod_class:
    raise SystemExit('FarlandsReforged takes FMLJavaModLoadingContext; Forge 51 looks only for a no-arg '
                     'constructor and mod loading would fail with NoSuchMethodException.')

# 4. pack.mcmeta must use the pre-1.21.11 schema, or the data pack is silently dropped and the
#    advancement never registers - with no error anywhere except one line in the server log.
pack = pack_mcmeta.get('pack', {})
if 'min_format' in pack or 'max_format' in pack:
    raise SystemExit('pack.mcmeta uses the 1.21.11+ min_format/max_format schema; before 1.21.11 it fails '
                     'to parse and the mod data pack is dropped.')
if not isinstance(pack.get('pack_format'), int):
    raise SystemExit('pack.mcmeta has no integer pack_format.')

# 5. Mixin 0.8.5, which every Forge 1.20.6 build bundles, rejects a static @Redirect handler inside an
#    instance method; the server dies during bootstrap. The shared sources declare them static.
for mixin in ('BlendedNoiseMixin', 'ImprovedNoiseMixin'):
    listing = subprocess.run(['javap', '-p', '-cp', str(jar), f'com.shigeo.farlandsreforged.mixin.{mixin}'],
                             capture_output=True, text=True, check=True).stdout
    if re.search(r'\bstatic\b[^\n]*farlandsreforged\$', listing):
        raise SystemExit(f'{mixin} has a static handler; Mixin 0.8.5 on Forge 1.20.6 rejects it.')

print(f'OK: {jar.name} targets Minecraft {props["minecraft_version"]} ({props["minecraft_version_range"]}) '
      f'on Forge {props["forge_version"]}, Java {props["java_version"]}, all {len(MIXINS)} mixins present, '
      f'SRG refmap and reobfuscated calls, no-arg mod constructor, pack_format '
      f'{pack_mcmeta["pack"]["pack_format"]}.')
