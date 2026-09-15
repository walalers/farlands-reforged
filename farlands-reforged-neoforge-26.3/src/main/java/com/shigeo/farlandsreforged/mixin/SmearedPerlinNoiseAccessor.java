package com.shigeo.farlandsreforged.mixin;

import net.minecraft.world.level.levelgen.synth.SmearedPerlinNoise;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;

/** Vertical smear scale of a legacy terrain octave, read by {@link com.shigeo.farlandsreforged.FarlandsClassicNoise}. */
@Mixin(SmearedPerlinNoise.class)
public interface SmearedPerlinNoiseAccessor {
    @Accessor("fudgeYScale")
    double farlandsreforged$fudgeYScale();
}
