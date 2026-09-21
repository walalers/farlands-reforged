# Farlands Reforged — Forge 1.21 … 1.21.10

Forge build for the older half of the Minecraft 1.21 family (1.21.2 excluded — Forge never shipped one).

Same terrain code as every other project: `FarlandsRegion`
plus the seven worldgen mixins, with `CommandsMixin` and `ServerPlayerMixin` for the loader glue, and a
plain `config/farlandsreforged.properties` file.

**Forge 51-60 runs on Mojang's official names, not SRG.** An earlier version of this project assumed the
opposite — it reobfuscated the jar into SRG and generated a mixin refmap — and the result could not load
at all: the server died during bootstrap with *"@Shadow field f_208787_ was not located in the target
class DensityFunctions$Noise. No refMap loaded."* Disassembling an installed `forge-1.21-51.0.33` server
settles it: `DensityFunctions$Noise` has `noise` / `compute` / `xzScale`, and there is no SRG-named jar
anywhere in the install. So this project now does what `farlands-reforged-forge-1.21.11` and the 26.x
project do — no `reobf`, no refmap, `remap = false` on every `@Mixin`.

Do **not** infer the naming from the userdev `config.json`: it lists `universal-srg` for every version in
the family, which is a build artifact and not a statement about runtime names. Only the installed server
answers the question.

The one thing that really is different from `farlands-reforged-forge-1.21.11`:

- **ForgeGradle 6, not 7.** That means the FG6 spelling of the run configurations, and Gradle 8 —
  which cannot run on Java 25, so this project's Gradle itself needs **Java 21**:

```bash
JAVA_HOME=/path/to/jdk-21 ./gradlew build
python scripts/verify_artifact.py
```

Two more things differ from the 1.21.11 project, both found by running a real Forge server:

- **The mod class needs a no-arg constructor.** Forge 51 calls `getDeclaredConstructor()` with no
  arguments at all, so the `FMLJavaModLoadingContext` constructor used by the 1.21.11 project is never
  found and loading fails with `NoSuchMethodException`. Forge 52 and up ask for the context constructor
  first but fall back to the no-arg one, so a single no-arg constructor covers 1.21 through 1.21.10.
- **`pack.mcmeta` uses the old `pack_format` schema.** The `min_format` / `max_format` keys the 26.x and
  1.21.11 projects use do not exist before 1.21.11; on 1.21 the metadata fails to parse, the mod's data
  pack is silently dropped, and the "...where am I?" advancement never registers. `supported_formats`
  spans 34-99 here because one file has to satisfy both the resource-pack and data-pack checks across
  the whole range (1.21 is resource 34 / data 48; 1.21.10 is far higher).

The sources also carry the two 1.21-family differences: `ResourceLocation` instead of `Identifier`, and
`source.hasPermission(Commands.LEVEL_GAMEMASTERS)` instead of `Commands.hasPermission(...)`. Minecraft
1.21.11 uses the newer names, and a different build system entirely, so it is built from
`farlands-reforged-forge-1.21.11`.

## Versions

`gradle.properties` targets 1.21 / Forge 51.0.0. The rest are real builds of this project:

```bash
JAVA_HOME=/path/to/jdk-21 ./gradlew build -Pminecraft_version=1.21.4 \
  -Pminecraft_version_range='[1.21.4]' -Pforge_version=54.1.18 -Pforge_loader_major=54 \
  -Pmod_version=0.4.0+mc1.21.4-forge
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
