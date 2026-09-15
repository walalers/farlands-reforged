package com.shigeo.farlandsreforged;

import net.minecraft.world.level.levelgen.densityfunction.DensityBuffer;
import net.minecraft.world.level.levelgen.densityfunction.DensitySampler;
import net.minecraft.world.level.levelgen.densityfunction.DensityVolume;
import net.minecraft.world.level.levelgen.densityfunction.SamplerContext;

/**
 * Wraps the compiled {@code minecraft:noodle} noise so it reads -1 inside the Far Lands. The noodle function only
 * carves where that noise is non-negative, so the tunnels switch off there and nowhere else.
 */
public record FarlandsNoodleSampler(DensitySampler vanilla) implements DensitySampler {
    @Override
    public float sampleValue(SamplerContext context, int x, int y, int z) {
        if (FarlandsConfig.terrainEnabled() && FarlandsRegion.isInFarlands(x, z)) {
            return -1.0F;
        }
        return this.vanilla.sampleValue(context, x, y, z);
    }

    @Override
    public void sampleVolume(SamplerContext context, DensityBuffer buffer, DensityVolume volume) {
        this.vanilla.sampleVolume(context, buffer, volume);
        if (!FarlandsConfig.terrainEnabled()) {
            return;
        }
        long farX = Math.max(Math.abs((long) volume.minBlockX()), Math.abs((long) volume.maxBlockX()));
        long farZ = Math.max(Math.abs((long) volume.minBlockZ()), Math.abs((long) volume.maxBlockZ()));
        if (farX < FarlandsRegion.CLASSIC_FARLANDS_START && farZ < FarlandsRegion.CLASSIC_FARLANDS_START) {
            return;
        }
        for (int iz = 0; iz < volume.sizeZ(); iz++) {
            int blockZ = volume.blockZ(iz);
            for (int ix = 0; ix < volume.sizeX(); ix++) {
                if (!FarlandsRegion.isInFarlands(volume.blockX(ix), blockZ)) {
                    continue;
                }
                for (int iy = 0; iy < volume.sizeY(); iy++) {
                    buffer.set(volume.indexUnchecked(ix, iy, iz), -1.0F);
                }
            }
        }
    }
}
