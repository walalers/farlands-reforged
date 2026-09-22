package com.shigeo.farlandsreforged;

import net.fabricmc.loader.api.FabricLoader;
import net.fabricmc.loader.api.ModContainer;
import net.fabricmc.loader.api.metadata.ModOrigin;
import net.minecraft.network.chat.TextComponent;
import net.minecraft.server.packs.FilePackResources;
import net.minecraft.server.packs.FolderPackResources;
import net.minecraft.server.packs.PackResources;
import net.minecraft.server.packs.metadata.MetadataSectionSerializer;
import net.minecraft.server.packs.repository.Pack;
import net.minecraft.server.packs.repository.PackCompatibility;
import net.minecraft.server.packs.repository.PackSource;
import net.minecraft.server.packs.repository.RepositorySource;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.function.Supplier;

/**
 * Exposes this mod's own {@code data/} and {@code assets/} as a built-in pack.
 *
 * <p>Fabric Loader, unlike Forge and NeoForge, does not turn a mod's resource directories into packs -
 * that is Fabric API's resource loader, and this mod deliberately does not depend on Fabric API. Without
 * this the {@code where_am_i} advancement JSON is dead weight in the jar: the server never reads it,
 * {@code getAdvancement(...)} returns null, and {@link FarlandsEvents} silently does nothing. No error is
 * ever logged, which is why only a {@code /datapack list} shows the problem.
 *
 * <p>This is the 1.18.2 - 1.19.2 shape of the pack API, the oldest this mod supports. There is no
 * {@code PathPackResources}: vanilla reads packs only from a {@link File}, a zip through
 * {@link FilePackResources} or a directory through {@link FolderPackResources}. So the pack points at
 * the jar Fabric loaded this mod from, not at the jar's internal root path. {@code Pack} is built from its
 * constructor with the compatibility given directly, so no {@code pack.mcmeta} is read, as in every other
 * project.
 */
public final class FarlandsModPack {
    private FarlandsModPack() {
    }

    /**
     * Added to every {@code PackRepository} by {@code PackRepositoryMixin}; serves both pack types. The
     * second argument, the repository's own pack constructor, reads a {@code pack.mcmeta} and is not used.
     */
    public static final RepositorySource SOURCE = (consumer, constructor) -> {
        File source = modSource();
        if (source == null) {
            return;
        }

        // The metadata is given in code below, so the pack has no pack.mcmeta - and on 1.18.2 - 1.19.2 both
        // readers throw rather than return null for a missing one. Every resource reload asks each pack
        // for its "filter" section, so without these overrides the server logs "Failed to get filter
        // section from pack" as an ERROR each time, although the pack loads fine.
        Supplier<PackResources> resources = source.isDirectory()
                ? () -> new FolderPackResources(source) {
                    @Override
                    public <T> T getMetadataSection(MetadataSectionSerializer<T> serializer) {
                        return null;
                    }
                }
                : () -> new FilePackResources(source) {
                    @Override
                    public <T> T getMetadataSection(MetadataSectionSerializer<T> serializer) {
                        return null;
                    }
                };

        // required + fixed: this is mod content, not something a player should be able to turn off.
        consumer.accept(new Pack(
                FarlandsReforged.MOD_ID,
                true,
                resources,
                new TextComponent("Farlands Reforged"),
                new TextComponent("Farlands Reforged resources"),
                PackCompatibility.COMPATIBLE,
                Pack.Position.TOP,
                true,
                PackSource.BUILT_IN));
    };

    /**
     * The jar (or, in a development run, the directory holding {@code data/}) this mod was loaded from.
     * Null for a jar nested inside another mod's jar, which has no file of its own to open.
     */
    private static File modSource() {
        return FabricLoader.getInstance()
                .getModContainer(FarlandsReforged.MOD_ID)
                .map(ModContainer::getOrigin)
                .filter(origin -> origin.getKind() == ModOrigin.Kind.PATH)
                .flatMap(origin -> origin.getPaths().stream()
                        .filter(path -> Files.isRegularFile(path) || Files.isDirectory(path.resolve("data")))
                        .findFirst())
                .map(Path::toFile)
                .orElse(null);
    }
}
