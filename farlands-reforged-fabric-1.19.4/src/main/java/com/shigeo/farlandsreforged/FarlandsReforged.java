package com.shigeo.farlandsreforged;

import net.fabricmc.api.ModInitializer;

public final class FarlandsReforged implements ModInitializer {
    public static final String MOD_ID = "farlandsreforged";

    @Override
    public void onInitialize() {
        FarlandsConfig.load();
    }
}
