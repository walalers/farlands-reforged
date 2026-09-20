package com.shigeo.farlandsreforged.mixin;

import com.shigeo.farlandsreforged.FarlandsConfig;
import com.shigeo.farlandsreforged.FarlandsRegion;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Aquifer;
import net.minecraft.world.level.levelgen.DensityFunction;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * Beta filled every open block below sea level with water, which is why the tunnels through the Far Lands were
 * flooded up to y=63. Modern aquifers instead treat anything below the (ordinary-height) preliminary surface as
 * underground and hand out scattered pockets of water, lava and air. Inside the Far Lands this mixin uses the
 * dimension's global fluid rule for every column, which is exactly what vanilla does for terrain that is open
 * to the sky: water up to sea level. Beta had no deep lava layer, and in the Far Lands vanilla's one (below
 * y=-54) sits directly under a flooded world, where the water/lava contact queues tens of thousands of fluid
 * ticks per few hundred chunks and stalls the server. So lava from the global picker becomes water here.
 */
@Mixin(targets = "net.minecraft.world.level.levelgen.Aquifer$NoiseBasedAquifer")
public abstract class NoiseBasedAquiferMixin {
    @Shadow @Final private Aquifer.FluidPicker globalFluidPicker;
    @Shadow private boolean shouldScheduleFluidUpdate;

    @Inject(method = "computeSubstance", at = @At("HEAD"), cancellable = true)
    private void farlandsreforged$floodToSeaLevel(DensityFunction.FunctionContext context, double density, CallbackInfoReturnable<BlockState> cir) {
        if (!FarlandsConfig.terrainEnabled()) {
            return;
        }
        int x = context.blockX();
        int z = context.blockZ();
        if (!FarlandsRegion.isInFarlands(x, z)) {
            return;
        }
        if (density > 0.0) {
            this.shouldScheduleFluidUpdate = false;
            cir.setReturnValue(null);
            return;
        }
        int y = context.blockY();
        BlockState fluid = this.globalFluidPicker.computeFluid(x, y, z).at(y);
        if (fluid.is(Blocks.LAVA)) {
            fluid = Blocks.WATER.defaultBlockState();
        }
        // Let fluid on the very first Far Lands column settle against whatever vanilla generated next to it.
        this.shouldScheduleFluidUpdate = !fluid.isAir() && FarlandsRegion.isOnFarlandsSeam(x, z);
        cir.setReturnValue(fluid);
    }
}
