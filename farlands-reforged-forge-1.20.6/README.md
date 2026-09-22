# Farlands Reforged — Forge 1.20.6

Forge build for **Minecraft 1.20.6** (Forge 50). Forge never shipped a 1.20.5, just as it skipped 1.21.2.

It is a copy of `farlands-reforged-forge-1.21`, and everything that project's README says about ForgeGradle 6,
Gradle needing Java 21, official names at runtime (no `reobf`, no refmap, `remap = false`) and the no-arg
mod constructor applies here unchanged. Forge 50 runs on official names too: its installer remaps
Minecraft with Mojang's mappings (`ForgeAutoRenamingTool --names {MOJMAPS} --reverse`), exactly as 51 does.

```bash
JAVA_HOME=/path/to/jdk-21 ./gradlew build
python scripts/verify_artifact.py
```

## What differs from the 1.21 project

- **`new ResourceLocation(namespace, path)`.** `ResourceLocation.fromNamespaceAndPath` only exists from 1.21.
- **`data/farlandsreforged/advancements/`, plural.** Minecraft 1.21 renamed the data-pack folders to the
  singular, and 1.20.x reads only the plural one.
- **`pack.mcmeta` is `pack_format` 41 with `supported_formats` 32-41.** 1.20.6 is data pack 41 and
  resource pack 32, read out of the vanilla jar's `version.json`.
- **Every Forge 1.20.6 build bundles Mixin 0.8.5**, from 50.0.0 through 50.2.10 (read out of each
  installer's `version.json`). There is no newer build to set as a floor, as 51.0.23 was for 1.21, so
  the mod has to live with it. That causes two changes:
  - `farlandsreforged.mixins.json` declares **`JAVA_17`**. Mixin 0.8.5's `CompatibilityLevel` enum
    stops there, and `JAVA_21` kills the server during bootstrap. The classes themselves are still
    Java 21.
  - The two `@Redirect` handlers in `BlendedNoiseMixin` and `ImprovedNoiseMixin` are **not `static`**.
    Mixin 0.8.5 rejects a static handler inside an instance method:
    *"'static' modifier of handler method does not match target in BlendedNoise"*.

`scripts/verify_artifact.py` checks both, and `tools/audit_release.py` checks them for every pre-1.21
Forge jar in a release.

## Testing it needs Java 21

A Forge 50 server launched on Java 25 dies before loading any mod: its ASM cannot read the JDK's own
classes (*"Unsupported class file major version 69"*). That looks exactly like a broken mod.
`tools/modded_server_test.py` now always picks Java 21 for Minecraft 1.x.
