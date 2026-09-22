# Farlands Reforged — Fabric 1.20.2 … 1.20.4

Fabric build for **Minecraft 1.20.2, 1.20.3 and 1.20.4**. It is a copy of `farlands-reforged-fabric-1.20.6`.
The Far Lands mixins are unchanged: every target, `@Shadow` field and `@Redirect` call site is identical
from 1.20 to 1.20.6. The differences:

- **Java 17.** Minecraft before 1.20.5 ships with Java 17, so `java_version=17`: the toolchain, the
  `JAVA_17` mixin level, and `"java": ">=17"` in `fabric.mod.json`. A single Java 21 class would crash
  for anyone on the Java 17 these versions come with. `tools/audit_release.py` checks every class.
- **The advancement icon is `{"item": ...}`, not `{"id": ...}`.** Item stacks in JSON changed shape
  in 1.20.5, and the wrong key fails to parse, which drops the advancement.
- **`FarlandsModPack` uses the 1.20.2 – 1.20.4 pack API:** `Pack.create(...)` with a `Pack.Info` and
  `PathResourcesSupplier(path, true)`. `PackLocationInfo` and `PackSelectionConfig` only arrive in
  1.20.5. `tools/verify_pack_api.py` knows all three eras of this API and checks the right one per
  version.

```bash
./gradlew build -Pminecraft_version=1.20.2 -Pminecraft_version_range=1.20.2 \
  -Pmod_version=0.4.0+mc1.20.2-fabric
python scripts/verify_artifact.py
```

The three versions compile to byte-identical classes (`tools/compare_jars.py`) but ship as one jar each.
1.20 and 1.20.1 predate `AdvancementHolder` and use yet another pack API, so they live in
`farlands-reforged-fabric-1.20.1`.
