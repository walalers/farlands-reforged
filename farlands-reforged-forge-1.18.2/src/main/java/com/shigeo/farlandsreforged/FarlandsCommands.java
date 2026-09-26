package com.shigeo.farlandsreforged;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.LongArgumentType;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.TextComponent;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.Level;

public final class FarlandsCommands {
    private FarlandsCommands() {
    }

    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal("farlands")
            .executes(context -> showInfo(context.getSource()))
            .then(Commands.literal("set")
                .requires(source -> source.hasPermission(Commands.LEVEL_GAMEMASTERS))
                .then(Commands.argument("start", LongArgumentType.longArg(FarlandsConfig.MIN_START, FarlandsConfig.MAX_START))
                    .executes(context -> setStart(context.getSource(), LongArgumentType.getLong(context, "start"), true, true)))
                .then(Commands.literal("x")
                    .then(Commands.argument("start", LongArgumentType.longArg(FarlandsConfig.MIN_START, FarlandsConfig.MAX_START))
                        .executes(context -> setStart(context.getSource(), LongArgumentType.getLong(context, "start"), true, false))))
                .then(Commands.literal("z")
                    .then(Commands.argument("start", LongArgumentType.longArg(FarlandsConfig.MIN_START, FarlandsConfig.MAX_START))
                        .executes(context -> setStart(context.getSource(), LongArgumentType.getLong(context, "start"), false, true)))))
            .then(Commands.literal("reset")
                .requires(source -> source.hasPermission(Commands.LEVEL_GAMEMASTERS))
                .executes(context -> resetStart(context.getSource())))
            .then(Commands.literal("farman")
                .requires(source -> source.hasPermission(Commands.LEVEL_GAMEMASTERS))
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
        int startX = FarlandsRegion.startX();
        int startZ = FarlandsRegion.startZ();
        double x = Math.abs(source.getPosition().x());
        double z = Math.abs(source.getPosition().z());
        long distance = Math.max(0L, (long) Math.ceil(Math.min(startX - x, startZ - z)));

        tell(source, new TextComponent("Farlands Reforged restores classic Far Lands-style terrain generation."));
        tell(source, new TextComponent("The Far Lands start at ±" + startX + " on X and ±" + startZ + " on Z (classic: ±" + FarlandsConfig.CLASSIC_FARLANDS_START + ")."));
        tell(source, new TextComponent("Distance to the Far Lands: " + distance + " blocks."));
        tell(source, new TextComponent("Terrain enabled: " + FarlandsConfig.terrainEnabled() + "; advancement enabled: " + FarlandsConfig.advancementEnabled() + "; FarMan enabled: " + FarlandsConfig.farManEnabled() + "."));
        tell(source, new TextComponent("Inspired by AdyTech99's Farlands Reborn. Respect to the old noise ghosts."));
        return 1;
    }

    /**
     * CommandSourceStack.sendSystemMessage only arrives in 1.19.1. sendSuccess without broadcasting is the
     * same message to the same source on 1.18.2 and 1.19.x, except that it respects a silenced source.
     */
    private static void tell(CommandSourceStack source, Component message) {
        source.sendSuccess(message, false);
    }

    private static int setStart(CommandSourceStack source, long start, boolean onX, boolean onZ) {
        FarlandsConfig.setFarlandsStart(onX ? start : FarlandsConfig.farlandsStartX(), onZ ? start : FarlandsConfig.farlandsStartZ());
        source.sendSuccess(new TextComponent("The Far Lands now start at ±" + FarlandsRegion.startX() + " on X and ±" + FarlandsRegion.startZ() + " on Z. Chunks that already exist keep their terrain."), true);
        return 1;
    }

    private static int resetStart(CommandSourceStack source) {
        FarlandsConfig.setFarlandsStart(FarlandsConfig.CLASSIC_FARLANDS_START, FarlandsConfig.CLASSIC_FARLANDS_START);
        source.sendSuccess(new TextComponent("The Far Lands start at the classic ±" + FarlandsConfig.CLASSIC_FARLANDS_START + " again. Chunks that already exist keep their terrain."), true);
        return 1;
    }

    private static int showFarMan(CommandSourceStack source) {
        tell(source, new TextComponent("FarMan is " + (FarlandsConfig.farManEnabled() ? "on" : "off") + ". He only walks the Far Lands (past ±" + FarlandsRegion.startX() + " on X or ±" + FarlandsRegion.startZ() + " on Z, in the Overworld)."));
        return 1;
    }

    private static int setFarMan(CommandSourceStack source, boolean enabled) {
        FarlandsConfig.setFarManEnabled(enabled);
        source.sendSuccess(new TextComponent(enabled ? "FarMan is on. He is waiting in the Far Lands." : "FarMan is off."), true);
        return 1;
    }

    private static int summonFarMan(CommandSourceStack source, boolean behind) throws CommandSyntaxException {
        ServerPlayer player = source.getPlayerOrException();
        if (!FarlandsConfig.farManEnabled()) {
            source.sendFailure(new TextComponent("FarMan is off. Turn him on with /farlands farman on."));
            return 0;
        }
        if (player.getLevel().dimension() != Level.OVERWORLD || !FarlandsEvents.isInFarlands(player)) {
            source.sendFailure(new TextComponent("FarMan only walks the Far Lands."));
            return 0;
        }
        if (!(behind ? FarMan.scare(player) : FarMan.summon(player))) {
            source.sendFailure(new TextComponent("FarMan found nowhere to stand. Try again somewhere more open."));
            return 0;
        }
        return 1;
    }
}
