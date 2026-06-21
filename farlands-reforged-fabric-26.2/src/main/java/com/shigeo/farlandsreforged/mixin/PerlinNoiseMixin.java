package com.shigeo.farlandsreforged.mixin;

import com.shigeo.farlandsreforged.FarlandsConfig;
import net.minecraft.world.level.levelgen.synth.PerlinNoise;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(PerlinNoise.class)
public abstract class PerlinNoiseMixin {
    @Inject(method = "wrap(D)D", at = @At("HEAD"), cancellable = true)
    private static void farlandsreforged$keepFullPrecision(double coordinate, CallbackInfoReturnable<Double> cir) {
        if (FarlandsConfig.terrainEnabled()) {
            cir.setReturnValue(coordinate);
        }
    }
}
