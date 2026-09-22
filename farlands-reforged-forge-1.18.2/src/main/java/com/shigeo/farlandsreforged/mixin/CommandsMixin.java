package com.shigeo.farlandsreforged.mixin;

import com.mojang.brigadier.CommandDispatcher;
import com.shigeo.farlandsreforged.FarlandsCommands;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(Commands.class)
/** 1.18.2 has no CommandBuildContext: the constructor takes the command selection alone. */
public abstract class CommandsMixin {
    @Shadow @Final private CommandDispatcher<CommandSourceStack> dispatcher;

    @Inject(method = "<init>", at = @At("TAIL"))
    private void farlandsreforged$registerCommand(Commands.CommandSelection environment, CallbackInfo ci) {
        FarlandsCommands.register(this.dispatcher);
    }
}
