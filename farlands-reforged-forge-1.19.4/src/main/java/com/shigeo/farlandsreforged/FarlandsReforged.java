package com.shigeo.farlandsreforged;

import net.minecraftforge.fml.common.Mod;

@Mod(FarlandsReforged.MOD_ID)
public final class FarlandsReforged {
    public static final String MOD_ID = "farlandsreforged";

    // Forge 51 (Minecraft 1.21) calls getDeclaredConstructor() with no arguments at all, so the
    // FMLJavaModLoadingContext constructor that farlands-reforged-forge-1.21.11 uses is never found and
    // mod loading dies with NoSuchMethodException. Forge 52 and up ask for the context constructor first
    // but fall back to this one, so a plain no-arg constructor covers 1.21 through 1.21.10. Nothing here
    // needed the context anyway: the config reads the static FMLPaths.CONFIGDIR, and the command and
    // advancement hooks are installed by mixins rather than by an event bus.
    public FarlandsReforged() {
        FarlandsConfig.load();
    }
}
