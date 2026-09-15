package com.shigeo.farlandsreforged;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.LongArgumentType;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;

public final class FarlandsCommands {
    private FarlandsCommands() {}

    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal("farlands")
                .executes(commandContext -> showInfo(commandContext.getSource()))
                .then(Commands.literal("set")
                        .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .then(Commands.argument("threshold", LongArgumentType.longArg(FarlandsConfig.MIN_START, FarlandsConfig.MAX_START))
                                .executes(commandContext -> setThreshold(commandContext.getSource(), LongArgumentType.getLong(commandContext, "threshold")))))
                .then(Commands.literal("reset")
                        .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .executes(commandContext -> resetThreshold(commandContext.getSource()))));
    }

    private static int showInfo(CommandSourceStack source) {
        long threshold = FarlandsConfig.farlandsStartCoordinate();
        double x = Math.abs(source.getPosition().x());
        double z = Math.abs(source.getPosition().z());
        long distance = Math.max(0L, (long) Math.ceil(threshold - Math.max(x, z)));

        source.sendSystemMessage(Component.literal("Farlands Reforged restores classic Far Lands-style terrain generation."));
        source.sendSystemMessage(Component.literal("Classic threshold: ±" + FarlandsConfig.CLASSIC_FARLANDS_START + " blocks on X/Z."));
        source.sendSystemMessage(Component.literal("Configured advancement threshold: ±" + threshold + " blocks."));
        source.sendSystemMessage(Component.literal("Distance to configured threshold: " + distance + " blocks."));
        source.sendSystemMessage(Component.literal("Terrain enabled: " + FarlandsConfig.terrainEnabled() + "; advancement enabled: " + FarlandsConfig.advancementEnabled() + "."));
        source.sendSystemMessage(Component.literal("Inspired by AdyTech99's Farlands Reborn. Respect to the old noise ghosts."));
        return 1;
    }

    private static int setThreshold(CommandSourceStack source, long threshold) {
        FarlandsConfig.setFarlandsStartCoordinate(threshold);
        source.sendSuccess(() -> Component.literal("Farlands advancement threshold set to ±" + threshold + " blocks. Terrain generation remains classic/authentic."), true);
        return 1;
    }

    private static int resetThreshold(CommandSourceStack source) {
        FarlandsConfig.resetFarlandsStartCoordinate();
        source.sendSuccess(() -> Component.literal("Farlands advancement threshold reset to the classic ±" + FarlandsConfig.CLASSIC_FARLANDS_START + " blocks."), true);
        return 1;
    }
}
