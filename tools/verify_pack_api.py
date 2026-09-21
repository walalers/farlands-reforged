#!/usr/bin/env python3
"""Check that every type FarlandsModPack and PackRepositoryMixin touch exists, per Minecraft version.

`verify_injections.py` covers the seven worldgen mixins; it predates the Fabric data-pack fix and knows
nothing about it. This is the same idea applied to that fix: disassemble the real Minecraft classes and
confirm each constructor, field and method the pack code names is actually there.

It matters more here than it looks. The pack code is the one part of the mod that vanilla can break
quietly: Minecraft 26.3 replaced `Pack.ResourcesSupplier.openPrimary`/`openFull` with
`openMetadata`/`openResources`, and the only reason that did not break this mod is that the resources
come from vanilla's own `PathPackResources.PathResourcesSupplier`. A check that just compiled would not
have noticed either way.

Usage:
    verify_pack_api.py <mojang-mapped-minecraft.jar> [...]

The jars Loom leaves behind work directly:
    ~/.gradle/caches/fabric-loom/minecraftMaven/net/minecraft/minecraft-merged/<ver>-*/*.jar
"""

import re
import subprocess
import sys
from pathlib import Path

PACKS = "net.minecraft.server.packs"
REPO = f"{PACKS}.repository"

# (class, kind, what to find) - 'sig' is a substring match against a javap line.
CHECKS = [
    (f"{REPO}.PackRepository", "sig", "PackRepository(net.minecraft.server.packs.repository.RepositorySource...)"),
    (f"{REPO}.PackRepository", "sig", "java.util.Set<net.minecraft.server.packs.repository.RepositorySource> sources"),
    (f"{REPO}.RepositorySource", "sig", "loadPacks(java.util.function.Consumer"),
    (f"{REPO}.Pack", "sig", f"Pack({PACKS}.PackLocationInfo, {REPO}.Pack$ResourcesSupplier, {REPO}.Pack$Metadata, {PACKS}.PackSelectionConfig)"),
    (f"{REPO}.Pack$Metadata", "sig", f"Metadata(net.minecraft.network.chat.Component, {REPO}.PackCompatibility, net.minecraft.world.flag.FeatureFlagSet, java.util.List"),
    (f"{REPO}.Pack$Position", "sig", "TOP"),
    (f"{REPO}.PackCompatibility", "sig", "COMPATIBLE"),
    (f"{REPO}.PackSource", "sig", "BUILT_IN"),
    (f"{PACKS}.PackLocationInfo", "sig", f"PackLocationInfo(java.lang.String, net.minecraft.network.chat.Component, {REPO}.PackSource, java.util.Optional"),
    (f"{PACKS}.PackSelectionConfig", "sig", f"PackSelectionConfig(boolean, {REPO}.Pack$Position, boolean)"),
    (f"{PACKS}.PathPackResources$PathResourcesSupplier", "sig", "PathResourcesSupplier(java.nio.file.Path)"),
    # The supplier is handed to Pack's constructor, so it has to actually be a ResourcesSupplier.
    (f"{PACKS}.PathPackResources$PathResourcesSupplier", "impl", f"{REPO}.Pack$ResourcesSupplier"),
]


def javap(jar, cls):
    result = subprocess.run(
        ["javap", "-p", "-cp", str(jar), cls],
        capture_output=True, text=True,
    )
    return result.stdout if result.returncode == 0 else None


def version_of(jar):
    """The directory Loom uses is '<version>-loom.mappings...' or '<version>-null.unspecified...'."""
    match = re.match(r"(.+?)-(?:loom|null)\.", jar.parent.name)
    return match.group(1) if match else jar.parent.name


def main():
    jars = [Path(a) for a in sys.argv[1:]]
    if not jars:
        sys.exit(__doc__)

    worst = 0
    for jar in jars:
        version = version_of(jar)
        disassembled, problems = {}, []

        for cls, kind, want in CHECKS:
            if cls not in disassembled:
                disassembled[cls] = javap(jar, cls)
            out = disassembled[cls]
            if out is None:
                problems.append(f"class missing: {cls}")
            elif kind == "sig" and want not in out:
                problems.append(f"{cls.rsplit('.', 1)[-1]}: no {want}")
            elif kind == "impl" and want not in out.split("{", 1)[0]:
                problems.append(f"{cls.rsplit('.', 1)[-1]}: does not implement {want}")

        if problems:
            worst = 1
            print(f"FAIL {version}")
            for problem in problems:
                print(f"       {problem}")
        else:
            print(f"ok   {version}   all {len(CHECKS)} pack API checks present")

    return worst


if __name__ == "__main__":
    sys.exit(main())
