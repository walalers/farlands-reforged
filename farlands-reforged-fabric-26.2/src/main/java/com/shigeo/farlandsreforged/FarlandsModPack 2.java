package com.shigeo.farlandsreforged;

import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.network.chat.Component;
import net.minecraft.server.packs.PackLocationInfo;
import net.minecraft.server.packs.PackSelectionConfig;
import net.minecraft.server.packs.PathPackResources;
import net.minecraft.server.packs.repository.Pack;
import net.minecraft.server.packs.repository.PackCompatibility;
import net.minecraft.server.packs.repository.PackSource;
import net.minecraft.server.packs.repository.RepositorySource;
import net.minecraft.world.flag.FeatureFlagSet;

import java.nio.file.Path;
import java.util.List;
import java.util.Optional;

/**
 * Exposes this mod's own {@code data/} and {@code assets/} as a built-in pack.
 *
 * <p>Fabric Loader, unlike Forge and NeoForge, does not turn a mod's resource directories into packs -
 * that is Fabric API's resource loader, and this mod deliberately does not depend on Fabric API. Without
 * this the {@code where_am_i} advancement JSON is dead weight in the jar: the server never reads it,
 * {@code server.getAdvancements().get(...)} returns null, and {@link FarlandsEvents} silently does
 * nothing. No error is ever logged, which is why only a {@code /datapack list} shows the problem.
 *
 * <p>Two deliberate choices keep this one file working across every Minecraft version this mod targets:
 *
 * <ul>
 *   <li>The pack is built from {@link Pack}'s constructor with hand-written metadata rather than
 *       {@code Pack.readMetaAndCreate}, so the jar needs no {@code pack.mcmeta}. That matters across a
 *       version range: {@code pack_format} numbers change nearly every release and a stale one silently
 *       drops the pack instead of failing loudly.
 *   <li>Resources come from vanilla's own {@link PathPackResources.PathResourcesSupplier}, so the
 *       {@code Pack.ResourcesSupplier} interface staying still is vanilla's problem rather than ours -
 *       Minecraft 26.3 replaced its {@code openPrimary}/{@code openFull} pair with
 *       {@code openMetadata}/{@code openResources}, and this code did not have to care.
 * </ul>
 */
public final class FarlandsModPack {
    private FarlandsModPack() {
    }

    /** Added to every {@code PackRepository} by {@code PackRepositoryMixin}; serves both pack types. */
    public static final RepositorySource SOURCE = consumer -> {
        Path root = FabricLoader.getInstance()
                .getModContainer(FarlandsReforged.MOD_ID)
                .map(container -> container.getRootPaths().isEmpty() ? null : container.getRootPaths().get(0))
                .orElse(null);
        if (root == null) {
            return;
        }

        PackLocationInfo location = new PackLocationInfo(
                FarlandsReforged.MOD_ID,
                Component.literal("Farlands Reforged"),
                PackSource.BUILT_IN,
                Optional.empty());

        Pack.Metadata metadata = new Pack.Metadata(
                Component.literal("Farlands Reforged resources"),
                PackCompatibility.COMPATIBLE,
                FeatureFlagSet.of(),
                List.of());

        // required + fixed: this is mod content, not something a player should be able to turn off.
        consumer.accept(new Pack(location,
                new PathPackResources.PathResourcesSupplier(root),
                metadata,
                new PackSelectionConfig(true, Pack.Position.TOP, true)));
    };
}
