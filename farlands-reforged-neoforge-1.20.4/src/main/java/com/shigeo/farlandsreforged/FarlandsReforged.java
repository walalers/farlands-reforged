package com.shigeo.farlandsreforged;

import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModLoadingContext;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.config.ModConfig;
import net.neoforged.neoforge.common.NeoForge;

@Mod(FarlandsReforged.MOD_ID)
public final class FarlandsReforged {
    public static final String MOD_ID = "farlandsreforged";

    // Only the mod bus is injected, and the config goes through ModLoadingContext: every FML from 1.0.2
    // (NeoForge 20.2) to 2.x (20.4) supports both, while ModContainer.registerConfig and ModContainer
    // injection arrive later.
    public FarlandsReforged(IEventBus modEventBus) {
        ModLoadingContext.get().registerConfig(ModConfig.Type.COMMON, FarlandsConfig.SPEC);
        modEventBus.addListener(FarlandsConfig::onConfigEvent);
        NeoForge.EVENT_BUS.addListener(FarlandsCommands::register);
        NeoForge.EVENT_BUS.addListener(FarlandsEvents::onPlayerTick);
    }
}
