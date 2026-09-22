"""Sanity-check a built Farlands Reforged Forge jar.

Beyond the usual metadata checks this guards the three things that once made every jar in this range
unloadable, each of which a successful build happily produced anyway:

  * Forge 51-60 runs on Mojang's **official** names. An earlier version of this project reobfuscated the
    jar into SRG and shipped a refmap; the server then died on "@Shadow field f_208787_ was not located".
    So: no refmap, no SRG identifiers anywhere.
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
    if refmap_name in names:
        raise SystemExit(f'{refmap_name} is in the jar; Forge 51-60 runs on official names, so a refmap '
                         'means the jar was reobfuscated into SRG and will not load.')
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

# 1. Nothing in the jar may carry an SRG name. Two mechanisms used to put them there - the refmap for
#    injection points, and reobfJar rewriting @Shadow members in place - and both are gone now. A single
#    m_123456_ / f_123456_ anywhere means reobfuscation crept back in and the jar will not load.
srg = re.compile(rb'\b[mf]_\d+_\b')
reobfuscated = sorted(n for n, data in classes.items() if srg.search(data))
if reobfuscated:
    raise SystemExit('SRG names found in: ' + ', '.join(reobfuscated)
                     + ' -- the jar was reobfuscated, but Forge 51-60 runs on official names.')
if 'refmap' in json.loads(mixins):
    raise SystemExit('The mixin config declares a refmap; it must not, on official names.')

# 2. CommandsMixin shadows Commands.dispatcher. On official names that field keeps its real name; if it
#    were rewritten the mixin would attach to nothing and /farlands would never register.
if b'dispatcher' not in classes['com/shigeo/farlandsreforged/mixin/CommandsMixin.class']:
    raise SystemExit('CommandsMixin no longer shadows "dispatcher" under its official name.')

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
      f'no refmap and no SRG names, no-arg mod constructor, pack_format '
      f'{pack_mcmeta["pack"]["pack_format"]}.')
