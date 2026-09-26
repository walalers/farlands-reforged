package com.shigeo.farlandsreforged;

import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.advancements.AdvancementProgress;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.neoforged.neoforge.event.TickEvent;

public final class FarlandsEvents {
    private static final ResourceLocation WHERE_AM_I_ADVANCEMENT = new ResourceLocation(FarlandsReforged.MOD_ID, "farlands/where_am_i");

    private FarlandsEvents() {}

    // PlayerTickEvent.Post only exists from NeoForge 20.5; before that it is one event with a phase.
    public static void onPlayerTick(TickEvent.PlayerTickEvent event) {
        if (event.phase != TickEvent.Phase.END) {
            return;
        }
        if (!(event.player instanceof ServerPlayer player)) {
            return;
        }
        if (player.level().isClientSide()) {
            return;
        }
        FarMan.tick(player);
        if (!FarlandsConfig.advancementEnabled()) {
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

    static boolean isInFarlands(ServerPlayer player) {
        return isInFarlands(player.getX(), player.getZ());
    }

    static boolean isInFarlands(double x, double z) {
        long threshold = FarlandsConfig.farlandsStartCoordinate();
        return Math.abs(x) >= threshold || Math.abs(z) >= threshold;
    }
}
