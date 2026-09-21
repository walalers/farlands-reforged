package com.shigeo.farlandsreforged.mixin;

import com.shigeo.farlandsreforged.FarlandsModPack;
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
 */
@Mixin(PackRepository.class)
public abstract class PackRepositoryMixin {
    @Shadow @Final @Mutable private Set<RepositorySource> sources;

    @Inject(method = "<init>", at = @At("RETURN"))
    private void farlandsreforged$addBuiltInPack(RepositorySource[] sources, CallbackInfo ci) {
        Set<RepositorySource> merged = new LinkedHashSet<>(this.sources);
        merged.add(FarlandsModPack.SOURCE);
        this.sources = merged;
    }
}
