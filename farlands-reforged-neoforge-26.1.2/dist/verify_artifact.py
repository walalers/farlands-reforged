import sys
import zipfile
from pathlib import Path

jar = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('build/libs/farlandsreforged-0.2.0+mc26.1.2-neoforge.jar')
mc_artifact = Path('build/moddev/artifacts/minecraft-patched-26.1.2.76.jar')
required_entries = {
    'META-INF/neoforge.mods.toml',
    'farlandsreforged.mixins.json',
    'com/shigeo/farlandsreforged/FarlandsReforged.class',
    'com/shigeo/farlandsreforged/FarlandsConfig.class',
    'com/shigeo/farlandsreforged/FarlandsCommands.class',
    'com/shigeo/farlandsreforged/FarlandsEvents.class',
    'com/shigeo/farlandsreforged/mixin/PerlinNoiseMixin.class',
    'data/farlandsreforged/advancement/farlands/where_am_i.json',
    'assets/farlandsreforged/lang/en_us.json',
}

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
    'modId = "farlandsreforged"',
    'version = "0.2.0+mc26.1.2-neoforge"',
    'versionRange = "[26.1.2,26.2)"',
    'Inspired by AdyTech99',
    'config = "farlandsreforged.mixins.json"',
    'PerlinNoiseMixin',
    'JAVA_25',
    '"trigger": "minecraft:impossible"',
    '"...where am I?"',
    'Farlands Reforged restores classic Far Lands-style terrain generation',
]
combined = mods_toml + '\n' + mixins + '\n' + advancement + '\n' + lang
missing_text = [t for t in expected_text if t not in combined]
if missing_text:
    raise SystemExit('Missing expected metadata/data text: ' + ', '.join(missing_text))

if mc_artifact.exists():
    with zipfile.ZipFile(mc_artifact) as zf:
        cls = zf.read('net/minecraft/world/level/levelgen/synth/PerlinNoise.class')
    if b'wrap' not in cls or b'(D)D' not in cls:
        raise SystemExit('Minecraft 26.1.2 PerlinNoise no longer appears to expose wrap(D)D; mixin target needs remapping.')

print(f'OK: {jar} contains v0.2 NeoForge metadata, config/command/event classes, advancement, lang, and targets PerlinNoise.wrap(D)D.')
