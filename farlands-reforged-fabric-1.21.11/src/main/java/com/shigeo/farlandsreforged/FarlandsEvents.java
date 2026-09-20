package com.shigeo.farlandsreforged;

import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.advancements.AdvancementProgress;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;

import java.util.ArrayList;
import java.util.List;

public final class FarlandsEvents {
    private static final Identifier WHERE_AM_I_ADVANCEMENT = Identifier.fromNamespaceAndPath(FarlandsReforged.MOD_ID, "farlands/where_am_i");

    private FarlandsEvents() {}

    public static void awardIfInFarlands(ServerPlayer player) {
        if (!FarlandsConfig.advancementEnabled()) {
            return;
        }
        if (!isInFarlands(player)) {
            return;
        }

        MinecraftServer server = player.level().getServer();
        AdvancementHolder advancement = server.getAdvancements().get(WHERE_AM_I_ADVANCEMENT);
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

    private static boolean isInFarlands(ServerPlayer player) {
        long threshold = FarlandsConfig.farlandsStartCoordinate();
        return Math.abs(player.getX()) >= threshold || Math.abs(player.getZ()) >= threshold;
    }
}
