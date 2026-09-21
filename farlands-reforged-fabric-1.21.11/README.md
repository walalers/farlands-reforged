# Farlands Reforged — Fabric 1.21.11

Fabric build for Minecraft `1.21.11`, the last release before the 26.x versioning.

Its sources are identical to the 26.1.2 / 26.2 projects: 1.21.11 already renamed `ResourceLocation` to
`Identifier` and already has `Commands.hasPermission(PermissionCheck)`, so nothing in the mod had to
change. Minecraft 1.21 … 1.21.10 still use the old names and live in `farlands-reforged-fabric-1.21`.

Unlike the 26.x jars, 1.21.11 Minecraft is obfuscated, so this project maps it with
`loom.officialMojangMappings()` and Loom remaps the finished jar to intermediary. It builds on **Java 21**.

## Build

```bash
./gradlew build
python scripts/verify_artifact.py
```

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
