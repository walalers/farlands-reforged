package com.shigeo.farlandsreforged;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.LongArgumentType;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;

public final class FarlandsCommands {
    private FarlandsCommands() {
    }

    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal("farlands")
            .executes(context -> showInfo(context.getSource()))
            .then(Commands.literal("set")
                .requires(source -> source.hasPermission(Commands.LEVEL_GAMEMASTERS))
                .then(Commands.argument("threshold", LongArgumentType.longArg(FarlandsConfig.MIN_START, FarlandsConfig.MAX_START))
                    .executes(context -> setThreshold(context.getSource(), LongArgumentType.getLong(context, "threshold")))))
            .then(Commands.literal("reset")
                .requires(source -> source.hasPermission(Commands.LEVEL_GAMEMASTERS))
                .executes(context -> resetThreshold(context.getSource()))));
    }

    private static int showInfo(CommandSourceStack source) {
        long threshold = FarlandsConfig.farlandsStartCoordinate();
        double x = Math.abs(source.getPosition().x());
        double z = Math.abs(source.getPosition().z());
        long distance = Math.max(0L, (long) Math.ceil(threshold - Math.max(x, z)));

        tell(source, Component.literal("Farlands Reforged restores classic Far Lands-style terrain generation."));
        tell(source, Component.literal("Classic threshold: ±12550821 blocks on X/Z."));
        tell(source, Component.literal("Configured advancement threshold: ±" + threshold + " blocks."));
        tell(source, Component.literal("Distance to configured threshold: " + distance + " blocks."));
        tell(source, Component.literal("Terrain enabled: " + FarlandsConfig.terrainEnabled() + "; advancement enabled: " + FarlandsConfig.advancementEnabled() + "."));
        tell(source, Component.literal("Inspired by AdyTech99's Farlands Reborn. Respect to the old noise ghosts."));
        return 1;
    }

    /**
     * CommandSourceStack.sendSystemMessage only arrives in 1.19.1. sendSuccess without broadcasting is the
     * same message to the same source on every 1.19.x, except that it respects a silenced source.
     */
    private static void tell(CommandSourceStack source, Component message) {
        source.sendSuccess(message, false);
    }

    private static int setThreshold(CommandSourceStack source, long threshold) {
        FarlandsConfig.setFarlandsStartCoordinate(threshold);
        source.sendSuccess(Component.literal("Farlands advancement threshold set to ±" + threshold + " blocks."), true);
        return 1;
    }

    private static int resetThreshold(CommandSourceStack source) {
        FarlandsConfig.resetFarlandsStartCoordinate();
        source.sendSuccess(Component.literal("Farlands advancement threshold reset to the classic ±12550821 blocks."), true);
        return 1;
    }
}
