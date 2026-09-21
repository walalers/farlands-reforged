package com.shigeo.farlandsreforged.mixin;

import com.shigeo.farlandsreforged.FarlandsConfig;
import com.shigeo.farlandsreforged.FarlandsRegion;
import net.minecraft.world.level.levelgen.DensityFunction;
import net.minecraft.world.level.levelgen.Noises;
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
@Mixin(targets = "net.minecraft.world.level.levelgen.DensityFunctions$Noise", remap = false)
public abstract class NoodleCavesMixin {
    @Shadow @Final private DensityFunction.NoiseHolder noise;

    @Inject(method = "compute", at = @At("HEAD"), cancellable = true)
    private void farlandsreforged$noNoodlesInFarlands(DensityFunction.FunctionContext context, CallbackInfoReturnable<Double> cir) {
        if (FarlandsConfig.terrainEnabled()
                && FarlandsRegion.isInFarlands(context.blockX(), context.blockZ())
                && this.noise.noiseData().is(Noises.NOODLE)) {
            cir.setReturnValue(-1.0);
        }
    }
}
