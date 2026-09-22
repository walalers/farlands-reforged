# Farlands Reforged — Fabric 1.18.2

Fabric build for **Minecraft 1.18.2**, the oldest this mod supports. It is `farlands-reforged-fabric-1.19.2`
(Java 17, the `File`-based built-in pack, `sendSuccess` for every `/farlands` line) with three differences:

- **`TextComponent`, not `Component.literal`.** `literal` arrives in 1.19.
- **`Commands` has no `CommandBuildContext`.** Its constructor takes the command selection alone, and
  `CommandsMixin`'s handler matches that.
- **No `DensityFunction.NoiseHolder`.** It arrives in 1.19; on 1.18.2 `DensityFunctions$Noise` holds the
  noise key directly as `Holder<NormalNoise.NoiseParameters> noiseData`, so `NoodleCavesMixin` shadows that
  field and tests `noiseData.is(Noises.NOODLE)`.

1.18.2 is the first version with the density-function world generator the Far Lands mechanisms hook into.
Minecraft 1.18 and 1.18.1 generate terrain through `NoiseSampler` with the caves written into the code, so
there is nothing for those mixins to attach to, and this mod does not support them.

```bash
gradle build
python scripts/verify_artifact.py
```
