package com.shigeo.farlandsreforged;

import net.neoforged.fml.event.config.ModConfigEvent;
import net.neoforged.neoforge.common.ModConfigSpec;

public final class FarlandsConfig {
    public static final long CLASSIC_FARLANDS_START = 12_550_821L;
    public static final long MIN_START = 1L;
    /** The Far Lands can only be brought closer: past the classic start the noise has already overflowed. */
    public static final long MAX_START = CLASSIC_FARLANDS_START;

    public static final ModConfigSpec SPEC;
    public static final ModConfigSpec.BooleanValue ENABLE_TERRAIN;
    public static final ModConfigSpec.BooleanValue ENABLE_ADVANCEMENT;
    public static final ModConfigSpec.BooleanValue ENABLE_FARMAN;
    public static final ModConfigSpec.LongValue FARLANDS_START_X;
    public static final ModConfigSpec.LongValue FARLANDS_START_Z;

    static {
        ModConfigSpec.Builder builder = new ModConfigSpec.Builder();

        builder.push("general");
        ENABLE_TERRAIN = builder
                .comment("If true, Farlands Reforged preserves full Perlin noise precision so classic Far Lands-style terrain can generate.",
                        "Default: true. Disable only for troubleshooting or vanilla worldgen comparisons.")
                .define("enableFarlandsTerrain", true);
        ENABLE_ADVANCEMENT = builder
                .comment("If true, players earn the hidden Far Lands advancement when they cross the configured threshold.")
                .define("enableWhereAmIAdvancement", true);
        FARLANDS_START_X = builder
                .comment("Where the Far Lands start on the X axis, in blocks from the centre of the world (both directions).",
                        "The classic, Beta 1.7.3 value is 12550821, which is also the furthest out they can start. Any value from 1 up",
                        "brings them closer. Chunks that already exist keep their terrain. /farlands, the advancement and FarMan follow it too.")
                .defineInRange("farlandsStartX", CLASSIC_FARLANDS_START, MIN_START, MAX_START);
        FARLANDS_START_Z = builder
                .comment("Where the Far Lands start on the Z axis. Same rules as farlandsStartX.")
                .defineInRange("farlandsStartZ", CLASSIC_FARLANDS_START, MIN_START, MAX_START);
        ENABLE_FARMAN = builder
                .comment("If true, FarMan haunts players who stay in the Far Lands: omens, distant sightings, and him standing behind you.",
                        "He never hurts anyone; the worst he does is a scare. Off by default. Ops can also use /farlands farman on|off.")
                .define("enableFarMan", false);
        builder.pop();

        SPEC = builder.build();
    }

    /** Cached because the terrain mixins read it inside the hottest world-generation loops. */
    private static volatile boolean terrainEnabled = true;

    private FarlandsConfig() {}

    public static boolean terrainEnabled() {
        return terrainEnabled;
    }

    /** Mod-bus listener: refreshes the cached toggles whenever this config is loaded or reloaded. */
    public static void onConfigEvent(ModConfigEvent event) {
        if (event.getConfig().getSpec() == SPEC) {
            terrainEnabled = safeBoolean(ENABLE_TERRAIN, true);
            FarlandsRegion.setStart(farlandsStartX(), farlandsStartZ());
        }
    }

    public static boolean advancementEnabled() {
        return safeBoolean(ENABLE_ADVANCEMENT, true);
    }

    public static boolean farManEnabled() {
        return safeBoolean(ENABLE_FARMAN, false);
    }

    public static void setFarManEnabled(boolean enabled) {
        ENABLE_FARMAN.set(enabled);
        ENABLE_FARMAN.save();
    }

    public static long farlandsStartX() {
        return safeLong(FARLANDS_START_X, CLASSIC_FARLANDS_START);
    }

    public static long farlandsStartZ() {
        return safeLong(FARLANDS_START_Z, CLASSIC_FARLANDS_START);
    }

    /** Moves where the Far Lands start. Chunks that already exist keep their terrain. */
    public static void setFarlandsStart(long x, long z) {
        FARLANDS_START_X.set(x);
        FARLANDS_START_Z.set(z);
        FARLANDS_START_X.save();
        FarlandsRegion.setStart(x, z);
    }

    private static boolean safeBoolean(ModConfigSpec.BooleanValue value, boolean fallback) {
        try {
            return value.get();
        } catch (IllegalStateException | NullPointerException ignored) {
            return fallback;
        }
    }

    private static long safeLong(ModConfigSpec.LongValue value, long fallback) {
        try {
            return value.get();
        } catch (IllegalStateException | NullPointerException ignored) {
            return fallback;
        }
    }
}
