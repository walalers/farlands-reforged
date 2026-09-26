package com.shigeo.farlandsreforged;

import net.minecraft.advancements.Advancement;
import net.minecraft.advancements.AdvancementProgress;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;

import java.util.ArrayList;
import java.util.List;

public final class FarlandsEvents {
    private static final ResourceLocation WHERE_AM_I_ADVANCEMENT = new ResourceLocation(FarlandsReforged.MOD_ID, "farlands/where_am_i");

    private FarlandsEvents() {}

    public static void awardIfInFarlands(ServerPlayer player) {
        if (!FarlandsConfig.advancementEnabled()) {
            return;
        }
        if (!isInFarlands(player)) {
            return;
        }

        MinecraftServer server = player.level().getServer();
        // Before 1.20.2 there is no AdvancementHolder, and the lookup is getAdvancement.
        Advancement advancement = server.getAdvancements().getAdvancement(WHERE_AM_I_ADVANCEMENT);
        if (advancement == null) {
            return;
        }

        AdvancementProgress progress = player.getAdvancements().getOrStartProgress(advancement);
        if (progress.isDone()) {
            return;
        }

        List<String> remaining = new ArrayList<>();
        progress.getRemainingCriteria().forEach(remaining::add);
        for (String criterion : remaining) {
            player.getAdvancements().award(advancement, criterion);
        }
    }

    static boolean isInFarlands(ServerPlayer player) {
        return isInFarlands(player.getX(), player.getZ());
    }

    static boolean isInFarlands(double x, double z) {
        long threshold = FarlandsConfig.farlandsStartCoordinate();
        return Math.abs(x) >= threshold || Math.abs(z) >= threshold;
    }
}
