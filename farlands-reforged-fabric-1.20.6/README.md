# Farlands Reforged — Fabric 1.20.5 / 1.20.6

Fabric build for **Minecraft 1.20.5 and 1.20.6**. It is a copy of `farlands-reforged-fabric-1.21` with
two changes, both outside the Far Lands mechanisms themselves:

- `FarlandsEvents` builds its id with `new ResourceLocation(namespace, path)`.
  `ResourceLocation.fromNamespaceAndPath` only exists from 1.21.
- The advancement lives in `data/farlandsreforged/advancements/` (plural). Minecraft 1.21 renamed the
  data-pack folders to the singular, and 1.20.x reads only the plural one. The jar would not fail
  loudly with the wrong folder. The server boots, the terrain is perfect, and the advancement never
  registers.

Every mixin target, `@Shadow` field and `@Redirect` call site is present in both versions with the same
signature (`tools/check_targets.py`, `tools/verify_injections.py`), and so is every type the data-pack
fix touches (`tools/verify_pack_api.py`). It builds on **Java 21**, which 1.20.5 already requires.

## Build

`gradle.properties` targets 1.20.6. 1.20.5 is a real build of this same project:

```bash
./gradlew build -Pminecraft_version=1.20.5 -Pminecraft_version_range=1.20.5 \
  -Pmod_version=0.4.0+mc1.20.5-fabric
python scripts/verify_artifact.py
```

The 1.20.5 and 1.20.6 builds compile to byte-identical classes (`tools/compare_jars.py`). They still ship
as separate jars, one per version, like the rest of the release.

## Why static `@Redirect` handlers are fine here, but not on Forge or NeoForge

`BlendedNoiseMixin` and `ImprovedNoiseMixin` declare their handlers `static` inside instance methods.
Mixin before 0.8.6 rejects that, and Forge 1.20.6 and NeoForge 20.x both bundle 0.8.5, so their
1.20.6 projects make the handlers non-static. Every Fabric Loader this jar accepts (`>=0.16.0`)
bundles Mixin 0.8.7, which allows it.

`PackRepositoryMixin` works exactly as in the 1.21 project. See that project's README for why it exists
and how to verify it: `/datapack list` on a real server must name `farlandsreforged`.
