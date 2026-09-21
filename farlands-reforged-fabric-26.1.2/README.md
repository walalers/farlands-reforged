# Farlands Reforged Fabric

Fabric build for Minecraft `26.1.2`.

Tiny Fabric version of Farlands Reforged. Restores the classic Far Lands: the legacy 3D terrain noise overflows exactly as it did in Beta 1.7.3, the overflowed density decides solid-versus-air, and the surface and water follow the old rules (grass on every ledge, flooded to sea level). See the repository README for the full explanation. Includes `/farlands`, config, and the `...where am I?` advancement.

## Build

```bash
./gradlew build
python scripts/verify_artifact.py
```

## Why `PackRepositoryMixin` exists

Fabric Loader, unlike Forge and NeoForge, does **not** turn a mod's `data/` and `assets/` directories
into packs - that is Fabric API's resource loader, and this mod deliberately does not depend on Fabric
API. Without help, the `where_am_i` advancement JSON is dead weight in the jar: the server never reads
it, `server.getAdvancements().get(...)` returns null, and `FarlandsEvents` silently does nothing.
Nothing is logged and the terrain still works, so the only visible symptom is `/datapack list` showing
`vanilla` and nothing else.

`PackRepositoryMixin` adds a built-in pack to every `PackRepository`, which is what Fabric API does
internally. Two choices keep one implementation working across every version this mod targets: the pack
is built from `Pack`'s constructor with hand-written `Pack.Metadata` rather than
`Pack.readMetaAndCreate`, so no `pack.mcmeta` is needed (a stale `pack_format` silently drops the pack);
and the resources come from vanilla's own `PathPackResources.PathResourcesSupplier`, so changes to the
`Pack.ResourcesSupplier` interface are vanilla's problem - 26.3 replaced `openPrimary`/`openFull` with
`openMetadata`/`openResources` and this code did not have to change.

**To verify after a change:** `/datapack list` on a real server must list `farlandsreforged`, and a jar
rebuilt with the advancement JSON deliberately corrupted must make the server log `Couldn't parse data
file farlandsreforged:farlands/where_am_i`. Silence means the pack is not being read.
