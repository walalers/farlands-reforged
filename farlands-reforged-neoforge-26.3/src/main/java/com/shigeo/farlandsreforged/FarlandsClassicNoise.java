package com.shigeo.farlandsreforged;

import com.shigeo.farlandsreforged.mixin.GradientNoiseAccessor;
import com.shigeo.farlandsreforged.mixin.SmearedPerlinNoiseAccessor;
import net.minecraft.util.Mth;
import net.minecraft.world.level.levelgen.densityfunction.DensityBuffer;
import net.minecraft.world.level.levelgen.densityfunction.DensitySampler;
import net.minecraft.world.level.levelgen.densityfunction.DensityVolume;
import net.minecraft.world.level.levelgen.densityfunction.SamplerContext;
import net.minecraft.world.level.levelgen.synth.BlendedNoise;
import net.minecraft.world.level.levelgen.synth.NoiseStack;
import net.minecraft.world.level.levelgen.synth.SmearedPerlinNoise;

/**
 * The legacy 3D terrain noise ({@code old_blended_noise}) evaluated the way Beta 1.7.3 (and Farlands Reforged on
 * 26.2) did: double precision, no coordinate wrap, Beta-era floor.
 *
 * <p>Minecraft 26.3 samples this noise in {@code float} and wraps every Perlin coordinate into +-2^24 inside the
 * sampler itself. Removing the wrap is not enough there: the overflowed fade curve blows past the float range
 * and turns into infinities. So beyond the point where vanilla's wrap starts to change anything, this class
 * recomputes the noise in double from the very same octaves (permutations, offsets and smear scales) that
 * vanilla built for the world seed. Closer to the origin the vanilla float sampler is used untouched.
 */
public final class FarlandsClassicNoise {
    /** Vanilla's wrap is the identity below 2^24; the limit noise reaches that at 2^24 / 171.103 = 98,053 blocks. */
    public static final int WRAP_FREE_LIMIT = 98_000;
    /** Keeps exploded densities finite once they are handed back to the float pipeline. */
    private static final double MAX_DENSITY = 1.0E30;
    /** {@code compileSampler} calls {@code createFbmSet} first on the same thread; this hands the octaves across. */
    public static final ThreadLocal<BlendedNoise.FbmSet> PENDING_FBM = new ThreadLocal<>();

    /** The Perlin gradient table shared by 26.2's {@code SimplexNoise.GRADIENT} and 26.3's {@code GradientNoise.GRADIENT}. */
    private static final int[][] GRADIENT = {
            {1, 1, 0}, {-1, 1, 0}, {1, -1, 0}, {-1, -1, 0},
            {1, 0, 1}, {-1, 0, 1}, {1, 0, -1}, {-1, 0, -1},
            {0, 1, 1}, {0, -1, 1}, {0, 1, -1}, {0, -1, -1},
            {1, 1, 0}, {0, -1, 1}, {-1, 1, 0}, {0, -1, -1}
    };

    private final Octave[] minLimit;
    private final Octave[] maxLimit;
    private final Octave[] main;
    private final double xzMultiplier;
    private final double yMultiplier;
    private final double mainXzScale;
    private final double mainYScale;

    public FarlandsClassicNoise(BlendedNoise.FbmSet fbm, BlendedNoise noise) {
        this.xzMultiplier = 684.412 * noise.xzScale();
        this.yMultiplier = 684.412 * noise.yScale();
        this.mainXzScale = this.xzMultiplier / noise.xzFactor();
        this.mainYScale = this.yMultiplier / noise.yFactor();
        // Octave counts and amplitudes as BlendedNoise.createFbmSet passes them to createFbm.
        this.minLimit = octaves(fbm.minLimitNoise(), -15, 0.9999847412109375);
        this.maxLimit = octaves(fbm.maxLimitNoise(), -15, 0.9999847412109375);
        this.main = octaves(fbm.mainNoise(), -7, 12.75);
    }

    /** True once vanilla's coordinate wrap can differ from the classic, unwrapped noise. */
    public static boolean beyondWrap(long blockX, long blockZ) {
        return Math.abs(blockX) >= WRAP_FREE_LIMIT || Math.abs(blockZ) >= WRAP_FREE_LIMIT;
    }

    /** Same result as 26.2's {@code BlendedNoise.compute} with every {@code PerlinNoise.wrap} call removed. */
    public double compute(int blockX, int blockY, int blockZ) {
        double x = blockX;
        double y = blockY;
        double z = blockZ;
        double alpha = stack(this.main, x * this.mainXzScale, y * this.mainYScale, z * this.mainXzScale) + 0.5;
        double min = alpha < 1.0 ? stack(this.minLimit, x * this.xzMultiplier, y * this.yMultiplier, z * this.xzMultiplier) : 0.0;
        double max = alpha > 0.0 ? stack(this.maxLimit, x * this.xzMultiplier, y * this.yMultiplier, z * this.xzMultiplier) : 0.0;
        return Mth.clampedLerp(alpha, min, max);
    }

    private static double stack(Octave[] octaves, double x, double y, double z) {
        double total = 0.0;
        for (Octave octave : octaves) {
            total += octave.amplitude * octave.sample(x * octave.frequency, y * octave.frequency, z * octave.frequency);
        }
        return total;
    }

