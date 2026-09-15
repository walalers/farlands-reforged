package com.shigeo.farlandsreforged.mixin;

import net.minecraft.world.level.levelgen.synth.GradientNoise;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;

/** Permutation table and offsets of a Perlin octave, read by {@link com.shigeo.farlandsreforged.FarlandsClassicNoise}. */
@Mixin(GradientNoise.class)
public interface GradientNoiseAccessor {
    @Accessor("perms")
    byte[] farlandsreforged$perms();

    @Accessor("offsetX")
    double farlandsreforged$offsetX();

    @Accessor("offsetY")
    double farlandsreforged$offsetY();

    @Accessor("offsetZ")
    double farlandsreforged$offsetZ();
}
