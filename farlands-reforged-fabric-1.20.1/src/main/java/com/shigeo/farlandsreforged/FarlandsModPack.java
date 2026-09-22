package com.shigeo.farlandsreforged;

import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.SharedConstants;
import net.minecraft.network.chat.Component;
import net.minecraft.server.packs.PackType;
import net.minecraft.server.packs.PathPackResources;
import net.minecraft.server.packs.repository.Pack;
import net.minecraft.server.packs.repository.PackSource;
import net.minecraft.server.packs.repository.RepositorySource;
import net.minecraft.world.flag.FeatureFlagSet;

import java.nio.file.Path;

/**
 * Exposes this mod's own {@code data/} and {@code assets/} as a built-in pack.
 *
 * <p>Fabric Loader, unlike Forge and NeoForge, does not turn a mod's resource directories into packs -
 * that is Fabric API's resource loader, and this mod deliberately does not depend on Fabric API. Without
 * this the {@code where_am_i} advancement JSON is dead weight in the jar: the server never reads it,
 * {@code server.getAdvancements().get(...)} returns null, and {@link FarlandsEvents} silently does
 * nothing. No error is ever logged, which is why only a {@code /datapack list} shows the problem.
 *
 * <p>This is the 1.20 - 1.20.1 shape of the pack API: {@code Pack.create} takes a {@code PackType},
 * {@code Pack.Info} holds a raw format number, and there is no {@code PathResourcesSupplier} yet, so the
 * supplier is a lambda around vanilla's {@link PathPackResources}. As in every other project, the pack
 * is assembled in code rather than from a {@code pack.mcmeta}, so no hard-coded {@code pack_format}
 * can go stale and silently drop it.
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

        // Pack.Info carries a raw format number here, and compatibility is worked out from it and the
        // PackType passed to create. Using the running game's own data-pack format keeps it compatible
        // on every version this jar covers. The PackType only feeds that check: the resources below
        // serve assets/ and data/ alike, so the same pack works in the client's resource repository.
        PackType type = PackType.SERVER_DATA;
        Pack.Info info = new Pack.Info(
                Component.literal("Farlands Reforged resources"),
                SharedConstants.getCurrentVersion().getPackVersion(type),
                FeatureFlagSet.of());

        // required + fixed: this is mod content, not something a player should be able to turn off.
        consumer.accept(Pack.create(
                FarlandsReforged.MOD_ID,
                Component.literal("Farlands Reforged"),
                true,
                name -> new PathPackResources(name, root, true),
                info,
                type,
                Pack.Position.TOP,
                true,
                PackSource.BUILT_IN));
    };
}