    /** Mirrors {@code BlendedNoise.createFbm}: layer 0 is full frequency, each later layer halves it and doubles the amplitude. */
    private static Octave[] octaves(NoiseStack stack, int firstOctave, double totalAmplitude) {
        int count = -firstOctave + 1;
        double frequency = 1.0;
        double amplitude = totalAmplitude / (Math.pow(2.0, count) - 1.0);
        Octave[] octaves = new Octave[count];
        for (int i = 0; i < count; i++) {
            SmearedPerlinNoise noise = (SmearedPerlinNoise) stack.getLayer(i);
            GradientNoiseAccessor gradient = (GradientNoiseAccessor) noise;
            octaves[i] = new Octave(gradient.farlandsreforged$perms(), gradient.farlandsreforged$offsetX(),
                    gradient.farlandsreforged$offsetY(), gradient.farlandsreforged$offsetZ(),
                    ((SmearedPerlinNoiseAccessor) noise).farlandsreforged$fudgeYScale(), frequency, (float) amplitude);
            frequency /= 2.0;
            amplitude *= 2.0;
        }
        return octaves;
    }

    private static float toFloat(double density) {
        return (float) Math.max(-MAX_DENSITY, Math.min(MAX_DENSITY, density));
    }

    private record Octave(byte[] perms, double offsetX, double offsetY, double offsetZ, double fudgeYScale,
                          double frequency, double amplitude) {
        /** 26.2's {@code ImprovedNoise.noise(x, y, z, yScale, yMax)} without the wrap, in double. */
        double sample(double x, double y, double z) {
            double dx = x + this.offsetX;
            double dy = y + this.offsetY;
            double dz = z + this.offsetZ;
            int ix = FarlandsRegion.classicFloor(dx);
            int iy = FarlandsRegion.classicFloor(dy);
            int iz = FarlandsRegion.classicFloor(dz);
            double fx = dx - ix;
            double fy = dy - iy;
            double fz = dz - iz;
            double fudge = 0.0;
            if (this.fudgeYScale != 0.0) {
                double clampedY = y >= 0.0 && y < fy ? y : fy;
                fudge = FarlandsRegion.classicFloor(clampedY / this.fudgeYScale + 1.0E-7) * this.fudgeYScale;
            }
            return sampleAndLerp(ix, iy, iz, fx, fy - fudge, fz, fy);
        }

        private double sampleAndLerp(int x, int y, int z, double fx, double fy, double fz, double fyLerp) {
            int a = p(x);
            int b = p(x + 1);
            int aa = p(a + y);
            int ab = p(a + y + 1);
            int ba = p(b + y);
            int bb = p(b + y + 1);
            double d0 = grad(p(aa + z), fx, fy, fz);
            double d1 = grad(p(ba + z), fx - 1.0, fy, fz);
            double d2 = grad(p(ab + z), fx, fy - 1.0, fz);
            double d3 = grad(p(bb + z), fx - 1.0, fy - 1.0, fz);
            double d4 = grad(p(aa + z + 1), fx, fy, fz - 1.0);
            double d5 = grad(p(ba + z + 1), fx - 1.0, fy, fz - 1.0);
            double d6 = grad(p(ab + z + 1), fx, fy - 1.0, fz - 1.0);
            double d7 = grad(p(bb + z + 1), fx - 1.0, fy - 1.0, fz - 1.0);
            return Mth.lerp3(smoothstep(fx), smoothstep(fyLerp), smoothstep(fz), d0, d1, d2, d3, d4, d5, d6, d7);
        }

        private int p(int index) {
            return this.perms[index & 255] & 255;
        }

        private static double grad(int hash, double x, double y, double z) {
            int[] g = GRADIENT[hash & 15];
            return g[0] * x + g[1] * y + g[2] * z;
        }

        private static double smoothstep(double t) {
            return t * t * t * (t * (t * 6.0 - 15.0) + 10.0);
        }
    }

    /** Vanilla's compiled {@code old_blended_noise} sampler, with the classic noise swapped in far from the origin. */
    public record Sampler(DensitySampler vanilla, FarlandsClassicNoise classic) implements DensitySampler {
        @Override
        public float sampleValue(SamplerContext context, int x, int y, int z) {
            if (!FarlandsConfig.terrainEnabled() || !beyondWrap(x, z)) {
                return this.vanilla.sampleValue(context, x, y, z);
            }
            return toFloat(this.classic.compute(x, y, z));
        }

        @Override
        public void sampleVolume(SamplerContext context, DensityBuffer buffer, DensityVolume volume) {
            long farX = Math.max(Math.abs((long) volume.minBlockX()), Math.abs((long) volume.maxBlockX()));
            long farZ = Math.max(Math.abs((long) volume.minBlockZ()), Math.abs((long) volume.maxBlockZ()));
            if (!FarlandsConfig.terrainEnabled() || !beyondWrap(farX, farZ)) {
                this.vanilla.sampleVolume(context, buffer, volume);
                return;
            }
            for (int iz = 0; iz < volume.sizeZ(); iz++) {
                int blockZ = volume.blockZ(iz);
                for (int ix = 0; ix < volume.sizeX(); ix++) {
                    int blockX = volume.blockX(ix);
                    for (int iy = 0; iy < volume.sizeY(); iy++) {
                        buffer.set(volume.indexUnchecked(ix, iy, iz), toFloat(this.classic.compute(blockX, volume.blockY(iy), blockZ)));
                    }
                }
            }
        }
    }
}
