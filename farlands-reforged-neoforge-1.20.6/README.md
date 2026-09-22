# Farlands Reforged — NeoForge 1.20.5 / 1.20.6

NeoForge build for **Minecraft 1.20.5 and 1.20.6**. It is a copy of `farlands-reforged-neoforge-1.21`,
and every difference below was found by checking a real artifact, not assumed:

- **`new ResourceLocation(namespace, path)`.** `ResourceLocation.fromNamespaceAndPath` only exists from 1.21.
- **`data/farlandsreforged/advancements/`, plural.** Minecraft 1.21 renamed the data-pack folders to the
  singular, and 1.20.x reads only the plural one. The wrong folder fails silently: the advancement just
  never registers.
- **`loader_version_range=[3,)`.** NeoForge 20.5 and 20.6 ship FancyModLoader 3.0.x (3.0.18 through 3.0.45),
  while 21.x ships 4.x. With the 1.21 project's `[4,)`, NeoForge would refuse to load the mod at all.
- **The two `@Redirect` handlers are not `static`.** NeoForge 20.x bundles Fabric's Mixin fork at
  0.13.4, which is Mixin 0.8.5. It rejects a static handler inside an instance method
  (*"'static' modifier of handler method does not match target"*), and the server dies during bootstrap.
  NeoForge 21.0 moved to Mixin 0.8.6, which allows it. That's why the 1.21+ projects can keep theirs static.

## Build

```bash
./gradlew build
python scripts/verify_artifact.py
```

`gradle.properties` targets 1.20.6 on NeoForge 20.6.141, and the jar accepts `[20.6.0,20.7)`.

## 1.20.5 is a retargeted copy of the 1.20.6 jar

NeoForge 1.20.5 never left beta (20.5.0-beta … 20.5.21-beta), and ModDevGradle cannot build against
it: those betas were never published with the `neoforge-moddev-bundle` variant it needs. So the 1.20.5
jar is the 1.20.6 build with its metadata rewritten by `tools/retarget_jar.py`:

```bash
python tools/retarget_jar.py --neoforge farlandsreforged-V+mc1.20.6-neoforge.jar \
  farlandsreforged-V+mc1.20.5-neoforge.jar --mod-version V+mc1.20.5-neoforge \
  --minecraft '[1.20.5]' --loader '[20.5.14-beta,20.6)'
```

Three things make that sound:
- The Fabric 1.20.5 and 1.20.6 builds compile to byte-identical classes, so no Minecraft API this mod
  touches differs between the two.
- Every NeoForge class the sources use is in the 20.5 universal jar, **from 20.5.14-beta on**.
  `PlayerTickEvent.Post` does not exist in 20.5.0 … 20.5.13-beta, which is why the jar declares that
  floor.
- It is tested on a real NeoForge 20.5.14-beta server.
