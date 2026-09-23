package com.shigeo.farlandsreforged.mixin;

import com.shigeo.farlandsreforged.FarlandsConfig;
import com.shigeo.farlandsreforged.FarlandsRegion;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * 26.3 compiles a {@code range_choice} whose two branches are constants into a separate sampler. It gets the same
 * overflow pass-through as {@link RangeChoiceMixin}, so every range choice behaves the way it did on 26.2.
 */
@Mixin(targets = "net.minecraft.world.level.levelgen.densityfunction.op.RangeChoiceFunction$ConstSampler", remap = false)
public abstract class RangeChoiceConstSamplerMixin {
    @Inject(method = "choose", at = @At("HEAD"), cancellable = true)
    private void farlandsreforged$passOverflowThrough(float value, CallbackInfoReturnable<Float> cir) {
        if (FarlandsConfig.terrainEnabled() && FarlandsRegion.isOverflowed(value)) {
            cir.setReturnValue(value);
        }
    }
}
