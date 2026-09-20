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

    /** True if a column is at or beyond the classic Far Lands threshold on the X or Z axis. */
    public static boolean isInFarlands(int blockX, int blockZ) {
        return blockX >= CLASSIC_FARLANDS_START || blockX <= -CLASSIC_FARLANDS_START
                || blockZ >= CLASSIC_FARLANDS_START || blockZ <= -CLASSIC_FARLANDS_START;
    }

    /** True if a column sits on the first block of the Far Lands (used to let fluids settle at the seam). */
    public static boolean isOnFarlandsSeam(int blockX, int blockZ) {
        return Math.abs(blockX) == CLASSIC_FARLANDS_START || Math.abs(blockZ) == CLASSIC_FARLANDS_START;
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
