package com.shigeo.farlandsreforged;

/**
 * Pure helpers describing where and how the classic Far Lands break down. Shared by every mixin so the
 * numbers live in one place.
 *
 * <p>Background: the legacy 3D terrain noise ({@code old_blended_noise}) samples its first octave at
 * {@code blockX * 684.412 * 0.25 = blockX * 171.103}. Once that exceeds 2^31 the integer cast inside the
 * Perlin sampler saturates, the fractional part is no longer in [0, 1), and the fade curve explodes. That is
 * the Far Lands, and it starts at 2^31 / 171.103 = 12,550,824 in noise space, which the 4-block interpolation
 * cell turns into the classic 12,550,821 in block space.
 */
public final class FarlandsRegion {
    /** Classic block coordinate at which the Far Lands appear on either axis (Beta 1.7.3 and earlier). */
    public static final int CLASSIC_FARLANDS_START = 12_550_821;

    /**
     * Vanilla's density pipeline uses -1,000,000 as "negative infinity". Any density with a magnitude at or
     * beyond this can only come from an overflowed noise sample, so it doubles as the "we are inside the Far
     * Lands" detector for density values.
     */
    public static final double OVERFLOW_DENSITY = 1.0E6;

    private FarlandsRegion() {}

    /**
     * Where the Far Lands start on each axis: the classic value, unless the config brings them closer. Cached here
     * because the terrain mixins read them inside the hottest world-generation loops.
     */
    private static volatile int startX = CLASSIC_FARLANDS_START;
    private static volatile int startZ = CLASSIC_FARLANDS_START;

    /**
     * Sets where the Far Lands start. The legacy noise is sampled every 4 blocks, on a grid the classic start sits
     * on, so each value is moved out (by at most 3 blocks) to the next point on that grid. The wall then stands
     * exactly on the start, as it does at the classic one, and the seam checks below match it.
     */
    public static void setStart(long x, long z) {
        startX = onNoiseGrid(x);
        startZ = onNoiseGrid(z);
    }

    public static int startX() {
        return startX;
    }

    public static int startZ() {
        return startZ;
    }

    private static int onNoiseGrid(long start) {
        long clamped = Math.max(1L, Math.min(CLASSIC_FARLANDS_START, start));
        return (int) (clamped + Math.floorMod(CLASSIC_FARLANDS_START - clamped, 4L));
    }

    /** True if a column is at or beyond the Far Lands start on the X or Z axis. */
    public static boolean isInFarlands(int blockX, int blockZ) {
        int x = startX;
        int z = startZ;
        return blockX >= x || blockX <= -x || blockZ >= z || blockZ <= -z;
    }

    /** True if a column sits on the first block of the Far Lands (used to let fluids settle at the seam). */
    public static boolean isOnFarlandsSeam(int blockX, int blockZ) {
        return Math.abs(blockX) == startX || Math.abs(blockZ) == startZ;
    }

    /**
     * The X coordinate the legacy terrain noise is read at for a block. Up to the start it is the block's own; past
     * it, the noise is read as if the column stood {@code CLASSIC_FARLANDS_START - start} blocks further out, so it
     * overflows - the Far Lands wall - at the configured start instead of the classic one. The jump in the noise
     * falls on the wall itself, where Beta's terrain broke off anyway. At the classic start this is the identity.
     */
    public static int noiseX(int blockX) {
        return shift(blockX, startX);
    }

    /** The Z counterpart of {@link #noiseX}. */
    public static int noiseZ(int blockZ) {
        return shift(blockZ, startZ);
    }

    private static int shift(int block, int start) {
        int offset = CLASSIC_FARLANDS_START - start;
        if (offset == 0 || (block < start && block > -start)) {
            return block;
        }
        return block >= start ? block + offset : block - offset;
    }

    /** True if a density value is so large it must have come from an overflowed noise sample. */
    public static boolean isOverflowed(double density) {
        return density >= OVERFLOW_DENSITY || density <= -OVERFLOW_DENSITY;
    }

    /**
     * The floor used by the Beta-era noise generator: {@code int i = (int) d; if (d < i) i--;}.
     *
     * <p>Identical to {@code Mth.floor} for every value the game normally produces. Past the integer limit the
     * two differ on the negative axis: modern {@code (int) Math.floor(d)} saturates to Integer.MIN_VALUE, while
     * the classic version decrements that and wraps around to Integer.MAX_VALUE. Using the classic floor keeps
     * the negative-coordinate Far Lands looking the way they did originally.
     */
    public static int classicFloor(double value) {
        int truncated = (int) value;
        return value < (double) truncated ? truncated - 1 : truncated;
    }
}
