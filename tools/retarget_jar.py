#!/usr/bin/env python3
"""Rewrite a built jar's loader metadata so it targets a different Minecraft version.

Some Minecraft versions differ only in ways this mod never touches: every compiled class in the
26.1, 26.1.1, 26.1.2 and 26.2 jars is byte-identical, per loader. Building each of those separately
would download a whole Minecraft version to produce the same bytes, so the 26.1 and 26.1.1 jars are
made by copying the 26.1.2 build and rewriting the two lines of metadata that name a version.

That is only sound when the classes really are identical, so check before you trust it:

    unzip -p <jar> '*.class' | shasum

must match between the source jar and a real build of the target version. `tools/compare_jars.py`
does the same job across a whole family.

Usage:
    retarget_jar.py --fabric   src.jar out.jar --mod-version V --minecraft '>=26.1 <26.1.1'
    retarget_jar.py --neoforge src.jar out.jar --mod-version V --minecraft '[26.1,26.1.1)' \
        --loader '[26.1,26.1.1)'
"""

import argparse
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

FABRIC_META = "fabric.mod.json"
# NeoForge renamed its metadata file in 20.5; older builds read META-INF/mods.toml like Forge.
NEOFORGE_METAS = ("META-INF/neoforge.mods.toml", "META-INF/mods.toml")


def rewrite_fabric(text, mod_version, minecraft):
    data = json.loads(text)
    data["version"] = mod_version
    data["depends"]["minecraft"] = minecraft
    return json.dumps(data, indent=2) + "\n"


def rewrite_neoforge(text, mod_version, minecraft, loader):
    """Rewrite the mod version plus the neoforge and minecraft dependency ranges.

    The file is edited as text rather than parsed as TOML: it has two `versionRange` keys that are
    told apart only by which `[[dependencies.farlandsreforged]]` block they sit in, and a round-trip
    through a TOML library would reformat and reorder a file a human maintains.
    """
    out, current_dep = [], None
    seen = {"version": False, "neoforge": False, "minecraft": False}

    for line in text.splitlines(keepends=True):
        mod_id = re.match(r'\s*modId\s*=\s*"([^"]+)"', line)
        if mod_id:
            current_dep = mod_id.group(1)

        if not seen["version"] and re.match(r'\s*version\s*=\s*"', line):
            line = re.sub(r'(version\s*=\s*)"[^"]*"', rf'\1"{mod_version}"', line)
            seen["version"] = True
        elif re.match(r"\s*versionRange\s*=", line) and current_dep in ("neoforge", "minecraft"):
            new = loader if current_dep == "neoforge" else minecraft
            line = re.sub(r'(versionRange\s*=\s*)"[^"]*"', rf'\1"{new}"', line)
            seen[current_dep] = True

        out.append(line)

    missing = [k for k, v in seen.items() if not v]
    if missing:
        sys.exit(f"error: never found {', '.join(missing)} in the NeoForge mods.toml")
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    loader = ap.add_mutually_exclusive_group(required=True)
    loader.add_argument("--fabric", action="store_true")
    loader.add_argument("--neoforge", action="store_true")
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--mod-version", required=True)
    ap.add_argument("--minecraft", required=True, help="the minecraft dependency range")
    ap.add_argument("--loader", help="the neoforge dependency range (NeoForge only)")
    args = ap.parse_args()

    if args.neoforge and not args.loader:
        sys.exit("error: --neoforge needs --loader")

    src, out = Path(args.src), Path(args.out)
    with zipfile.ZipFile(src) as zf:
        wanted = (FABRIC_META,) if args.fabric else NEOFORGE_METAS
        member = next((m for m in wanted if m in zf.namelist()), None)
        if member is None:
            sys.exit(f"error: {src.name} has no {' or '.join(wanted)}")
        original = zf.read(member).decode("utf-8")

    if args.fabric:
        patched = rewrite_fabric(original, args.mod_version, args.minecraft)
    else:
        patched = rewrite_neoforge(original, args.mod_version, args.minecraft, args.loader)

    # Copy every other entry across untouched, preserving order and compression.
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = patched.encode("utf-8") if item.filename == member else zin.read(item.filename)
            info = zipfile.ZipInfo(item.filename, date_time=item.date_time)
            info.compress_type = item.compress_type
            info.external_attr = item.external_attr
            zout.writestr(info, data)
    shutil.move(tmp, out)
    print(f"{src.name} -> {out.name}  ({member} retargeted to {args.minecraft})")


if __name__ == "__main__":
    main()
