package com.shigeo.farlandsreforged;

import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.network.chat.Component;
import net.minecraft.server.packs.PathPackResources;
import net.minecraft.server.packs.repository.Pack;
import net.minecraft.server.packs.repository.PackCompatibility;
import net.minecraft.server.packs.repository.PackSource;
import net.minecraft.server.packs.repository.RepositorySource;
import net.minecraft.world.flag.FeatureFlagSet;

import java.nio.file.Path;
import java.util.List;

/**
 * Exposes this mod's own {@code data/} and {@code assets/} as a built-in pack.
 *
 * <p>Fabric Loader, unlike Forge and NeoForge, does not turn a mod's resource directories into packs -
 * that is Fabric API's resource loader, and this mod deliberately does not depend on Fabric API. Without
 * this the {@code where_am_i} advancement JSON is dead weight in the jar: the server never reads it,
 * {@code server.getAdvancements().get(...)} returns null, and {@link FarlandsEvents} silently does
 * nothing. No error is ever logged, which is why only a {@code /datapack list} shows the problem.
 *
 * <p>This is the 1.20.2 - 1.20.4 shape of the pack API: {@code Pack.create} with a {@code Pack.Info},
 * where 1.20.5 and later take a {@code PackLocationInfo} and {@code PackSelectionConfig}. Two deliberate
 * choices carry over unchanged from the newer projects:
 *
 * <ul>
 *   <li>The pack is built from {@code Pack.create} with hand-written metadata rather than
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

        Pack.Info info = new Pack.Info(
                Component.literal("Farlands Reforged resources"),
                PackCompatibility.COMPATIBLE,
                FeatureFlagSet.of(),
                List.of());

        // required + fixed: this is mod content, not something a player should be able to turn off.
        consumer.accept(Pack.create(
                FarlandsReforged.MOD_ID,
                Component.literal("Farlands Reforged"),
                true,
                new PathPackResources.PathResourcesSupplier(root, true),
                info,
                Pack.Position.TOP,
                true,
                PackSource.BUILT_IN));
    };
}
