# Farlands Reforged — Forge

Forge build of Farlands Reforged. Same terrain code as the Fabric and NeoForge projects (the seven worldgen mixins
and `FarlandsRegion`); only the loader glue differs:

- Commands and the advancement check are hooked through `CommandsMixin` and `ServerPlayerMixin`.
- Config is a plain `config/farlandsreforged.properties` file (`enableFarlandsTerrain`, `enableWhereAmIAdvancement`,
  `farlandsStartCoordinate`).
- Every mixin uses `remap = false` (Minecraft 26.x ships official names, and Forge has no refmap for them), and
  the mixin config declares `JAVA_21` because Forge's bundled Mixin 0.8.7 does not know newer levels.

Target: Minecraft `26.2`, Forge `65.0.0` (ForgeGradle 7). The other Minecraft versions are real builds of this
project with the versions passed on the command line:

```bash
./gradlew build -Pminecraft_version=26.1.2 -Pforge_version=64.0.10 -Pforge_loader_major=64 \
  "-Pminecraft_version_range=[26.1.2,26.2)" -Pmod_version=0.3.1+mc26.1.2-forge
```

| Minecraft | forge_version | forge_loader_major |
|-----------|---------------|--------------------|
| 26.2      | 65.0.0        | 65                 |
| 26.1.2    | 64.0.10       | 64                 |
| 26.1.1    | 63.0.2        | 63                 |
| 26.1      | 62.0.9        | 62                 |
