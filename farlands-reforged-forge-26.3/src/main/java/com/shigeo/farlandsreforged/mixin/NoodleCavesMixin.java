package com.shigeo.farlandsreforged.mixin;

import com.shigeo.farlandsreforged.FarlandsNoodleSampler;
import net.minecraft.world.level.levelgen.Noises;
import net.minecraft.world.level.levelgen.densityfunction.DensityFunction;
import net.minecraft.world.level.levelgen.densityfunction.DensitySampler;
import net.minecraft.world.level.levelgen.densityfunction.generator.NoiseFunction;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Noodle caves are the long, thin tunnels modern Minecraft carves everywhere through the final density
 * ({@code min(terrain, overworld/caves/noodle)}), so they bore straight through the Far Lands walls and sheets.
 * Beta had nothing like them. The noodle function only carves where the {@code minecraft:noodle} noise is
 * non-negative, so reporting that noise as -1 inside the Far Lands turns the tunnels off there and nowhere else.
 */
@Mixin(value = NoiseFunction.class, remap = false)
public abstract class NoodleCavesMixin {
    @Inject(method = "compileSampler", at = @At("RETURN"), cancellable = true)
    private void farlandsreforged$noNoodlesInFarlands(DensityFunction.CompileContext context, CallbackInfoReturnable<DensitySampler> cir) {
        if (((NoiseFunction) (Object) this).noise().is(Noises.NOODLE)) {
            cir.setReturnValue(new FarlandsNoodleSampler(cir.getReturnValue()));
        }
    }
}
