package com.shigeo.farlandsreforged;

import net.neoforged.fml.event.config.ModConfigEvent;
import net.neoforged.neoforge.common.ModConfigSpec;

public final class FarlandsConfig {
    public static final long CLASSIC_FARLANDS_START = 12_550_821L;
    public static final long MIN_START = 1L;
    public static final long MAX_START = 30_000_000L;

    public static final ModConfigSpec SPEC;
    public static final ModConfigSpec.BooleanValue ENABLE_TERRAIN;
    public static final ModConfigSpec.BooleanValue ENABLE_ADVANCEMENT;
    public static final ModConfigSpec.LongValue FARLANDS_START_COORDINATE;

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
        FARLANDS_START_COORDINATE = builder
                .comment("Classic Far Lands threshold used by /farlands and the advancement detector.",
                        "The terrain effect itself always breaks down at the classic 12,550,821 like Beta did; changing this value does not move the real Far Lands.",
                        "Classic value: 12550821")
                .defineInRange("farlandsStartCoordinate", CLASSIC_FARLANDS_START, MIN_START, MAX_START);
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
        }
    }

    public static boolean advancementEnabled() {
        return safeBoolean(ENABLE_ADVANCEMENT, true);
    }

    public static long farlandsStartCoordinate() {
        return safeLong(FARLANDS_START_COORDINATE, CLASSIC_FARLANDS_START);
    }

    public static void setFarlandsStartCoordinate(long coordinate) {
        FARLANDS_START_COORDINATE.set(coordinate);
        FARLANDS_START_COORDINATE.save();
    }

    public static void resetFarlandsStartCoordinate() {
        setFarlandsStartCoordinate(CLASSIC_FARLANDS_START);
    }

    private static boolean safeBoolean(ModConfigSpec.BooleanValue value, boolean fallback) {
        try {
            return value.getAsBoolean();
        } catch (IllegalStateException | NullPointerException ignored) {
            return fallback;
        }
    }

    private static long safeLong(ModConfigSpec.LongValue value, long fallback) {
        try {
            return value.getAsLong();
        } catch (IllegalStateException | NullPointerException ignored) {
            return fallback;
        }
    }
}
