package com.shigeo.farlandsreforged.mixin;

import com.shigeo.farlandsreforged.FarlandsConfig;
import com.shigeo.farlandsreforged.FarlandsRegion;
import net.minecraft.core.BlockPos;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.chunk.ChunkGenerator;
import net.minecraft.world.level.levelgen.feature.UnderwaterMagmaFeature;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Vanilla scatters magma on the floor of flooded caves (44-52 attempts per chunk in most overworld biomes). The
 * Far Lands are flooded from bedrock to sea level, so nearly every attempt succeeds and each magma block grows a
 * bubble column up through ~100 blocks of water, queueing thousands of block ticks per chunk. Beta had no magma,
 * so the feature is skipped inside the Far Lands.
 */
@Mixin(value = UnderwaterMagmaFeature.class, remap = false)
public abstract class UnderwaterMagmaFeatureMixin {
    @Inject(method = "place", at = @At("HEAD"), cancellable = true)
    private void farlandsreforged$skipInFarlands(WorldGenLevel level, ChunkGenerator generator, RandomSource random, BlockPos origin, CallbackInfoReturnable<Boolean> cir) {
        if (FarlandsConfig.terrainEnabled() && FarlandsRegion.isInFarlands(origin.getX(), origin.getZ())) {
            cir.setReturnValue(false);
        }
    }
}
