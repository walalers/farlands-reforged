package com.shigeo.farlandsreforged;

import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.fml.config.ModConfig;
import net.neoforged.neoforge.common.NeoForge;

@Mod(FarlandsReforged.MOD_ID)
public final class FarlandsReforged {
    public static final String MOD_ID = "farlandsreforged";

    public FarlandsReforged(IEventBus modEventBus, ModContainer modContainer) {
        modContainer.registerConfig(ModConfig.Type.COMMON, FarlandsConfig.SPEC);
        NeoForge.EVENT_BUS.addListener(FarlandsCommands::register);
        NeoForge.EVENT_BUS.addListener(FarlandsEvents::onPlayerTick);
    }
}
