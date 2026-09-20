package com.shigeo.farlandsreforged;

import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;

@Mod(FarlandsReforged.MOD_ID)
public final class FarlandsReforged {
    public static final String MOD_ID = "farlandsreforged";

    public FarlandsReforged(FMLJavaModLoadingContext context) {
        FarlandsConfig.load();
    }
}
