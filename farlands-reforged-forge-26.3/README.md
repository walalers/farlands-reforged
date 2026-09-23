# Farlands Reforged — Forge 26.3

Forge build of Farlands Reforged for Minecraft 26.3. Minecraft 26.3 rewrote world generation, so this project
carries the 26.3 terrain code (the worldgen mixins, the two accessors, `FarlandsClassicNoise`,
`FarlandsNoodleSampler` and `FarlandsRegion`, identical to `farlands-reforged-fabric-26.3` and
`farlands-reforged-neoforge-26.3`) with the Forge glue from `farlands-reforged-forge-26.2`:

- Commands and the advancement check are hooked through `CommandsMixin` and `ServerPlayerMixin`.
- Config is a plain `config/farlandsreforged.properties` file (`enableFarlandsTerrain`, `enableWhereAmIAdvancement`,
  `farlandsStartCoordinate`).
- Every mixin uses `remap = false` (Minecraft 26.x ships official names, and Forge has no refmap for them), and
  the mixin config declares `JAVA_21` because Forge's bundled Mixin 0.8.7 does not know newer levels.

Target: Minecraft `26.3`, Forge `66.0.3` (ForgeGradle 7); the jar declares Forge 66 or newer.

```bash
./gradlew build
```

With the same seed, its Far Lands terrain matches the Fabric and NeoForge 26.3 builds block for block
(`tools/modded_server_test.py --probe 12550850 0`).
