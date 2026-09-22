# Farlands Reforged — Forge 1.18.2

Forge build for **Minecraft 1.18.2 (Forge 40)**. It is `farlands-reforged-forge-1.19.4` (SRG at runtime,
refmap and reobf, Mixin 0.8.5, Java 17, the version's own formats in `pack.mcmeta`) with the three 1.18.2
differences described in `farlands-reforged-fabric-1.18.2`: `TextComponent` instead of `Component.literal`,
a `Commands` constructor without `CommandBuildContext`, and `NoodleCavesMixin` shadowing
`DensityFunctions$Noise.noiseData` because `DensityFunction.NoiseHolder` does not exist yet.

`pack.mcmeta` is resource format 8 / data format 9. Every Forge 1.18.2 build, 40.0.0 through 40.3.12,
bundles Mixin 0.8.5.

```bash
JAVA_HOME=/path/to/jdk-21 ./gradlew build
python scripts/verify_artifact.py
```
