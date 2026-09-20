package com.shigeo.farlandsreforged.mixin;

import com.shigeo.farlandsreforged.FarlandsConfig;
import com.shigeo.farlandsreforged.FarlandsRegion;
import net.minecraft.util.Mth;
import net.minecraft.world.level.levelgen.synth.ImprovedNoise;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/**
 * Uses the Beta-era floor inside the Perlin sampler. For every ordinary coordinate it returns exactly what
 * {@code Mth.floor} returns; it only differs once a coordinate passes the integer limit on the negative axis,
 * where the classic code wrapped around instead of saturating. See {@link FarlandsRegion#classicFloor}.
 */
@Mixin(value = ImprovedNoise.class, remap = false)
public abstract class ImprovedNoiseMixin {
    @Redirect(
            method = "noise(DDDDD)D",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/util/Mth;floor(D)I")
    )
    private static int farlandsreforged$classicFloor(double value) {
        return FarlandsConfig.terrainEnabled() ? FarlandsRegion.classicFloor(value) : Mth.floor(value);
    }
}
