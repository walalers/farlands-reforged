package com.shigeo.farlandsreforged.mixin;

import com.shigeo.farlandsreforged.FarlandsConfig;
import com.shigeo.farlandsreforged.FarlandsRegion;
import net.minecraft.world.level.levelgen.DensityFunction;
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
    // Not static, unlike the 1.21+ projects: every Forge 1.20.x build bundles Mixin 0.8.5, which rejects a
    // static handler inside an instance method ("'static' modifier of handler method does not match target").
    @Redirect(
            method = "compute(Lnet/minecraft/world/level/levelgen/DensityFunction$FunctionContext;)D",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/levelgen/synth/PerlinNoise;wrap(D)D")
    )
    private double farlandsreforged$keepFullPrecision(double coordinate) {
        return FarlandsConfig.terrainEnabled() ? coordinate : PerlinNoise.wrap(coordinate);
    }

    /**
     * Reads the legacy noise at the shifted column when the Far Lands are configured to start closer than the
     * classic threshold, so the overflow that makes them lands on the configured start. See
     * {@link FarlandsRegion#noiseX}; at the classic start it changes nothing.
     */
    @Redirect(
            method = "compute(Lnet/minecraft/world/level/levelgen/DensityFunction$FunctionContext;)D",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/levelgen/DensityFunction$FunctionContext;blockX()I")
    )
    private int farlandsreforged$shiftX(DensityFunction.FunctionContext context) {
        int blockX = context.blockX();
        return FarlandsConfig.terrainEnabled() ? FarlandsRegion.noiseX(blockX) : blockX;
    }

    @Redirect(
            method = "compute(Lnet/minecraft/world/level/levelgen/DensityFunction$FunctionContext;)D",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/levelgen/DensityFunction$FunctionContext;blockZ()I")
    )
    private int farlandsreforged$shiftZ(DensityFunction.FunctionContext context) {
        int blockZ = context.blockZ();
        return FarlandsConfig.terrainEnabled() ? FarlandsRegion.noiseZ(blockZ) : blockZ;
    }
}
