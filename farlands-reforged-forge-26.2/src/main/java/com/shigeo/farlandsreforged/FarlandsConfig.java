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
    public static final long MAX_START = 30_000_000L;

    private static final Properties PROPERTIES = new Properties();
    private static final String ENABLE_TERRAIN = "enableFarlandsTerrain";
    private static final String ENABLE_ADVANCEMENT = "enableWhereAmIAdvancement";
    private static final String FARLANDS_START = "farlandsStartCoordinate";
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

    public static long farlandsStartCoordinate() {
        return parseLong(PROPERTIES.getProperty(FARLANDS_START), CLASSIC_FARLANDS_START);
    }

    public static void setFarlandsStartCoordinate(long coordinate) {
        long clamped = Math.max(MIN_START, Math.min(MAX_START, coordinate));
        PROPERTIES.setProperty(FARLANDS_START, Long.toString(clamped));
        save();
    }

    public static void resetFarlandsStartCoordinate() {
        setFarlandsStartCoordinate(CLASSIC_FARLANDS_START);
    }

    private static void setDefaults() {
        PROPERTIES.setProperty(ENABLE_TERRAIN, "true");
        PROPERTIES.setProperty(ENABLE_ADVANCEMENT, "true");
        PROPERTIES.setProperty(ENABLE_FARMAN, "false");
        PROPERTIES.setProperty(FARLANDS_START, Long.toString(CLASSIC_FARLANDS_START));
    }

    private static void sanitize() {
        PROPERTIES.putIfAbsent(ENABLE_TERRAIN, "true");
        PROPERTIES.putIfAbsent(ENABLE_ADVANCEMENT, "true");
        PROPERTIES.putIfAbsent(ENABLE_FARMAN, "false");
        long clamped = Math.max(MIN_START, Math.min(MAX_START, farlandsStartCoordinate()));
        PROPERTIES.setProperty(FARLANDS_START, Long.toString(clamped));
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
                PROPERTIES.store(output, "Farlands Reforged Forge config. The threshold controls /farlands, the advancement and where FarMan walks; terrain remains classic-authentic. enableFarMan turns on the FarMan haunting (off by default).");
            }
        } catch (IOException ignored) {
        }
    }
}
