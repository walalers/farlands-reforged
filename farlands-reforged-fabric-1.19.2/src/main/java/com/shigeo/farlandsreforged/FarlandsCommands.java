package com.shigeo.farlandsreforged;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.LongArgumentType;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;

public final class FarlandsCommands {
    private FarlandsCommands() {}

    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal("farlands")
                .executes(commandContext -> showInfo(commandContext.getSource()))
                .then(Commands.literal("set")
                        .requires(source -> source.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .then(Commands.argument("threshold", LongArgumentType.longArg(FarlandsConfig.MIN_START, FarlandsConfig.MAX_START))
                                .executes(commandContext -> setThreshold(commandContext.getSource(), LongArgumentType.getLong(commandContext, "threshold")))))
                .then(Commands.literal("reset")
                        .requires(source -> source.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .executes(commandContext -> resetThreshold(commandContext.getSource())))
                .then(Commands.literal("farman")
                        .requires(source -> source.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .executes(commandContext -> showFarMan(commandContext.getSource()))
                        .then(Commands.literal("on")
                                .executes(commandContext -> setFarMan(commandContext.getSource(), true)))
                        .then(Commands.literal("off")
                                .executes(commandContext -> setFarMan(commandContext.getSource(), false)))
                        .then(Commands.literal("summon")
                                .executes(commandContext -> summonFarMan(commandContext.getSource(), false)))
                        .then(Commands.literal("scare")
                                .executes(commandContext -> summonFarMan(commandContext.getSource(), true)))));
    }

    private static int showInfo(CommandSourceStack source) {
        long threshold = FarlandsConfig.farlandsStartCoordinate();
        double x = Math.abs(source.getPosition().x());
        double z = Math.abs(source.getPosition().z());
        long distance = Math.max(0L, (long) Math.ceil(threshold - Math.max(x, z)));

        tell(source, Component.literal("Farlands Reforged restores classic Far Lands-style terrain generation."));
        tell(source, Component.literal("Classic threshold: ±" + FarlandsConfig.CLASSIC_FARLANDS_START + " blocks on X/Z."));
        tell(source, Component.literal("Configured advancement threshold: ±" + threshold + " blocks."));
        tell(source, Component.literal("Distance to configured threshold: " + distance + " blocks."));
        tell(source, Component.literal("Terrain enabled: " + FarlandsConfig.terrainEnabled() + "; advancement enabled: " + FarlandsConfig.advancementEnabled() + "; FarMan enabled: " + FarlandsConfig.farManEnabled() + "."));
        tell(source, Component.literal("Inspired by AdyTech99's Farlands Reborn. Respect to the old noise ghosts."));
        return 1;
    }

    /**
     * CommandSourceStack.sendSystemMessage only arrives in 1.19.1. sendSuccess without broadcasting is the
     * same message to the same source on 1.19 - 1.19.2, except that it respects a silenced source.
     */
    private static void tell(CommandSourceStack source, Component message) {
        source.sendSuccess(message, false);
    }

    private static int setThreshold(CommandSourceStack source, long threshold) {
        FarlandsConfig.setFarlandsStartCoordinate(threshold);
        source.sendSuccess(Component.literal("Farlands advancement threshold set to ±" + threshold + " blocks. Terrain generation remains classic/authentic."), true);
        return 1;
    }

    private static int resetThreshold(CommandSourceStack source) {
        FarlandsConfig.resetFarlandsStartCoordinate();
        source.sendSuccess(Component.literal("Farlands advancement threshold reset to the classic ±" + FarlandsConfig.CLASSIC_FARLANDS_START + " blocks."), true);
        return 1;
    }

    private static int showFarMan(CommandSourceStack source) {
        tell(source, Component.literal("FarMan is " + (FarlandsConfig.farManEnabled() ? "on" : "off") + ". He only walks the Far Lands (past ±" + FarlandsConfig.farlandsStartCoordinate() + " blocks in the Overworld)."));
        return 1;
    }

    private static int setFarMan(CommandSourceStack source, boolean enabled) {
        FarlandsConfig.setFarManEnabled(enabled);
        source.sendSuccess(Component.literal(enabled ? "FarMan is on. He is waiting in the Far Lands." : "FarMan is off."), true);
        return 1;
    }

    private static int summonFarMan(CommandSourceStack source, boolean behind) throws CommandSyntaxException {
        ServerPlayer player = source.getPlayerOrException();
        if (!FarlandsConfig.farManEnabled()) {
            source.sendFailure(Component.literal("FarMan is off. Turn him on with /farlands farman on."));
            return 0;
        }
        if (player.getLevel().dimension() != Level.OVERWORLD || !FarlandsEvents.isInFarlands(player)) {
            source.sendFailure(Component.literal("FarMan only walks the Far Lands."));
            return 0;
        }
        if (!(behind ? FarMan.scare(player) : FarMan.summon(player))) {
            source.sendFailure(Component.literal("FarMan found nowhere to stand. Try again somewhere more open."));
            return 0;
        }
        return 1;
    }
}
