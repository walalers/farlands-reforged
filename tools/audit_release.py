#!/usr/bin/env python3
"""Audit a directory of built jars before they are released.

Each project has its own `scripts/verify_artifact.py` that checks one jar in detail. This is the other
half: it looks at the whole release at once and checks the things that are only wrong *relative* to the
other jars - a filename that disagrees with the version inside, a Fabric jar that is missing the
data-pack fix, a Forge jar with no `pack.mcmeta`, a mixin listed in the config but absent from the jar.

Every rule here exists because the corresponding mistake has actually shipped:

  * The Fabric data-pack fix was missing from 9 of 12 jars in one release, and nothing failed loudly -
    the advancement simply never registered. Hence FABRIC_REQUIRED.
  * Forge silently drops a mod's data pack when `pack.mcmeta` is missing or uses the wrong schema, with
    no log line. Hence the Forge pack.mcmeta rule.
  * build/libs keeps jars from older releases, so a glob can pick up a stale one. Hence checking the
    declared version against the filename.

Usage:
    audit_release.py <dir-of-jars> --version 0.4.0
"""

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

CLASS_ROOT = "com/shigeo/farlandsreforged"

# The worldgen mechanisms every jar must carry, whatever the loader. Each entry is a set of
# alternatives, because Minecraft occasionally moves a mechanism between classes and the mod follows:
# 26.3 renamed `ImprovedNoise` to `GradientNoise` and split the sampler, so there the same job is done
# by two accessors. Listing the alternatives keeps the check honest without pinning it to one era's
# class names.
WORLDGEN_MIXINS = [
    ("BlendedNoiseMixin",),
    ("ImprovedNoiseMixin", "GradientNoiseAccessor"),  # Perlin coordinate precision
    ("RangeChoiceMixin",),
    ("SurfaceRulesContextMixin",),
    ("NoiseBasedAquiferMixin",),
    ("UnderwaterMagmaFeatureMixin",),
    ("NoodleCavesMixin",),
]
# Fabric has no loader events, so the command and advancement hooks are mixins too, and
# PackRepositoryMixin is what makes the mod's data pack exist at all on Fabric.
FABRIC_REQUIRED = ["CommandsMixin", "ServerPlayerMixin", "PackRepositoryMixin"]
FABRIC_CLASSES = ["FarlandsModPack"]

ADVANCEMENT = "data/farlandsreforged/advancement/farlands/where_am_i.json"
LANG = "assets/farlandsreforged/lang/en_us.json"


def loader_of(name):
    for loader in ("fabric", "neoforge", "forge"):
        if name.endswith(f"-{loader}.jar"):
            return loader
    return None


def declared_version(zf, loader):
    if loader == "fabric":
        return json.loads(zf.read("fabric.mod.json"))["version"]
    meta = "META-INF/neoforge.mods.toml" if loader == "neoforge" else "META-INF/mods.toml"
    text = zf.read(meta).decode("utf-8")
    match = re.search(r'^\s*version\s*=\s*"([^"]+)"', text, re.M)
    return match.group(1) if match else None


def audit(path, version):
    """Return a list of problems with one jar; empty means it is fine."""
    name = path.name
    problems = []

    loader = loader_of(name)
    if loader is None:
        return [f"cannot tell which loader {name} is for"]

    expected_mc = name[len(f"farlandsreforged-{version}+mc"):-len(f"-{loader}.jar")]

    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())

        # 1. The version inside must match the filename, or build/libs handed us a stale jar.
        want = f"{version}+mc{expected_mc}-{loader}"
        got = declared_version(zf, loader)
        if got != want:
            problems.append(f"declares version {got!r}, filename says {want!r}")

        # 2. Mixin config must list the right mixins, and each must be present as a class.
        config = [n for n in names if n.endswith("farlandsreforged.mixins.json")]
        if not config:
            problems.append("no farlandsreforged.mixins.json")
        else:
            listed = json.loads(zf.read(config[0]))["mixins"]
            required = WORLDGEN_MIXINS + [
                (m,) for m in (FABRIC_REQUIRED if loader == "fabric" else [])
            ]
            for alternatives in required:
                found = [m for m in alternatives if m in listed]
                if not found:
                    problems.append(f"mixins.json lists none of {' / '.join(alternatives)}")
                for mixin in found:
                    if f"{CLASS_ROOT}/mixin/{mixin}.class" not in names:
                        problems.append(f"{mixin} listed but not in the jar")
            for mixin in listed:
                if f"{CLASS_ROOT}/mixin/{mixin}.class" not in names:
                    problems.append(f"mixins.json lists {mixin}, which is not in the jar")
            # The pack fix is Fabric-only; on Forge and NeoForge the loader does this itself.
            if loader != "fabric" and "PackRepositoryMixin" in listed:
                problems.append("PackRepositoryMixin present on a non-Fabric jar")

        # 3. Fabric needs the pack plumbing classes; the other loaders must not have them.
        for cls in FABRIC_CLASSES:
            present = f"{CLASS_ROOT}/{cls}.class" in names
            if loader == "fabric" and not present:
                problems.append(f"missing {cls} - the advancement will silently never register")
            if loader != "fabric" and present:
                problems.append(f"{cls} present on a non-Fabric jar")

        # 4. The advertised content has to actually be in there.
        if ADVANCEMENT not in names:
            problems.append("no where_am_i advancement JSON")
        if LANG not in names:
            problems.append("no en_us.json lang file")

        # 5. Forge reads a mod's data pack only if pack.mcmeta parses, and says nothing when it does
        #    not. The schema changed at 1.21.11, so check the right one is used.
        if loader == "forge":
            if "pack.mcmeta" not in names:
                problems.append("Forge jar has no pack.mcmeta - its data pack is silently dropped")
            else:
                meta = json.loads(zf.read("pack.mcmeta"))["pack"]
                old_family = expected_mc.startswith("1.21") and expected_mc != "1.21.11"
                if old_family and "supported_formats" not in meta:
                    problems.append("pack.mcmeta lacks supported_formats, which 1.21-1.21.10 needs")
                if not old_family and not ({"min_format", "max_format"} & set(meta)):
                    problems.append("pack.mcmeta lacks min_format/max_format")
        elif "pack.mcmeta" in names:
            # Deliberate: pack_format numbers change nearly every release and a stale one silently
            # drops the pack, so Fabric builds the metadata in code instead.
            problems.append("unexpected pack.mcmeta (Fabric/NeoForge builds do not use one)")

    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--version", required=True)
    args = ap.parse_args()

    jars = sorted(Path(args.directory).glob("*.jar"))
    if not jars:
        sys.exit(f"no jars in {args.directory}")

    bad = 0
    for jar in jars:
        problems = audit(jar, args.version)
        if problems:
            bad += 1
            print(f"FAIL {jar.name}")
            for problem in problems:
                print(f"       {problem}")

    print(f"\n{len(jars) - bad}/{len(jars)} jars pass")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
