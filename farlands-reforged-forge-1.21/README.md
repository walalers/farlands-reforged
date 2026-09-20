# Farlands Reforged — Forge 1.21 … 1.21.11

Forge build for the Minecraft 1.21 family. Same terrain code as every other project: `FarlandsRegion`
plus the seven worldgen mixins, with `CommandsMixin` and `ServerPlayerMixin` for the loader glue, and a
plain `config/farlandsreforged.properties` file.

**This project is not a copy of `farlands-reforged-forge-26.2` with the versions swapped**, for two
reasons:

- **Forge runs on SRG names here.** Its userdev `config.json` ships a `universal-srg` jar for every
  version from 1.21 to 1.21.11, where Minecraft 26.x ships official names. So the 26.x project's
  `@Mixin(..., remap = false)` cannot be reused: the mixins are remapped normally and the
  `org.spongepowered.mixin` plugin generates the refmap that lets them find their targets at runtime.
- **ForgeGradle 6, not 7.** That means the FG6 spelling of the run configurations, and Gradle 8 —
  which cannot run on Java 25, so this project's Gradle itself needs **Java 21**:

```bash
JAVA_HOME=/path/to/jdk-21 ./gradlew build
python scripts/verify_artifact.py
```

The sources also carry the two 1.21-family differences: `ResourceLocation` instead of `Identifier`, and
`source.hasPermission(Commands.LEVEL_GAMEMASTERS)` instead of `Commands.hasPermission(...)`. Minecraft
1.21.11 uses the newer names, so it is built from `farlands-reforged-forge-1.21.11`.

## Versions

`gradle.properties` targets 1.21 / Forge 51.0.0. The rest are real builds of this project:

```bash
JAVA_HOME=/path/to/jdk-21 ./gradlew build -Pminecraft_version=1.21.4 \
  -Pminecraft_version_range='[1.21.4]' -Pforge_version=54.1.18 -Pforge_loader_major=54 \
  -Pmod_version=0.3.1+mc1.21.4-forge
```

| Minecraft | forge_version | forge_loader_major |
|-----------|---------------|--------------------|
| 1.21      | 51.0.0        | 51                 |
| 1.21.1    | 52.1.16       | 52                 |
| 1.21.2    | —             | Forge never shipped one |
| 1.21.3    | 53.1.12       | 53                 |
| 1.21.4    | 54.1.18       | 54                 |
| 1.21.5    | 55.1.13       | 55                 |
| 1.21.6    | 56.0.0        | 56                 |
| 1.21.7    | 57.0.0        | 57                 |
| 1.21.8    | 58.1.22       | 58                 |
| 1.21.9    | 59.0.5        | 59                 |
| 1.21.10   | 60.1.15       | 60                 |

## Why every version needs its own jar

`tools/compare_jars.py` puts these ten jars in two groups, splitting at 1.21.6 — the same place Fabric and
NeoForge split, but for two reasons rather than one:

- `ServerPlayer.level()` becomes covariant there and returns `ServerLevel`, which changes `FarlandsEvents`.
- `CommandSourceStack.hasPermission(int)` changes SRG name from `m_6761_` to `m_81369_`, which changes
  `FarlandsCommands`.

That second one is Forge-only and worth remembering: `reobfJar` bakes version-specific SRG ids into the jar,
where Fabric's intermediary names are designed to stay stable across versions. A Forge jar is tied to the
version it was built against more tightly than a Fabric one, so do not widen `minecraft_version_range` here
on the assumption that two releases behave the same.
