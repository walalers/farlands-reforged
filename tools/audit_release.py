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
import subprocess
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

LANG = "assets/farlandsreforged/lang/en_us.json"
# (resource, data) pack formats of each version before 1.20, from its version.json. Forge builds for
# them write both into pack.mcmeta.
FORGE_OLD_PACK_FORMATS = {"1.18.2": (8, 9), "1.19": (9, 10), "1.19.1": (9, 10), "1.19.2": (9, 10),
                          "1.19.3": (12, 10), "1.19.4": (13, 12)}


def mc_tuple(mc):
    return tuple(int(part) for part in mc.split("."))


def advancement_path(mc):
    # Minecraft 1.21 renamed the plural data-pack folders (advancements/ -> advancement/). A jar with
    # the wrong one boots fine and the advancement just never registers.
    folder = "advancements" if mc_tuple(mc) < (1, 21) else "advancement"
    return f"data/farlandsreforged/{folder}/farlands/where_am_i.json"


def loader_of(name):
    for loader in ("fabric", "neoforge", "forge"):
        if name.endswith(f"-{loader}.jar"):
            return loader
    return None


def neoforge_toml(zf):
    """NeoForge reads META-INF/neoforge.mods.toml from 20.5 on, and META-INF/mods.toml before."""
    names = zf.namelist()
    return next((m for m in ("META-INF/neoforge.mods.toml", "META-INF/mods.toml") if m in names), None)


