# Farlands Reforged — Fabric 1.21 … 1.21.10

Fabric build for the older half of the Minecraft 1.21 family: **1.21, 1.21.1, 1.21.2, 1.21.3, 1.21.4,
1.21.5, 1.21.6, 1.21.7, 1.21.8, 1.21.9 and 1.21.10**. Minecraft 1.21.11 lives in
`farlands-reforged-fabric-1.21.11` instead, because it renamed `ResourceLocation` to `Identifier` and
turned command permission levels into `PermissionCheck` objects.

Same terrain code as every other project (`FarlandsRegion` plus the seven worldgen mixins). Two things
differ from the 26.x sources, both outside the Far Lands mechanisms themselves:

- `FarlandsEvents` uses `ResourceLocation`, not `Identifier`.
- `FarlandsCommands` guards `set`/`reset` with `source -> source.hasPermission(Commands.LEVEL_GAMEMASTERS)`,
  because `Commands.hasPermission(PermissionCheck)` does not exist yet.

Unlike the 26.x jars, 1.21.x Minecraft is obfuscated, so this project maps it with
`loom.officialMojangMappings()` and Loom remaps the finished jar to intermediary. It builds on **Java 21**.

## Build

`gradle.properties` targets 1.21. Every other version is a real build of this same project with the
version passed on the command line:

```bash
./gradlew build -Pminecraft_version=1.21.4 \
  "-Pminecraft_version_range=>=1.21.4 <1.21.5" \
  -Pmod_version=0.3.1+mc1.21.4-fabric
python scripts/verify_artifact.py
```

| Minecraft | minecraft_version_range |
|-----------|-------------------------|
| 1.21      | `>=1.21 <1.21.2`        |
| 1.21.1    | `>=1.21 <1.21.2`        |
| 1.21.2    | `>=1.21.2 <1.21.4`      |
| 1.21.3    | `>=1.21.2 <1.21.4`      |
| 1.21.4    | `>=1.21.4 <1.21.5`      |
| 1.21.5    | `>=1.21.5 <1.21.6`      |
| 1.21.6    | `>=1.21.6 <1.21.9`      |
| 1.21.7    | `>=1.21.6 <1.21.9`      |
| 1.21.8    | `>=1.21.6 <1.21.9`      |
| 1.21.9    | `>=1.21.9 <1.21.11`     |
| 1.21.10   | `>=1.21.9 <1.21.11`     |

The ranges group versions whose mixin targets are byte-for-byte compatible, which is what
`tools/check_targets.py` and `tools/verify_injections.py` in the repository root check.
