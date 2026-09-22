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
# Common to every era: the repository the mixin hooks, and the constants every era's code names.
COMMON = [
    (f"{REPO}.PackRepository", "sig", "PackRepository(net.minecraft.server.packs.repository.RepositorySource...)"),
    (f"{REPO}.PackRepository", "sig", "java.util.Set<net.minecraft.server.packs.repository.RepositorySource> sources"),
    (f"{REPO}.RepositorySource", "sig", "loadPacks(java.util.function.Consumer"),
    (f"{REPO}.Pack$Position", "sig", "TOP"),
    (f"{REPO}.PackSource", "sig", "BUILT_IN"),
]

# 1.18.2 - 1.19.2: the oldest shape. PackRepository takes a Pack.PackConstructor (its PackType constructor
# delegates to that one, which is the one the mixin hooks), loadPacks passes one too, and there is no
# PathPackResources - packs are read from a java.io.File, a zip or a directory. Pack is built from its
# constructor with the compatibility given directly.
CHECKS_1_19 = [
    (f"{REPO}.PackRepository", "sig", f"PackRepository({REPO}.Pack$PackConstructor, {REPO}.RepositorySource...)"),
    (f"{REPO}.PackRepository", "sig", f"PackRepository({PACKS}.PackType, {REPO}.RepositorySource...)"),
    (f"{REPO}.PackRepository", "sig", "java.util.Set<net.minecraft.server.packs.repository.RepositorySource> sources"),
    (f"{REPO}.RepositorySource", "sig", f"loadPacks(java.util.function.Consumer<{REPO}.Pack>, {REPO}.Pack$PackConstructor)"),
    (f"{REPO}.Pack", "sig", f"Pack(java.lang.String, boolean, java.util.function.Supplier<{PACKS}.PackResources>, net.minecraft.network.chat.Component, net.minecraft.network.chat.Component, {REPO}.PackCompatibility, {REPO}.Pack$Position, boolean, {REPO}.PackSource)"),
    (f"{REPO}.PackCompatibility", "sig", "COMPATIBLE"),
    (f"{REPO}.Pack$Position", "sig", "TOP"),
    (f"{REPO}.PackSource", "sig", "BUILT_IN"),
    (f"{PACKS}.FilePackResources", "sig", "FilePackResources(java.io.File)"),
    (f"{PACKS}.FolderPackResources", "sig", "FolderPackResources(java.io.File)"),
    (f"{PACKS}.AbstractPackResources", "impl", f"{PACKS}.PackResources"),
    # Overridden to return null: the pack has no pack.mcmeta, and these readers throw for a missing one.
    (f"{PACKS}.AbstractPackResources", "sig", f"public <T> T getMetadataSection({PACKS}.metadata.MetadataSectionSerializer<T>)"),
]

# 1.19.3 - 1.19.4: the 1.20 - 1.20.1 API, except that the pack format comes from the compile-time
# SharedConstants.DATA_PACK_FORMAT - getPackVersion takes com.mojang.bridge's PackType on 1.19.3.
CHECKS_1_19_3 = COMMON + [
    (f"{REPO}.Pack", "sig", f"Pack create(java.lang.String, net.minecraft.network.chat.Component, boolean, {REPO}.Pack$ResourcesSupplier, {REPO}.Pack$Info, {PACKS}.PackType, {REPO}.Pack$Position, boolean, {REPO}.PackSource)"),
    (f"{REPO}.Pack$Info", "sig", "Info(net.minecraft.network.chat.Component, int, net.minecraft.world.flag.FeatureFlagSet)"),
    (f"{REPO}.Pack$ResourcesSupplier", "sig", f"{PACKS}.PackResources open(java.lang.String)"),
    (f"{PACKS}.PathPackResources", "sig", "PathPackResources(java.lang.String, java.nio.file.Path, boolean)"),
    ("net.minecraft.SharedConstants", "sig", "public static final int DATA_PACK_FORMAT"),
    (f"{PACKS}.PackType", "sig", "SERVER_DATA"),
]

# 1.20 - 1.20.1: Pack.create takes a PackType, Pack.Info carries a raw format number, and there is no
# PathResourcesSupplier - the supplier is a single open(name) method.
CHECKS_1_20 = COMMON + [
    (f"{REPO}.Pack", "sig", f"Pack create(java.lang.String, net.minecraft.network.chat.Component, boolean, {REPO}.Pack$ResourcesSupplier, {REPO}.Pack$Info, {PACKS}.PackType, {REPO}.Pack$Position, boolean, {REPO}.PackSource)"),
    (f"{REPO}.Pack$Info", "sig", "Info(net.minecraft.network.chat.Component, int, net.minecraft.world.flag.FeatureFlagSet)"),
    (f"{REPO}.Pack$ResourcesSupplier", "sig", f"{PACKS}.PackResources open(java.lang.String)"),
    (f"{PACKS}.PathPackResources", "sig", "PathPackResources(java.lang.String, java.nio.file.Path, boolean)"),
    ("net.minecraft.SharedConstants", "sig", "net.minecraft.WorldVersion getCurrentVersion()"),
    ("net.minecraft.WorldVersion", "sig", f"int getPackVersion({PACKS}.PackType)"),
    (f"{PACKS}.PackType", "sig", "SERVER_DATA"),
]

# 1.20.2 - 1.20.4: no PackType, Pack.Info takes a PackCompatibility, and PathResourcesSupplier exists
# but still takes an isBuiltin flag.
CHECKS_1_20_2 = COMMON + [
    (f"{REPO}.Pack", "sig", f"Pack create(java.lang.String, net.minecraft.network.chat.Component, boolean, {REPO}.Pack$ResourcesSupplier, {REPO}.Pack$Info, {REPO}.Pack$Position, boolean, {REPO}.PackSource)"),
    (f"{REPO}.Pack$Info", "sig", f"Info(net.minecraft.network.chat.Component, {REPO}.PackCompatibility, net.minecraft.world.flag.FeatureFlagSet, java.util.List"),
    (f"{REPO}.PackCompatibility", "sig", "COMPATIBLE"),
    (f"{PACKS}.PathPackResources$PathResourcesSupplier", "sig", "PathResourcesSupplier(java.nio.file.Path, boolean)"),
    (f"{PACKS}.PathPackResources$PathResourcesSupplier", "impl", f"{REPO}.Pack$ResourcesSupplier"),
]

# 1.20.5 and later.
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


def checks_for(version):
    """The pack API changed shape twice within 1.19.x and twice more within 1.20.x; FarlandsModPack has a version for each."""
    parts = tuple(int(p) for p in re.findall(r"\d+", version)[:3])
    if parts < (1, 19, 3):
        return CHECKS_1_19
    if parts < (1, 20):
        return CHECKS_1_19_3
    if parts < (1, 20, 2):
        return CHECKS_1_20
    if parts < (1, 20, 5):
        return CHECKS_1_20_2
    return CHECKS


def main():
    jars = [Path(a) for a in sys.argv[1:]]
    if not jars:
        sys.exit(__doc__)

    worst = 0
    for jar in jars:
        version = version_of(jar)
        checks = checks_for(version)
        disassembled, problems = {}, []

        for cls, kind, want in checks:
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
            print(f"ok   {version}   all {len(checks)} pack API checks present")

    return worst


if __name__ == "__main__":
    sys.exit(main())
