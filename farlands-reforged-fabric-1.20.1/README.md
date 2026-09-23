# Farlands Reforged — Fabric 1.20 / 1.20.1

Fabric build for **Minecraft 1.20 and 1.20.1**. It is `farlands-reforged-fabric-1.20.4` (Java 17,
`{"item": ...}` advancement icon, plural `advancements/` folder) plus the two things that are older still:

- **No `AdvancementHolder`.** Before 1.20.2, `ServerAdvancementManager.getAdvancement(id)` returns a
  plain `Advancement`, and `PlayerAdvancements` takes that. `FarlandsEvents` uses those.
- **The oldest pack API.** `Pack.create` takes a `PackType`, `Pack.Info` holds a raw format number
  instead of a compatibility value, and `PathResourcesSupplier` does not exist yet, so
  `FarlandsModPack` passes `name -> new PathPackResources(name, root, true)`. The format number is the
  running game's own (`SharedConstants.getCurrentVersion().getPackVersion(SERVER_DATA)`), so it is never
  stale.

```bash
./gradlew build -Pminecraft_version=1.20 -Pminecraft_version_range=1.20 -Pmod_version=0.5.0+mc1.20-fabric
python scripts/verify_artifact.py
```

1.20 and 1.20.1 compile to byte-identical classes, one jar each.
