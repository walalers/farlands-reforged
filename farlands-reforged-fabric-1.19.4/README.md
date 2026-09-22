# Farlands Reforged — Fabric 1.19.3 / 1.19.4

Fabric build for **Minecraft 1.19.3 and 1.19.4**. It is `farlands-reforged-fabric-1.20.1` (Java 17,
`{"item": ...}` advancement icon, plural `advancements/` folder, `getAdvancement` lookup, the same
`Pack.create` / `Pack.Info` / `PathPackResources` pack API) with three differences, none in the Far Lands
mechanisms:

- **No `Entity.level()`.** It arrived in 1.20. `FarlandsEvents` reaches the server through
  `ServerPlayer.server`, a public field in every 1.19.x.
- **`sendSuccess` takes a `Component`,** not a `Supplier<Component>` (that changed in 1.20).
- **The pack format is `SharedConstants.DATA_PACK_FORMAT`.** `getCurrentVersion().getPackVersion(...)`
  takes Mojang's old `com.mojang.bridge.game.PackType` on 1.19.3 and the game's own `PackType` on 1.19.4,
  so no one call compiles for both. The constant exists in both, and the compiler inlines it: each build
  carries its own version's format (10 on 1.19.3, 12 on 1.19.4), and every version gets its own build.

```bash
gradle build -Pminecraft_version=1.19.3 -Pminecraft_version_range=1.19.3 -Pmod_version=0.4.0+mc1.19.3-fabric
python scripts/verify_artifact.py
```

The two jars differ in `FarlandsModPack` alone, in that inlined number.
