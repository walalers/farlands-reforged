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
 * that did not exist back then (jaggedness, cave noise, aquifers...) do not glitch early or unevenly. With the start
 * set beyond the classic one, this noise keeps its wrap too, up to the start (see {@link FarlandsRegion#keepsWrapX}).
 */
@Mixin(value = BlendedNoise.class, remap = false)
public abstract class BlendedNoiseMixin {
    /*
     * compute() wraps each octave's coordinates in X, Y, Z order: calls 0-2 for the main noise, 3-5 for the two limit
     * noises. The order is the same in every version from 1.18.2 on. Each axis gets its own redirect so that, with a
     * start set beyond the classic one, a column short of it on one axis keeps the wrap on that axis only.
     */
    @Redirect(
            method = "compute(Lnet/minecraft/world/level/levelgen/DensityFunction$FunctionContext;)D",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/levelgen/synth/PerlinNoise;wrap(D)D", ordinal = 0)
    )
    private static double farlandsreforged$mainX(double coordinate, DensityFunction.FunctionContext context) {
        return farlandsreforged$wrapX(coordinate, context);
    }

    @Redirect(
            method = "compute(Lnet/minecraft/world/level/levelgen/DensityFunction$FunctionContext;)D",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/levelgen/synth/PerlinNoise;wrap(D)D", ordinal = 1)
    )
    private static double farlandsreforged$mainY(double coordinate) {
        return farlandsreforged$wrapY(coordinate);
    }

    @Redirect(
            method = "compute(Lnet/minecraft/world/level/levelgen/DensityFunction$FunctionContext;)D",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/levelgen/synth/PerlinNoise;wrap(D)D", ordinal = 2)
    )
    private static double farlandsreforged$mainZ(double coordinate, DensityFunction.FunctionContext context) {
        return farlandsreforged$wrapZ(coordinate, context);
    }

    @Redirect(
            method = "compute(Lnet/minecraft/world/level/levelgen/DensityFunction$FunctionContext;)D",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/levelgen/synth/PerlinNoise;wrap(D)D", ordinal = 3)
    )
    private static double farlandsreforged$limitX(double coordinate, DensityFunction.FunctionContext context) {
        return farlandsreforged$wrapX(coordinate, context);
    }

    @Redirect(
            method = "compute(Lnet/minecraft/world/level/levelgen/DensityFunction$FunctionContext;)D",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/levelgen/synth/PerlinNoise;wrap(D)D", ordinal = 4)
    )
    private static double farlandsreforged$limitY(double coordinate) {
        return farlandsreforged$wrapY(coordinate);
    }

    @Redirect(
            method = "compute(Lnet/minecraft/world/level/levelgen/DensityFunction$FunctionContext;)D",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/levelgen/synth/PerlinNoise;wrap(D)D", ordinal = 5)
    )
    private static double farlandsreforged$limitZ(double coordinate, DensityFunction.FunctionContext context) {
        return farlandsreforged$wrapZ(coordinate, context);
    }

    private static double farlandsreforged$wrapX(double coordinate, DensityFunction.FunctionContext context) {
        boolean keepWrap = !FarlandsConfig.terrainEnabled()
                || (FarlandsRegion.startsBeyondClassicX() && FarlandsRegion.keepsWrapX(context.blockX()));
        return keepWrap ? PerlinNoise.wrap(coordinate) : coordinate;
    }

    private static double farlandsreforged$wrapY(double coordinate) {
        return FarlandsConfig.terrainEnabled() ? coordinate : PerlinNoise.wrap(coordinate);
    }

    private static double farlandsreforged$wrapZ(double coordinate, DensityFunction.FunctionContext context) {
        boolean keepWrap = !FarlandsConfig.terrainEnabled()
                || (FarlandsRegion.startsBeyondClassicZ() && FarlandsRegion.keepsWrapZ(context.blockZ()));
        return keepWrap ? PerlinNoise.wrap(coordinate) : coordinate;
    }

    /**
     * Reads the legacy noise at the shifted column when the Far Lands are configured to start somewhere other than
     * the classic threshold, so the overflow that makes them lands on the configured start. See
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
