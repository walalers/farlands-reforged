package com.shigeo.farlandsreforged.mixin;

import com.shigeo.farlandsreforged.FarlandsConfig;
import com.shigeo.farlandsreforged.FarlandsRegion;
import net.minecraft.world.level.levelgen.densityfunction.DensityBuffer;
import net.minecraft.world.level.levelgen.densityfunction.DensitySampler;
import net.minecraft.world.level.levelgen.densityfunction.DensityVolume;
import net.minecraft.world.level.levelgen.densityfunction.SamplerContext;
import net.minecraft.world.level.levelgen.densityfunction.ScopedDensityBuffer;
import org.spongepowered.asm.mixin.Final;
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
@Mixin(targets = "net.minecraft.world.level.levelgen.densityfunction.op.RangeChoiceFunction$Sampler", remap = false)
public abstract class RangeChoiceMixin {
    @Shadow @Final private DensitySampler input;
    @Shadow @Final private float minInclusive;
    @Shadow @Final private float maxExclusive;
    @Shadow @Final private DensitySampler whenInRange;
    @Shadow @Final private DensitySampler whenOutOfRange;

    @Inject(method = "sampleValue", at = @At("HEAD"), cancellable = true)
    private void farlandsreforged$passOverflowThrough(SamplerContext context, int x, int y, int z, CallbackInfoReturnable<Float> cir) {
        if (!FarlandsConfig.terrainEnabled()) {
            return;
        }
        float value = this.input.sampleValue(context, x, y, z);
        if (FarlandsRegion.isOverflowed(value)) {
            cir.setReturnValue(value);
        } else if (value >= this.minInclusive && value < this.maxExclusive) {
            cir.setReturnValue(this.whenInRange.sampleValue(context, x, y, z));
        } else {
            cir.setReturnValue(this.whenOutOfRange.sampleValue(context, x, y, z));
        }
    }

    @Inject(method = "sampleVolume", at = @At("HEAD"), cancellable = true)
    private void farlandsreforged$passOverflowThroughVolume(SamplerContext context, DensityBuffer buffer, DensityVolume volume, CallbackInfo ci) {
        if (!FarlandsConfig.terrainEnabled()) {
            return;
        }
        this.whenInRange.sampleVolume(context, buffer, volume);
        try (ScopedDensityBuffer inputs = context.acquireBuffer(volume)) {
            this.input.sampleVolume(context, inputs, volume);
            try (ScopedDensityBuffer outside = context.acquireBuffer(volume)) {
                this.whenOutOfRange.sampleVolume(context, outside, volume);
                for (int i = 0; i < buffer.size(); i++) {
                    float value = inputs.get(i);
                    if (FarlandsRegion.isOverflowed(value)) {
                        buffer.set(i, value);
                    } else if (!(value >= this.minInclusive && value < this.maxExclusive)) {
                        buffer.set(i, outside.get(i));
                    }
                }
            }
        }
        ci.cancel();
    }
}
