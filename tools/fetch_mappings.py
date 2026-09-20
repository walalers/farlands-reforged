#!/usr/bin/env python3
"""Download the mapping files the other tools in this folder read.

    python tools/fetch_mappings.py 1.21 1.21.1 1.21.2 ... 1.21.11

Writes Mojang's official mappings to tools/mappings/<version>.txt and Fabric's intermediary to
tools/intermediary/<version>.tiny. Both are cached, so re-running is cheap. Minecraft 26.x ships
deobfuscated and has no client_mappings; those versions are skipped with a note.
"""
import json, os, sys, urllib.request, zipfile, io

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = 'https://launchermeta.mojang.com/mc/game/version_manifest_v2.json'
INTERMEDIARY = 'https://maven.fabricmc.net/net/fabricmc/intermediary/{v}/intermediary-{v}-v2.jar'

versions = sys.argv[1:]
if not versions:
    raise SystemExit(__doc__)

os.makedirs(os.path.join(HERE, 'mappings'), exist_ok=True)
os.makedirs(os.path.join(HERE, 'intermediary'), exist_ok=True)

manifest = json.load(urllib.request.urlopen(MANIFEST))
index = {v['id']: v['url'] for v in manifest['versions']}

for v in versions:
    if v not in index:
        print(f'{v}: not in the version manifest'); continue

    out = os.path.join(HERE, 'mappings', f'{v}.txt')
    if os.path.exists(out):
        print(f'{v}: mappings cached')
    else:
        meta = json.load(urllib.request.urlopen(index[v]))
        if 'client_mappings' not in meta['downloads']:
            print(f'{v}: no client_mappings (this version ships deobfuscated)')
        else:
            urllib.request.urlretrieve(meta['downloads']['client_mappings']['url'], out)
            print(f'{v}: mappings {os.path.getsize(out) // 1024} KiB')

    out = os.path.join(HERE, 'intermediary', f'{v}.tiny')
    if os.path.exists(out):
        print(f'{v}: intermediary cached')
        continue
    try:
        blob = urllib.request.urlopen(INTERMEDIARY.format(v=v)).read()
    except Exception as exc:
        print(f'{v}: no intermediary ({exc})'); continue
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        with open(out, 'wb') as fh:
            fh.write(zf.read('mappings/mappings.tiny'))
    print(f'{v}: intermediary {os.path.getsize(out) // 1024} KiB')
