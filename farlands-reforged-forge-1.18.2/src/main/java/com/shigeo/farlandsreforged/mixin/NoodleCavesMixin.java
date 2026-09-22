package com.shigeo.farlandsreforged.mixin;

import com.shigeo.farlandsreforged.FarlandsConfig;
import com.shigeo.farlandsreforged.FarlandsRegion;
import net.minecraft.core.Holder;
import net.minecraft.world.level.levelgen.DensityFunction;
import net.minecraft.world.level.levelgen.Noises;
import net.minecraft.world.level.levelgen.synth.NormalNoise;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Noodle caves are the long, thin tunnels modern Minecraft carves everywhere through the final density
 * ({@code min(terrain, overworld/caves/noodle)}), so they bore straight through the Far Lands walls and sheets.
 * Beta had nothing like them. The noodle function only carves where the {@code minecraft:noodle} noise is
 * non-negative, so reporting that noise as -1 inside the Far Lands turns the tunnels off there and nowhere else.
 */
@Mixin(targets = "net.minecraft.world.level.levelgen.DensityFunctions$Noise")
public abstract class NoodleCavesMixin {
    // 1.18.2 has no DensityFunction.NoiseHolder yet; the noise key sits directly on this record.
    @Shadow @Final private Holder<NormalNoise.NoiseParameters> noiseData;

    @Inject(method = "compute", at = @At("HEAD"), cancellable = true)
    private void farlandsreforged$noNoodlesInFarlands(DensityFunction.FunctionContext context, CallbackInfoReturnable<Double> cir) {
        if (FarlandsConfig.terrainEnabled()
                && FarlandsRegion.isInFarlands(context.blockX(), context.blockZ())
                && this.noiseData.is(Noises.NOODLE)) {
            cir.setReturnValue(-1.0);
        }
    }
}
