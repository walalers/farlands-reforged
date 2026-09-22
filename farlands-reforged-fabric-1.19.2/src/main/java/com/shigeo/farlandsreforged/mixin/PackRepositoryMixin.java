package com.shigeo.farlandsreforged.mixin;

import com.shigeo.farlandsreforged.FarlandsModPack;
import net.minecraft.server.packs.repository.Pack;
import net.minecraft.server.packs.repository.PackRepository;
import net.minecraft.server.packs.repository.RepositorySource;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Mutable;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.LinkedHashSet;
import java.util.Set;

/**
 * Adds this mod's built-in pack to every {@link PackRepository}, which is what makes the
 * "...where am I?" advancement exist on Fabric at all. See {@link FarlandsModPack}.
 *
 * <p>The repository keeps its sources in a set built inside the constructor, so the field is replaced
 * on the way out rather than added to - the original may be immutable.
 *
 * <p>1.19 - 1.19.2 have two constructors. The {@code PackType} one only builds a pack constructor and
 * delegates to this one, so hooking this one covers both.
 */
@Mixin(PackRepository.class)
public abstract class PackRepositoryMixin {
    @Shadow @Final @Mutable private Set<RepositorySource> sources;

    @Inject(method = "<init>(Lnet/minecraft/server/packs/repository/Pack$PackConstructor;[Lnet/minecraft/server/packs/repository/RepositorySource;)V",
            at = @At("RETURN"))
    private void farlandsreforged$addBuiltInPack(Pack.PackConstructor constructor, RepositorySource[] sources, CallbackInfo ci) {
        Set<RepositorySource> merged = new LinkedHashSet<>(this.sources);
        merged.add(FarlandsModPack.SOURCE);
        this.sources = merged;
    }
}
