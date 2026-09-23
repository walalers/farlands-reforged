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
./gradlew build -Pminecraft_version=1.21.4 -Pminecraft_version_range=1.21.4 \
  -Pmod_version=0.5.0+mc1.21.4-fabric
python scripts/verify_artifact.py
```

Each version gets its own build and its own jar. That is not just caution: Loom remaps the finished jar
to intermediary, and while every mixin target in this family keeps the same intermediary name, one
ordinary call does not. From 1.21.6 on, `ServerPlayer` overrides `level()` covariantly to return
`ServerLevel` instead of `Level`, so `FarlandsEvents` compiles to a different call depending on the
version it was built against, even though its source never changes. The break is one-directional — the
inherited `Level level()` still exists on the newer versions — which is exactly the kind of thing that
looks fine until somebody runs the wrong jar. `tools/compare_jars.py` in the repository root is what
catches it: it hashes the compiled classes and groups the jars that really are interchangeable.

## Why `PackRepositoryMixin` exists

Fabric Loader, unlike Forge and NeoForge, does **not** turn a mod's `data/` and `assets/` directories
into packs - that is Fabric API's resource loader, and this mod deliberately does not depend on Fabric
API. Without help, `data/farlandsreforged/advancement/farlands/where_am_i.json` is dead weight in the
jar: the server never reads it, `server.getAdvancements().get(...)` returns null, and `FarlandsEvents`
silently does nothing. Nothing is logged, the terrain still works perfectly, and the only visible symptom
is that `/datapack list` shows `vanilla` and nothing else.

`PackRepositoryMixin` adds a built-in pack to every `PackRepository`, which is what Fabric API does
internally. The pack is assembled from `Pack`'s constructor with hand-written `Pack.Metadata` rather than
`Pack.readMetaAndCreate`, so no `pack.mcmeta` is needed - deliberately, because `pack_format` numbers
change nearly every release and a stale one silently drops the pack instead of failing loudly.

Every type it touches - `PackRepository(RepositorySource...)`, `RepositorySource.loadPacks`, `Pack`,
`Pack.Metadata`, `PackLocationInfo`, `PackSelectionConfig`, `PathPackResources` - is identical across
1.21 through 1.21.11, checked with `javap` against the Mojang-mapped jar for each version.

**To verify it after a change:** `/datapack list` on a real server must list `farlandsreforged`, and
rebuilding the jar with the advancement JSON deliberately corrupted must make the server log
`Couldn't parse data file farlandsreforged:farlands/where_am_i`. Silence there means the pack is not
being read.
