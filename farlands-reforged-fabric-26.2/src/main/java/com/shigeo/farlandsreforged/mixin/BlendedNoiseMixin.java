package com.shigeo.farlandsreforged.mixin;

import com.shigeo.farlandsreforged.FarlandsConfig;
import net.minecraft.world.level.levelgen.synth.BlendedNoise;
import net.minecraft.world.level.levelgen.synth.PerlinNoise;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/**
 * The legacy 3D terrain noise ({@code old_blended_noise}) is the direct descendant of the Beta-era terrain
 * generator, and it is the only noise that broke down in the original Far Lands. Vanilla wraps its coordinates
 * into +-16,777,216 before sampling; skipping that wrap lets the sampler overflow exactly where it did in Beta
 * 1.7.3 (2^31 / 171.103 = 12,550,824 in noise space). Every other noise keeps its wrap, so terrain features
 * that did not exist back then (jaggedness, cave noise, aquifers...) do not glitch early or unevenly.
 */
@Mixin(BlendedNoise.class)
public abstract class BlendedNoiseMixin {
    @Redirect(
            method = "compute(Lnet/minecraft/world/level/levelgen/DensityFunction$FunctionContext;)D",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/levelgen/synth/PerlinNoise;wrap(D)D")
    )
    private static double farlandsreforged$keepFullPrecision(double coordinate) {
        return FarlandsConfig.terrainEnabled() ? coordinate : PerlinNoise.wrap(coordinate);
    }
}
