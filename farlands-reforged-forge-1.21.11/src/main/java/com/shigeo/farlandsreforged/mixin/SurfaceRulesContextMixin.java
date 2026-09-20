package com.shigeo.farlandsreforged.mixin;

import com.shigeo.farlandsreforged.FarlandsConfig;
import com.shigeo.farlandsreforged.FarlandsRegion;
import net.minecraft.world.level.levelgen.WorldGenerationContext;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Beta's surface pass dressed every stone floor that had air above it: grass on the top of the Far Lands and on
 * every ledge above sea level, dirt on the flooded ledges below. Modern surface rules only run near the
 * "preliminary surface" (which ignores the 3D noise entirely, so inside the Far Lands it points at ordinary
 * terrain height). Treating every Far Lands column as above that surface restores the grassy, tree-covered
 * top and the dirt-and-grass ledges inside the walls.
 *
 * <p>The level returned is the bottom of the world rather than an arbitrary "minus infinity": the frozen-ocean
 * iceberg pass walks every column down to this level, so it must stay a real build height.
 */
@Mixin(targets = "net.minecraft.world.level.levelgen.SurfaceRules$Context", remap = false)
public abstract class SurfaceRulesContextMixin {
    @Shadow @Final private WorldGenerationContext context;
    @Shadow private int blockX;
    @Shadow private int blockZ;

    @Inject(method = "getMinSurfaceLevel", at = @At("HEAD"), cancellable = true)
    private void farlandsreforged$dressEveryFarlandsLedge(CallbackInfoReturnable<Integer> cir) {
        if (FarlandsConfig.terrainEnabled() && FarlandsRegion.isInFarlands(this.blockX, this.blockZ)) {
            cir.setReturnValue(this.context.getMinGenY());
        }
    }
}
