package com.shigeo.farlandsreforged.mixin;

import com.shigeo.farlandsreforged.FarlandsClassicNoise;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.levelgen.densityfunction.DensitySampler;
import net.minecraft.world.level.levelgen.synth.BlendedNoise;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * The legacy 3D terrain noise ({@code old_blended_noise}) is the direct descendant of the Beta-era terrain
 * generator, and it is the only noise that broke down in the original Far Lands. Vanilla wraps its coordinates
 * into +-16,777,216 before sampling; skipping that wrap lets the sampler overflow exactly where it did in Beta
 * 1.7.3 (2^31 / 171.103 = 12,550,824 in noise space). Every other noise keeps its wrap, so terrain features
 * that did not exist back then (jaggedness, cave noise, aquifers...) do not glitch early or unevenly.
 *
 * <p>On 26.3 the wrap lives inside the shared float Perlin sampler, so instead of redirecting it this mixin
 * wraps the compiled sampler with {@link FarlandsClassicNoise}, which evaluates the same octaves in double
 * without the wrap wherever the wrap would make a difference.
 */
@Mixin(value = BlendedNoise.class, remap = false)
public abstract class BlendedNoiseMixin {
    @Inject(method = "createFbmSet", at = @At("RETURN"))
    private void farlandsreforged$rememberOctaves(RandomSource random, CallbackInfoReturnable<BlendedNoise.FbmSet> cir) {
        FarlandsClassicNoise.PENDING_FBM.set(cir.getReturnValue());
    }

    @Inject(
            method = "compileSampler(Lnet/minecraft/util/RandomSource;)Lnet/minecraft/world/level/levelgen/densityfunction/DensitySampler;",
            at = @At("RETURN"),
            cancellable = true
    )
    private void farlandsreforged$keepFullPrecision(RandomSource random, CallbackInfoReturnable<DensitySampler> cir) {
        BlendedNoise.FbmSet octaves = FarlandsClassicNoise.PENDING_FBM.get();
        FarlandsClassicNoise.PENDING_FBM.remove();
        if (octaves != null) {
            FarlandsClassicNoise classic = new FarlandsClassicNoise(octaves, (BlendedNoise) (Object) this);
            cir.setReturnValue(new FarlandsClassicNoise.Sampler(cir.getReturnValue(), classic));
        }
    }
}
