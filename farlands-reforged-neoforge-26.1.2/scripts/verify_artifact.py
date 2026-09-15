import sys
import zipfile
from pathlib import Path

jar = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('build/libs/farlandsreforged-0.3.1+mc26.1.2-neoforge.jar')
mc_artifact = Path('build/moddev/artifacts/minecraft-patched-26.1.2.76.jar')
required_entries = {
    'META-INF/neoforge.mods.toml',
    'farlandsreforged.mixins.json',
    'com/shigeo/farlandsreforged/FarlandsReforged.class',
    'com/shigeo/farlandsreforged/FarlandsConfig.class',
    'com/shigeo/farlandsreforged/FarlandsCommands.class',
    'com/shigeo/farlandsreforged/FarlandsEvents.class',
    'com/shigeo/farlandsreforged/FarlandsRegion.class',
    'com/shigeo/farlandsreforged/mixin/BlendedNoiseMixin.class',
    'com/shigeo/farlandsreforged/mixin/ImprovedNoiseMixin.class',
    'com/shigeo/farlandsreforged/mixin/RangeChoiceMixin.class',
    'com/shigeo/farlandsreforged/mixin/SurfaceRulesContextMixin.class',
    'com/shigeo/farlandsreforged/mixin/NoiseBasedAquiferMixin.class',
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
    'version = "0.3.1+mc26.1.2-neoforge"',
    'versionRange = "[26.1.2,26.2)"',
    'Inspired by AdyTech99',
    'config = "farlandsreforged.mixins.json"',
    'BlendedNoiseMixin',
    'RangeChoiceMixin',
    'NoiseBasedAquiferMixin',
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

print(f'OK: {jar} contains v0.3 NeoForge metadata, config/command/event classes, advancement, lang, and every terrain mixin target still exists.')
