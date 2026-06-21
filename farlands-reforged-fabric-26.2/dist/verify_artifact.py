import sys
import zipfile
from pathlib import Path

jar = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('build/libs/farlandsreforged-0.2.0+mc26.2-fabric.jar')
required_entries = {
    'fabric.mod.json',
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
    fabric = zf.read('fabric.mod.json').decode('utf-8')
    mixins = zf.read('farlandsreforged.mixins.json').decode('utf-8')
    advancement = zf.read('data/farlandsreforged/advancement/farlands/where_am_i.json').decode('utf-8')
    lang = zf.read('assets/farlandsreforged/lang/en_us.json').decode('utf-8')
expected = [
    '"id": "farlandsreforged"',
    '"version": "0.2.0+mc26.2-fabric"',
    '"minecraft": ">=26.2 <26.3"',
    '"fabricloader": ">=0.19.0"',
    'PerlinNoiseMixin',
    'JAVA_25',
    '"trigger": "minecraft:impossible"',
    '"...where am I?"',
    'Inspired by AdyTech99',
]
combined = '\n'.join([fabric, mixins, advancement, lang])
miss = [e for e in expected if e not in combined]
if miss:
    raise SystemExit('Missing expected metadata/data text: ' + ', '.join(miss))
if '${' in combined:
    raise SystemExit('Unexpanded placeholder found in jar metadata/resources')
print(f'OK: {jar} contains Fabric 26.2 metadata, config/command/event classes, advancement, lang, and mixin config.')
