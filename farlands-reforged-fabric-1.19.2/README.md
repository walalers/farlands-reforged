# Farlands Reforged — Fabric 1.19 / 1.19.1 / 1.19.2

Fabric build for **Minecraft 1.19, 1.19.1 and 1.19.2**. It is
`farlands-reforged-fabric-1.19.4` with the oldest pack API and one missing command method:

- **Packs are read from a `java.io.File`.** There is no `PathPackResources`: vanilla has
  `FilePackResources` for a zip and `FolderPackResources` for a directory. `FarlandsModPack` points them at
  the jar Fabric loaded the mod from (`ModContainer.getOrigin()`), not at a path inside it. A jar nested in
  another mod's jar has no file of its own, and then the pack is skipped.
- **The pack is built from `Pack`'s constructor,** with `PackCompatibility.COMPATIBLE` given directly, so
  still no `pack.mcmeta`. Both readers throw rather than return null when asked for a `pack.mcmeta`
  section, though, and every resource reload asks each pack for its `filter` section, so they are
  subclassed to answer null. Without that the server logs `Failed to get filter section from pack` as an
  ERROR on each reload, harmlessly but alarmingly.
- **`PackRepository` has two constructors.** The `PackType` one builds a `Pack.PackConstructor` and
  delegates to the other, so `PackRepositoryMixin` hooks that one only. `RepositorySource.loadPacks` takes
  the pack constructor too; it reads a `pack.mcmeta` and is not used.
- **`CommandSourceStack.sendSystemMessage` only arrives in 1.19.1.** `/farlands` answers through
  `sendSuccess(message, false)`, which sends the same message to the same source.

```bash
gradle build -Pminecraft_version=1.19 -Pminecraft_version_range=1.19 -Pmod_version=0.5.0+mc1.19-fabric
python scripts/verify_artifact.py
```

1.19, 1.19.1 and 1.19.2 compile to byte-identical classes, one jar each.
