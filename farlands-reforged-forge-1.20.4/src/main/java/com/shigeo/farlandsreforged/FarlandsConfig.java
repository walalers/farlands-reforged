package com.shigeo.farlandsreforged;

import net.minecraftforge.fml.loading.FMLPaths;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Properties;

public final class FarlandsConfig {
    public static final long CLASSIC_FARLANDS_START = 12_550_821L;
    public static final long MIN_START = 1L;
    /** The Far Lands can only be brought closer: past the classic start the noise has already overflowed. */
    public static final long MAX_START = CLASSIC_FARLANDS_START;

    private static final Properties PROPERTIES = new Properties();
    private static final String ENABLE_TERRAIN = "enableFarlandsTerrain";
    private static final String ENABLE_ADVANCEMENT = "enableWhereAmIAdvancement";
    private static final String FARLANDS_START_X = "farlandsStartX";
    private static final String FARLANDS_START_Z = "farlandsStartZ";
    /** Before 0.6.0 this moved only /farlands and the advancement; the terrain start replaced it. */
    private static final String LEGACY_FARLANDS_START = "farlandsStartCoordinate";
    private static final String ENABLE_FARMAN = "enableFarMan";

    private static Path configPath;

    private FarlandsConfig() {
    }

    public static void load() {
        configPath = FMLPaths.CONFIGDIR.get().resolve("farlandsreforged.properties");
        setDefaults();
        if (Files.exists(configPath)) {
            try (InputStream input = Files.newInputStream(configPath)) {
                PROPERTIES.load(input);
            } catch (IOException ignored) {
                setDefaults();
            }
        }
        sanitize();
        terrainEnabled = Boolean.parseBoolean(PROPERTIES.getProperty(ENABLE_TERRAIN, "true"));
    }

    /** Cached because the terrain mixins read it inside the hottest world-generation loops. */
    private static volatile boolean terrainEnabled = true;

    public static boolean terrainEnabled() {
        return terrainEnabled;
    }

    public static boolean advancementEnabled() {
        return Boolean.parseBoolean(PROPERTIES.getProperty(ENABLE_ADVANCEMENT, "true"));
    }

    public static boolean farManEnabled() {
        return Boolean.parseBoolean(PROPERTIES.getProperty(ENABLE_FARMAN, "false"));
    }

    public static void setFarManEnabled(boolean enabled) {
        PROPERTIES.setProperty(ENABLE_FARMAN, Boolean.toString(enabled));
        save();
    }

    public static long farlandsStartX() {
        return parseLong(PROPERTIES.getProperty(FARLANDS_START_X), CLASSIC_FARLANDS_START);
    }

    public static long farlandsStartZ() {
        return parseLong(PROPERTIES.getProperty(FARLANDS_START_Z), CLASSIC_FARLANDS_START);
    }

    /** Moves where the Far Lands start. Chunks that already exist keep their terrain. */
    public static void setFarlandsStart(long x, long z) {
        PROPERTIES.setProperty(FARLANDS_START_X, Long.toString(clampStart(x)));
        PROPERTIES.setProperty(FARLANDS_START_Z, Long.toString(clampStart(z)));
        FarlandsRegion.setStart(farlandsStartX(), farlandsStartZ());
        save();
    }

    private static long clampStart(long start) {
        return Math.max(MIN_START, Math.min(MAX_START, start));
    }

    private static void setDefaults() {
        PROPERTIES.setProperty(ENABLE_TERRAIN, "true");
        PROPERTIES.setProperty(ENABLE_ADVANCEMENT, "true");
        PROPERTIES.setProperty(ENABLE_FARMAN, "false");
        PROPERTIES.setProperty(FARLANDS_START_X, Long.toString(CLASSIC_FARLANDS_START));
        PROPERTIES.setProperty(FARLANDS_START_Z, Long.toString(CLASSIC_FARLANDS_START));
    }

    private static void sanitize() {
        PROPERTIES.putIfAbsent(ENABLE_TERRAIN, "true");
        PROPERTIES.putIfAbsent(ENABLE_ADVANCEMENT, "true");
        PROPERTIES.putIfAbsent(ENABLE_FARMAN, "false");
        PROPERTIES.remove(LEGACY_FARLANDS_START);
        PROPERTIES.setProperty(FARLANDS_START_X, Long.toString(clampStart(farlandsStartX())));
        PROPERTIES.setProperty(FARLANDS_START_Z, Long.toString(clampStart(farlandsStartZ())));
        FarlandsRegion.setStart(farlandsStartX(), farlandsStartZ());
        save();
    }

    private static long parseLong(String value, long fallback) {
        try {
            return Long.parseLong(value);
        } catch (NumberFormatException ignored) {
            return fallback;
        }
    }

    private static void save() {
        if (configPath == null) {
            return;
        }
        try {
            Files.createDirectories(configPath.getParent());
            try (OutputStream output = Files.newOutputStream(configPath)) {
                PROPERTIES.store(output, "Farlands Reforged Forge config. enableFarlandsTerrain toggles the authentic Far Lands. farlandsStartX and farlandsStartZ move where they start, from 1 up to the classic 12550821 (chunks that already exist keep their terrain). enableFarMan turns on the FarMan haunting (off by default).");
            }
        } catch (IOException ignored) {
        }
    }
}
