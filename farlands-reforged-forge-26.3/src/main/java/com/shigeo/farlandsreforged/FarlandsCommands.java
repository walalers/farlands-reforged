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
    private FarlandsCommands() {
    }

    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal("farlands")
            .executes(context -> showInfo(context.getSource()))
            .then(Commands.literal("set")
                .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                .then(Commands.argument("threshold", LongArgumentType.longArg(FarlandsConfig.MIN_START, FarlandsConfig.MAX_START))
                    .executes(context -> setThreshold(context.getSource(), LongArgumentType.getLong(context, "threshold")))))
            .then(Commands.literal("reset")
                .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                .executes(context -> resetThreshold(context.getSource())))
            .then(Commands.literal("farman")
                .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                .executes(context -> showFarMan(context.getSource()))
                .then(Commands.literal("on")
                    .executes(context -> setFarMan(context.getSource(), true)))
                .then(Commands.literal("off")
                    .executes(context -> setFarMan(context.getSource(), false)))
                .then(Commands.literal("summon")
                    .executes(context -> summonFarMan(context.getSource(), false)))
                .then(Commands.literal("scare")
                    .executes(context -> summonFarMan(context.getSource(), true)))));
    }

    private static int showInfo(CommandSourceStack source) {
        long threshold = FarlandsConfig.farlandsStartCoordinate();
        double x = Math.abs(source.getPosition().x());
        double z = Math.abs(source.getPosition().z());
        long distance = Math.max(0L, (long) Math.ceil(threshold - Math.max(x, z)));

        source.sendSystemMessage(Component.literal("Farlands Reforged restores classic Far Lands-style terrain generation."));
        source.sendSystemMessage(Component.literal("Classic threshold: ±12550821 blocks on X/Z."));
        source.sendSystemMessage(Component.literal("Configured advancement threshold: ±" + threshold + " blocks."));
        source.sendSystemMessage(Component.literal("Distance to configured threshold: " + distance + " blocks."));
        source.sendSystemMessage(Component.literal("Terrain enabled: " + FarlandsConfig.terrainEnabled() + "; advancement enabled: " + FarlandsConfig.advancementEnabled() + "; FarMan enabled: " + FarlandsConfig.farManEnabled() + "."));
        source.sendSystemMessage(Component.literal("Inspired by AdyTech99's Farlands Reborn. Respect to the old noise ghosts."));
        return 1;
    }

    private static int setThreshold(CommandSourceStack source, long threshold) {
        FarlandsConfig.setFarlandsStartCoordinate(threshold);
        source.sendSuccess(() -> Component.literal("Farlands advancement threshold set to ±" + threshold + " blocks."), true);
        return 1;
    }

    private static int resetThreshold(CommandSourceStack source) {
        FarlandsConfig.resetFarlandsStartCoordinate();
        source.sendSuccess(() -> Component.literal("Farlands advancement threshold reset to the classic ±12550821 blocks."), true);
        return 1;
    }

    private static int showFarMan(CommandSourceStack source) {
        source.sendSystemMessage(Component.literal("FarMan is " + (FarlandsConfig.farManEnabled() ? "on" : "off") + ". He only walks the Far Lands (past ±" + FarlandsConfig.farlandsStartCoordinate() + " blocks in the Overworld)."));
        return 1;
    }

    private static int setFarMan(CommandSourceStack source, boolean enabled) {
        FarlandsConfig.setFarManEnabled(enabled);
        source.sendSuccess(() -> Component.literal(enabled ? "FarMan is on. He is waiting in the Far Lands." : "FarMan is off."), true);
        return 1;
    }

    private static int summonFarMan(CommandSourceStack source, boolean behind) throws CommandSyntaxException {
        ServerPlayer player = source.getPlayerOrException();
        if (!FarlandsConfig.farManEnabled()) {
            source.sendFailure(Component.literal("FarMan is off. Turn him on with /farlands farman on."));
            return 0;
        }
        if (player.level().dimension() != Level.OVERWORLD || !FarlandsEvents.isInFarlands(player)) {
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