def declared_version(zf, loader):
    if loader == "fabric":
        return json.loads(zf.read("fabric.mod.json"))["version"]
    meta = neoforge_toml(zf) if loader == "neoforge" else "META-INF/mods.toml"
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

        # 0. No jar entry should have a space in its path. This catches a specific and nasty failure:
        #    the repository lives under ~/Desktop, which iCloud Drive syncs, and iCloud resolves a
        #    conflict by leaving a duplicate directory beside the original - "farlandsreforged 2",
        #    "lang 5". Gradle then sweeps those into the jar, which silently doubles in size and gains
        #    a package whose name is not even a legal Java identifier. It is invisible to every other
        #    check here, because the real classes are all still present and correct.
        junk = sorted(n for n in names if " " in n)
        if junk:
            problems.append(f"{len(junk)} entries with a space in the path, e.g. {junk[0]!r} "
                            f"- stale duplicates swept in from a dirty build directory")

        # 1. The version inside must match the filename, or build/libs handed us a stale jar.
        want = f"{version}+mc{expected_mc}-{loader}"
        got = declared_version(zf, loader)
        if got != want:
            problems.append(f"declares version {got!r}, filename says {want!r}")

        # 1b. The FancyModLoader major, and the metadata file name, follow the NeoForge line: 20.2-20.4
        #     ship FML 1-2 and read mods.toml, 20.5-20.6 ship FML 3, 21.x and later FML 4+ - and the
        #     latter two read neoforge.mods.toml. A loaderVersion above what the line ships is refused
        #     before any of the mod runs; a file under the wrong name is not read at all.
        if loader == "neoforge" and mc_tuple(expected_mc) < (1, 21):
            old_line = mc_tuple(expected_mc) < (1, 20, 5)
            want_file = "META-INF/mods.toml" if old_line else "META-INF/neoforge.mods.toml"
            want_fml = "[1,)" if old_line else "[3,)"
            if want_file not in names:
                problems.append(f"no {want_file}, which is what NeoForge for {expected_mc} reads")
            else:
                toml = zf.read(want_file).decode("utf-8")
                match = re.search(r'^\s*loaderVersion\s*=\s*"([^"]+)"', toml, re.M)
                if not match or match.group(1) != want_fml:
                    problems.append(f"loaderVersion {match and match.group(1)!r}; NeoForge for "
                                    f"{expected_mc} needs {want_fml}")

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
            # Every Forge 1.20.6 build bundles Mixin 0.8.5, which knows no level past JAVA_17 and
            # kills the server during bootstrap on anything higher. (Forge 1.21 had the same Mixin
            # before 51.0.23, which is why that jar declares [51.0.23,).)
            level = json.loads(zf.read(config[0])).get("compatibilityLevel")
            if loader == "forge" and mc_tuple(expected_mc) < (1, 21) and level != "JAVA_17":
                problems.append(f"compatibilityLevel {level}; Forge before 1.21 has Mixin 0.8.5, "
                                "which stops at JAVA_17")
            # The same Mixin 0.8.5 (NeoForge 20.x bundles it too) rejects a static handler inside an
            # instance method, and both @Redirect targets are instance methods.
            if loader != "fabric" and mc_tuple(expected_mc) < (1, 21):
                for mixin in ("BlendedNoiseMixin", "ImprovedNoiseMixin"):
                    listing = subprocess.run(
                        ["javap", "-p", "-cp", str(path), f"com.shigeo.farlandsreforged.mixin.{mixin}"],
                        capture_output=True, text=True).stdout
                    if re.search(r"\bstatic\b[^\n]*farlandsreforged\$", listing):
                        problems.append(f"{mixin} has a static handler, which Mixin 0.8.5 rejects")
            # Forge before 1.20.6 runs on SRG, so the refmap is what points each injection at its SRG
            # target; from 1.20.6 it runs on Mojang's names and a refmap means the jar was wrongly
            # reobfuscated. A build-cache hit once dropped the refmap without any error.
            if loader == "forge":
                refmap_name = json.loads(zf.read(config[0])).get("refmap")
                if mc_tuple(expected_mc) < (1, 20, 6):
                    if not refmap_name or refmap_name not in names:
                        problems.append(f"no refmap ({refmap_name!r}); Forge {expected_mc} runs on SRG")
                    else:
                        mappings = json.loads(zf.read(refmap_name)).get("mappings", {})
                        for mixin in listed:
                            entries = mappings.get(f"{CLASS_ROOT}/mixin/{mixin}", {})
                            if mixin != "CommandsMixin" and not re.search(r"\b[mf]_\d+_\b", str(entries)):
                                problems.append(f"{mixin} has no SRG refmap entries")
                elif refmap_name or any(n.endswith("refmap.json") for n in names):
                    problems.append(f"refmap present, but Forge {expected_mc} runs on Mojang's names")
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
        if advancement_path(expected_mc) not in names:
            problems.append(f"no {advancement_path(expected_mc)}")
        else:
            # Item stacks in JSON became {"id": ...} in 1.20.5; before that they are {"item": ...}. The
            # wrong key fails to parse and the advancement is dropped with one line in the server log.
            icon = json.loads(zf.read(advancement_path(expected_mc)))["display"]["icon"]
            key = "item" if mc_tuple(expected_mc) < (1, 20, 5) else "id"
            if key not in icon:
                problems.append(f"advancement icon {icon}; Minecraft {expected_mc} needs {key!r}")

        # 4b. Minecraft before 1.20.5 runs on Java 17, so no class may be newer than Java 17 (major 61).
        if mc_tuple(expected_mc) < (1, 20, 5):
            newer = sorted(n for n in names if n.endswith(".class")
                           and int.from_bytes(zf.read(n)[6:8], "big") > 61)
            if newer:
                problems.append(f"{len(newer)} classes newer than Java 17, e.g. {newer[0]}")
        if LANG not in names:
            problems.append("no en_us.json lang file")

        # 5. Forge reads a mod's data pack only if pack.mcmeta parses, and says nothing when it does
        #    not. The schema changed at 1.21.11, so check the right one is used.
        if loader == "forge":
            if "pack.mcmeta" not in names:
                problems.append("Forge jar has no pack.mcmeta - its data pack is silently dropped")
            else:
                meta = json.loads(zf.read("pack.mcmeta"))["pack"]
                # Before 1.20 the format changed inside the family, so each build carries its own
                # version's numbers, in vanilla's key and in Forge's forge:*_pack_format keys.
                if expected_mc in FORGE_OLD_PACK_FORMATS:
                    resource, data = FORGE_OLD_PACK_FORMATS[expected_mc]
                    got = (meta.get("pack_format"), meta.get("forge:resource_pack_format"),
                           meta.get("forge:data_pack_format"))
                    if got != (data, resource, data):
                        problems.append(f"pack.mcmeta formats {got}; Minecraft {expected_mc} is "
                                        f"resource {resource} / data {data}")
                # supported_formats exists from 1.20.2 (pack format 18) until 1.21.11 replaced it.
                old_family = mc_tuple(expected_mc) < (1, 21, 11)
                if (1, 20, 2) <= mc_tuple(expected_mc) and old_family and "supported_formats" not in meta:
                    problems.append("pack.mcmeta lacks supported_formats, which 1.20.2-1.21.10 needs")
                if not old_family and not ({"min_format", "max_format"} & set(meta)):
                    problems.append("pack.mcmeta lacks min_format/max_format")
        elif loader == "neoforge" and mc_tuple(expected_mc) < (1, 20, 5):
            # NeoForge 20.2 and 20.3 (and early 20.4) make a mod's resources into a pack only if the
            # jar has pack.mcmeta; without it they log "Missing metadata in pack" and drop it, and the
            # server otherwise runs perfectly. Later builds merge every mod into one mod_data pack.
            if "pack.mcmeta" not in names:
                problems.append("NeoForge jar has no pack.mcmeta - 20.2/20.3 silently drop its data pack")
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
