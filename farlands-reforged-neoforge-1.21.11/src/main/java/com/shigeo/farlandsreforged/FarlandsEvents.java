package com.shigeo.farlandsreforged;

import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.advancements.AdvancementProgress;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.event.tick.PlayerTickEvent;

public final class FarlandsEvents {
    private static final Identifier WHERE_AM_I_ADVANCEMENT = Identifier.fromNamespaceAndPath(FarlandsReforged.MOD_ID, "farlands/where_am_i");

    private FarlandsEvents() {}

    public static void onPlayerTick(PlayerTickEvent.Post event) {
        if (!FarlandsConfig.advancementEnabled()) {
            return;
        }
        if (!(event.getEntity() instanceof ServerPlayer player)) {
            return;
        }
        if (player.level().isClientSide()) {
            return;
        }
        if (!isInFarlands(player)) {
            return;
        }

        AdvancementHolder advancement = player.level().getServer().getAdvancements().get(WHERE_AM_I_ADVANCEMENT);
        if (advancement == null) {
            return;
        }

        AdvancementProgress progress = player.getAdvancements().getOrStartProgress(advancement);
        if (progress.isDone()) {
            return;
        }

        for (String criterion : progress.getRemainingCriteria()) {
            player.getAdvancements().award(advancement, criterion);
        }
    }

    private static boolean isInFarlands(ServerPlayer player) {
        long threshold = FarlandsConfig.farlandsStartCoordinate();
        return Math.abs(player.getX()) >= threshold || Math.abs(player.getZ()) >= threshold;
    }
}
