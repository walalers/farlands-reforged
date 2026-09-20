package com.shigeo.farlandsreforged.mixin;

import com.shigeo.farlandsreforged.FarlandsConfig;
import com.shigeo.farlandsreforged.FarlandsRegion;
import net.minecraft.world.level.levelgen.DensityFunction;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * The heart of the authentic Far Lands look.
 *
 * <p>In Beta the exploded noise value <em>was</em> the terrain density: positive meant stone, negative meant
 * air, and the wild magnitudes produced the stretched walls, sheets and tunnels. Modern world generation
 * instead feeds the density into a {@code range_choice} whose "negative infinity" is -1,000,000. Overflowed
 * noise blows far past that on both sides, so vanilla routes <em>every</em> Far Lands sample into the
 * "deep underground" branch and the result is a featureless solid slab from bedrock to the build limit.
 *
 * <p>This mixin lets any overflowed input pass straight through the choice, so the sign of the classic noise
 * decides solid-versus-air again. Vanilla never produces inputs of that magnitude, so ordinary terrain is
 * untouched.
 */
@Mixin(targets = "net.minecraft.world.level.levelgen.DensityFunctions$RangeChoice")
public abstract class RangeChoiceMixin {
    @Shadow public abstract DensityFunction input();
    @Shadow public abstract double minInclusive();
    @Shadow public abstract double maxExclusive();
    @Shadow public abstract DensityFunction whenInRange();
    @Shadow public abstract DensityFunction whenOutOfRange();

    @Inject(method = "compute", at = @At("HEAD"), cancellable = true)
    private void farlandsreforged$passOverflowThrough(DensityFunction.FunctionContext context, CallbackInfoReturnable<Double> cir) {
        if (!FarlandsConfig.terrainEnabled()) {
            return;
        }
        double value = this.input().compute(context);
        if (FarlandsRegion.isOverflowed(value)) {
            cir.setReturnValue(value);
        } else if (value >= this.minInclusive() && value < this.maxExclusive()) {
            cir.setReturnValue(this.whenInRange().compute(context));
        } else {
            cir.setReturnValue(this.whenOutOfRange().compute(context));
        }
    }

    @Inject(method = "fillArray", at = @At("HEAD"), cancellable = true)
    private void farlandsreforged$passOverflowThroughArray(double[] values, DensityFunction.ContextProvider provider, CallbackInfo ci) {
        if (!FarlandsConfig.terrainEnabled()) {
            return;
        }
        this.input().fillArray(values, provider);
        for (int i = 0; i < values.length; i++) {
            double value = values[i];
            if (FarlandsRegion.isOverflowed(value)) {
                continue;
            }
            DensityFunction branch = value >= this.minInclusive() && value < this.maxExclusive() ? this.whenInRange() : this.whenOutOfRange();
            values[i] = branch.compute(provider.forIndex(i));
        }
        ci.cancel();
    }
}
