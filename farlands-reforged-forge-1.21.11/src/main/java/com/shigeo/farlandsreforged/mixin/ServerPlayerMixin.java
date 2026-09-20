package com.shigeo.farlandsreforged.mixin;

import com.shigeo.farlandsreforged.FarlandsEvents;
import net.minecraft.server.level.ServerPlayer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ServerPlayer.class)
public abstract class ServerPlayerMixin {
    @Inject(method = "doTick", at = @At("TAIL"))
    private void farlandsreforged$awardAdvancement(CallbackInfo ci) {
        FarlandsEvents.awardIfInFarlands((ServerPlayer) (Object) this);
    }
}
